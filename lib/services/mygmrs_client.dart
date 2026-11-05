import 'dart:convert';
import 'dart:io';

import '../models/radio_channel.dart';
import '../models/repeater_search.dart';

const myGmrsBrokerBase = String.fromEnvironment(
  'MYGMRS_BROKER_BASE',
  defaultValue: 'https://newchirp.net',
);

abstract interface class MyGmrsService {
  bool get signedIn;

  Future<void> signIn();

  Future<void> signOut();

  Future<RepeaterSearchResults> searchRepeaters({
    required String state,
    String query = '',
    double? latitude,
    double? longitude,
    double? distanceKm,
    bool openOnly = false,
    int limit = 100,
  });
}

class MyGmrsException implements Exception {
  const MyGmrsException(this.message);

  final String message;

  @override
  String toString() => message;
}

class MyGmrsClient implements MyGmrsService {
  MyGmrsClient({
    Uri? brokerBase,
    Future<void> Function(Uri uri)? openBrowser,
    Duration signInTimeout = const Duration(minutes: 5),
  }) : brokerBase = brokerBase ?? Uri.parse(myGmrsBrokerBase),
       _openBrowser = openBrowser ?? _openSystemBrowser,
       _signInTimeout = signInTimeout;

  final Uri brokerBase;
  final Future<void> Function(Uri uri) _openBrowser;
  final Duration _signInTimeout;

  String? _sessionToken;
  DateTime? _sessionExpiresAt;

  @override
  bool get signedIn =>
      _sessionToken != null &&
      _sessionExpiresAt?.isAfter(DateTime.now()) == true;

  @override
  Future<void> signIn() async {
    final start = await _postJson('/api/mygmrs/oauth/start', const {});
    final handoffToken = '${start['handoffToken'] ?? ''}';
    final authorizeUrl = Uri.tryParse('${start['authorizeUrl'] ?? ''}');
    if (handoffToken.isEmpty ||
        authorizeUrl == null ||
        !authorizeUrl.isScheme('https')) {
      throw const MyGmrsException(
        'newchirp.net returned an invalid myGMRS sign-in response.',
      );
    }
    await _openBrowser(authorizeUrl);
    final deadline = DateTime.now().add(_signInTimeout);
    while (DateTime.now().isBefore(deadline)) {
      await Future<void>.delayed(const Duration(milliseconds: 1200));
      final poll = await _jsonRequest(
        'POST',
        brokerBase.replace(path: '/api/mygmrs/oauth/poll'),
        contentType: ContentType.json,
        body: '{}',
        authorization: 'Bearer $handoffToken',
      );
      if (poll.statusCode == HttpStatus.accepted) continue;
      if (poll.statusCode == HttpStatus.ok) {
        _storeSession(poll.body);
        return;
      }
      final message = '${poll.body['error'] ?? poll.rawBody}'.trim();
      throw MyGmrsException(
        message.isEmpty
            ? 'myGMRS sign-in failed with HTTP ${poll.statusCode}.'
            : message,
      );
    }
    throw const MyGmrsException(
      'myGMRS sign-in timed out. Return to NewChirp and try again.',
    );
  }

  void _storeSession(Map<String, dynamic> response) {
    final sessionToken = '${response['sessionToken'] ?? ''}';
    if (sessionToken.isEmpty) {
      throw const MyGmrsException(
        'newchirp.net did not return a myGMRS session.',
      );
    }
    final expiresIn = (response['expiresIn'] as num?)?.toInt() ?? 43200;
    _sessionToken = sessionToken;
    _sessionExpiresAt = DateTime.now().add(Duration(seconds: expiresIn));
  }

  @override
  Future<void> signOut() async {
    final sessionToken = _sessionToken;
    _sessionToken = null;
    _sessionExpiresAt = null;
    if (sessionToken == null) return;
    try {
      await _jsonRequest(
        'POST',
        brokerBase.replace(path: '/api/mygmrs/oauth/logout'),
        contentType: ContentType.json,
        body: '{}',
        authorization: 'Bearer $sessionToken',
      );
    } on MyGmrsException {
      // Local sign-out still succeeds if the network is unavailable.
    }
  }

  Future<void> ensureSignedIn() async {
    if (signedIn) return;
    _sessionToken = null;
    _sessionExpiresAt = null;
    await signIn();
  }

