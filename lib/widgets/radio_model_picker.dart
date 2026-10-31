import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

const String _allVendors = 'All manufacturers';
const String _recentVendors = 'Recent';
const int _maxRecentModels = 8;
final RegExp _querySeparators = RegExp(r'[\s_-]+');
final RegExp _queryTerms = RegExp(r'\s+');

String displayRadioModelName(String model) => model.replaceAll('_', ' ');

String _vendorSlug(String vendor) => vendor.replaceAll(' ', '_');

String _modelNameWithinVendor(String model, String vendor) {
  final prefix = '${_vendorSlug(vendor)}_';
  return model.startsWith(prefix)
      ? displayRadioModelName(model.substring(prefix.length))
      : displayRadioModelName(model);
}

class _VendorModels {
  const _VendorModels(this.vendor, this.models);

  final String vendor;
  final List<String> models;
}

List<_VendorModels> _groupModels(
  List<String> models,
  Map<String, List<String>> vendorModels,
) {
  final available = models.toSet();
  if (vendorModels.isNotEmpty) {
    final groups = <_VendorModels>[];
    final grouped = <String>{};
    for (final entry in vendorModels.entries) {
      final groupedModels =
          entry.value.where(available.contains).toSet().toList()..sort();
      if (groupedModels.isEmpty) continue;
      groups.add(_VendorModels(entry.key, groupedModels));
      grouped.addAll(groupedModels);
    }
    final remaining = available.difference(grouped).toList()..sort();
    if (remaining.isNotEmpty) {
      groups.add(_VendorModels('Other', remaining));
    }
    groups.sort(
      (a, b) => a.vendor.toLowerCase().compareTo(b.vendor.toLowerCase()),
    );
    return groups;
  }

  final inferred = <String, List<String>>{};
  for (final model in models) {
    final separator = model.indexOf('_');
    final vendor = separator < 0 ? 'Other' : model.substring(0, separator);
    inferred.putIfAbsent(vendor, () => []).add(model);
  }
  final groups = [
    for (final entry in inferred.entries)
      _VendorModels(
        entry.key.replaceAll('_', ' '),
        entry.value.toList()..sort(),
      ),
  ]..sort((a, b) => a.vendor.toLowerCase().compareTo(b.vendor.toLowerCase()));
  return groups;
}

class RadioModelPicker extends StatefulWidget {
  const RadioModelPicker({
    super.key,
    required this.models,
    required this.selectedModel,
    required this.onSelected,
    this.vendorModels = const {},
    this.enabled = true,
  });

  final List<String> models;
  final Map<String, List<String>> vendorModels;
  final String? selectedModel;
  final ValueChanged<String> onSelected;
  final bool enabled;

  @override
  State<RadioModelPicker> createState() => _RadioModelPickerState();
}

class _RadioModelPickerState extends State<RadioModelPicker> {
  final List<String> _recentModels = [];

  @override
  void initState() {
    super.initState();
    _remember(widget.selectedModel);
  }

