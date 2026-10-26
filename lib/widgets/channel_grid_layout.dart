import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Which channel row is highlighted. Notifies listeners with the previous
/// index still available, so only those two rows need to repaint.
class ChannelSelection extends ValueNotifier<int> {
  ChannelSelection(super.value);

  int? previous;

  void choose(int index) {
    if (value == index) return;
    previous = value;
    value = index;
  }
}

/// Live column widths. A drag writes one column without rebuilding the grid.
class ColumnWidthSlots {
  final Map<String, ValueNotifier<double>> _slots = {};

  ValueNotifier<double> slot(String id, double fallback) {
    return _slots.putIfAbsent(id, () => ValueNotifier<double>(fallback));
  }

  double read(String id, double fallback) => slot(id, fallback).value;

  void write(String id, double width) {
    final notifier = slot(id, width);
    if (notifier.value == width) return;
    notifier.value = width;
  }

  void dispose() {
    for (final notifier in _slots.values) {
      notifier.dispose();
    }
    _slots.clear();
  }
}

/// Applies a column width around [child] without rebuilding [child].
class ColumnWidthBox extends StatelessWidget {
  const ColumnWidthBox({super.key, required this.width, required this.child});

  final ValueListenable<double> width;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<double>(
      valueListenable: width,
      builder: (context, width, child) => SizedBox(width: width, child: child),
      child: child,
    );
  }
}

/// Width of the channel grid. [resize] updates the width while [child] stays
/// the same widget, so the rows are not rebuilt while a column edge is dragged.
class ChannelTableWidth extends StatefulWidget {
  const ChannelTableWidth({
    super.key,
    required this.width,
    required this.height,
    required this.holdWidth,
    required this.child,
  });

  final double width;
  final double height;
  final bool holdWidth;
  final Widget child;

  @override
  State<ChannelTableWidth> createState() => ChannelTableWidthState();
}

class ChannelTableWidthState extends State<ChannelTableWidth> {
  late double _width = widget.width;

  void resize(double width) {
    if (!mounted || _width == width) return;
    setState(() => _width = width);
  }

  @override
  void didUpdateWidget(ChannelTableWidth oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.holdWidth) return;
    if (widget.width != _width) _width = widget.width;
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(width: _width, height: widget.height, child: widget.child);
  }
}

/// Row background. Listens for selection and repaints only when this row is
/// the old or new selection. [child] is the cells and is left in place.
class ChannelRowFrame extends StatefulWidget {
  const ChannelRowFrame({
    super.key,
    required this.selection,
    required this.index,
    required this.dropTarget,
    required this.cleared,
    required this.child,
  });

  final ChannelSelection selection;
  final int index;
  final bool dropTarget;
  final bool cleared;
  final Widget child;

  @override
  State<ChannelRowFrame> createState() => ChannelRowFrameState();
}

class ChannelRowFrameState extends State<ChannelRowFrame> {
  @override
  void initState() {
    super.initState();
    widget.selection.addListener(_onSelectionChanged);
  }

  @override
  void didUpdateWidget(ChannelRowFrame oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selection != widget.selection) {
      oldWidget.selection.removeListener(_onSelectionChanged);
      widget.selection.addListener(_onSelectionChanged);
    }
  }

  @override
  void dispose() {
    widget.selection.removeListener(_onSelectionChanged);
    super.dispose();
  }

  void _onSelectionChanged() {
    final selection = widget.selection;
    final involved =
        selection.value == widget.index || selection.previous == widget.index;
    if (!involved || !mounted) return;
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final selected = widget.selection.value == widget.index;
    final color = widget.dropTarget
        ? const Color(0xFFD7EAE1)
        : selected
        ? const Color(0xFFE8F3ED)
        : widget.cleared
        ? const Color(0xFFFAFAFA)
        : Colors.white;
    return Container(height: 45, color: color, child: widget.child);
  }
}
