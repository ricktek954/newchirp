import 'radio_channel.dart';

/// CHIRP id for the experimental Baofeng GM-32 driver.
const baofengGm32Model = 'Baofeng_GM-32';

/// Dropdown value that opens the manual receive-frequency box.
const gm32ManualFrequencyValue = 'manual';

/// This radio uses the GM-32 channel editor.
bool isBaofengGm32(String? model) => model == baofengGm32Model;

/// Official receive frequency in Hz for GMRS channels 1 through 22.
int? gmrsStandardRxHz(int channel) {
  if (channel >= 1 && channel <= 7) {
    return 462562500 + (channel - 1) * 25000;
  }
  if (channel >= 8 && channel <= 14) {
    return 467562500 + (channel - 8) * 25000;
  }
  if (channel >= 15 && channel <= 22) {
    return 462550000 + (channel - 15) * 25000;
  }
  return null;
}

/// GMRS channel 1-22 for a receive frequency, or null when it is not one.
int? gmrsChannelForHz(int hz) {
  for (var channel = 1; channel <= 22; channel++) {
    if (gmrsStandardRxHz(channel) == hz) return channel;
  }
  return null;
}

/// GMRS channel stored in this row, from its receive frequency.
int? gmrsChannelNumber(RadioChannel channel) =>
    gmrsChannelForHz((channel.frequency * 1000000).round());

/// The eight repeater inputs, 467.550 through 467.725 MHz.
bool isGmrsRepeaterInputHz(int hz) {
  if (hz < 467550000 || hz > 467725000) return false;
  return (hz - 467550000) % 25000 == 0;
}

/// A new row has no receive frequency yet.
bool gm32FrequencyIsUnset(double frequencyMhz) =>
    (frequencyMhz * 1000000).round() <= 0;

/// Menu line for one GMRS channel.
String gm32ChannelMenuLabel(int channel) {
  final hz = gmrsStandardRxHz(channel);
  if (hz == null) return 'GMRS channel $channel';
  return 'GMRS channel $channel, ${gm32MhzLabel(hz)}';
}

/// Frequency text with six decimal places.
String gm32MhzLabel(int hz) {
  final whole = hz ~/ 1000000;
  final fraction = (hz % 1000000).toString().padLeft(6, '0');
  return '$whole.$fraction';
}

/// True when the manual frequency box should start open.
bool gm32NeedsFrequencyBox(RadioChannel channel) {
  if (channel.cleared || gm32FrequencyIsUnset(channel.frequency)) {
    return false;
  }
  return gmrsChannelNumber(channel) == null;
}

/// Channels 8-14 transmit narrowband on the radio's Low step.
bool gm32RequiresNarrowLow(RadioChannel channel) {
  final number = gmrsChannelNumber(channel);
  return number != null && number >= 8 && number <= 14;
}

/// Receive-channel menu, including a manual frequency choice.
Map<String, String> gm32ReceiveChoices(
  RadioChannel channel, {
  required bool enteringFrequency,
}) {
  final choices = <String, String>{};
  if (!enteringFrequency && gm32FrequencyIsUnset(channel.frequency)) {
    choices[''] = '';
  }
  for (var number = 1; number <= 22; number++) {
    choices['$number'] = gm32ChannelMenuLabel(number);
  }
  choices[gm32ManualFrequencyValue] = 'Enter a frequency';
  return choices;
}

/// Selected receive-channel menu value.
String gm32ReceiveValue(
  RadioChannel channel, {
  required bool enteringFrequency,
}) {
  if (enteringFrequency) return gm32ManualFrequencyValue;
  if (gm32FrequencyIsUnset(channel.frequency)) return '';
  final match = gmrsChannelNumber(channel);
  if (match != null) return '$match';
  return gm32ManualFrequencyValue;
}

