import 'dart:convert';
import 'dart:io';

/// Remembers whether the Channel Library file-save warning should stay hidden.
class FileSaveWarningStore {
  FileSaveWarningStore({String? path}) : _path = path ?? _defaultPath();

  final String _path;

  /// True only when the person checked "Do not show me this message again"
  /// and then chose OK.
  Future<bool> isHidden() async {
    final file = File(_path);
    if (!await file.exists()) return false;
    try {
      final data = jsonDecode(await file.readAsString());
      if (data is! Map) return false;
      return data['hideFileSaveWarning'] == true;
    } on FormatException {
      return false;
    } on FileSystemException {
      return false;
    }
  }

  /// Records "don't show this again" for the file-save warning.
  Future<void> hide() async {
    final file = File(_path);
    await file.parent.create(recursive: true);
    await file.writeAsString(
      jsonEncode({'version': 1, 'hideFileSaveWarning': true}),
      flush: true,
    );
  }

  /// Settings file in the per-user app data folder for this platform.
  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/file-save-warning.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\file-save-warning.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/file-save-warning.json';
  }
}
