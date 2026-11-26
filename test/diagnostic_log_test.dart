import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/diagnostic_log.dart';

void main() {
  test('diagnostic log keeps a bounded recent session history', () async {
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-diagnostics-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final log = DiagnosticLog(maxEntries: 3, rootDirectory: directory);
    await log.initialize();

    for (var index = 0; index < 6; index++) {
      log.record('test', 'event $index');
    }
    await log.flush();

    expect(log.entryCount, 3);
    final report = log.buildReport();
    expect(report, contains('event 3'));
    expect(report, contains('event 5'));
    expect(report, isNot(contains('event 2')));

    final file = File('${directory.path}/diagnostics.jsonl');
    expect(await file.exists(), isTrue);
    expect((await file.readAsLines()).length, 6);
  });

  test('diagnostic report submits background events', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => server.close(force: true));
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-diagnostics-submit-',
    );
    addTearDown(() => directory.delete(recursive: true));
    Map<String, dynamic>? received;
    server.listen((request) async {
      received =
          jsonDecode(await utf8.decoder.bind(request).join())
              as Map<String, dynamic>;
      request.response.headers.contentType = ContentType.json;
      request.response.write('{"ok":true}');
      await request.response.close();
    });
    final log = DiagnosticLog(
      endpoint: Uri.parse(
        'http://${server.address.address}:${server.port}/api/bug-report',
      ),
      rootDirectory: directory,
    );
    await log.initialize();
    log.record(
      'radio',
      'Radio identification failed',
      context: {'model': 'Retevis_RT86S', 'port': 'COM5'},
    );

    await log.submit(
      email: 'operator@example.com',
      description: 'Radio identification failed.',
      radio: 'Retevis RT86S',
      firmware: '2.01.39',
      version: '1.0.23',
      cable: 'FTDI COM5',
    );

    expect(received?['source'], 'newchirp-desktop');
    expect(received?['radio'], 'Retevis RT86S');
    expect(received?['firmware'], '2.01.39');
    expect(received?['debugLog'], contains('Radio identification failed'));
    expect(received?['debugLog'], contains('"model":"Retevis_RT86S"'));
  });

  test('diagnostic report attaches the radio image when asked', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => server.close(force: true));
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-diagnostics-image-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final received = <Map<String, dynamic>>[];
    server.listen((request) async {
      received.add(
        jsonDecode(await utf8.decoder.bind(request).join())
            as Map<String, dynamic>,
      );
      request.response.headers.contentType = ContentType.json;
      request.response.write('{"ok":true}');
      await request.response.close();
    });
    final image = File('${directory.path}/newchirp-m_gw8h2n.img');
    final bytes = List<int>.generate(11584, (index) => index & 0xff);
    await image.writeAsBytes(bytes);
    final log = DiagnosticLog(
      endpoint: Uri.parse(
        'http://${server.address.address}:${server.port}/api/bug-report',
      ),
      rootDirectory: directory,
    );
    await log.initialize();
    Future<void> send(String? path) => log.submit(
      email: 'operator@example.com',
      description: 'Channel map could not be decoded.',
      radio: 'Icom_IC-E90',
      firmware: '',
      version: '1.0.76',
      cable: 'COM9',
      imagePath: path,
    );

    await send(image.path);
    await send(null);
    await send('${directory.path}/missing.img');

    final attached = received[0]['image'] as Map<String, dynamic>;
    expect(attached['name'], 'newchirp-m_gw8h2n.img');
    expect(base64Decode(attached['data'] as String), bytes);
    expect(received[1].containsKey('image'), isFalse);
    expect(received[2].containsKey('image'), isFalse);
    expect(DiagnosticLog.reportImage(image.path), isNotNull);
    await image.writeAsBytes(List<int>.filled(4 * 1024 * 1024 + 1, 0));
    expect(DiagnosticLog.reportImage(image.path), isNull, reason: 'too big');
  });

  test('diagnostic submission surfaces service errors', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(() => server.close(force: true));
    server.listen((request) async {
      await request.drain<void>();
      request.response.statusCode = HttpStatus.serviceUnavailable;
      request.response.headers.contentType = ContentType.json;
      request.response.write('{"error":"Mail unavailable."}');
      await request.response.close();
    });
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-diagnostics-error-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final log = DiagnosticLog(
      endpoint: Uri.parse(
        'http://${server.address.address}:${server.port}/api/bug-report',
      ),
      rootDirectory: directory,
    );
    await log.initialize();

    await expectLater(
      log.submit(
        email: 'operator@example.com',
        description: 'Radio identification failed.',
        radio: 'Retevis RT86S',
        firmware: '2.01.39',
        version: '1.0.23',
        cable: 'FTDI COM5',
      ),
      throwsA(
        isA<DiagnosticReportException>().having(
          (error) => error.message,
          'message',
          'Mail unavailable.',
        ),
      ),
    );
  });
}
