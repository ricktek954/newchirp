import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

import 'chirp_test_source.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('loads IC-2730A settings when CHIRP omits float maximum', () async {
    final source = requireChirpSourceForTests();
    final image = File('${Directory.systemTemp.path}/newchirp-ic2730-$pid.img');
    await image.writeAsBytes(List<int>.filled(21312, 0), flush: true);
    addTearDown(() async {
      if (await image.exists()) await image.delete();
    });

    final settings = await RadioBridge(
      sourcePath: source,
    ).readSettings(model: 'Icom_IC-2730A', imagePath: image.path);

    expect(settings.hasSettings, isTrue);
    expect(settings.items, isNotEmpty);
  });
}
