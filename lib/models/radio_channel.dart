const standardDtcsCodes = <int>[
  23,
  25,
  26,
  31,
  32,
  36,
  43,
  47,
  51,
  53,
  54,
  65,
  71,
  72,
  73,
  74,
  114,
  115,
  116,
  122,
  125,
  131,
  132,
  134,
  143,
  145,
  152,
  155,
  156,
  162,
  165,
  172,
  174,
  205,
  212,
  223,
  225,
  226,
  243,
  244,
  245,
  246,
  251,
  252,
  255,
  261,
  263,
  265,
  266,
  271,
  274,
  306,
  311,
  315,
  325,
  331,
  332,
  343,
  346,
  351,
  356,
  364,
  365,
  371,
  411,
  412,
  413,
  423,
  431,
  432,
  445,
  446,
  452,
  454,
  455,
  462,
  464,
  465,
  466,
  503,
  506,
  516,
  523,
  526,
  532,
  546,
  565,
  606,
  612,
  624,
  627,
  631,
  632,
  654,
  662,
  664,
  703,
  712,
  723,
  731,
  732,
  734,
  743,
  754,
];

const standardCtcssTones = <double>[
  67.0,
  69.3,
  71.9,
  74.4,
  77.0,
  79.7,
  82.5,
  85.4,
  88.5,
  91.5,
  94.8,
  97.4,
  100.0,
  103.5,
  107.2,
  110.9,
  114.8,
  118.8,
  123.0,
  127.3,
  131.8,
  136.5,
  141.3,
  146.2,
  151.4,
  156.7,
  159.8,
  162.2,
  165.5,
  167.9,
  171.3,
  173.8,
  177.3,
  179.9,
  183.5,
  186.2,
  189.9,
  192.8,
  196.6,
  199.5,
  203.5,
  206.5,
  210.7,
  218.1,
  225.7,
  229.1,
  233.6,
  241.8,
  250.3,
  254.1,
];

const _scanLabels = <String, String>{
  '': 'Include',
  'S': 'Skip',
  'P': 'Priority',
};

/// Word shown for a stored scan code. Unknown codes stay visible.
String scanLabel(String skip) => _scanLabels[skip] ?? skip;

/// Edit-screen choices for the scan codes this radio allows.
Map<String, String> scanChoices(List<String>? allowed) {
  final values = (allowed == null || allowed.isEmpty)
      ? _scanLabels.keys.toList()
      : allowed;
  return {for (final value in values) value: scanLabel(value)};
}

/// CHIRP id for the experimental Midland MXT295 driver.
const midlandMxt295Model = 'Midland_MXT295';

/// This radio's list uses Midland's channel numbers instead of raw slots.
bool showsMidlandChannelNumbers(String? model) => model == midlandMxt295Model;

/// Channel number shown in the list.
///
/// For the MXT295, [location] is still the radio's memory slot. The label
/// matches the Midland screen: channels 1-99, with RPTR 15-22 between them.
/// Other radios show the slot number unchanged.
String channelNumberLabel(String? model, int location) {
  if (!showsMidlandChannelNumbers(model)) return '$location';
  if (location < 1 || location > 107) return '$location';
  if (location <= 15) return '$location';
  if (location <= 30) {
    final offset = location - 15;
    final channel = 15 + offset ~/ 2;
    if (offset.isOdd) return 'RPTR $channel';
    return '$channel';
  }
  return '${location - 8}';
}

/// Receive frequency, in MHz, for each MXT295 repeater row.
///
/// The keys are memory slots. RPTR 15 through RPTR 22 always stay in the
/// radio. An empty one makes channel-down skip channels when repeater
/// channels are turned off.
const midlandRepeaterRxMhz = <int, double>{
  16: 462.550,
  18: 462.575,
  20: 462.600,
  22: 462.625,
  24: 462.650,
  26: 462.675,
  28: 462.700,
  30: 462.725,
};

/// Whether [location] is one of the eight repeater rows on this radio.
bool isMidlandRepeaterRow(String? model, int location) =>
    showsMidlandChannelNumbers(model) &&
    midlandRepeaterRxMhz.containsKey(location);

/// Midland channel 1-22 for a memory slot. Slots 31-107 are not fixed.
int? _midlandGmrsChannel(int location) {
  if (location >= 1 && location <= 15) return location;
  if (location >= 16 && location <= 30) {
    final offset = location - 15;
    return 15 + offset ~/ 2;
  }
  return null;
}

