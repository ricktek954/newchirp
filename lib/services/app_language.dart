import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';

/// Interface languages. Driver instructions, radio errors and setting names
/// come from CHIRP and stay in English.
const supportedLanguageCodes = ['en', 'es', 'fr'];

/// Native names shown in the language menu, so each is readable to its
/// speakers whatever the current language.
const languageNativeNames = {
  'en': 'English',
  'es': 'Español',
  'fr': 'Français',
};

/// The chosen interface language; null follows the computer's language.
final appLocale = ValueNotifier<Locale?>(null);

Locale? localeForLanguageCode(String code) =>
    supportedLanguageCodes.contains(code) ? Locale(code) : null;

/// Remembers the language picked in the sidebar ("system" or a code).
class AppLanguageStore {
  AppLanguageStore({String? path}) : _path = path ?? _defaultPath();

  final String _path;

  Future<String> load() async {
    try {
      final file = File(_path);
      if (!await file.exists()) return 'system';
      final data = jsonDecode(await file.readAsString());
      final code = data is Map ? data['language'] : null;
      return code is String && supportedLanguageCodes.contains(code)
          ? code
          : 'system';
    } on FormatException {
      return 'system';
    } on FileSystemException {
      return 'system';
    }
  }

  Future<void> save(String code) async {
    try {
      final file = File(_path);
      await file.parent.create(recursive: true);
      await file.writeAsString(
        jsonEncode({'version': 1, 'language': code}),
        flush: true,
      );
    } on FileSystemException {
      // A preference that cannot be saved must never interrupt the app.
    }
  }

  static String _defaultPath() {
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return '$home/Library/Application Support/NewChirp/language.json';
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return '$appData\\NewChirp\\language.json';
    }
    final home = Platform.environment['HOME'] ?? '.';
    final config = Platform.environment['XDG_CONFIG_HOME'] ?? '$home/.config';
    return '$config/newchirp/language.json';
  }
}
