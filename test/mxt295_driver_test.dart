import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the hardware-tested Midland MXT295 driver', () async {
    final source = requireChirpSourceForTests();
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Midland_MXT295'));
    final instructions = await bridge.instructions('Midland_MXT295');
    expect(instructions.experimental, isNull);
    expect(instructions.info, contains('Hardware-tested MXT295 support.'));
    expect(
      instructions.preDownload,
      contains('Keep a backup of your radio from the Midland program.'),
    );
    expect(instructions.preDownload, contains('Bluetooth mic off'));
    expect(instructions.preDownload, contains('Click OK to download'));
    expect(
      instructions.preUpload,
      'Make a backup of your radio from the Midland program before '
      'changing it with NewChirp.',
    );
  });
}
