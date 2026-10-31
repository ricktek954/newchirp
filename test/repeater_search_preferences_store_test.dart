import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/repeater_search_preferences_store.dart';

void main() {
  test('RepeaterBook optional filters default off and persist', () async {
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-repeater-preferences-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final path = '${directory.path}/preferences.json';
    final defaults = await RepeaterSearchPreferencesStore(path: path).load();

    expect(defaults.openOnly, isFalse);
    expect(defaults.fmOnly, isFalse);

    await RepeaterSearchPreferencesStore(
      path: path,
    ).save(const RepeaterSearchPreferences(openOnly: true, fmOnly: false));
    final restored = await RepeaterSearchPreferencesStore(path: path).load();

    expect(restored.openOnly, isTrue);
    expect(restored.fmOnly, isFalse);
  });
}