  @override
  Future<RepeaterSearchResults> searchRepeaters({
    required String state,
    String query = '',
    double? latitude,
    double? longitude,
    double? distanceKm,
    bool openOnly = false,
    int limit = 100,
  }) async {
    await ensureSignedIn();
    final payload = <String, dynamic>{
      if (state.isNotEmpty && state != 'All') 'state': _stateCode(state),
      if (query.trim().isNotEmpty) 'search': query.trim(),
      if (latitude != null) 'latitude': '$latitude',
      if (longitude != null) 'longitude': '$longitude',
      if (distanceKm != null)
        'range': '${(distanceKm / 1.609344).ceil().clamp(1, 250)}',
      'limit': '${limit.clamp(1, 100)}',
    };
    final sessionToken = _sessionToken;
    if (sessionToken == null) {
      throw const MyGmrsException(
        'Your myGMRS session expired. Sign in again.',
      );
    }
    final response = await _jsonRequest(
      'POST',
      brokerBase.replace(path: '/api/mygmrs/repeaters/search'),
      contentType: ContentType.json,
      body: jsonEncode(payload),
      authorization: 'Bearer $sessionToken',
    );
    if (response.statusCode == HttpStatus.unauthorized) {
      _sessionToken = null;
      _sessionExpiresAt = null;
      throw MyGmrsException(
        '${response.body['error'] ?? 'Your myGMRS session expired. Sign in again.'}',
      );
    }
    if (response.statusCode != HttpStatus.ok) {
      throw MyGmrsException(_apiError(response));
    }
    return convertRepeaterResponse(response.body, openOnly: openOnly);
  }

  RepeaterSearchResults convertRepeaterResponse(
    Map<String, dynamic> payload, {
    bool openOnly = false,
  }) {
    final items = payload['items'];
    if (items is! List) {
      throw const MyGmrsException(
        'myGMRS returned an unexpected repeater response.',
      );
    }
    final total =
        ((payload['info'] as Map?)?['total'] as num?)?.toInt() ?? items.length;
    final results = <RepeaterSearchResult>[];
    for (final rawItem in items) {
      if (rawItem is! Map) continue;
      final item = rawItem.cast<String, dynamic>();
      final frequency = double.tryParse('${item['Frequency'] ?? ''}');
      if (frequency == null || frequency <= 0) continue;
      final open = item['ORI'] == 'Yes' || item['Type'] == 'Open System';
      if (openOnly && !open) continue;

      final txTone = _ctcssTone(item['PL In']);
      final rxTone = _ctcssTone(item['PL Out']);
      final channel = RadioChannel(
        location: results.length + 1,
        name: '${item['Name'] ?? item['Owner'] ?? 'GMRS Repeater'}',
        frequency: frequency,
        duplex: _gmrsRepeaterOutput(frequency) ? '+' : '',
        offset: _gmrsRepeaterOutput(frequency) ? 5 : 0,
        mode: 'FM',
        step: 5,
      );
      _applyTones(channel, txTone, rxTone);

      final owner = '${item['Owner'] ?? ''}'.trim();
      final rules = '${item['Rules'] ?? ''}'.trim();
      final details = <String>[
        'myGMRS',
        if (owner.isNotEmpty) owner,
        if (item['Travel'] == 'Yes') 'Travel tone',
        if (item['Status'] == 'Offline') 'Offline',
        if (rules.isNotEmpty) rules,
      ];
      channel.comment = details.join(' - ');

      final distanceMiles = (item['Distance'] as num?)?.toDouble();
      results.add(
        RepeaterSearchResult(
          channel: channel,
          callsign: '',
          city: '${item['Location'] ?? ''}',
          county: '',
          state: '${item['State'] ?? ''}',
          use: open ? 'OPEN' : 'CLOSED',
          service: 'GMRS',
          latitude: (item['Latitude'] as num?)?.toDouble(),
          longitude: (item['Longitude'] as num?)?.toDouble(),
          distanceKm: distanceMiles == null ? null : distanceMiles * 1.609344,
        ),
      );
    }
    if (results.isEmpty && total > 0) {
      throw const MyGmrsException(
        'myGMRS found repeaters, but none included a usable frequency. '
        'Sign in with an active GMRS license; Premium is required for PL '
        'tones and repeater rules.',
      );
    }
    return RepeaterSearchResults(
      source: 'myGMRS',
      sourceUrl: 'https://mygmrs.com',
      totalMatches: total,
      results: results,
    );
  }

