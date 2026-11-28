import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Installed builds keep NewChirp's drivers in newchirp_drivers/ beside
  // CHIRP's package. With no driver folder configured, the app must find it
  // so NewChirp drivers load after CHIRP's and win their IDs (2026-11-28).
  test(
    'bundled newchirp_drivers folder is found and takes precedence',
    () async {
      final source = requireChirpSourceForTests();
      final bundle = await Directory.systemTemp.createTemp('newchirp-bundle');
      addTearDown(() => bundle.delete(recursive: true));
      await Link(
        '${bundle.path}/chirp',
      ).create(Directory('$source/chirp').absolute.path);
      final drivers = Directory('${bundle.path}/newchirp_drivers');
      await drivers.create();
      for (final entity in Directory('drivers').listSync()) {
        if (entity is File && entity.path.endsWith('.py')) {
          await entity.copy('${drivers.path}/${entity.uri.pathSegments.last}');
        }
      }

      final bridge = RadioBridge(sourcePath: bundle.path);
      final models = await bridge.models();
      expect(models, contains('Kenwood_TK-359'));
      expect(models, contains('Yaesu_FTM-150E'));
      final ftx1 = await bridge.instructions('Yaesu_FTX-1');
      expect(ftx1.experimental, contains('live CAT interface'));
    },
  );
}
