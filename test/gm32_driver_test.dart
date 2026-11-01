import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the experimental Baofeng GM-32 driver', () async {
    final source = chirpSourceForTests();
    if (source == null) {
      markTestSkipped('CHIRP source is not on this Mac');
    }
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Baofeng_GM-32'));
    final instructions = await bridge.instructions('Baofeng_GM-32');
    expect(instructions.experimental, contains('experimental'));
    expect(instructions.experimental, contains('bank names'));
    expect(instructions.experimental, contains('tested on a radio'));
    expect(instructions.experimental, contains('backup'));
    expect(instructions.preDownload, contains('Turn off the radio'));
    expect(instructions.preDownload, contains('unedited image'));
    expect(instructions.preUpload, contains('Keep a backup image'));
  });
}