  Future<Map<String, dynamic>> _postJson(
    String path,
    Map<String, dynamic> payload,
  ) async {
    final response = await _jsonRequest(
      'POST',
      brokerBase.replace(path: path),
      contentType: ContentType.json,
      body: jsonEncode(payload),
    );
    if (response.statusCode != HttpStatus.ok) {
      throw MyGmrsException(_apiError(response));
    }
    return response.body;
  }

  Future<_JsonResponse> _jsonRequest(
    String method,
    Uri uri, {
    ContentType? contentType,
    String? body,
    String? authorization,
  }) async {
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 20);
    try {
      final request = await client.openUrl(method, uri);
      request.headers
        ..set(HttpHeaders.acceptHeader, 'application/json')
        ..set(HttpHeaders.userAgentHeader, 'NewChirp');
      if (contentType != null) request.headers.contentType = contentType;
      if (authorization != null) {
        request.headers.set(HttpHeaders.authorizationHeader, authorization);
      }
      if (body != null) request.write(body);
      final response = await request.close();
      final text = await response.transform(utf8.decoder).join();
      Map<String, dynamic> json = const {};
      if (text.trim().isNotEmpty) {
        try {
          final decoded = jsonDecode(text);
          if (decoded is Map) json = decoded.cast<String, dynamic>();
        } on FormatException {
          if (response.statusCode == HttpStatus.ok) {
            throw const MyGmrsException(
              'myGMRS returned an invalid JSON response.',
            );
          }
        }
      }
      return _JsonResponse(response.statusCode, json, text);
    } on SocketException catch (error) {
      throw MyGmrsException('Could not reach myGMRS: ${error.message}');
    } finally {
      client.close(force: true);
    }
  }

  static String _apiError(_JsonResponse response) {
    final message =
        '${response.body['error_description'] ?? response.body['error'] ?? response.body['message'] ?? ''}'
            .trim();
    if (message.isNotEmpty) {
      return 'myGMRS error ${response.statusCode}: $message';
    }
    if (response.statusCode == HttpStatus.forbidden) {
      return 'myGMRS access was denied. The requested permission or account '
          'feature is not active.';
    }
    if (response.statusCode == HttpStatus.tooManyRequests) {
      return 'myGMRS rate limit reached. Wait before searching again.';
    }
    return 'myGMRS request failed with HTTP ${response.statusCode}.';
  }
}

class _JsonResponse {
  const _JsonResponse(this.statusCode, this.body, this.rawBody);

  final int statusCode;
  final Map<String, dynamic> body;
  final String rawBody;
}

double? _ctcssTone(Object? raw) {
  final match = RegExp(r'(\d+(?:\.\d+)?)').firstMatch('${raw ?? ''}');
  return match == null ? null : double.tryParse(match.group(1)!);
}

String _stateCode(String state) {
  const codes = <String, String>{
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Guam': 'GU',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Puerto Rico': 'PR',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virgin Islands': 'VI',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
  };
  return codes[state] ?? state;
}

bool _gmrsRepeaterOutput(double frequency) =>
    frequency >= 462.550 && frequency <= 462.725;

void _applyTones(RadioChannel channel, double? txTone, double? rxTone) {
  if (txTone == null && rxTone == null) return;
  if (txTone != null && rxTone != null && txTone == rxTone) {
    channel
      ..tone = 'TSQL'
      ..txTone = txTone
      ..rxTone = rxTone;
    return;
  }
  if (txTone != null && rxTone == null) {
    channel
      ..tone = 'Tone'
      ..txTone = txTone;
    return;
  }
  channel
    ..tone = 'Cross'
    ..txTone = txTone ?? 88.5
    ..rxTone = rxTone ?? 88.5
    ..crossMode = switch ((txTone != null, rxTone != null)) {
      (true, true) => 'Tone->Tone',
      (false, true) => '->Tone',
      _ => 'Tone->Tone',
    };
}

Future<void> _openSystemBrowser(Uri uri) async {
  final ProcessResult result;
  if (Platform.isMacOS) {
    result = await Process.run('open', [uri.toString()]);
  } else if (Platform.isWindows) {
    result = await Process.run('rundll32', [
      'url.dll,FileProtocolHandler',
      uri.toString(),
    ]);
  } else if (Platform.isLinux) {
    result = await Process.run('xdg-open', [uri.toString()]);
  } else {
    throw const MyGmrsException(
      'Opening a browser is not supported on this platform.',
    );
  }
  if (result.exitCode != 0) {
    throw MyGmrsException(
      'Could not open the myGMRS sign-in page in a browser. '
      'Open this address manually: $uri',
    );
  }
}
