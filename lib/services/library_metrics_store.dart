import 'dart:convert';
import 'dart:io';

/// Remembers whether the Channel Library summary cards are collapsed.
///
/// Collapsing them gives the channel table more rows on small screens
/// (2026-11-20 UV-32 owner request).
class LibraryMetricsStore {
  LibraryMetricsStore({String? path}) : _path = path ?? _defaultPath();

  final String _path;

  /// Whether the library metrics panel was left collapsed (false if unknown).
  Future<bool> isCollapsed() async {
    final file = File(_path);
    try {
      if (!await file.exists()) return false;
      final data = jsonDecode(await file.readAsString());
      return data is Map && data['collapsed'] == true;
    } on FormatException {
      return false;
    } on FileSystemException {
      return false;
    }
  }

  /// Remembers whether the library metrics panel is collapsed. Errors are ignored.
  Future<void> setCollapsed(bool collapsed) async {
    try {
      final file = File(_path);
      await file.parent.create(recursive: true);
      await file.writeAsString(
        jsonEncode({'version': 1, 'collapsed': collapsed}),
        flush: true,
      );
    } on FileSystemException {
      // A preference that cannot be saved must never interrupt the app.
    }
  }

  /// Settings file in the per-user app data folder for this platform.
  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/library-metrics.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\library-metrics.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/library-metrics.json';
  }
}
