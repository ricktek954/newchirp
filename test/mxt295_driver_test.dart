import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the experimental Midland MXT295 driver', () async {
    final source = Directory('build_support/chirp-20261016').existsSync()
        ? 'build_support/chirp-20261016'
        : Directory('build_support/chirp-20261023').existsSync()
        ? 'build_support/chirp-20261023'
        : '../chirp-20260626';
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Midland_MXT295'));
    final instructions = await bridge.instructions('Midland_MXT295');
    expect(instructions.experimental, isEmpty);
    expect(instructions.info, isNull);
    expect(
      instructions.preDownload,
      contains('This driver for Midland radios is experimental.'),
    );
    expect(
      instructions.preDownload,
      contains('keep a backup of your radio from the Midland program.'),
    );
    expect(instructions.preDownload, contains('Bluetooth mic off'));
    expect(instructions.preDownload, contains('Click OK to download'));
    expect(
      instructions.preUpload,
      'This Midland driver is experimental.  Make a backup of '
      'your radio before using this experimental driver to make '
      'any changes.',
    );
  });
}
