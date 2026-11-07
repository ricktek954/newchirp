import 'dart:convert';
import 'dart:io';

/// Search criteria remembered between repeater-directory sessions.
class RepeaterSearchPreferences {
  const RepeaterSearchPreferences({
    this.provider = 'repeaterBook',
    this.country = 'United States',
    this.region = 'New York',
    this.service = 'all',
    this.sortOrder = 'source',
    this.query = '',
    this.latitude = '',
    this.longitude = '',
    this.radiusKm = '',
    this.openOnly = false,
    this.fmOnly = false,
    this.mapView = false,
  });

  final String provider;
  final String country;
  final String region;
  final String service;
  final String sortOrder;
  final String query;
  final String latitude;
  final String longitude;
  final String radiusKm;
  final bool openOnly;
  final bool fmOnly;
  final bool mapView;

  Map<String, dynamic> toJson() => {
    'provider': provider,
    'country': country,
    'region': region,
    'service': service,
    'sortOrder': sortOrder,
    'query': query,
    'latitude': latitude,
    'longitude': longitude,
    'radiusKm': radiusKm,
    'openOnly': openOnly,
    'fmOnly': fmOnly,
    'mapView': mapView,
  };
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
        provider: data['provider'] is String
            ? data['provider'] as String
            : 'repeaterBook',
        country: data['country'] is String
            ? data['country'] as String
            : 'United States',
        region: data['region'] is String
            ? data['region'] as String
            : 'New York',
        service: data['service'] is String ? data['service'] as String : 'all',
        sortOrder: data['sortOrder'] is String
            ? data['sortOrder'] as String
            : 'source',
        query: data['query'] is String ? data['query'] as String : '',
        latitude: data['latitude'] is String ? data['latitude'] as String : '',
        longitude: data['longitude'] is String
            ? data['longitude'] as String
            : '',
        radiusKm: data['radiusKm'] is String ? data['radiusKm'] as String : '',
        openOnly: data['openOnly'] == true,
        fmOnly: data['fmOnly'] == true,
        mapView: data['mapView'] == true,
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
      jsonEncode({'version': 2, ...preferences.toJson()}),
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