/// Official receive frequency in Hz for one of the 22 GMRS channels.
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

/// Menu line for the receive-channel dropdown.
String gmrsChannelMenuLabel(int channel) {
  final hz = gmrsStandardRxHz(channel);
  if (hz == null) return 'GMRS Channel $channel';
  return 'GMRS Channel $channel, ${mhzLabelFromHz(hz)}';
}

/// Official receive frequency in Hz for MXT295 channels 1 through 22.
///
/// Returns null for channels 23 through 99. Those rows pick one of the
/// same 22 GMRS channels from the list.
int? midlandFixedRxHz(int location) {
  final channel = _midlandGmrsChannel(location);
  if (channel == null) return null;
  return gmrsStandardRxHz(channel);
}

/// GMRS channel shown for this row. Fixed rows use the slot. Other rows
/// use the stored receive frequency.
int? midlandReceiveGmrsChannel(int location, double frequencyMhz) {
  final fixed = _midlandGmrsChannel(location);
  if (fixed != null) return fixed;
  return gmrsChannelForHz((frequencyMhz * 1000000).round());
}

/// A new row has no receive channel yet. 146.52 MHz is the old placeholder.
bool midlandReceiveChannelIsUnset(double frequencyMhz) {
  final hz = (frequencyMhz * 1000000).round();
  return hz == 0 || hz == 146520000;
}

/// Dropdown rows for Receive channel. Fixed rows have one choice.
///
/// An unset row starts with a blank line so the box does not show a
/// placeholder frequency.
Map<String, String> midlandReceiveChannelChoices(
  int location,
  double frequencyMhz,
) {
  final fixed = _midlandGmrsChannel(location);
  if (fixed != null) {
    return {'$fixed': gmrsChannelMenuLabel(fixed)};
  }
  final choices = <String, String>{};
  final hz = (frequencyMhz * 1000000).round();
  if (midlandReceiveChannelIsUnset(frequencyMhz)) {
    choices[''] = '';
  } else if (gmrsChannelForHz(hz) == null) {
    choices['custom'] = '${mhzLabelFromHz(hz)} MHz';
  }
  for (var channel = 1; channel <= 22; channel++) {
    choices['$channel'] = gmrsChannelMenuLabel(channel);
  }
  return choices;
}

/// Selected value for [midlandReceiveChannelChoices].
String midlandReceiveChannelValue(int location, double frequencyMhz) {
  final fixed = _midlandGmrsChannel(location);
  if (fixed != null) return '$fixed';
  final match = gmrsChannelForHz((frequencyMhz * 1000000).round());
  if (match != null) return '$match';
  if (midlandReceiveChannelIsUnset(frequencyMhz)) return '';
  return 'custom';
}

/// Channels 1 through 22 already have a receive channel, so the list
/// cannot move them.
bool midlandReceiveChannelIsLocked(int location) =>
    _midlandGmrsChannel(location) != null;

/// GMRS repeater outputs from 462.550 through 462.725 MHz.
bool isGmrsRepeaterOutputMhz(double mhz) {
  final hz = (mhz * 1000000).round();
  if (hz < 462550000 || hz > 462725000) return false;
  return (hz - 462550000) % 25000 == 0;
}

String mhzLabelFromHz(int hz) {
  final whole = hz ~/ 1000000;
  final fraction = (hz % 1000000).toString().padLeft(6, '0');
  return '$whole.$fraction';
}

bool _isPlusFiveMhz(double offset) => (offset * 1000000).round() == 5000000;

bool _isZeroMhz(double offset) => (offset * 1000000).round() == 0;

/// Duplex choices for one MXT295 slot.
///
/// Channels 1 through 7 stay simplex. Channels 8 through 14 are receive
/// only. Repeater rows are +5 MHz. A receive channel of 1 through 14 on
/// any other row also stays simplex. The current value stays in the list
/// when it is not legal, so the editor shows what is stored.
Map<String, String> midlandDuplexChoices(
  int location,
  String current, {
  double? frequencyMhz,
}) {
  final Map<String, String> allowed;
  final gmrs = frequencyMhz == null
      ? null
      : gmrsChannelForHz((frequencyMhz * 1000000).round());
  if (location >= 8 && location <= 14) {
    allowed = {'off': 'off'};
  } else if (midlandRepeaterRxMhz.containsKey(location)) {
    allowed = {'+': '+'};
  } else if ((location >= 1 && location <= 7) || (gmrs != null && gmrs <= 14)) {
    allowed = {'': 'Simplex'};
  } else {
    allowed = {'': 'Simplex', '+': '+', 'off': 'off'};
  }
  if (!allowed.containsKey(current)) {
    allowed[current] = current.isEmpty ? 'Simplex' : current;
  }
  return allowed;
}

