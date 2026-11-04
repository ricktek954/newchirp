import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/mygmrs_client.dart';

void main() {
  test('builds an OAuth authorization URL with PKCE and repeater scope', () {
    final client = MyGmrsClient(
      clientId: 'test-client',
      redirectUri: Uri.parse('http://127.0.0.1:8765/callback'),
      apiBase: Uri.parse('https://api.example.test'),
    );

    final uri = client.buildAuthorizeUri(
      state: 'expected-state',
      codeChallenge: 'challenge-value',
    );

    expect(uri.path, '/oauth/authorize');
    expect(uri.queryParameters['client_id'], 'test-client');
    expect(
      uri.queryParameters['redirect_uri'],
      'http://127.0.0.1:8765/callback',
    );
    expect(uri.queryParameters['scope'], 'repeaters:read');
    expect(uri.queryParameters['state'], 'expected-state');
    expect(uri.queryParameters['code_challenge'], 'challenge-value');
    expect(uri.queryParameters['code_challenge_method'], 'S256');
  });

  test('converts myGMRS repeater data into a GMRS channel', () {
    final client = MyGmrsClient(clientId: 'test-client');

    final results = client.convertRepeaterResponse({
      'success': true,
      'info': {'total': 1},
      'items': [
        {
          'ID': 10,
          'Name': 'Example Repeater',
          'Location': 'Example Town',
          'State': 'NJ',
          'Frequency': '462.575',
          'PL In': '141.3 Hz',
          'PL Out': '141.3 Hz',
          'Type': 'Open System',
          'Owner': 'exampleuser',
          'ORI': 'Yes',
          'Travel': 'Yes',
          'Status': 'Online',
          'Latitude': 40.0,
          'Longitude': -74.0,
          'Distance': 10,
          'Rules': 'Open to licensed GMRS users.',
        },
      ],
    });

    final result = results.results.single;
    expect(results.source, 'myGMRS');
    expect(result.channel.frequency, 462.575);
    expect(result.channel.duplex, '+');
    expect(result.channel.offset, 5);
    expect(result.channel.tone, 'TSQL');
    expect(result.channel.txTone, 141.3);
    expect(result.channel.rxTone, 141.3);
    expect(result.use, 'OPEN');
    expect(result.service, 'GMRS');
    expect(result.distanceKm, closeTo(16.09344, 0.00001));
    expect(result.channel.comment, contains('exampleuser'));
    expect(result.channel.comment, contains('Travel tone'));
    expect(result.channel.comment, contains('Open to licensed GMRS users.'));
  });

  test('explains when myGMRS omits frequencies', () {
    final client = MyGmrsClient(clientId: 'test-client');

    expect(
      () => client.convertRepeaterResponse({
        'success': true,
        'info': {'total': 2},
        'items': [
          {'ID': 1, 'Name': 'Hidden frequency'},
        ],
      }),
      throwsA(
        isA<MyGmrsException>().having(
          (error) => error.message,
          'message',
          contains('active GMRS license'),
        ),
      ),
    );
  });

  test(
    'completes authorization-code PKCE flow with a loopback callback',
    () async {
      final tokenServer = await HttpServer.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      addTearDown(() => tokenServer.close(force: true));
      tokenServer.listen((request) async {
        expect(request.uri.path, '/oauth/token');
        final body = utf8.decode(
          await request.fold<List<int>>([], (bytes, chunk) {
            bytes.addAll(chunk);
            return bytes;
          }),
        );
        expect(body, contains('grant_type=authorization_code'));
        expect(body, contains('code=test-code'));
        expect(body, contains('client_id=test-client'));
        expect(body, contains('code_verifier='));
        request.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write(
            '{"access_token":"access","token_type":"Bearer",'
            '"expires_in":3600,"refresh_token":"refresh",'
            '"scope":"repeaters:read"}',
          );
        await request.response.close();
      });

      final callbackProbe = await ServerSocket.bind(
        InternetAddress.loopbackIPv4,
        0,
      );
      final callbackPort = callbackProbe.port;
      await callbackProbe.close();

      final client = MyGmrsClient(
        clientId: 'test-client',
        redirectUri: Uri.parse('http://127.0.0.1:$callbackPort/callback'),
        apiBase: Uri.parse('http://127.0.0.1:${tokenServer.port}'),
        openBrowser: (authorizeUri) async {
          final state = authorizeUri.queryParameters['state']!;
          final redirect = Uri.parse(
            authorizeUri.queryParameters['redirect_uri']!,
          );
          final callback = redirect.replace(
            queryParameters: {'code': 'test-code', 'state': state},
          );
          final http = HttpClient();
          try {
            final request = await http.getUrl(callback);
            final response = await request.close();
            await response.drain<void>();
            expect(response.statusCode, HttpStatus.ok);
          } finally {
            http.close(force: true);
          }
        },
      );

      await client.signIn();

      expect(client.signedIn, isTrue);
    },
  );
}
