import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  test('parses CHIRP radio settings trees', () {
    final settings = RadioSettings.fromJson({
      'hasSettings': true,
      'settings': [
        {
          'id': [0],
          'name': 'basic',
          'shortName': 'Basic Settings',
          'kind': 'group',
          'children': [
            {
              'id': [0, 0],
              'name': 'settings.squelch',
              'shortName': 'Squelch',
              'kind': 'choice',
              'value': '3',
              'options': ['Off', '1', '3'],
              'mutable': true,
            },
          ],
        },
      ],
    });

    expect(settings.hasSettings, isTrue);
    final group = settings.items.single;
    expect(group.isGroup, isTrue);
    expect(group.label, 'Basic Settings');
    final setting = group.children.single;
    expect(setting.label, 'Squelch');
    expect(setting.options, ['Off', '1', '3']);
    expect(setting.changed, isFalse);
    expect(setting.toChangeJson(), {
      'id': [0, 0],
      'value': '3',
    });
  });

  test('parses numeric setting limits and values', () {
    final setting = RadioSettingNode.fromJson({
      'id': [1, 2],
      'name': 'settings.vox',
      'shortName': 'VOX',
      'kind': 'integer',
      'value': 2,
      'mutable': true,
      'min': 1,
      'max': 5,
    });

    expect(setting.value, 2);
    expect(setting.min, 1);
    expect(setting.max, 5);
    expect(setting.invalid, isFalse);
  });

  test('parses the refreshed image path from a live settings read', () {
    final settings = RadioSettings.fromJson({
      'hasSettings': true,
      'imagePath': '/tmp/newchirp-live.img',
      'settings': <Object?>[],
    });

    expect(settings.imagePath, '/tmp/newchirp-live.img');
  });

  test('readSettings requires exactly one radio source', () async {
    final bridge = RadioBridge();

    await expectLater(
      bridge.readSettings(model: 'Baofeng_UV-5R_Mini'),
      throwsArgumentError,
    );
    await expectLater(
      bridge.readSettings(
        model: 'Baofeng_UV-5R_Mini',
        imagePath: 'stored.img',
        port: 'COM1',
      ),
      throwsArgumentError,
    );
  });

  test('detects radio drivers that require uppercase names', () {
    final uppercase = RadioCapabilities.fromJson({
      'validCharacters': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
    });
    final mixedCase = RadioCapabilities.fromJson({
      'validCharacters': 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
    });
    final missing = RadioCapabilities.fromJson(const {});

    expect(uppercase.uppercaseNames, isTrue);
    expect(mixedCase.uppercaseNames, isFalse);
    expect(missing.uppercaseNames, isFalse);
  });

  test('parses radio memory bounds', () {
    final capabilities = RadioCapabilities.fromJson({
      'memoryStart': 1,
      'memoryEnd': 199,
    });

    expect(capabilities.memoryStart, 1);
    expect(capabilities.memoryEnd, 199);
  });

  test('parses supported frequency bands', () {
    final capabilities = RadioCapabilities.fromJson({
      'validBands': [
        {'startMhz': 108, 'endMhz': 136},
        {'startMhz': 400, 'endMhz': 520},
      ],
    });

    expect(capabilities.validBands, hasLength(2));
    expect(capabilities.validBands.first.startMhz, 108);
    expect(capabilities.validBands.last.endMhz, 520);
  });
}
