import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes the CS750 CPS importer', () async {
    final source = Directory('build_support/chirp-20261023').existsSync()
        ? 'build_support/chirp-20261023'
        : '../chirp-20260626';
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');

    expect(await bridge.models(), contains('Connect_Systems_CS750'));
    final instructions = await bridge.instructions('Connect_Systems_CS750');
    expect(instructions.experimental, contains('read-only live download'));
    expect(instructions.info, contains('.rdb'));
    expect(instructions.experimental, contains('Upload is not enabled'));
  });
}