/// Channels 1-14, a GMRS 1-14 receive channel, and the repeater rows
/// cannot change duplex.
bool midlandDuplexIsLocked(int location, {double? frequencyMhz}) {
  if (location >= 1 && location <= 14) return true;
  if (midlandRepeaterRxMhz.containsKey(location)) return true;
  if (frequencyMhz == null) return false;
  final gmrs = gmrsChannelForHz((frequencyMhz * 1000000).round());
  return gmrs != null && gmrs <= 14;
}

/// Offset can be chosen only for GMRS channels 15 through 22.
///
/// Repeater rows stay on +5 MHz, so that choice is not open there.
bool midlandCanSelectOffset(int location, double frequencyMhz) {
  if (location >= 1 && location <= 14) return false;
  if (midlandRepeaterRxMhz.containsKey(location)) return false;
  final gmrs = midlandReceiveGmrsChannel(location, frequencyMhz);
  return gmrs != null && gmrs >= 15 && gmrs <= 22;
}

/// Why this MXT295 channel is not legal. Empty for every other radio.
///
/// The driver enforces the same rules in drivers/newchirp_mxt295.py.
List<String> midlandGmrsIssues(String? model, RadioChannel channel) {
  if (!showsMidlandChannelNumbers(model) || channel.cleared) return const [];
  final issues = <String>[];
  final label = channelNumberLabel(model, channel.location);
  final name = label.startsWith('RPTR') ? label : 'Channel $label';
  final fixedHz = midlandFixedRxHz(channel.location);
  if (fixedHz != null && (channel.frequency * 1000000).round() != fixedHz) {
    issues.add('$name must stay on ${mhzLabelFromHz(fixedHz)} MHz.');
  }
  final location = channel.location;
  if (location >= 8 && location <= 14) {
    if (channel.duplex != 'off' || !_isZeroMhz(channel.offset)) {
      issues.add('Channels 8 through 14 stay receive only. Duplex stays off.');
    }
    return issues;
  }
  if (isMidlandRepeaterRow(model, location)) {
    if (channel.duplex != '+' || !_isPlusFiveMhz(channel.offset)) {
      issues.add('Repeater rows use a +5 MHz offset.');
    }
    return issues;
  }
  if (location >= 1 &&
      location <= 7 &&
      (channel.duplex != '' || !_isZeroMhz(channel.offset))) {
    issues.add('Channels 1 through 14 stay simplex.');
    return issues;
  }
  final picked = gmrsChannelForHz((channel.frequency * 1000000).round());
  if (location > 30 &&
      picked != null &&
      picked <= 14 &&
      (channel.duplex != '' || !_isZeroMhz(channel.offset))) {
    issues.add('Channels 1 through 14 stay simplex.');
    return issues;
  }
  if (channel.duplex == '+') {
    if (!_isPlusFiveMhz(channel.offset)) {
      issues.add('Repeater offset must be +5 MHz.');
    } else if (!isGmrsRepeaterOutputMhz(channel.frequency)) {
      issues.add(
        'A +5 MHz offset is only for GMRS repeater frequencies '
        '462.550 through 462.725 MHz.',
      );
    }
  } else if (channel.duplex == '' || channel.duplex == 'off') {
    if (!_isZeroMhz(channel.offset)) {
      issues.add('Offset must be 0 unless duplex is +5 MHz.');
    }
  } else {
    issues.add(
      'This radio only allows simplex, receive only (off), '
      'or a +5 MHz repeater.',
    );
  }
  return issues;
}

class RadioChannel {
  RadioChannel({
    required this.location,
    required this.name,
    required this.frequency,
    this.cleared = false,
    this.duplex = '',
    this.offset = 0.6,
    this.tone = '',
    this.txTone = 88.5,
    this.rxTone = 88.5,
    this.dtcs = 23,
    this.dtcsPolarity = 'NN',
    this.rxDtcs = 23,
    this.crossMode = 'Tone->Tone',
    this.mode = 'FM',
    this.step = 5.0,
    this.skip = '',
    this.power = '',
    this.comment = '',
    List<ChannelExtraField>? extras,
  }) : extras = extras ?? [];

