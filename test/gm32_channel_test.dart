import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/gm32_channel.dart';
import 'package:newchirp/models/radio_channel.dart';

RadioChannel gm32Row({
  required int location,
  required double frequency,
  String duplex = '',
  double offset = 0,
  String mode = 'FM',
  String power = 'High',
  String name = 'CH',
}) {
  return RadioChannel(
    location: location,
    name: name,
    frequency: frequency,
    duplex: duplex,
    offset: offset,
    mode: mode,
    power: power,
  );
}

double mhz(int channel) => gmrsStandardRxHz(channel)! / 1000000;

void main() {
  test('a new GM-32 row starts with no receive channel', () {
    final channel = gm32Row(location: 40, frequency: 0, power: '');
    expect(gm32FrequencyIsUnset(channel.frequency), isTrue);
    expect(gm32ReceiveValue(channel, enteringFrequency: false), '');
    expect(
      gm32ReceiveChoices(
        channel,
        enteringFrequency: false,
      )[gm32ManualFrequencyValue],
      'Enter a frequency',
    );
    expect(gm32ChannelIssues(baofengGm32Model, channel), [
      'Choose a GMRS channel or enter a receive frequency.',
    ]);
    expect(gm32ChannelIssues('Baofeng_UV-32', channel), isEmpty);
  });

  test('typing a GMRS frequency keeps the manual choice open', () {
    final channel = gm32Row(location: 40, frequency: mhz(1));
    expect(
      gm32ReceiveValue(channel, enteringFrequency: true),
      gm32ManualFrequencyValue,
    );
  });

  test('channels 1 through 7 stay simplex', () {
    final channel = gm32Row(
      location: 1,
      frequency: mhz(1),
      duplex: '+',
      offset: 5,
    );
    applyGm32Rules(channel);
    expect(channel.duplex, '');
    expect(channel.offset, 0);
    expect(gm32DuplexChoices(channel).keys, ['']);
    expect(gm32ChannelIssues(baofengGm32Model, channel), isEmpty);
  });

  test('channels 8 through 14 default to simplex, narrow, and Low', () {
    final channel = gm32Row(
      location: 8,
      frequency: mhz(8),
      duplex: '+',
      offset: 5,
      mode: 'FM',
      power: 'High',
    );
    useGm32ReceiveChannel(channel, 8);
    expect(channel.frequency, mhz(8));
    expect(channel.duplex, '');
    expect(channel.offset, 0);
    expect(channel.mode, 'NFM');
    expect(channel.power, 'Low');
    expect(gm32DuplexChoices(channel).keys, ['', 'off']);
    expect(gm32ChannelIssues(baofengGm32Model, channel), isEmpty);
  });

  test('channels 8 through 14 can stay receive-only', () {
    final channel = gm32Row(
      location: 9,
      frequency: mhz(9),
      duplex: 'off',
      mode: 'FM',
      power: 'High',
    );
    applyGm32Rules(channel);
    expect(channel.duplex, 'off');
    expect(channel.mode, 'NFM');
    expect(channel.power, 'Low');
    expect(gm32ChannelIssues(baofengGm32Model, channel), isEmpty);
  });

  test('channels 15 through 22 keep a +5 MHz repeater', () {
    final channel = gm32Row(
      location: 16,
      frequency: mhz(16),
      duplex: '+',
      offset: 0.6,
    );
    applyGm32Rules(channel);
    expect(channel.duplex, '+');
    expect(channel.offset, 5);
    expect(gm32DuplexChoices(channel).keys, ['', '+', 'off']);
    expect(gm32ChannelIssues(baofengGm32Model, channel), isEmpty);
  });

  test('channels 15 through 22 drop a minus shift back to simplex', () {
    final channel = gm32Row(
      location: 16,
      frequency: mhz(16),
      duplex: '-',
      offset: 5,
    );
    applyGm32Rules(channel);
    expect(channel.duplex, '');
    expect(channel.offset, 0);
  });

  test('a repeater input can transmit simplex but not with a plus shift', () {
    final channel = gm32Row(
      location: 31,
      frequency: 467.550,
      duplex: '+',
      offset: 5,
    );
    applyGm32Rules(channel);
    expect(channel.duplex, '');
    expect(channel.offset, 0);
    expect(gm32DuplexChoices(channel).keys, ['', 'off']);
    expect(gmrsChannelNumber(channel), isNull);
  });

  test('a frequency that is not GMRS is receive-only', () {
    final channel = gm32Row(
      location: 31,
      frequency: 470.550,
      duplex: '',
      name: 'HAMs',
      mode: 'FM',
      power: 'High',
    );
    applyGm32Rules(channel);
    expect(channel.duplex, 'off');
    expect(channel.offset, 0);
    expect(channel.mode, 'FM');
    expect(channel.power, 'High');
    expect(
      gm32ReceiveValue(channel, enteringFrequency: false),
      gm32ManualFrequencyValue,
    );
    expect(gm32DuplexChoices(channel).keys, ['off']);
    expect(gm32ChannelIssues(baofengGm32Model, channel), isEmpty);
  });
}
