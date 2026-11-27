import 'dart:convert';
import 'dart:io';

class RadioSelection {
  const RadioSelection({this.model, this.port});

  final String? model;
  final String? port;
}

class RadioSelectionStore {
  RadioSelectionStore({String? path}) : _path = path ?? _defaultPath();

  final String _path;

  /// Reads the last selected radio model and port; null when missing or unreadable.
  Future<RadioSelection?> load() async {
    final file = File(_path);
    if (!await file.exists()) return null;
    try {
      final data = jsonDecode(await file.readAsString()) as Map;
      final modelValue = data['model'];
      final portValue = data['port'];
      return RadioSelection(
        model: modelValue is String ? modelValue : null,
        port: portValue is String ? portValue : null,
      );
    } on FormatException {
      return null;
    } on FileSystemException {
      return null;
    }
  }

  /// Remembers the selected radio model and port for the next launch.
  Future<void> save(RadioSelection selection) async {
    final file = File(_path);
    await file.parent.create(recursive: true);
    await file.writeAsString(
      jsonEncode({
        'version': 1,
        'model': selection.model,
        'port': selection.port,
      }),
      flush: true,
    );
  }

  /// Settings file in the per-user app data folder for this platform.
  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/radio-selection.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\radio-selection.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/radio-selection.json';
  }
}
