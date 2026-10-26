import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';
import 'package:newchirp/services/radio_helper_session.dart';

String? chirpSourceForTest() {
  const candidates = [
    'build_support/chirp-21e42e4518c167548af90ed7f9edf75e516c491a',
    'build_support/chirp-20261023',
    'build_support/chirp-20261016',
    '../chirp-20260626',
  ];
  for (final candidate in candidates) {
    if (File('$candidate/chirp/chirp_common.py').existsSync()) return candidate;
  }
  return null;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('session commands accept only known options', () {
    expect(encodeRadioHelperCommand(['list-models']), {
      'command': 'list-models',
    });
    expect(
      encodeRadioHelperCommand([
        'repeaterbook-search',
        '--state',
        'California',
        '--fm-only',
        '--latitude',
        '34.05',
      ]),
      {
        'command': 'repeaterbook-search',
        'state': 'California',
        'fm_only': true,
        'latitude': 34.05,
      },
    );
    expect(
      () => encodeRadioHelperCommand(['os.system']),
      throwsA(isA<RadioBridgeException>()),
    );
    expect(
      () => encodeRadioHelperCommand(['list-models', '--source', '/tmp']),
      throwsA(isA<RadioBridgeException>()),
    );
  });

  test('later catalog calls reuse one helper process', () async {
    final source = chirpSourceForTest();
    if (source == null) {
      markTestSkipped('CHIRP source for tests was not found.');
      return;
    }
    final bridge = RadioBridge(sourcePath: source);
    addTearDown(bridge.close);

    final first = await bridge.models();
    final pid = bridge.debugHelperPid;
    final probes = bridge.debugPythonProbeCount;
    final second = await bridge.models();
    final instructions = await bridge.instructions('Baofeng_UV-5R_Mini');

    expect(pid, isNotNull);
    expect(bridge.debugHelperPid, pid);
    expect(bridge.debugPythonProbeCount, probes);
    expect(probes, 1);
    expect(second, first);
    expect(first, contains('Baofeng_UV-5R'));
    expect(instructions.preDownload, contains('Turn off your radio'));

    await expectLater(
      bridge.instructions('Not_A_Real_Radio_ZZZ'),
      throwsA(isA<RadioBridgeException>()),
    );
    expect(bridge.debugHelperPid, pid);
    expect(await bridge.models(), first);

    bridge.close();
    expect(bridge.debugHelperPid, isNull);
  }, timeout: const Timeout(Duration(minutes: 2)));
}