/// Duplex menu for the current receive frequency.
///
/// Channels 1-7 stay simplex. Channels 8-14 start simplex and may also
/// be receive-only. Channels 15-22 may be simplex, a +5 MHz repeater,
/// or receive-only. Anything else is receive-only.
Map<String, String> gm32DuplexChoices(RadioChannel channel) {
  if (gm32FrequencyIsUnset(channel.frequency)) {
    return const {'': 'Simplex'};
  }
  final number = gmrsChannelNumber(channel);
  if (number != null && number <= 7) return const {'': 'Simplex'};
  if (number != null && number <= 14) {
    return const {'': 'Simplex', 'off': 'TX off'};
  }
  if (number != null) {
    return const {'': 'Simplex', '+': '+ shift', 'off': 'TX off'};
  }
  final hz = (channel.frequency * 1000000).round();
  if (isGmrsRepeaterInputHz(hz)) {
    return const {'': 'Simplex', 'off': 'TX off'};
  }
  return const {'off': 'TX off'};
}

/// Puts one GMRS menu choice onto this row and starts it simplex.
void useGm32ReceiveChannel(RadioChannel channel, int channelNumber) {
  if (channel.cleared) return;
  final hz = gmrsStandardRxHz(channelNumber);
  if (hz == null) return;
  channel.frequency = hz / 1000000;
  channel.duplex = '';
  channel.offset = 0;
  applyGm32Rules(channel);
}

/// Applies the GM-32 transmit limits to the current frequency.
void applyGm32Rules(RadioChannel channel) {
  if (channel.cleared) return;
  if (gm32FrequencyIsUnset(channel.frequency)) {
    channel.duplex = '';
    channel.offset = 0;
    return;
  }
  final hz = (channel.frequency * 1000000).round();
  final number = gmrsChannelForHz(hz);
  if (number == null) {
    if (isGmrsRepeaterInputHz(hz) && channel.duplex != 'off') {
      channel.duplex = '';
    } else if (!isGmrsRepeaterInputHz(hz)) {
      channel.duplex = 'off';
    }
    channel.offset = 0;
    return;
  }
  if (number <= 7) {
    channel.duplex = '';
    channel.offset = 0;
    return;
  }
  if (number <= 14) {
    if (channel.duplex != 'off') {
      channel.duplex = '';
    }
    channel.offset = 0;
    channel.mode = 'NFM';
    channel.power = 'Low';
    return;
  }
  if (channel.duplex == '+') {
    channel.offset = 5;
  } else if (channel.duplex == 'off') {
    channel.offset = 0;
  } else {
    channel.duplex = '';
    channel.offset = 0;
  }
}

/// Why this GM-32 row is not legal. Empty for every other radio.
List<String> gm32ChannelIssues(String? model, RadioChannel channel) {
  if (!isBaofengGm32(model) || channel.cleared) return const [];
  if (gm32FrequencyIsUnset(channel.frequency)) {
    return const ['Choose a GMRS channel or enter a receive frequency.'];
  }
  final issues = <String>[];
  final number = gmrsChannelNumber(channel);
  final offsetHz = (channel.offset * 1000000).round();
  if (number != null && number <= 7) {
    if (channel.duplex != '' || offsetHz != 0) {
      issues.add('GMRS channels 1 through 7 stay simplex.');
    }
  } else if (number != null && number <= 14) {
    if (channel.duplex != '' && channel.duplex != 'off') {
      issues.add('GMRS channels 8 through 14 stay simplex or receive-only.');
    }
    if (offsetHz != 0) {
      issues.add('Offset stays at 0 on channels 8 through 14.');
    }
    if (channel.mode != 'NFM' || channel.power != 'Low') {
      issues.add('GMRS channels 8 through 14 use narrow FM and Low power.');
    }
  } else if (number != null) {
    if (channel.duplex == '+') {
      if (offsetHz != 5000000) {
        issues.add('A GMRS repeater uses a +5 MHz offset.');
      }
    } else if (channel.duplex == '' || channel.duplex == 'off') {
      if (offsetHz != 0) {
        issues.add('Offset stays at 0 unless duplex is +5 MHz.');
      }
    } else {
      issues.add('Use simplex, +5 MHz, or receive-only on this GMRS channel.');
    }
  } else if (isGmrsRepeaterInputHz((channel.frequency * 1000000).round())) {
    if (channel.duplex != '' && channel.duplex != 'off') {
      issues.add('A GMRS repeater input stays simplex or receive-only.');
    }
    if (offsetHz != 0) issues.add('Offset stays at 0 on a repeater input.');
  } else if (channel.duplex != 'off' || offsetHz != 0) {
    issues.add(
      'A frequency that is not GMRS is receive-only. Duplex stays off.',
    );
  }
  return issues;
}
