import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/models/repeater_search.dart';

void main() {
  test('parses RepeaterBook channel and location metadata', () {
    final results = RepeaterSearchResults.fromJson({
      'source': 'RepeaterBook',
      'sourceUrl': 'https://repeaterbook.com',
      'totalMatches': 1,
      'results': [
        {
          'channel': {
            'location': 1,
            'name': 'WB2ECR',
            'frequency': 146.865,
            'duplex': '+',
            'offset': 0.6,
            'tone': 'Tone',
            'txTone': 151.4,
            'rxTone': 88.5,
            'mode': 'FM',
          },
          'callsign': 'WB2ECR',
          'city': 'Buffalo',
          'county': 'Erie',
          'state': 'New York',
          'use': 'OPEN',
          'service': 'Amateur',
          'latitude': 42.8864,
          'longitude': -78.8784,
          'distanceKm': 12.3,
        },
      ],
    });

    expect(results.totalMatches, 1);
    expect(results.results.single.channel.frequency, 146.865);
    expect(results.results.single.location, 'Buffalo, Erie County, New York');
    expect(results.results.single.distanceKm, 12.3);
    expect(results.results.single.service, 'Amateur');
    expect(results.results.single.latitude, 42.8864);
    expect(results.results.single.longitude, -78.8784);
  });

  test('sorts repeater results by city or county case-insensitively', () {
    RepeaterSearchResult result(String callsign, String city, String county) =>
        RepeaterSearchResult(
          channel: RadioChannel(location: 1, name: callsign, frequency: 146),
          callsign: callsign,
          city: city,
          county: county,
          state: 'Florida',
          use: 'OPEN',
          service: 'Amateur',
        );
    final results = [
      result('W3', 'Fort Lauderdale', 'Broward'),
      result('W1', 'Boca Raton', 'Palm Beach'),
      result('W2', 'Coral Springs', 'broward'),
    ];

    expect(
      sortRepeaterResults(
        results,
        RepeaterSortOrder.city,
      ).map((result) => result.city),
      ['Boca Raton', 'Coral Springs', 'Fort Lauderdale'],
    );
    expect(
      sortRepeaterResults(
        results,
        RepeaterSortOrder.county,
      ).map((result) => result.county.toLowerCase()),
      ['broward', 'broward', 'palm beach'],
    );
    expect(
      filterRepeaterResults(
        results,
        'broward fort',
      ).map((result) => result.callsign),
      ['W3'],
    );
  });
}
