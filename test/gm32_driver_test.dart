import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

String? _chirpSource() {
  const candidates = [
    'build_support/chirp-20261023',
    'build_support/chirp-20261016',
    '../chirp-20260626',
  ];
  for (final path in candidates) {
    if (Directory(path).existsSync()) return path;
  }
  final configured = Platform.environment['CHIRP_SOURCE'];
  if (configured != null && Directory(configured).existsSync()) {
    return configured;
  }
  return null;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the experimental Baofeng GM-32 driver', () async {
    final source = _chirpSource();
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
