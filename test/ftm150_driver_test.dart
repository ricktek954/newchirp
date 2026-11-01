import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the experimental Yaesu FTM-150 driver', () async {
    final source = requireChirpSourceForTests();
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Yaesu_FTM-150R'));
    final instructions = await bridge.instructions('Yaesu_FTM-150R');
    expect(instructions.experimental, contains('experimental'));
    expect(instructions.info, contains('SCU-56'));
    expect(instructions.preUpload, contains('58 This -> Other'));
  });

  test('FT-857 exposes its clone-mode read and write instructions', () async {
    final source = requireChirpSourceForTests();
    final bridge = RadioBridge(sourcePath: source);

    final instructions = await bridge.instructions('Yaesu_FT-857_897');
    expect(instructions.preDownload, contains('CLONE MODE'));
    expect(instructions.preDownload, contains('[C](SEND)'));
    expect(instructions.preUpload, contains('ACC jack'));
    expect(instructions.preUpload, contains('[A](RCV)'));
  });
}