  int location;
  bool cleared;
  String name;
  double frequency;
  String duplex;
  double offset;
  String tone;
  double txTone;
  double rxTone;
  int dtcs;
  String dtcsPolarity;
  int rxDtcs;
  String crossMode;
  String mode;
  double step;
  String skip;
  String power;
  String comment;
  List<ChannelExtraField> extras;

  double? get transmitFrequency {
    if (duplex == 'off') return null;
    if (duplex == 'split') return offset;
    if (duplex == '+') return frequency + offset;
    if (duplex == '-') return frequency - offset;
    return frequency;
  }

  RadioChannel copy() => RadioChannel.fromJson(toJson());

  void clear() {
    cleared = true;
    name = '';
    frequency = 0;
    duplex = '';
    offset = 0;
    tone = '';
    txTone = 0;
    rxTone = 0;
    dtcs = 23;
    dtcsPolarity = 'NN';
    rxDtcs = 23;
    crossMode = 'Tone->Tone';
    mode = 'FM';
    step = 5;
    skip = '';
    power = '';
    comment = '';
    extras.clear();
  }

  /// Sets this row to one of the 22 GMRS receive channels.
  ///
  /// The row starts simplex with no offset. Choosing duplex + later
  /// sets the offset to 5 MHz. Fixed rows 1 through 22 do not move.
  void useGmrsReceiveChannel(int channelNumber) {
    if (cleared || _midlandGmrsChannel(location) != null) return;
    final hz = gmrsStandardRxHz(channelNumber);
    if (hz == null) return;
    frequency = hz / 1000000;
    duplex = '';
    offset = 0;
  }

  /// Snaps locked MXT295 fields to the legal GMRS values.
  ///
  /// Channels 23 through 99 keep their frequency. An illegal duplex on
  /// those rows is left in place so the editor can explain it.
  void prepareMxt295Editor() {
    if (cleared) return;
    final fixedHz = midlandFixedRxHz(location);
    if (fixedHz != null) {
      frequency = fixedHz / 1000000;
    }
    if (location >= 8 && location <= 14) {
      duplex = 'off';
      offset = 0;
      return;
    }
    if (midlandRepeaterRxMhz.containsKey(location)) {
      duplex = '+';
      offset = 5;
      return;
    }
    if (location >= 1 && location <= 7) {
      duplex = '';
      offset = 0;
      return;
    }
    final picked = gmrsChannelForHz((frequency * 1000000).round());
    if (location > 30 && picked != null && picked <= 14) {
      duplex = '';
      offset = 0;
      return;
    }
    if (duplex == '+') {
      offset = 5;
    } else if (duplex == '' || duplex == 'off') {
      offset = 0;
    }
  }

  /// Puts the standard GMRS repeater back in this row and clears the name.
  ///
  /// Does nothing when [location] is not one of the eight repeater slots.
  void restorePlainMidlandRepeater() {
    final plainFrequency = midlandRepeaterRxMhz[location];
    if (plainFrequency == null) return;
    cleared = false;
    name = '';
    frequency = plainFrequency;
    duplex = '+';
    offset = 5;
    tone = '';
    txTone = 88.5;
    rxTone = 88.5;
    dtcs = 23;
    dtcsPolarity = 'NN';
    rxDtcs = 23;
    crossMode = 'Tone->Tone';
    mode = 'FM';
    step = 12.5;
    skip = 'S';
    power = 'High';
    comment = '';
    extras.clear();
  }

  Map<String, dynamic> toJson() => {
    'location': location,
    'cleared': cleared,
    'name': name,
    'frequency': frequency,
    'duplex': duplex,
    'offset': offset,
    'tone': tone,
    'txTone': txTone,
    'rxTone': rxTone,
    'dtcs': dtcs,
    'dtcsPolarity': dtcsPolarity,
    'rxDtcs': rxDtcs,
    'crossMode': crossMode,
    'mode': mode,
    'step': step,
    'skip': skip,
    'power': power,
    'comment': comment,
    'extras': extras.map((field) => field.toJson()).toList(),
  };

