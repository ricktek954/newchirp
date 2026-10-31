import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'catalog exposes experimental read/write Icom ID-50 and ID-52',
    () async {
      final source = Directory('build_support/chirp-20261023').existsSync()
          ? 'build_support/chirp-20261023'
          : '../chirp-20260626';
      final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');
    final catalog = await bridge.modelCatalog();
    final models = catalog.models;
    final icom = catalog.groups.singleWhere((group) => group.name == 'Icom');

      for (final model in ['Icom_ID-50', 'Icom_ID-52']) {
        expect(models, contains(model));
      expect(icom.models, contains(model));
        final instructions = await bridge.instructions(model);
        expect(instructions.experimental, contains('experimental'));
        expect(
          instructions.experimental,
          contains('Reading and writing are enabled'),
        );
        expect(instructions.preDownload, contains('unedited download'));
        expect(instructions.preUpload, contains('known-good backup image'));
      }
    },
  );
}
