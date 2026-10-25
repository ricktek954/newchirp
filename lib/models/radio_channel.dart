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

  List<String> validate({int? minimumLocation, int? maximumLocation}) {
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
    if (name.length > 16) issues.add('Name may be too long for many radios.');
    return issues;
  }
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
