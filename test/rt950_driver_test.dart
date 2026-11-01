import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the read-only RT-950 driver', () async {
    final source = requireChirpSourceForTests();
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Radtel_RT-950'));
    final instructions = await bridge.instructions('Radtel_RT-950');
    expect(instructions.experimental, contains('read-only'));
    expect(instructions.info, contains('115200'));
    expect(instructions.preDownload, contains('Do not attempt an upload'));
  });
}