  factory RadioChannel.fromJson(Map<String, dynamic> json) => RadioChannel(
    location: (json['location'] as num?)?.toInt() ?? 0,
    cleared: json['cleared'] as bool? ?? false,
    name: json['name']?.toString() ?? '',
    frequency: (json['frequency'] as num?)?.toDouble() ?? 0,
    duplex: json['duplex']?.toString() ?? '',
    offset: (json['offset'] as num?)?.toDouble() ?? 0,
    tone: json['tone']?.toString() ?? '',
    txTone: (json['txTone'] as num?)?.toDouble() ?? 88.5,
    rxTone: (json['rxTone'] as num?)?.toDouble() ?? 88.5,
    dtcs: (json['dtcs'] as num?)?.toInt() ?? 23,
    dtcsPolarity: json['dtcsPolarity']?.toString() ?? 'NN',
    rxDtcs: (json['rxDtcs'] as num?)?.toInt() ?? 23,
    crossMode: json['crossMode']?.toString() ?? 'Tone->Tone',
    mode: json['mode']?.toString() ?? 'FM',
    step: (json['step'] as num?)?.toDouble() ?? 5,
    skip: json['skip']?.toString() ?? '',
    power: json['power']?.toString() ?? '',
    comment: json['comment']?.toString() ?? '',
    extras: (json['extras'] as List? ?? const [])
        .map(
          (item) =>
              ChannelExtraField.fromJson((item as Map).cast<String, dynamic>()),
        )
        .toList(),
  );

  static int? nextAvailableLocation(
    Iterable<RadioChannel> channels, {
    int minimum = 1,
    int? maximum,
  }) {
    if (maximum != null && maximum < minimum) return null;
    final occupied = channels.map((channel) => channel.location).toSet();
    final highest = occupied.fold<int?>(
      null,
      (current, location) =>
          current == null || location > current ? location : current,
    );
    if (highest != null) {
      final next = highest + 1;
      if (next >= minimum && (maximum == null || next <= maximum)) {
        if (!occupied.contains(next)) return next;
      }
    } else {
      return minimum;
    }
    if (maximum == null) return minimum;
    for (var location = minimum; location <= maximum; location++) {
      if (!occupied.contains(location)) return location;
    }
    return null;
  }

  List<String> validate({
    int? minimumLocation,
    int? maximumLocation,
    String? radioModel,
    List<double> validTuningSteps = const [],
    List<({double startMhz, double endMhz})> validBands = const [],
    List<String> validModes = const [],
    List<String> validToneModes = const [],
    List<String> validCrossModes = const [],
    bool hasTuningStep = true,
  }) {
    final issues = <String>[];
    if (cleared) return issues;
    if (minimumLocation != null || maximumLocation != null) {
      final belowMinimum =
          minimumLocation != null && location < minimumLocation;
      final aboveMaximum =
          maximumLocation != null && location > maximumLocation;
      if (belowMinimum || aboveMaximum) {
        if (minimumLocation != null && maximumLocation != null) {
          issues.add(
            'Location must be between $minimumLocation and $maximumLocation '
            'for this radio.',
          );
        } else if (minimumLocation != null) {
          issues.add(
            'Location must be at least $minimumLocation for this radio.',
          );
        } else {
          issues.add(
            'Location must be at most $maximumLocation for this radio.',
          );
        }
      }
    } else if (location < 0) {
      issues.add('Location must be zero or greater.');
    }
    if (frequency <= 0 || frequency > 1300) {
      issues.add('Frequency must be between 0 and 1300 MHz.');
    }
    if (!const ['', '+', '-', 'split', 'off'].contains(duplex)) {
      issues.add('Duplex value is not supported.');
    }
    if (validModes.isNotEmpty && !validModes.contains(mode)) {
      issues.add(
        'Mode $mode is not supported by this radio. '
        'Supported modes: ${validModes.join(', ')}.',
      );
    }
    if (validToneModes.isNotEmpty && !validToneModes.contains(tone)) {
      issues.add(
        'Tone mode ${tone.isEmpty ? 'none' : tone} is not supported by this '
        'radio. Supported tone modes: '
        '${validToneModes.map((value) => value.isEmpty ? 'none' : value).join(', ')}.',
      );
    }
    if (tone == 'Cross' &&
        validCrossModes.isNotEmpty &&
        !validCrossModes.contains(crossMode)) {
      issues.add(
        'Cross tone $crossMode is not supported by this radio. Supported '
        'cross tones: ${validCrossModes.join(', ')}.',
      );
    }
    if (name.length > 16) issues.add('Name may be too long for many radios.');
    if (hasTuningStep && validTuningSteps.isNotEmpty && frequency > 0) {
      final frequencyHz = (frequency * 1000000).round();
      final stepSupported = validTuningSteps.any(
        (step) => _frequencyFitsStep(frequencyHz, step),
      );
      if (!stepSupported) {
        final nearest = _nearestFrequencyForSteps(
          frequencyHz,
          validTuningSteps,
        );
        final suggestion = nearest == null
            ? ''
            : ' Nearest supported frequency: '
                  '${(nearest / 1000000).toStringAsFixed(6)} MHz.';
        issues.add(
          'Frequency ${frequency.toStringAsFixed(6)} MHz cannot be '
          'programmed on this radio.$suggestion',
        );
      }
    }
    if (frequency > 0 &&
        validBands.isNotEmpty &&
        !validBands.any(
          (band) => band.startMhz <= frequency && frequency < band.endMhz,
        )) {
      final ranges = validBands
          .map(
            (band) =>
                '${band.startMhz.toStringAsFixed(3)}-'
                '${band.endMhz.toStringAsFixed(3)}',
          )
          .join(' MHz, ');
      issues.add(
        'Frequency ${frequency.toStringAsFixed(6)} MHz is outside this '
        'radio’s supported ranges: $ranges MHz.',
      );
    }
    issues.addAll(midlandGmrsIssues(radioModel, this));
    return issues;
  }
}

