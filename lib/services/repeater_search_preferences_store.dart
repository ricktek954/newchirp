import 'dart:convert';
import 'dart:io';

/// Optional filters remembered between RepeaterBook searches.
class RepeaterSearchPreferences {
  const RepeaterSearchPreferences({this.openOnly = false, this.fmOnly = false});

  final bool openOnly;
  final bool fmOnly;

  Map<String, dynamic> toJson() => {'openOnly': openOnly, 'fmOnly': fmOnly};
}

class RepeaterSearchPreferencesStore {
  RepeaterSearchPreferencesStore({String? path})
    : _path = path ?? _defaultPath();

  final String _path;

  Future<RepeaterSearchPreferences> load() async {
    final file = File(_path);
    if (!await file.exists()) return const RepeaterSearchPreferences();
    try {
      final data = jsonDecode(await file.readAsString());
      if (data is! Map) return const RepeaterSearchPreferences();
      return RepeaterSearchPreferences(
        openOnly: data['openOnly'] == true,
        fmOnly: data['fmOnly'] == true,
      );
    } on FormatException {
      return const RepeaterSearchPreferences();
    } on FileSystemException {
      return const RepeaterSearchPreferences();
    }
  }

  Future<void> save(RepeaterSearchPreferences preferences) async {
    final file = File(_path);
    await file.parent.create(recursive: true);
    await file.writeAsString(
      jsonEncode({'version': 1, ...preferences.toJson()}),
      flush: true,
    );
  }

  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/'
          'repeater-search-preferences.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\repeater-search-preferences.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/repeater-search-preferences.json';
  }
}
