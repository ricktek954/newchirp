import 'package:flutter/material.dart';

import '../models/radio_channel.dart';
import '../models/radio_mapping.dart';

class RadioMappingDialog extends StatefulWidget {
  const RadioMappingDialog({
    super.key,
    required this.models,
    required this.channels,
    required this.radioName,
  });

  final List<RadioMappingModel> models;
  final List<RadioChannel> channels;
  final String radioName;

  @override
  State<RadioMappingDialog> createState() => _RadioMappingDialogState();
}

class _RadioMappingDialogState extends State<RadioMappingDialog> {
  late List<RadioMappingModel> _models;
  int _modelIndex = 0;
  int _mappingIndex = 0;
  String _query = '';
  String? _error;
  final _nameController = TextEditingController();
  final _searchController = TextEditingController();

  RadioMappingModel get _model => _models[_modelIndex];

  RadioMappingEntry? get _mapping {
    if (_model.mappings.isEmpty ||
        _mappingIndex < 0 ||
        _mappingIndex >= _model.mappings.length) {
      return null;
    }
    return _model.mappings[_mappingIndex];
  }

  @override
  void initState() {
    super.initState();
    _models = widget.models
        .map(
          (model) => model.copyWith(
            mappings: model.mappings
                .map(
                  (mapping) => mapping.copyWith(
                    channelLocations: List.of(mapping.channelLocations),
                  ),
                )
                .toList(),
          ),
        )
        .toList();
    _selectInitialMapping();
  }

