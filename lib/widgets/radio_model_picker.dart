import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

const int _maxVisibleRadioModels = 100;
const double _optionHeight = 48;

String displayRadioModelName(String model) => model.replaceAll('_', ' ');

class _RadioModelCandidate {
  _RadioModelCandidate(this.model)
    : foldedLabel = model.replaceAll('_', ' ').toLowerCase(),
      compactLabel = model
          .replaceAll('_', ' ')
          .toLowerCase()
          .replaceAll(RegExp(r'[\s_-]+'), '');

  final String model;
  final String foldedLabel;
  final String compactLabel;
}

class _RadioModelMatches {
  const _RadioModelMatches(this.count, this.visible);

  final int count;
  final List<String> visible;
}

class RadioModelPicker extends StatefulWidget {
  const RadioModelPicker({
    super.key,
    required this.models,
    required this.selectedModel,
    required this.onSelected,
    this.enabled = true,
  });

  final List<String> models;
  final String? selectedModel;
  final ValueChanged<String> onSelected;
  final bool enabled;

  @override
  State<RadioModelPicker> createState() => _RadioModelPickerState();
}

class _RadioModelPickerState extends State<RadioModelPicker> {
  late final TextEditingController _controller;
  late final FocusNode _focusNode;
  late final ValueNotifier<String> _query;
  late final ScrollController _optionsScrollController;
  List<_RadioModelCandidate> _candidates = const [];
  String? _cachedQuery;
  _RadioModelMatches? _cachedMatches;

  @override
  void initState() {
    super.initState();
    _query = ValueNotifier(_selectedLabel);
    _candidates = _buildCandidates();
    _controller = TextEditingController(text: _query.value);
    _optionsScrollController = ScrollController();
    _focusNode = FocusNode(debugLabel: 'Radio model type-ahead')
      ..addListener(_handleFocusChange);
  }

