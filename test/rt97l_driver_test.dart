import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the read-only RT97L driver', () async {
    final source = Directory('build_support/chirp-20261023').existsSync()
        ? 'build_support/chirp-20261023'
        : '../chirp-20260626';
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Retevis_RT97L'));
    final instructions = await bridge.instructions('Retevis_RT97L');
    expect(instructions.experimental, contains('read-only'));
    expect(instructions.info, contains('9600'));
    expect(instructions.preDownload, contains('report channel'));
  });
}
