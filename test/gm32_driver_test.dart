import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the experimental GM-32 profile', () async {
    final source = Directory('build_support/chirp-20261023').existsSync()
        ? 'build_support/chirp-20261023'
        : '../chirp-20260626';
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Baofeng_GM-32'));
    final instructions = await bridge.instructions('Baofeng_GM-32');
    expect(instructions.experimental, contains('experimental'));
    expect(instructions.experimental, contains('bank-name'));
    expect(instructions.preDownload, contains('unedited image'));
  });
}