  void _selectInitialMapping() {
    final mapping = _mapping;
    if (mapping != null) _nameController.text = mapping.name;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _selectModel(int index) {
    setState(() {
      _modelIndex = index;
      _mappingIndex = 0;
      _error = null;
      _query = '';
      _searchController.clear();
      final mapping = _mapping;
      _nameController.text = mapping?.name ?? '';
    });
  }

  void _selectMapping(int index) {
    setState(() {
      _mappingIndex = index;
      _error = null;
      final mapping = _mapping;
      _nameController.text = mapping?.name ?? '';
    });
  }

  void _replaceMapping(RadioMappingEntry updated) {
    final mappings = List<RadioMappingEntry>.of(_model.mappings);
    mappings[_mappingIndex] = updated;
    final models = List<RadioMappingModel>.of(_models);
    models[_modelIndex] = _model.copyWith(mappings: mappings);
    setState(() {
      _models = models;
      _error = null;
    });
  }

  void _renameMapping(String value) {
    final mapping = _mapping;
    if (mapping == null) return;
    _replaceMapping(mapping.copyWith(name: value));
  }

  void _setMembership(int location, bool selected) {
    final mapping = _mapping;
    if (mapping == null || !_model.editable) return;
    final locations = List<int>.of(mapping.channelLocations);
    if (selected) {
      if (!locations.contains(location)) locations.add(location);
    } else {
      locations.remove(location);
    }

    var mappings = List<RadioMappingEntry>.of(_model.mappings);
    if (selected && !_model.multiple) {
      for (var index = 0; index < mappings.length; index++) {
        if (index == _mappingIndex) continue;
        final other = mappings[index];
        if (other.channelLocations.contains(location)) {
          mappings[index] = other.copyWith(
            channelLocations: other.channelLocations
                .where((value) => value != location)
                .toList(),
          );
        }
      }
    }
    mappings[_mappingIndex] = mapping.copyWith(channelLocations: locations);
    final models = List<RadioMappingModel>.of(_models);
    models[_modelIndex] = _model.copyWith(mappings: mappings);
    setState(() {
      _models = models;
      _error = null;
    });
  }

  void _save() {
    for (final model in _models) {
      for (final mapping in model.mappings) {
        if (mapping.name.trim().isEmpty &&
            mapping.channelLocations.isNotEmpty) {
          setState(() {
            _error =
                'Give every ${model.name.toLowerCase()} entry a name before '
                'saving.';
          });
          return;
        }
      }
    }
    Navigator.pop(context, _models);
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final available = MediaQuery.sizeOf(context);
    final dialogWidth = (available.width - 80).clamp(360.0, 940.0).toDouble();
    final dialogHeight = (available.height - 80).clamp(320.0, 700.0).toDouble();
    return Dialog(
      clipBehavior: Clip.antiAlias,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 980, maxHeight: 760),
        child: SizedBox(
          width: dialogWidth,
          height: dialogHeight,
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 18, 12, 14),
                child: Row(
                  children: [
                    Icon(
                      Icons.account_tree_outlined,
                      color: colorScheme.primary,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Banks and zones',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          Text(
                            widget.radioName,
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: () => Navigator.pop(context),
                      tooltip: 'Close',
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              if (_models.length > 1)
                Padding(
                  padding: const EdgeInsets.fromLTRB(22, 12, 22, 0),
                  child: DropdownButtonFormField<int>(
                    initialValue: _modelIndex,
                    decoration: const InputDecoration(
                      labelText: 'Type',
                      isDense: true,
                    ),
                    items: [
                      for (var index = 0; index < _models.length; index++)
                        DropdownMenuItem(
                          value: index,
                          child: Text(_models[index].name),
                        ),
                    ],
                    onChanged: (value) {
                      if (value != null) _selectModel(value);
                    },
                  ),
                ),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SizedBox(
                      width: 270,
                      child: Column(
                        children: [
                          Padding(
                            padding: const EdgeInsets.fromLTRB(18, 16, 18, 8),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    _model.name,
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleSmall,
                                  ),
                                ),
                                Text(
                                  '${_model.mappings.length}',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ),
                          Expanded(
                            child: ListView.builder(
                              padding: const EdgeInsets.fromLTRB(10, 0, 10, 12),
                              itemCount: _model.mappings.length,
                              itemBuilder: (context, index) {
                                final mapping = _model.mappings[index];
                                return ListTile(
                                  selected: index == _mappingIndex,
                                  selectedTileColor: colorScheme
                                      .primaryContainer
                                      .withValues(alpha: 0.45),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(9),
                                  ),
                                  leading: Icon(
                                    mapping.channelLocations.isEmpty
                                        ? Icons.add_box_outlined
                                        : Icons.folder_outlined,
                                  ),
                                  title: Text(
                                    mapping.name,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  subtitle: Text(
                                    mapping.channelLocations.isEmpty
                                        ? 'Add a channel to create'
                                        : '${mapping.channelLocations.length} channels',
                                  ),
                                  onTap: () => _selectMapping(index),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                    const VerticalDivider(width: 1),
                    Expanded(
                      child: _mapping == null
                          ? const Center(
                              child: Text(
                                'This radio does not expose editable banks.',
                              ),
                            )
                          : _buildMappingEditor(context),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 12, 18, 12),
                child: Row(
                  children: [
                    if (!_model.editable)
                      const Expanded(
                        child: Text(
                          'These banks are fixed by the radio and are shown '
                          'for reference.',
                        ),
                      )
                    else
                      Expanded(
                        child: Text(
                          _error ??
                              (_error == null && _model.multiple
                                  ? 'A channel may belong to more than one entry.'
                                  : 'A channel can belong to one entry.'),
                          style: TextStyle(
                            color: _error == null
                                ? Theme.of(context).colorScheme.onSurfaceVariant
                                : Theme.of(context).colorScheme.error,
                          ),
                        ),
                      ),
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Cancel'),
                    ),
                    const SizedBox(width: 8),
                    FilledButton(
                      key: const ValueKey('apply-radio-mappings'),
                      onPressed: _save,
                      child: const Text('Use these changes'),
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

  Widget _buildMappingEditor(BuildContext context) {
    final mapping = _mapping!;
    final channels = [...widget.channels]
      ..sort((left, right) => left.location.compareTo(right.location));
    final needle = _query.trim().toLowerCase();
    final filtered = channels.where((channel) {
      if (needle.isEmpty) return true;
      return channel.location.toString().contains(needle) ||
          channel.name.toLowerCase().contains(needle) ||
          channel.frequency.toString().contains(needle);
    }).toList();
    final canEditName = _model.editable && mapping.nameEditable;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            key: const ValueKey('radio-mapping-name'),
            controller: _nameController,
            enabled: canEditName,
            maxLength: 32,
            onChanged: _renameMapping,
            decoration: InputDecoration(
              labelText: 'Name',
              helperText: mapping.channelLocations.isEmpty
                  ? 'This empty entry is the radio’s spare bank or zone. '
                        'Add a channel to create it.'
                  : '${mapping.channelLocations.length} channels selected',
            ),
          ),
          const SizedBox(height: 6),
          TextField(
            key: const ValueKey('radio-mapping-channel-search'),
            controller: _searchController,
            onChanged: (value) => setState(() => _query = value),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              labelText: 'Find a channel',
              isDense: true,
            ),
          ),
          const SizedBox(height: 10),
          Expanded(
            child: Card(
              clipBehavior: Clip.antiAlias,
              child: filtered.isEmpty
                  ? const Center(child: Text('No matching channels'))
                  : ListView.builder(
                      itemCount: filtered.length,
                      itemBuilder: (context, index) {
                        final channel = filtered[index];
                        final selected = mapping.channelLocations.contains(
                          channel.location,
                        );
                        final detail = channel.name.isEmpty
                            ? '${channel.frequency.toStringAsFixed(4)} MHz'
                            : '${channel.name} • '
                                  '${channel.frequency.toStringAsFixed(4)} MHz';
                        return CheckboxListTile(
                          key: ValueKey(
                            'radio-mapping-channel-${channel.location}',
                          ),
                          dense: true,
                          value: selected,
                          onChanged: _model.editable
                              ? (value) => _setMembership(
                                  channel.location,
                                  value ?? false,
                                )
                              : null,
                          title: Text(
                            'Channel ${channel.location}',
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(
                            detail,
                            overflow: TextOverflow.ellipsis,
                          ),
                          controlAffinity: ListTileControlAffinity.leading,
                        );
                      },
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