  @override
  void didUpdateWidget(RadioModelPicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!listEquals(oldWidget.models, widget.models)) {
      _candidates = _buildCandidates();
      _cachedQuery = null;
      _cachedMatches = null;
    }
    if (oldWidget.selectedModel != widget.selectedModel) {
      final nextQuery = _selectedLabel;
      if (!_focusNode.hasFocus || _query.value != nextQuery) {
        _query.value = nextQuery;
        _setControllerText(nextQuery);
      }
    }
  }

  @override
  void dispose() {
    _focusNode
      ..removeListener(_handleFocusChange)
      ..dispose();
    _query.dispose();
    _optionsScrollController.dispose();
    _controller.dispose();
    super.dispose();
  }

  String get _selectedLabel {
    final selectedModel = widget.selectedModel;
    return selectedModel == null ? '' : displayRadioModelName(selectedModel);
  }

  List<_RadioModelCandidate> _buildCandidates() =>
      widget.models.map(_RadioModelCandidate.new).toList(growable: false);

  void _setControllerText(String value) {
    _controller.value = TextEditingValue(
      text: value,
      selection: TextSelection.collapsed(offset: value.length),
    );
  }

  void _handleFocusChange() {
    if (!mounted) return;
    if (_focusNode.hasFocus) {
      setState(() {});
      return;
    }

    // A dismissed partial search must not look like a selected radio.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted ||
          _focusNode.hasFocus ||
          _controller.text == _selectedLabel) {
        if (mounted) setState(() {});
        return;
      }
      _query.value = _selectedLabel;
      _setControllerText(_selectedLabel);
      setState(() {});
    });
  }

  void _handleSelected(String model) {
    final label = displayRadioModelName(model);
    _query.value = label;
    _setControllerText(label);
    widget.onSelected(model);
  }

  _RadioModelMatches _matchesForQuery(String query) {
    final foldedQuery = query.trim().toLowerCase();
    if (_cachedQuery == foldedQuery && _cachedMatches != null) {
      return _cachedMatches!;
    }

    final terms = foldedQuery
        .split(RegExp(r'\s+'))
        .where((term) => term.isNotEmpty)
        .toList(growable: false);
    final compactQuery = foldedQuery.replaceAll(RegExp(r'[\s_-]+'), '');
    var count = 0;
    final visible = <String>[];

    for (final candidate in _candidates) {
      final matches =
          foldedQuery.isEmpty ||
          candidate.foldedLabel.contains(foldedQuery) ||
          terms.every(candidate.foldedLabel.contains) ||
          (compactQuery.isNotEmpty &&
              candidate.compactLabel.contains(compactQuery));
      if (!matches) continue;
      count++;
      if (visible.length < _maxVisibleRadioModels) {
        visible.add(candidate.model);
      }
    }

    final result = _RadioModelMatches(count, List.unmodifiable(visible));
    _cachedQuery = foldedQuery;
    _cachedMatches = result;
    return result;
  }

  String? _searchHelperFor(String query) {
    if (!_focusNode.hasFocus || query.trim().isEmpty) return null;
    final count = _matchesForQuery(query).count;
    if (count == 0) return 'No radio models match this search.';
    if (count > _maxVisibleRadioModels) {
      return 'Showing the first $_maxVisibleRadioModels of $count matches. '
          'Keep typing to narrow the list.';
    }
    return count == 1 ? '1 matching radio' : '$count matching radios';
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return RawAutocomplete<String>(
      textEditingController: _controller,
      focusNode: _focusNode,
      displayStringForOption: displayRadioModelName,
      optionsBuilder: (value) => _matchesForQuery(value.text).visible,
      onSelected: _handleSelected,
      fieldViewBuilder:
          (context, textEditingController, focusNode, onFieldSubmitted) {
            return ValueListenableBuilder<String>(
              valueListenable: _query,
              builder: (context, query, _) {
                return TextField(
                  key: const ValueKey('radio-model-typeahead-field'),
                  controller: textEditingController,
                  focusNode: focusNode,
                  enabled: widget.enabled,
                  selectAllOnFocus: true,
                  autocorrect: false,
                  enableSuggestions: false,
                  textInputAction: TextInputAction.search,
                  onChanged: (value) => _query.value = value,
                  onSubmitted: (_) => onFieldSubmitted(),
                  decoration: InputDecoration(
                    labelText:
                        'Radio model (${widget.models.length} available)',
                    hintText: 'Start typing a manufacturer or model',
                    helperText: _searchHelperFor(query),
                    prefixIcon: const Icon(Icons.settings_input_antenna),
                    suffixIcon: Icon(
                      Icons.manage_search,
                      color: widget.enabled
                          ? colorScheme.onSurfaceVariant
                          : colorScheme.onSurface.withValues(alpha: 0.38),
                    ),
                  ),
                );
              },
            );
          },
      optionsViewBuilder: (context, onSelected, options) {
        final visibleOptions = options.toList(growable: false);
        final highlightedIndex = AutocompleteHighlightedOption.of(context);
        final menuHeight = (visibleOptions.length * _optionHeight + 8)
            .clamp(0.0, 360.0)
            .toDouble();
        return Align(
          alignment: Alignment.topLeft,
          child: Material(
            key: const ValueKey('radio-model-typeahead-options'),
            elevation: 10,
            color: colorScheme.surface,
            clipBehavior: Clip.antiAlias,
            borderRadius: BorderRadius.circular(10),
            child: SizedBox(
              height: menuHeight,
              child: Scrollbar(
                controller: _optionsScrollController,
                child: ListView.builder(
                  key: const ValueKey('radio-model-typeahead-list'),
                  controller: _optionsScrollController,
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  itemExtent: _optionHeight,
                  itemCount: visibleOptions.length,
                  itemBuilder: (context, index) {
                    final model = visibleOptions[index];
                    final selected = model == widget.selectedModel;
                    return Material(
                      color: index == highlightedIndex
                          ? colorScheme.primary.withValues(alpha: 0.12)
                          : Colors.transparent,
                      child: InkWell(
                        key: ValueKey('radio-model-option-$model'),
                        onTap: () => onSelected(model),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 13,
                          ),
                          child: Row(
                            children: [
                              Expanded(
                                child: Text(
                                  displayRadioModelName(model),
                                  style: TextStyle(
                                    color: selected
                                        ? colorScheme.primary
                                        : colorScheme.onSurface,
                                    fontWeight: selected
                                        ? FontWeight.w600
                                        : FontWeight.w400,
                                  ),
                                ),
                              ),
                              if (selected)
                                Icon(
                                  Icons.check,
                                  size: 18,
                                  color: colorScheme.primary,
                                ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
