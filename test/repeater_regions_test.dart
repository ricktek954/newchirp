import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/repeater_counties.dart';
import 'package:newchirp/models/repeater_regions.dart';

void main() {
  test('bundled county reference covers every state and Puerto Rico', () {
    expect(repeaterUsCountiesByState, hasLength(52));
    expect(repeaterUsCountiesByState['Florida'], hasLength(67));
    expect(repeaterUsCountiesByState['Texas'], hasLength(254));
    expect(repeaterUsCountiesByState['Delaware'], hasLength(3));
    expect(repeaterUsCountiesByState['Puerto Rico'], isNotEmpty);
  });

  test('Florida county picker includes Broward without loaded results', () {
    final counties = repeaterCountiesForRegion(
      'United States',
      'Florida',
      const [],
    );

    expect(counties, contains('Broward'));
    expect(counties, contains('Miami-Dade'));
    expect(counties, contains('Palm Beach'));
    expect(counties, isNot(contains('Broward County')));
  });

  test('loaded county metadata is normalized and merged', () {
    final counties = repeaterCountiesForRegion(
      'United States',
      'Florida',
      const ['BROWARD', 'Broward County', 'New Repeater County'],
    );

    expect(counties.where((county) => county == 'Broward'), hasLength(1));
    expect(counties, contains('New Repeater'));
  });

  test('non-US regions retain counties supplied by their source', () {
    expect(
      repeaterCountiesForRegion('Canada', 'Ontario', const ['Toronto', 'York']),
      ['Toronto', 'York'],
    );
  });
}
