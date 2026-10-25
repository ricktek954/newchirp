import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

const int _maxVisibleRadioModels = 100;

String displayRadioModelName(String model) => model.replaceAll('_', ' ');

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
  String _query = '';

  @override
  void initState() {
    super.initState();
    _query = _selectedLabel;
    _controller = TextEditingController(text: _query);
    _focusNode = FocusNode(debugLabel: 'Radio model type-ahead')
      ..addListener(_handleFocusChange);
  }

  @override
  void didUpdateWidget(RadioModelPicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedModel != widget.selectedModel ||
        !listEquals(oldWidget.models, widget.models)) {
      final nextQuery = _selectedLabel;
      if (!_focusNode.hasFocus || _query != nextQuery) {
        _query = nextQuery;
        _setControllerText(nextQuery);
      }
    }
  }

  @override
  void dispose() {
    _focusNode
      ..removeListener(_handleFocusChange)
      ..dispose();
    _controller.dispose();
    super.dispose();
  }

  String get _selectedLabel {
    final selectedModel = widget.selectedModel;
    return selectedModel == null ? '' : displayRadioModelName(selectedModel);
  }

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
        return;
      }
      setState(() {
        _query = _selectedLabel;
        _setControllerText(_query);
      });
    });
  }

  void _handleSelected(String model) {
    final label = displayRadioModelName(model);
    setState(() {
      _query = label;
      _setControllerText(label);
    });
    widget.onSelected(model);
  }

  bool _matches(String model, String query) {
    final label = displayRadioModelName(model).toLowerCase();
    final foldedQuery = query.trim().toLowerCase();
    if (foldedQuery.isEmpty || label.contains(foldedQuery)) return true;

    final terms = foldedQuery
        .split(RegExp(r'\s+'))
        .where((term) => term.isNotEmpty);
    if (terms.every(label.contains)) return true;

    String compact(String value) => value.replaceAll(RegExp(r'[\s_-]+'), '');
    final compactQuery = compact(foldedQuery);
    return compactQuery.isNotEmpty && compact(label).contains(compactQuery);
  }

  List<String> _matchingModels(String query) => widget.models
      .where((model) => _matches(model, query))
      .take(_maxVisibleRadioModels)
      .toList(growable: false);

  int _matchingModelCount(String query) =>
      widget.models.where((model) => _matches(model, query)).length;

  String? get _searchHelper {
    if (!_focusNode.hasFocus || _query.trim().isEmpty) return null;
    final count = _matchingModelCount(_query);
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
      optionsBuilder: (value) => _matchingModels(value.text),
      onSelected: _handleSelected,
      fieldViewBuilder:
          (context, textEditingController, focusNode, onFieldSubmitted) {
            return TextField(
              key: const ValueKey('radio-model-typeahead-field'),
              controller: textEditingController,
              focusNode: focusNode,
              enabled: widget.enabled,
              selectAllOnFocus: true,
              autocorrect: false,
              enableSuggestions: false,
              textInputAction: TextInputAction.search,
              onChanged: (value) => setState(() => _query = value),
              onSubmitted: (_) => onFieldSubmitted(),
              decoration: InputDecoration(
                labelText: 'Radio model (${widget.models.length} available)',
                hintText: 'Start typing a manufacturer or model',
                helperText: _searchHelper,
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
      optionsViewBuilder: (context, onSelected, options) {
        final visibleOptions = options.toList(growable: false);
        final highlightedIndex = AutocompleteHighlightedOption.of(context);
        return Align(
          alignment: Alignment.topLeft,
          child: Material(
            key: const ValueKey('radio-model-typeahead-options'),
            elevation: 10,
            color: colorScheme.surface,
            clipBehavior: Clip.antiAlias,
            borderRadius: BorderRadius.circular(10),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 360),
              child: Scrollbar(
                child: ListView.builder(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  shrinkWrap: true,
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
