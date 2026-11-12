import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

class WindowState {
  const WindowState({
    required this.width,
    required this.height,
    required this.x,
    required this.y,
    this.maximized = false,
  });

  final double width;
  final double height;
  final double x;
  final double y;
  final bool maximized;

  Map<String, dynamic> toJson() => {
    'width': width,
    'height': height,
    'x': x,
    'y': y,
    'maximized': maximized,
  };
}

class WindowDisplayArea {
  const WindowDisplayArea({
    required this.left,
    required this.top,
    required this.width,
    required this.height,
    required this.scaleFactor,
  });

  final double left;
  final double top;
  final double width;
  final double height;
  final double scaleFactor;
}

/// Normalize saved bounds against the current display layout.
///
/// Windows can save window rectangles under one monitor's DPI basis and then
/// restore them after the window has moved to another monitor with a different
/// scale. In that layout, center on the primary display rather than trying to
/// reinterpret a position whose coordinate space is ambiguous.
WindowState? normalizeWindowStateForDisplays({
  required WindowState? state,
  required List<WindowDisplayArea> displays,
  required WindowDisplayArea primary,
  required bool centerOnMixedScale,
}) {
  if (state == null || displays.isEmpty) return state;

  final scaleFactors = displays
      .where((display) => display.scaleFactor > 0)
      .map((display) => (display.scaleFactor * 100).round())
      .toSet();
  final mixedScale = centerOnMixedScale && scaleFactors.length > 1;
  final accessible = displays.any((display) {
    final overlapWidth =
        math.min(state.x + state.width, display.left + display.width) -
        math.max(state.x, display.left);
    final overlapHeight =
        math.min(state.y + state.height, display.top + display.height) -
        math.max(state.y, display.top);
    final titleBarReachable =
        state.y >= display.top && state.y < display.top + display.height;
    return titleBarReachable && overlapWidth >= 100 && overlapHeight >= 100;
  });
  if (!mixedScale && accessible) return state;

  final width = math.min(state.width, primary.width);
  final height = math.min(state.height, primary.height);
  return WindowState(
    width: width,
    height: height,
    x: primary.left + (primary.width - width) / 2,
    y: primary.top + (primary.height - height) / 2,
    maximized: state.maximized,
  );
}

class WindowStateStore {
  WindowStateStore({String? path}) : _path = path ?? _defaultPath();

  final String _path;

  Future<WindowState?> load() async {
    final file = File(_path);
    if (!await file.exists()) return null;
    try {
      final data = jsonDecode(await file.readAsString()) as Map;
      final width = (data['width'] as num?)?.toDouble();
      final height = (data['height'] as num?)?.toDouble();
      final x = (data['x'] as num?)?.toDouble();
      final y = (data['y'] as num?)?.toDouble();
      if (width == null || height == null || x == null || y == null) {
        return null;
      }
      if (width < 200 || width > 10000 || height < 200 || height > 10000) {
        return null;
      }
      return WindowState(
        width: width,
        height: height,
        x: x,
        y: y,
        maximized: data['maximized'] == true,
      );
    } on FormatException {
      return null;
    } on FileSystemException {
      return null;
    }
  }

  Future<void> save(WindowState state) async {
    final file = File(_path);
    await file.parent.create(recursive: true);
    await file.writeAsString(
      jsonEncode({'version': 1, ...state.toJson()}),
      flush: true,
    );
  }

  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/window-state.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\window-state.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/window-state.json';
  }
}
