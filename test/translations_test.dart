import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _arb(String code) =>
    jsonDecode(File('lib/l10n/app_$code.arb').readAsStringSync())
        as Map<String, dynamic>;

Set<String> _placeholders(String message) =>
    RegExp(r'\{(\w+)[,}]').allMatches(message).map((m) => m[1]!).toSet();

void main() {
  test(
    'Spanish and French translate every message with the same placeholders',
    () {
      final english = _arb('en');
      final keys = english.keys.where((key) => !key.startsWith('@')).toSet();
      for (final code in ['es', 'fr']) {
        final other = _arb(code);
        final otherKeys = other.keys
            .where((key) => !key.startsWith('@'))
            .toSet();
        expect(keys.difference(otherKeys), isEmpty, reason: '$code is missing');
        expect(otherKeys.difference(keys), isEmpty, reason: '$code has extras');
        for (final key in keys.where((key) => key != '@@locale')) {
          expect(
            _placeholders(other[key] as String),
            _placeholders(english[key] as String),
            reason: '$code $key placeholders',
          );
        }
      }
    },
  );
}
