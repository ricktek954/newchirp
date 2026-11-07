import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/repeater_search_preferences_store.dart';

void main() {
  test('repeater search settings default and persist completely', () async {
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-repeater-preferences-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final path = '${directory.path}/preferences.json';
    final defaults = await RepeaterSearchPreferencesStore(path: path).load();

    expect(defaults.openOnly, isFalse);
    expect(defaults.fmOnly, isFalse);
    expect(defaults.provider, 'repeaterBook');
    expect(defaults.country, 'United States');
    expect(defaults.region, 'New York');
    expect(defaults.service, 'all');
    expect(defaults.sortOrder, 'source');
    expect(defaults.query, isEmpty);
    expect(defaults.latitude, isEmpty);
    expect(defaults.longitude, isEmpty);
    expect(defaults.radiusKm, isEmpty);
    expect(defaults.mapView, isFalse);

    await RepeaterSearchPreferencesStore(path: path).save(
      const RepeaterSearchPreferences(
        provider: 'myGmrs',
        country: 'Canada',
        region: 'Ontario',
        service: 'amateur',
        sortOrder: 'city',
        query: 'Toronto',
        latitude: '43.6532',
        longitude: '-79.3832',
        radiusKm: '75',
        openOnly: true,
        fmOnly: true,
        mapView: true,
      ),
    );
    final restored = await RepeaterSearchPreferencesStore(path: path).load();

    expect(restored.provider, 'myGmrs');
    expect(restored.country, 'Canada');
    expect(restored.region, 'Ontario');
    expect(restored.service, 'amateur');
    expect(restored.sortOrder, 'city');
    expect(restored.query, 'Toronto');
    expect(restored.latitude, '43.6532');
    expect(restored.longitude, '-79.3832');
    expect(restored.radiusKm, '75');
    expect(restored.openOnly, isTrue);
    expect(restored.fmOnly, isTrue);
    expect(restored.mapView, isTrue);
  });
}
