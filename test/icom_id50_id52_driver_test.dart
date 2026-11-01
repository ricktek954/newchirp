import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('catalog exposes experimental read-only Icom ID-50 and ID-52', () async {
    final source = requireChirpSourceForTests();
    final bridge = RadioBridge(sourcePath: source, newDriversPath: 'drivers');
    final catalog = await bridge.modelCatalog();
    final models = catalog.models;
    final icom = catalog.groups.singleWhere((group) => group.name == 'Icom');

    for (final model in ['Icom_ID-50', 'Icom_ID-52']) {
      expect(models, contains(model));
      expect(icom.models, contains(model));
      final instructions = await bridge.instructions(model);
      expect(instructions.experimental, contains('experimental'));
      expect(instructions.experimental, contains('uploads are disabled'));
      expect(instructions.preDownload, contains('read-only'));
    }
  });
}
