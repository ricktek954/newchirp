class FrequencyReferenceRow {
  const FrequencyReferenceRow({
    required this.channel,
    required this.frequency,
    required this.notes,
  });

  final String channel;
  final String frequency;
  final String notes;
}

class FrequencyReferenceGroup {
  const FrequencyReferenceGroup({
    required this.title,
    required this.note,
    required this.rows,
  });

  final String title;
  final String note;
  final List<FrequencyReferenceRow> rows;
}

class FrequencyReferencePlan {
  const FrequencyReferencePlan({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.source,
    required this.pdfAsset,
    required this.groups,
  });

  final String id;
  final String title;
  final String subtitle;
  final String source;
  final String pdfAsset;
  final List<FrequencyReferenceGroup> groups;
}

List<FrequencyReferenceRow> _australianUhfRows() {
  return [
    for (var channel = 1; channel <= 80; channel++)
      FrequencyReferenceRow(
        channel: '$channel',
        frequency:
            (channel <= 40
                    ? 476.425 + (channel - 1) * 0.025
                    : 476.4375 + (channel - 41) * 0.025)
                .toStringAsFixed(4),
        notes: _australianUhfNote(channel),
      ),
  ];
}

String _australianUhfNote(int channel) {
  if (channel >= 1 && channel <= 8) {
    return channel == 5
        ? 'Emergency output; input Ch 35'
        : 'Repeater output; input Ch ${channel + 30}';
  }
  if (channel >= 31 && channel <= 38) {
    return channel == 35
        ? 'Emergency input; output Ch 05'
        : 'Repeater input; output Ch ${(channel - 30).toString().padLeft(2, '0')}';
  }
  if (channel >= 41 && channel <= 48) {
    return const {44, 45}.contains(channel)
        ? 'Repeater output; guard caution'
        : 'Repeater output; input Ch ${channel + 30}';
  }
  if (channel >= 71 && channel <= 78) {
    return const {74, 75}.contains(channel)
        ? 'Repeater input; guard caution'
        : 'Repeater input; output Ch ${(channel - 30).toString().padLeft(2, '0')}';
  }
  if (channel >= 61 && channel <= 63) {
    return 'Guard channel; receive-only';
  }
  if (channel == 22 || channel == 23) {
    return 'Data/telemetry only; no voice';
  }
  return switch (channel) {
    10 => '4WD / off-road / parks',
    11 => 'Call channel; then move',
    18 => 'Caravan / camper convoy',
    29 => 'Road: Pacific / Hume Hwy',
    30 => 'UHF CB broadcasts / simplex',
    40 => 'Australia-wide road / truck',
    _ => 'General simplex',
  };
}

List<FrequencyReferenceRow> _standardCbRows() {
  const mhz = [
    26.965,
    26.975,
    26.985,
    26.995,
    27.005,
    27.015,
    27.025,
    27.055,
    27.065,
    27.075,
    27.085,
    27.105,
    27.115,
    27.125,
    27.135,
    27.155,
    27.165,
    27.175,
    27.185,
    27.205,
    27.215,
    27.225,
    27.255,
    27.235,
    27.245,
    27.265,
    27.275,
    27.285,
    27.295,
    27.305,
    27.315,
    27.325,
    27.335,
    27.345,
    27.355,
    27.365,
    27.375,
    27.385,
    27.395,
    27.405,
  ];
  return [
    for (var index = 0; index < mhz.length; index++)
      FrequencyReferenceRow(
        channel: '${index + 1}',
        frequency: mhz[index].toStringAsFixed(3),
        notes: switch (index) {
          8 => 'Emergency / calling convention',
          15 => 'Australia: local calling (LSB)',
          18 => 'Common highway / travel convention',
          34 => 'Australia: DX calling (LSB)',
          _ => 'AM/SSB 27 MHz CB',
        },
      ),
  ];
}

List<FrequencyReferenceRow> _ukCbRows() {
  return [
    for (var channel = 1; channel <= 40; channel++)
      FrequencyReferenceRow(
        channel: '$channel',
        frequency: (27.60125 + (channel - 1) * 0.01).toStringAsFixed(5),
        notes: 'UK 27 MHz CB (27/81 band)',
      ),
  ];
}