  @override
  void didUpdateWidget(RadioModelPicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedModel != widget.selectedModel) {
      _remember(widget.selectedModel);
    }
  }

  void _remember(String? model) {
    if (model == null || model.isEmpty) return;
    _recentModels
      ..remove(model)
      ..insert(0, model);
    if (_recentModels.length > _maxRecentModels) {
      _recentModels.removeRange(_maxRecentModels, _recentModels.length);
    }
  }

  Future<void> _openPicker() async {
    final selected = await showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (context) => _RadioModelDialog(
        models: widget.models,
        vendorModels: widget.vendorModels,
        selectedModel: widget.selectedModel,
        recentModels: List.unmodifiable(_recentModels),
      ),
    );
    if (selected == null || !mounted) return;
    setState(() => _remember(selected));
    widget.onSelected(selected);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final selectedModel = widget.selectedModel;
    final selectedVendor = selectedModel == null
        ? null
        : _groupModels(
            widget.models,
            widget.vendorModels,
          ).where((group) => group.models.contains(selectedModel)).firstOrNull;
    return Semantics(
      button: true,
      label: selectedModel == null
          ? 'Choose radio model'
          : 'Selected radio ${displayRadioModelName(selectedModel)}',
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          key: const ValueKey('radio-model-picker-field'),
          borderRadius: BorderRadius.circular(8),
          onTap: widget.enabled ? _openPicker : null,
          child: InputDecorator(
            isEmpty: selectedModel == null,
            decoration: InputDecoration(
              labelText: 'Radio model (${widget.models.length} available)',
              prefixIcon: const Icon(Icons.settings_input_antenna),
              suffixIcon: const Icon(Icons.arrow_drop_down),
              enabled: widget.enabled,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  selectedModel == null
                      ? 'Browse supported radios'
                      : displayRadioModelName(selectedModel),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.titleMedium,
                ),
                if (selectedVendor != null)
                  Text(
                    selectedVendor.vendor,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RadioModelDialog extends StatefulWidget {
  const _RadioModelDialog({
    required this.models,
    required this.vendorModels,
    required this.selectedModel,
    required this.recentModels,
  });

  final List<String> models;
  final Map<String, List<String>> vendorModels;
  final String? selectedModel;
  final List<String> recentModels;

  @override
  State<_RadioModelDialog> createState() => _RadioModelDialogState();
}

class _RadioModelDialogState extends State<_RadioModelDialog> {
  late final TextEditingController _searchController;
  late final FocusNode _searchFocus;
  late final List<_VendorModels> _groups;
  String? _vendor;
  String? _cachedQuery;
  String? _cachedVendor;
  List<_VendorModels>? _cachedGroups;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
    _searchFocus = FocusNode(debugLabel: 'Radio model catalog search');
    _groups = _groupModels(widget.models, widget.vendorModels);
    _vendor = _groups
        .where((group) => group.models.contains(widget.selectedModel))
        .map((group) => group.vendor)
        .firstOrNull;
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocus.dispose();
    super.dispose();
  }

  List<_VendorModels> _matchingGroups() {
    final query = _searchController.text.trim().toLowerCase();
    if (_cachedGroups != null &&
        _cachedQuery == query &&
        _cachedVendor == _vendor) {
      return _cachedGroups!;
    }

    final compactQuery = query.replaceAll(_querySeparators, '');
    final terms = query
        .split(_queryTerms)
        .where((term) => term.isNotEmpty)
        .toList(growable: false);

    Iterable<_VendorModels> source;
    if (query.isNotEmpty) {
      source = _groups;
    } else if (_vendor == _recentVendors) {
      final recentSet = widget.recentModels.toSet();
      source = [
        _VendorModels(
          _recentVendors,
          widget.recentModels.where(recentSet.contains).toList(),
        ),
      ];
    } else if (_vendor != null && _vendor != _allVendors) {
      source = _groups.where((group) => group.vendor == _vendor);
    } else {
      source = _groups;
    }

    if (query.isEmpty) {
      return _cacheGroups(query, source.toList(growable: false));
    }

    final matches = <_VendorModels>[];
    for (final group in source) {
      final models = group.models
          .where((model) {
            final haystack = '${displayRadioModelName(model)} ${group.vendor}'
                .toLowerCase();
            final compact = haystack.replaceAll(_querySeparators, '');
            return haystack.contains(query) ||
                terms.every(haystack.contains) ||
                (compactQuery.isNotEmpty && compact.contains(compactQuery));
          })
          .toList(growable: false);
      if (models.isNotEmpty) {
        matches.add(_VendorModels(group.vendor, models));
      }
    }
    return _cacheGroups(query, matches);
  }

  List<_VendorModels> _cacheGroups(String query, List<_VendorModels> groups) {
    _cachedQuery = query;
    _cachedVendor = _vendor;
    _cachedGroups = groups;
    return groups;
  }

  void _selectVendor(String? vendor) {
    setState(() {
      _vendor = vendor;
      _searchController.clear();
    });
    _searchFocus.requestFocus();
  }

  void _submitSearch() {
    final matches = _matchingGroups();
    if (matches.isEmpty || matches.first.models.isEmpty) return;
    Navigator.pop(context, matches.first.models.first);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final groups = _matchingGroups();
    final resultCount = groups.fold<int>(
      0,
      (total, group) => total + group.models.length,
    );
    return Dialog(
      key: const ValueKey('radio-model-picker-dialog'),
      insetPadding: const EdgeInsets.all(24),
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 920, maxHeight: 680),
        child: SizedBox(
          width: 900,
          height: 640,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 20, 16, 14),
                child: Row(
                  children: [
                    const Icon(Icons.settings_input_antenna, size: 28),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Choose your radio',
                            style: theme.textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            'Browse by manufacturer or search the complete '
                            'catalog.',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      tooltip: 'Close',
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
                child: TextField(
                  key: const ValueKey('radio-model-search'),
                  controller: _searchController,
                  focusNode: _searchFocus,
                  autofocus: true,
                  onChanged: (_) => setState(() {}),
                  onSubmitted: (_) => _submitSearch(),
                  decoration: InputDecoration(
                    hintText:
                        'Search by manufacturer or model, e.g. Icom ID-52',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isEmpty
                        ? null
                        : IconButton(
                            tooltip: 'Clear search',
                            onPressed: () {
                              _searchController.clear();
                              setState(() {});
                            },
                            icon: const Icon(Icons.clear),
                          ),
                  ),
                ),
              ),
              const Divider(height: 1),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SizedBox(
                      width: 224,
                      child: Material(
                        color: theme.colorScheme.surfaceContainerLow,
                        child: ListView(
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          children: [
                            if (widget.recentModels.isNotEmpty)
                              _VendorChoice(
                                key: const ValueKey(
                                  'radio-model-vendor-recent',
                                ),
                                label: _recentVendors,
                                count: widget.recentModels.length,
                                selected: _vendor == _recentVendors,
                                onTap: () => _selectVendor(_recentVendors),
                              ),
                            _VendorChoice(
                              key: const ValueKey('radio-model-vendor-all'),
                              label: _allVendors,
                              count: widget.models.length,
                              selected:
                                  _vendor == null || _vendor == _allVendors,
                              onTap: () => _selectVendor(null),
                            ),
                            const Padding(
                              padding: EdgeInsets.fromLTRB(18, 14, 18, 6),
                              child: Divider(),
                            ),
                            for (final group in _groups)
                              _VendorChoice(
                                key: ValueKey(
                                  'radio-model-vendor-${group.vendor}',
                                ),
                                label: group.vendor,
                                count: group.models.length,
                                selected: _vendor == group.vendor,
                                onTap: () => _selectVendor(group.vendor),
                              ),
                          ],
                        ),
                      ),
                    ),
                    const VerticalDivider(width: 1),
                    Expanded(
                      child: groups.isEmpty
                          ? Center(
                              child: Text(
                                'No radio models match this search.',
                                style: theme.textTheme.bodyLarge,
                              ),
                            )
                          : _ModelResultsList(
                              groups: groups,
                              selectedModel: widget.selectedModel,
                              onSelected: (model) =>
                                  Navigator.pop(context, model),
                            ),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 12, 16, 12),
                child: Row(
                  children: [
                    Text(
                      '$resultCount ${resultCount == 1 ? 'radio' : 'radios'}',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    const Spacer(),
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Cancel'),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _VendorChoice extends StatelessWidget {
  const _VendorChoice({
    super.key,
    required this.label,
    required this.count,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final int count;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 1),
      child: ListTile(
        dense: true,
        selected: selected,
        selectedTileColor: theme.colorScheme.primary.withValues(alpha: 0.12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        onTap: onTap,
        title: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
        trailing: Text(
          '$count',
          style: theme.textTheme.labelMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

class _ModelResultsList extends StatefulWidget {
  const _ModelResultsList({
    required this.groups,
    required this.selectedModel,
    required this.onSelected,
  });

  final List<_VendorModels> groups;
  final String? selectedModel;
  final ValueChanged<String> onSelected;

  @override
  State<_ModelResultsList> createState() => _ModelResultsListState();
}

class _ModelResultsListState extends State<_ModelResultsList> {
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rows = <Object>[];
    for (final group in widget.groups) {
      if (group.vendor != _recentVendors) {
        rows.add(_VendorHeading(group.vendor));
      }
      rows.addAll(
        group.models.map(
          (model) => _ModelEntry(model: model, vendor: group.vendor),
        ),
      );
    }
    return Scrollbar(
      controller: _scrollController,
      child: ListView.builder(
        key: const ValueKey('radio-model-results-list'),
        controller: _scrollController,
        primary: false,
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: rows.length,
        scrollCacheExtent: const ScrollCacheExtent.pixels(480),
        addAutomaticKeepAlives: false,
        itemBuilder: (context, index) {
          final row = rows[index];
          if (row is _VendorHeading) {
            return _SectionHeader(label: row.label);
          }
          final entry = row as _ModelEntry;
          return _ModelChoice(
            key: ValueKey('radio-model-option-${entry.model}'),
            model: entry.model,
            vendor: entry.vendor,
            selected: entry.model == widget.selectedModel,
            onTap: () => widget.onSelected(entry.model),
          );
        },
      ),
    );
  }
}

class _VendorHeading {
  const _VendorHeading(this.label);

  final String label;
}

class _ModelEntry {
  const _ModelEntry({required this.model, required this.vendor});

  final String model;
  final String vendor;
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 6),
      child: Text(
        label.toUpperCase(),
        style: theme.textTheme.labelSmall?.copyWith(
          color: theme.colorScheme.primary,
          fontWeight: FontWeight.w800,
          letterSpacing: 1.1,
        ),
      ),
    );
  }
}

class _ModelChoice extends StatelessWidget {
  const _ModelChoice({
    super.key,
    required this.model,
    required this.vendor,
    required this.selected,
    required this.onTap,
  });

  final String model;
  final String vendor;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final modelName = vendor == _recentVendors
        ? displayRadioModelName(model)
        : _modelNameWithinVendor(model, vendor);
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
      child: ListTile(
        selected: selected,
        selectedTileColor: theme.colorScheme.primary.withValues(alpha: 0.1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
        onTap: onTap,
        leading: Icon(
          selected ? Icons.check_circle : Icons.radio_outlined,
          color: selected
              ? theme.colorScheme.primary
              : theme.colorScheme.onSurfaceVariant,
        ),
        title: Text(modelName),
        subtitle: Text(vendor),
        trailing: selected
            ? Text(
                'Selected',
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w700,
                ),
              )
            : null,
      ),
    );
  }
}
