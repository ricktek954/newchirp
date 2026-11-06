import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/mygmrs_client.dart';

void main() {
  test('converts myGMRS repeater data into a GMRS channel', () {
    final client = MyGmrsClient();

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
    final client = MyGmrsClient();

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

  test('completes sign-in through the newchirp.net handoff relay', () async {
    final broker = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => broker.close(force: true));
    var polls = 0;
    var searches = 0;
    var signedOut = false;
    Map<String, dynamic>? searchPayload;
    broker.listen((request) async {
      if (request.uri.path == '/api/mygmrs/oauth/start') {
        expect(request.method, 'POST');
        request.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write(
            '{"handoffToken":"handoff-secret",'
            '"authorizeUrl":"https://mygmrs.test/oauth/authorize"}',
          );
      } else if (request.uri.path == '/api/mygmrs/oauth/poll') {
        expect(
          request.headers.value(HttpHeaders.authorizationHeader),
          'Bearer handoff-secret',
        );
        polls++;
        if (polls == 1) {
          request.response
            ..statusCode = HttpStatus.accepted
            ..headers.contentType = ContentType.json
            ..write('{"status":"pending"}');
        } else {
          request.response
            ..statusCode = HttpStatus.ok
            ..headers.contentType = ContentType.json
            ..write(
              '{"status":"ready","sessionToken":"session-token",'
              '"expiresIn":43200}',
            );
        }
      } else if (request.uri.path == '/api/mygmrs/repeaters/search') {
        expect(
          request.headers.value(HttpHeaders.authorizationHeader),
          'Bearer session-token',
        );
        searchPayload =
            jsonDecode(await utf8.decoder.bind(request).join())
                as Map<String, dynamic>;
        searches++;
        request.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write(
            '{"success":true,"info":{"total":1},"items":['
            '{"Name":"Relay","State":"NY","Frequency":"462.575",'
            '"Type":"Open System","Status":"Online"}]}',
          );
      } else if (request.uri.path == '/api/mygmrs/oauth/logout') {
        expect(
          request.headers.value(HttpHeaders.authorizationHeader),
          'Bearer session-token',
        );
        signedOut = true;
        request.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write('{"signedOut":true}');
      } else {
        request.response.statusCode = HttpStatus.notFound;
      }
      await request.response.close();
    });

    Uri? opened;
    final client = MyGmrsClient(
      brokerBase: Uri.parse('http://127.0.0.1:${broker.port}'),
      openBrowser: (authorizeUri) async => opened = authorizeUri,
      signInTimeout: const Duration(seconds: 5),
    );

    await client.signIn();

    expect(opened, Uri.parse('https://mygmrs.test/oauth/authorize'));
    expect(polls, 2);
    expect(client.signedIn, isTrue);

    final results = await client.searchRepeaters(
      state: 'New York',
      query: '33004',
      distanceKm: 40,
    );
    expect(searches, 1);
    expect(searchPayload?['zip'], '33004');
    expect(searchPayload?.containsKey('search'), isFalse);
    expect(searchPayload?['range'], '25');
    expect(results.results.single.channel.frequency, 462.575);

    await client.signOut();
    expect(signedOut, isTrue);
    expect(client.signedIn, isFalse);
  });

  test('cancelSignIn stops a pending OAuth wait', () async {
    final broker = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => broker.close(force: true));
    broker.listen((request) async {
      if (request.uri.path == '/api/mygmrs/oauth/start') {
        request.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write(
            '{"handoffToken":"cancel-handoff",'
            '"authorizeUrl":"https://mygmrs.test/oauth/authorize"}',
          );
      } else if (request.uri.path == '/api/mygmrs/oauth/poll') {
        request.response
          ..statusCode = HttpStatus.accepted
          ..headers.contentType = ContentType.json
          ..write('{"status":"pending"}');
      } else {
        request.response.statusCode = HttpStatus.notFound;
      }
      await request.response.close();
    });
    final client = MyGmrsClient(
      brokerBase: Uri.parse('http://127.0.0.1:${broker.port}'),
      openBrowser: (_) async {},
      signInTimeout: const Duration(seconds: 5),
      signInPollInterval: const Duration(milliseconds: 20),
    );

    final signIn = client.signIn();
    final expectation = expectLater(
      signIn,
      throwsA(
        isA<MyGmrsException>().having(
          (error) => error.message,
          'message',
          contains('cancelled'),
        ),
      ),
    );
    await Future<void>.delayed(const Duration(milliseconds: 50));
    client.cancelSignIn();
    await expectation;
    expect(client.signedIn, isFalse);
  });
}
