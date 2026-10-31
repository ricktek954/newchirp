import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/radio_channel.dart';

RadioChannel channelAt(int location) =>
    RadioChannel(location: location, name: 'CH $location', frequency: 146.52);

void main() {
  test('Midland MXT295 shows Midland channel numbers', () {
    expect(channelNumberLabel('Baofeng_UV-5R', 16), '16');
    expect(showsMidlandChannelNumbers('Baofeng_UV-5R'), isFalse);
    expect(showsMidlandChannelNumbers(midlandMxt295Model), isTrue);
    expect(channelNumberLabel(midlandMxt295Model, 1), '1');
    expect(channelNumberLabel(midlandMxt295Model, 15), '15');
    expect(channelNumberLabel(midlandMxt295Model, 16), 'RPTR 15');
    expect(channelNumberLabel(midlandMxt295Model, 17), '16');
    expect(channelNumberLabel(midlandMxt295Model, 18), 'RPTR 16');
    expect(channelNumberLabel(midlandMxt295Model, 19), '17');
    expect(channelNumberLabel(midlandMxt295Model, 29), '22');
    expect(channelNumberLabel(midlandMxt295Model, 30), 'RPTR 22');
    expect(channelNumberLabel(midlandMxt295Model, 31), '23');
    expect(channelNumberLabel(midlandMxt295Model, 107), '99');
    expect(channelNumberLabel(midlandMxt295Model, 0), '0');
  });

  test('Midland repeater rows reset to the plain GMRS repeater', () {
    expect(isMidlandRepeaterRow('Baofeng_UV-5R', 16), isFalse);
    expect(isMidlandRepeaterRow(midlandMxt295Model, 15), isFalse);
    expect(isMidlandRepeaterRow(midlandMxt295Model, 17), isFalse);
    expect(isMidlandRepeaterRow(midlandMxt295Model, 31), isFalse);
    expect(isMidlandRepeaterRow(midlandMxt295Model, 16), isTrue);
    expect(isMidlandRepeaterRow(midlandMxt295Model, 30), isTrue);
    expect(midlandRepeaterRxMhz[16], 462.550);
    expect(midlandRepeaterRxMhz[30], 462.725);

    final row = RadioChannel(
      location: 24,
      name: 'CALICO',
      frequency: 146.52,
      duplex: '',
      skip: '',
      power: 'Low',
    );
    row.restorePlainMidlandRepeater();
    expect(row.cleared, isFalse);
    expect(row.name, isEmpty);
    expect(row.frequency, 462.650);
    expect(row.duplex, '+');
    expect(row.offset, 5);
    expect(row.tone, isEmpty);
    expect(row.mode, 'FM');
    expect(row.step, 12.5);
    expect(row.skip, 'S');
    expect(row.power, 'High');

    final normal = channelAt(17);
    normal.restorePlainMidlandRepeater();
    expect(normal.name, 'CH 17');
    expect(normal.frequency, 146.52);
  });

  test('MXT295 channels 1 through 22 stay on legal GMRS values', () {
    expect(midlandFixedRxHz(1), 462562500);
    expect(midlandFixedRxHz(7), 462712500);
    expect(midlandFixedRxHz(8), 467562500);
    expect(midlandFixedRxHz(14), 467712500);
    expect(midlandFixedRxHz(15), 462550000);
    expect(midlandFixedRxHz(16), 462550000);
    expect(midlandFixedRxHz(17), 462575000);
    expect(midlandFixedRxHz(29), 462725000);
    expect(midlandFixedRxHz(30), 462725000);
    expect(midlandFixedRxHz(31), isNull);
    expect(mhzLabelFromHz(462562500), '462.562500');

    for (var slot = 1; slot <= 30; slot++) {
      final row = RadioChannel(
        location: slot,
        name: 'CH',
        frequency: 146.52,
        duplex: isMidlandRepeaterRow(midlandMxt295Model, slot) ? '+' : '',
        offset: 0.6,
      );
      row.prepareMxt295Editor();
      expect(
        midlandGmrsIssues(midlandMxt295Model, row),
        isEmpty,
        reason: 'slot $slot',
      );
      expect((row.frequency * 1000000).round(), midlandFixedRxHz(slot));
    }

    final receiveOnly = RadioChannel(
      location: 8,
      name: 'GMRS 8',
      frequency: 467.5625,
      duplex: '',
      offset: 0,
    );
    expect(
      midlandGmrsIssues(midlandMxt295Model, receiveOnly).join('\n'),
      contains('Duplex stays off'),
    );
    expect(midlandDuplexIsLocked(1), isTrue);
    expect(midlandDuplexChoices(1, ''), {'': 'Simplex'});
    expect(midlandDuplexIsLocked(8), isTrue);
    expect(midlandDuplexChoices(8, 'off'), {'off': 'off'});
    final simplexOnly = RadioChannel(
      location: 3,
      name: 'GMRS 3',
      frequency: 462.6125,
      duplex: 'off',
      offset: 0,
    );
    simplexOnly.prepareMxt295Editor();
    expect(simplexOnly.duplex, '');
    expect(simplexOnly.offset, 0);
    expect(gmrsChannelMenuLabel(1), 'GMRS Channel 1, 462.562500');
    expect(gmrsChannelMenuLabel(16), 'GMRS Channel 16, 462.575000');
    expect(
      midlandReceiveChannelChoices(31, 462.575),
      containsPair('16', 'GMRS Channel 16, 462.575000'),
    );
    expect(midlandReceiveChannelChoices(31, 462.575).length, 22);
    expect(midlandReceiveChannelValue(31, 0), isEmpty);
    expect(midlandReceiveChannelChoices(31, 0).keys.first, isEmpty);
    expect(midlandReceiveChannelValue(31, 146.52), isEmpty);
    expect(midlandReceiveChannelIsLocked(1), isTrue);
    expect(midlandReceiveChannelIsLocked(31), isFalse);
    receiveOnly.prepareMxt295Editor();
    expect(receiveOnly.duplex, 'off');
    expect(receiveOnly.offset, 0);
    expect(receiveOnly.validate(radioModel: midlandMxt295Model), isEmpty);

    final repeater = RadioChannel(
      location: 16,
      name: 'HIDESERT',
      frequency: 462.55,
      duplex: '-',
      offset: 5,
    );
    expect(midlandDuplexIsLocked(16), isTrue);
    repeater.prepareMxt295Editor();
    expect(repeater.duplex, '+');
    expect(repeater.offset, 5);
    expect(midlandGmrsIssues(midlandMxt295Model, repeater), isEmpty);

    final direct = RadioChannel(
      location: 15,
      name: 'GMRS 15',
      frequency: 462.55,
      duplex: 'split',
      offset: 467.55,
    );
    direct.prepareMxt295Editor();
    expect(direct.duplex, 'split');
    expect(
      midlandGmrsIssues(midlandMxt295Model, direct).join('\n'),
      contains('only allows simplex'),
    );
    expect(midlandDuplexChoices(15, 'split').keys, contains('split'));
    expect(midlandDuplexIsLocked(15), isFalse);

    final extra = RadioChannel(
      location: 38,
      name: 'BIKE03',
      frequency: 462.6125,
      duplex: '+',
      offset: 5,
    );
    expect(
      midlandGmrsIssues(midlandMxt295Model, extra).join('\n'),
      contains('stay simplex'),
    );
    extra.duplex = '';
    extra.offset = 0;
    expect(midlandGmrsIssues(midlandMxt295Model, extra), isEmpty);

    final picked = RadioChannel(location: 31, name: 'NEW', frequency: 146.52);
    picked.useGmrsReceiveChannel(16);
    expect(picked.frequency, 462.575);
    expect(picked.duplex, isEmpty);
    expect(picked.offset, 0);
    expect(midlandCanSelectOffset(31, picked.frequency), isTrue);
    picked.useGmrsReceiveChannel(4);
    expect(picked.duplex, isEmpty);
    expect(picked.offset, 0);
    expect(midlandDuplexIsLocked(31, frequencyMhz: picked.frequency), isTrue);
    expect(midlandCanSelectOffset(31, picked.frequency), isFalse);
    expect(midlandReceiveChannelValue(31, picked.frequency), '4');

    final otherRadio = channelAt(8);
    otherRadio.duplex = '';
    expect(midlandGmrsIssues('Baofeng_UV-5R', otherRadio), isEmpty);
    expect(otherRadio.validate(radioModel: 'Baofeng_UV-5R'), isEmpty);
  });

  test('scan codes use the same words in the list and the editor', () {
    expect(scanLabel(''), 'Include');
    expect(scanLabel('S'), 'Skip');
    expect(scanLabel('P'), 'Priority');
    expect(scanLabel('X'), 'X');
    expect(scanChoices(const ['', 'S']), {'': 'Include', 'S': 'Skip'});
    expect(scanChoices(null).keys.toList(), ['', 'S', 'P']);
  });

  test('provides the standard DTCS code set without a radio image', () {
    expect(standardDtcsCodes, hasLength(104));
    expect(standardDtcsCodes.first, 23);
    expect(standardDtcsCodes.last, 754);
    expect(standardDtcsCodes, containsAll([25, 131, 431, 732]));
  });

  test('next channel location stays within radio memory bounds', () {
    expect(
      RadioChannel.nextAvailableLocation(const [], minimum: 1, maximum: 199),
      1,
    );
    expect(
      RadioChannel.nextAvailableLocation(
        [channelAt(1), channelAt(2), channelAt(150)],
        minimum: 1,
        maximum: 199,
      ),
      151,
    );
    expect(
      RadioChannel.nextAvailableLocation(
        [channelAt(1), channelAt(2), channelAt(199)],
        minimum: 1,
        maximum: 199,
      ),
      3,
    );
    expect(
      RadioChannel.nextAvailableLocation(
        [channelAt(0), channelAt(2)],
        minimum: 0,
        maximum: 2,
      ),
      1,
    );
  });

  test('next channel location reports a full radio', () {
    expect(
      RadioChannel.nextAvailableLocation(
        [channelAt(1), channelAt(2), channelAt(3)],
        minimum: 1,
        maximum: 3,
      ),
      isNull,
    );
  });

  test('channel validation uses the selected radio memory bounds', () {
    expect(
      channelAt(200).validate(minimumLocation: 1, maximumLocation: 199),
      contains('Location must be between 1 and 199 for this radio.'),
    );
    expect(
      channelAt(107).validate(minimumLocation: 1, maximumLocation: 199),
      isEmpty,
    );
  });

  test('frequency validation names the nearest supported tuning step', () {
    const uv5rSteps = [2.5, 5.0, 6.25, 10.0, 12.5, 20.0, 25.0, 50.0];
    final unsupported = RadioChannel(
      location: 1,
      name: 'BAD',
      frequency: 462.1245,
    );

    final issues = unsupported.validate(validTuningSteps: uv5rSteps);

    expect(issues, hasLength(1));
    expect(issues.single, contains('462.124500 MHz'));
    expect(issues.single, contains('462.125000 MHz'));
    expect(
      RadioChannel(
        location: 1,
        name: 'GOOD',
        frequency: 462.125,
      ).validate(validTuningSteps: uv5rSteps),
      isEmpty,
    );
    expect(
      unsupported.validate(validTuningSteps: uv5rSteps, hasTuningStep: false),
      isEmpty,
    );
  });

  test('frequency validation rejects channels outside the radio bands', () {
    const bands = [
      (startMhz: 108.0, endMhz: 136.0),
      (startMhz: 136.0, endMhz: 174.0),
      (startMhz: 200.0, endMhz: 260.0),
      (startMhz: 350.0, endMhz: 390.0),
      (startMhz: 400.0, endMhz: 520.0),
    ];
    final unsupported = RadioChannel(
      location: 4,
      name: '900',
      frequency: 927.525,
    );

    final issues = unsupported.validate(validBands: bands);

    expect(issues, hasLength(1));
    expect(issues.single, contains('927.525000 MHz'));
    expect(issues.single, contains('400.000-520.000 MHz'));
    expect(
      RadioChannel(
        location: 4,
        name: 'UHF',
        frequency: 462.5625,
      ).validate(validBands: bands),
      isEmpty,
    );
  });

  test('mode validation rejects modes the selected radio cannot use', () {
    final digital = RadioChannel(
      location: 1,
      name: 'FUSION',
      frequency: 146.52,
      mode: 'DN',
    );

    final issues = digital.validate(validModes: const ['FM', 'NFM']);

    expect(issues, hasLength(1));
    expect(issues.single, contains('Mode DN is not supported'));
    expect(issues.single, contains('FM, NFM'));

    digital.mode = 'FM';
    expect(digital.validate(validModes: const ['FM', 'NFM']), isEmpty);
  });

  test('tone validation rejects unsupported cross-tone repeaters', () {
    final repeater = RadioChannel(
      location: 15,
      name: 'CROSS',
      frequency: 146.94,
      tone: 'Cross',
      crossMode: 'Tone->Tone',
      txTone: 100,
      rxTone: 123,
    );

    final issues = repeater.validate(
      validToneModes: const ['', 'Tone', 'TSQL', 'DTCS'],
    );

    expect(issues, hasLength(1));
    expect(issues.single, contains('Tone mode Cross is not supported'));
    expect(issues.single, contains('Tone, TSQL, DTCS'));

    expect(
      repeater.validate(
        validToneModes: const ['', 'Tone', 'TSQL', 'DTCS', 'Cross'],
        validCrossModes: const ['Tone->Tone'],
      ),
      isEmpty,
    );
  });
}