final marineVhfReferencePlan = FrequencyReferencePlan(
  id: 'marine-vhf',
  title: 'International Marine VHF',
  subtitle: 'ITU Appendix 18 marine voice and DSC channels',
  source:
      'ITU Radio Regulations Appendix 18; national channel restrictions may '
      'differ.',
  pdfAsset: 'assets/Marine_VHF_Frequency_Reference.pdf',
  groups: [
    FrequencyReferenceGroup(
      title: 'Marine VHF channels',
      note:
          'Ship transmit frequencies are shown. Duplex channels use a '
          '160-162 MHz coast-station transmit frequency.',
      rows: const [
        FrequencyReferenceRow(
          channel: '01',
          frequency: '156.050',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '02',
          frequency: '156.100',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '03',
          frequency: '156.150',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '04',
          frequency: '156.200',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '05',
          frequency: '156.250',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '06',
          frequency: '156.300',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '07',
          frequency: '156.350',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '08',
          frequency: '156.400',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '09',
          frequency: '156.450',
          notes: 'Calling',
        ),
        FrequencyReferenceRow(
          channel: '10',
          frequency: '156.500',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '11',
          frequency: '156.550',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '12',
          frequency: '156.600',
          notes: 'Port operations',
        ),
        FrequencyReferenceRow(
          channel: '13',
          frequency: '156.650',
          notes: 'Bridge-to-bridge',
        ),
        FrequencyReferenceRow(
          channel: '14',
          frequency: '156.700',
          notes: 'Port operations',
        ),
        FrequencyReferenceRow(
          channel: '15',
          frequency: '156.750',
          notes: 'Low power',
        ),
        FrequencyReferenceRow(
          channel: '16',
          frequency: '156.800',
          notes: 'Distress / safety / calling',
        ),
        FrequencyReferenceRow(
          channel: '17',
          frequency: '156.850',
          notes: 'Low power',
        ),
        FrequencyReferenceRow(
          channel: '18',
          frequency: '156.900',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '19',
          frequency: '156.950',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '20',
          frequency: '157.000',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '21',
          frequency: '157.050',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '22',
          frequency: '157.100',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '23',
          frequency: '157.150',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '24',
          frequency: '157.200',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '25',
          frequency: '157.250',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '26',
          frequency: '157.300',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '27',
          frequency: '157.350',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '28',
          frequency: '157.400',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '60',
          frequency: '156.025',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '61',
          frequency: '156.075',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '62',
          frequency: '156.125',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '63',
          frequency: '156.175',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '64',
          frequency: '156.225',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '65',
          frequency: '156.275',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '66',
          frequency: '156.325',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '67',
          frequency: '156.375',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '68',
          frequency: '156.425',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '69',
          frequency: '156.475',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '70',
          frequency: '156.525',
          notes: 'DSC only; no voice',
        ),
        FrequencyReferenceRow(
          channel: '71',
          frequency: '156.575',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '72',
          frequency: '156.625',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '73',
          frequency: '156.675',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '74',
          frequency: '156.725',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '75',
          frequency: '156.775',
          notes: 'Restrictions may apply',
        ),
        FrequencyReferenceRow(
          channel: '76',
          frequency: '156.825',
          notes: 'Restrictions may apply',
        ),
        FrequencyReferenceRow(
          channel: '77',
          frequency: '156.875',
          notes: 'Inter-ship',
        ),
        FrequencyReferenceRow(
          channel: '78',
          frequency: '156.925',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '79',
          frequency: '156.975',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '80',
          frequency: '157.025',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '81',
          frequency: '157.075',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '82',
          frequency: '157.125',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '83',
          frequency: '157.175',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '84',
          frequency: '157.225',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '85',
          frequency: '157.275',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '86',
          frequency: '157.325',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '87',
          frequency: '157.375',
          notes: 'Duplex',
        ),
        FrequencyReferenceRow(
          channel: '88',
          frequency: '157.425',
          notes: 'Duplex',
        ),
      ],
    ),
  ],
);

final cb27ReferencePlan = FrequencyReferencePlan(
  id: 'cb-27',
  title: '27 MHz CB',
  subtitle: 'US / Canada / Australia / New Zealand and UK CB channels',
  source:
      'FCC 47 CFR Part 95 Subpart D, ISED RSS-210, ACMA CB class licence, '
      'Ofcom UK CB rules.',
  pdfAsset: 'assets/CB_27MHz_Frequency_Reference.pdf',
  groups: [
    FrequencyReferenceGroup(
      title: '40-channel AM/SSB plan',
      note:
          'Shared channel numbering used in the US, Canada, Australia, and '
          'New Zealand. Power, mode, and licence rules differ by country.',
      rows: _standardCbRows(),
    ),
    FrequencyReferenceGroup(
      title: 'UK CB 27/81 band',
      note:
          'Legacy UK-only 40-channel FM band. Modern UK radios may also '
          'provide the CEPT/standard 40-channel plan above.',
      rows: _ukCbRows(),
    ),
  ],
);

final australianUhfCbReferencePlan = FrequencyReferencePlan(
  id: 'australia-uhf-cb',
  title: 'Australian UHF CB',
  subtitle: '80-channel 476-477 MHz Australian Citizens Band plan',
  source:
      'Australian Communications and Media Authority CB radio class licence.',
  pdfAsset: 'assets/Australia_UHF_CB_Frequency_Reference.pdf',
  groups: [
    FrequencyReferenceGroup(
      title: 'Australian UHF CB channels',
      note:
          'Two interleaved 25 kHz grids offset by 12.5 kHz. Repeater outputs '
          'are channels 1-8 and 41-48; inputs are 31-38 and 71-78, 750 kHz '
          'higher. Verify the current ACMA class licence before operating.',
      rows: _australianUhfRows(),
    ),
  ],
);

final internationalFrequencyReferencePlans = [
  marineVhfReferencePlan,
  cb27ReferencePlan,
  australianUhfCbReferencePlan,
];