bool _frequencyFitsStep(int frequencyHz, double stepKhz) {
  final stepHz = (stepKhz * 1000).round();
  if (stepHz <= 0) return false;
  if ((stepKhz - 8.33).abs() < 0.001) {
    return const {8330, 8333, 16660, 16666}.contains(frequencyHz % 25000);
  }
  return frequencyHz % stepHz == 0;
}

int? _nearestFrequencyForSteps(int frequencyHz, List<double> steps) {
  int? nearest;
  var nearestDistance = 1 << 62;
  for (final stepKhz in steps) {
    if ((stepKhz - 8.33).abs() < 0.001) continue;
    final stepHz = (stepKhz * 1000).round();
    if (stepHz <= 0) continue;
    final candidate = ((frequencyHz / stepHz).round() * stepHz);
    final distance = (candidate - frequencyHz).abs();
    if (distance < nearestDistance) {
      nearest = candidate;
      nearestDistance = distance;
    }
  }
  return nearest;
}

class ChannelExtraField {
  ChannelExtraField({
    required this.name,
    required this.label,
    required this.kind,
    required this.value,
    this.choices = const [],
    this.mutable = true,
    this.documentation,
  });

  final String name;
  final String label;
  final String kind;
  dynamic value;
  final List<String> choices;
  final bool mutable;
  final String? documentation;

  Map<String, dynamic> toJson() => {
    'name': name,
    'label': label,
    'kind': kind,
    'value': value,
    'choices': choices,
    'mutable': mutable,
    'documentation': documentation,
  };

  factory ChannelExtraField.fromJson(Map<String, dynamic> json) =>
      ChannelExtraField(
        name: json['name']?.toString() ?? '',
        label: json['label']?.toString() ?? '',
        kind: json['kind']?.toString() ?? 'string',
        value: json['value'],
        choices: (json['choices'] as List? ?? const [])
            .map((choice) => choice.toString())
            .toList(),
        mutable: json['mutable'] as bool? ?? true,
        documentation: json['documentation']?.toString(),
      );
}

List<RadioChannel> gmrsStarterChannels() {
  const frequencies = <double>[
    462.5625,
    462.5875,
    462.6125,
    462.6375,
    462.6625,
    462.6875,
    462.7125,
    467.5625,
    467.5875,
    467.6125,
    467.6375,
    467.6625,
    467.6875,
    467.7125,
    462.5500,
    462.5750,
    462.6000,
    462.6250,
    462.6500,
    462.6750,
    462.7000,
    462.7250,
  ];
  return [
    for (var i = 0; i < frequencies.length; i++)
      RadioChannel(
        location: i + 1,
        name: 'GMRS ${i + 1}',
        frequency: frequencies[i],
        duplex: i >= 14 ? '+' : '',
        offset: i >= 14 ? 5.0 : 0,
        mode: i < 7 ? 'NFM' : 'FM',
        step: 2.5,
        comment: i >= 14 ? 'GMRS repeater output' : 'GMRS simplex',
      ),
  ];
}
