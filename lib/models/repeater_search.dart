import 'radio_channel.dart';

enum RepeaterSortOrder { source, city, county }

List<RepeaterSearchResult> sortRepeaterResults(
  Iterable<RepeaterSearchResult> results,
  RepeaterSortOrder order,
) {
  final sorted = results.toList();
  if (order == RepeaterSortOrder.source) return sorted;
  int by(String left, String right) =>
      left.toLowerCase().compareTo(right.toLowerCase());
  sorted.sort((left, right) {
    final primary = switch (order) {
      RepeaterSortOrder.city => by(left.city, right.city),
      RepeaterSortOrder.county => by(left.county, right.county),
      RepeaterSortOrder.source => 0,
    };
    if (primary != 0) return primary;
    final secondary = switch (order) {
      RepeaterSortOrder.city => by(left.county, right.county),
      RepeaterSortOrder.county => by(left.city, right.city),
      RepeaterSortOrder.source => 0,
    };
    if (secondary != 0) return secondary;
    final callsign = by(left.callsign, right.callsign);
    if (callsign != 0) return callsign;
    return left.channel.frequency.compareTo(right.channel.frequency);
  });
  return sorted;
}

List<RepeaterSearchResult> filterRepeaterResults(
  Iterable<RepeaterSearchResult> results,
  String query,
) {
  final terms = query
      .trim()
      .toLowerCase()
      .split(RegExp(r'\s+'))
      .where((term) => term.isNotEmpty)
      .toList();
  if (terms.isEmpty) return results.toList();
  return results.where((result) {
    final haystack = [
      result.service,
      result.callsign,
      result.city,
      result.county,
      result.state,
      result.use,
      result.channel.name,
      result.channel.comment,
      result.channel.mode,
      result.channel.tone,
      result.channel.frequency.toString(),
    ].join(' ').toLowerCase();
    return terms.every(haystack.contains);
  }).toList();
}

class RepeaterSearchResult {
  const RepeaterSearchResult({
    required this.channel,
    required this.callsign,
    required this.city,
    required this.county,
    required this.state,
    required this.use,
    required this.service,
    this.latitude,
    this.longitude,
    this.distanceKm,
  });

  final RadioChannel channel;
  final String callsign;
  final String city;
  final String county;
  final String state;
  final String use;
  final String service;
  final double? latitude;
  final double? longitude;
  final double? distanceKm;

  String get location => [
    city,
    county.isEmpty ? '' : '$county County',
    state,
  ].where((part) => part.isNotEmpty).join(', ');

  factory RepeaterSearchResult.fromJson(Map<String, dynamic> json) {
    return RepeaterSearchResult(
      channel: RadioChannel.fromJson(
        (json['channel'] as Map).cast<String, dynamic>(),
      ),
      callsign: '${json['callsign'] ?? ''}',
      city: '${json['city'] ?? ''}',
      county: '${json['county'] ?? ''}',
      state: '${json['state'] ?? ''}',
      use: '${json['use'] ?? ''}',
      service: '${json['service'] ?? ''}',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      distanceKm: (json['distanceKm'] as num?)?.toDouble(),
    );
  }
}

class RepeaterSearchResults {
  const RepeaterSearchResults({
    required this.source,
    required this.sourceUrl,
    required this.totalMatches,
    required this.results,
  });

  final String source;
  final String sourceUrl;
  final int totalMatches;
  final List<RepeaterSearchResult> results;

  factory RepeaterSearchResults.fromJson(Map<String, dynamic> json) {
    return RepeaterSearchResults(
      source: '${json['source'] ?? 'RepeaterBook'}',
      sourceUrl: '${json['sourceUrl'] ?? 'https://repeaterbook.com'}',
      totalMatches: (json['totalMatches'] as num?)?.toInt() ?? 0,
      results: (json['results'] as List? ?? const [])
          .map(
            (item) => RepeaterSearchResult.fromJson(
              (item as Map).cast<String, dynamic>(),
            ),
          )
          .toList(),
    );
  }
}
