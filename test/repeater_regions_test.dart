import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/repeater_regions.dart';

void main() {
  test('includes RepeaterBook country and major regional datasets', () {
    expect(repeaterCountries, hasLength(103));
    expect(repeaterCountries, containsAll(['Canada', 'Germany', 'Japan']));
    expect(repeaterCountryChoices.take(3), [
      'United States',
      'Canada',
      'Mexico',
    ]);
    expect(repeaterCountryChoices, hasLength(103));
    expect(repeaterRegionsForCountry('United States'), contains('New York'));
    expect(repeaterRegionsForCountry('Canada'), contains('Ontario'));
    expect(repeaterRegionsForCountry('Mexico'), contains('Jalisco'));
    expect(repeaterRegionsForCountry('Germany'), ['All']);
  });

  test('only the United States exposes GMRS search', () {
    expect(repeaterCountrySupportsGmrs('United States'), isTrue);
    expect(repeaterCountrySupportsGmrs('Canada'), isFalse);
    expect(repeaterCountrySupportsGmrs('Germany'), isFalse);
  });
}
