import 'radio_channel.dart';

/// Regulatory plans supported by the built-in Marine VHF template.
enum MarineChannelPlan { unitedStates, international }

extension MarineChannelPlanDetails on MarineChannelPlan {
  String get label => switch (this) {
    MarineChannelPlan.unitedStates => 'United States',
    MarineChannelPlan.international => 'International (ITU)',
  };

  String get libraryName => switch (this) {
    MarineChannelPlan.unitedStates => 'US Marine VHF',
    MarineChannelPlan.international => 'International Marine VHF',
  };

  String get description => switch (this) {
    MarineChannelPlan.unitedStates =>
      'Nationwide US ship and coast channels from FCC 47 CFR Part 80, '
          'including DSC, AIS, and NOAA weather receive channels.',
    MarineChannelPlan.international =>
      'ITU Appendix 18 ship and coast channels. National authorities may '
          'change permitted use, power, or channel availability.',
  };

  String get source => switch (this) {
    MarineChannelPlan.unitedStates =>
      'FCC 47 CFR 80.371(c), 80.373(f), and NOAA Weather Radio',
    MarineChannelPlan.international => 'ITU Radio Regulations Appendix 18',
  };
}

class MarineChannelDefinition {
  const MarineChannelDefinition({
    required this.name,
    required this.receiveMhz,
    this.transmitMhz,
    required this.purpose,
  });

  final String name;
  final double receiveMhz;
  final double? transmitMhz;
  final String purpose;

  bool get receiveOnly => transmitMhz == null;
}

class MarineTemplateSelection {
  const MarineTemplateSelection({
    required this.plan,
    required this.programTransmit,
  });

  final MarineChannelPlan plan;
  final bool programTransmit;
}

List<RadioChannel> marineTemplateChannels(MarineTemplateSelection selection) {
  final definitions = marineChannelDefinitionsFor(selection.plan);
  return [
    for (var index = 0; index < definitions.length; index++)
      _channelFromDefinition(
        index + 1,
        definitions[index],
        programTransmit: selection.programTransmit,
        plan: selection.plan,
      ),
  ];
}

RadioChannel _channelFromDefinition(
  int location,
  MarineChannelDefinition definition, {
  required bool programTransmit,
  required MarineChannelPlan plan,
}) {
  final transmit = definition.transmitMhz;
  final canTransmit = programTransmit && transmit != null;
  final offset = canTransmit ? definition.receiveMhz - transmit : 0.0;
  final duplex = !canTransmit
      ? 'off'
      : offset > 0
      ? '-'
      : offset < 0
      ? '+'
      : '';
  return RadioChannel(
    location: location,
    name: definition.name,
    frequency: definition.receiveMhz,
    duplex: duplex,
    offset: offset.abs(),
    mode: 'FM',
    step: 5.0,
    comment:
        '${definition.purpose} • ${plan.source}'
        '${definition.receiveOnly ? ' • Receive only' : ''}',
  );
}

List<MarineChannelDefinition> marineChannelDefinitionsFor(
  MarineChannelPlan plan,
) => switch (plan) {
  MarineChannelPlan.unitedStates => usMarineVhfChannels,
  MarineChannelPlan.international => internationalMarineVhfChannels,
};

const usMarineVhfChannels = <MarineChannelDefinition>[
  MarineChannelDefinition(
    name: 'SEA 01',
    receiveMhz: 156.050,
    transmitMhz: 156.050,
    purpose: 'Port operations and commercial; limited VTS areas',
  ),
  MarineChannelDefinition(
    name: 'SEA 05',
    receiveMhz: 156.250,
    transmitMhz: 156.250,
    purpose: 'Port operations; limited VTS areas',
  ),
  MarineChannelDefinition(
    name: 'SEA 06',
    receiveMhz: 156.300,
    transmitMhz: 156.300,
    purpose: 'Intership safety and SAR',
  ),
  MarineChannelDefinition(
    name: 'SEA 07',
    receiveMhz: 156.350,
    transmitMhz: 156.350,
    purpose: 'Commercial',
  ),
  MarineChannelDefinition(
    name: 'SEA 08',
    receiveMhz: 156.400,
    transmitMhz: 156.400,
    purpose: 'Commercial intership',
  ),
  MarineChannelDefinition(
    name: 'SEA 09',
    receiveMhz: 156.450,
    transmitMhz: 156.450,
    purpose: 'Boater calling and commercial or non-commercial working',
  ),
  MarineChannelDefinition(
    name: 'SEA 10',
    receiveMhz: 156.500,
    transmitMhz: 156.500,
    purpose: 'Commercial',
  ),
  MarineChannelDefinition(
    name: 'SEA 11',
    receiveMhz: 156.550,
    transmitMhz: 156.550,
    purpose: 'VTS and port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 12',
    receiveMhz: 156.600,
    transmitMhz: 156.600,
    purpose: 'VTS and port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 13',
    receiveMhz: 156.650,
    transmitMhz: 156.650,
    purpose: 'Bridge-to-bridge navigation safety; normally 1 W',
  ),
  MarineChannelDefinition(
    name: 'SEA 14',
    receiveMhz: 156.700,
    transmitMhz: 156.700,
    purpose: 'VTS and port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 15',
    receiveMhz: 156.750,
    purpose: 'Environmental; coast-to-ship receive only',
  ),
  MarineChannelDefinition(
    name: 'SEA 16',
    receiveMhz: 156.800,
    transmitMhz: 156.800,
    purpose: 'International distress, safety, and calling',
  ),
  MarineChannelDefinition(
    name: 'SEA 17',
    receiveMhz: 156.850,
    transmitMhz: 156.850,
    purpose: 'Maritime control',
  ),
  MarineChannelDefinition(
    name: 'SEA 18',
    receiveMhz: 156.900,
    transmitMhz: 156.900,
    purpose: 'Commercial',
  ),
  MarineChannelDefinition(
    name: 'SEA 19',
    receiveMhz: 156.950,
    transmitMhz: 156.950,
    purpose: 'Commercial',
  ),
  MarineChannelDefinition(
    name: 'SEA 20',
    receiveMhz: 157.000,
    transmitMhz: 157.000,
    purpose: 'Port operations intership',
  ),
  MarineChannelDefinition(
    name: 'SEA 21',
    receiveMhz: 157.050,
    purpose: 'US Coast Guard; receive only for ordinary vessels',
  ),
  MarineChannelDefinition(
    name: 'SEA 22',
    receiveMhz: 157.100,
    transmitMhz: 157.100,
    purpose: 'US Coast Guard liaison and safety broadcasts',
  ),
  MarineChannelDefinition(
    name: 'SEA 23',
    receiveMhz: 157.150,
    purpose: 'US Government only; receive only',
  ),
  MarineChannelDefinition(
    name: 'SEA 24',
    receiveMhz: 161.800,
    transmitMhz: 157.200,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 25',
    receiveMhz: 161.850,
    transmitMhz: 157.250,
    purpose: 'Public correspondence; unavailable in some inland VPCSAs',
  ),
  MarineChannelDefinition(
    name: 'SEA 26',
    receiveMhz: 161.900,
    transmitMhz: 157.300,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 27',
    receiveMhz: 161.950,
    transmitMhz: 157.350,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 28',
    receiveMhz: 162.000,
    transmitMhz: 157.400,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 63',
    receiveMhz: 156.175,
    transmitMhz: 156.175,
    purpose: 'Port operations and commercial; limited VTS areas',
  ),
  MarineChannelDefinition(
    name: 'SEA 65',
    receiveMhz: 156.275,
    transmitMhz: 156.275,
    purpose: 'Port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 66',
    receiveMhz: 156.325,
    transmitMhz: 156.325,
    purpose: 'Port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 67',
    receiveMhz: 156.375,
    transmitMhz: 156.375,
    purpose: 'Bridge-to-bridge navigation; normally 1 W',
  ),
  MarineChannelDefinition(
    name: 'SEA 68',
    receiveMhz: 156.425,
    transmitMhz: 156.425,
    purpose: 'Non-commercial working',
  ),
  MarineChannelDefinition(
    name: 'SEA 69',
    receiveMhz: 156.475,
    transmitMhz: 156.475,
    purpose: 'Non-commercial working',
  ),
  MarineChannelDefinition(
    name: 'DSC 70',
    receiveMhz: 156.525,
    purpose: 'Digital Selective Calling; voice transmission prohibited',
  ),
  MarineChannelDefinition(
    name: 'SEA 71',
    receiveMhz: 156.575,
    transmitMhz: 156.575,
    purpose: 'Non-commercial working',
  ),
  MarineChannelDefinition(
    name: 'SEA 72',
    receiveMhz: 156.625,
    transmitMhz: 156.625,
    purpose: 'Non-commercial intership',
  ),
  MarineChannelDefinition(
    name: 'SEA 73',
    receiveMhz: 156.675,
    transmitMhz: 156.675,
    purpose: 'Port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 74',
    receiveMhz: 156.725,
    transmitMhz: 156.725,
    purpose: 'Port operations',
  ),
  MarineChannelDefinition(
    name: 'SEA 77',
    receiveMhz: 156.875,
    transmitMhz: 156.875,
    purpose: 'Pilot and docking communications; normally 1 W',
  ),
  MarineChannelDefinition(
    name: 'SEA 78',
    receiveMhz: 156.925,
    transmitMhz: 156.925,
    purpose: 'Non-commercial working',
  ),
  MarineChannelDefinition(
    name: 'SEA 79',
    receiveMhz: 156.975,
    transmitMhz: 156.975,
    purpose: 'Commercial and Great Lakes non-commercial',
  ),
  MarineChannelDefinition(
    name: 'SEA 80',
    receiveMhz: 157.025,
    transmitMhz: 157.025,
    purpose: 'Commercial and Great Lakes non-commercial',
  ),
  MarineChannelDefinition(
    name: 'SEA 81',
    receiveMhz: 157.075,
    purpose: 'US Government only; receive only',
  ),
  MarineChannelDefinition(
    name: 'SEA 82',
    receiveMhz: 157.125,
    purpose: 'US Government only; receive only',
  ),
  MarineChannelDefinition(
    name: 'SEA 83',
    receiveMhz: 157.175,
    purpose: 'US Government only; receive only for ordinary vessels',
  ),
  MarineChannelDefinition(
    name: 'SEA 84',
    receiveMhz: 161.825,
    transmitMhz: 157.225,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 85',
    receiveMhz: 161.875,
    transmitMhz: 157.275,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 86',
    receiveMhz: 161.925,
    transmitMhz: 157.325,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'SEA 88',
    receiveMhz: 157.425,
    transmitMhz: 157.425,
    purpose: 'Commercial and fishing; geographically limited',
  ),
  MarineChannelDefinition(
    name: 'AIS 1',
    receiveMhz: 161.975,
    purpose: 'Automatic Identification System; receive only',
  ),
  MarineChannelDefinition(
    name: 'AIS 2',
    receiveMhz: 162.025,
    purpose: 'Automatic Identification System; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 1',
    receiveMhz: 162.550,
    purpose: 'NOAA weather; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 2',
    receiveMhz: 162.400,
    purpose: 'NOAA weather; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 3',
    receiveMhz: 162.475,
    purpose: 'NOAA weather; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 4',
    receiveMhz: 162.425,
    purpose: 'NOAA weather; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 5',
    receiveMhz: 162.450,
    purpose: 'NOAA weather; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 6',
    receiveMhz: 162.500,
    purpose: 'NOAA weather; receive only',
  ),
  MarineChannelDefinition(
    name: 'WX 7',
    receiveMhz: 162.525,
    purpose: 'NOAA weather; receive only',
  ),
];

const internationalMarineVhfChannels = <MarineChannelDefinition>[
  MarineChannelDefinition(
    name: 'INT 01',
    receiveMhz: 160.650,
    transmitMhz: 156.050,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 02',
    receiveMhz: 160.700,
    transmitMhz: 156.100,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 03',
    receiveMhz: 160.750,
    transmitMhz: 156.150,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 04',
    receiveMhz: 160.800,
    transmitMhz: 156.200,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 05',
    receiveMhz: 160.850,
    transmitMhz: 156.250,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 06',
    receiveMhz: 156.300,
    transmitMhz: 156.300,
    purpose: 'Intership safety and ship-to-air',
  ),
  MarineChannelDefinition(
    name: 'INT 07',
    receiveMhz: 160.950,
    transmitMhz: 156.350,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 08',
    receiveMhz: 156.400,
    transmitMhz: 156.400,
    purpose: 'Intership working',
  ),
  MarineChannelDefinition(
    name: 'INT 09',
    receiveMhz: 156.450,
    transmitMhz: 156.450,
    purpose: 'Calling and working; national use varies',
  ),
  MarineChannelDefinition(
    name: 'INT 10',
    receiveMhz: 156.500,
    transmitMhz: 156.500,
    purpose: 'Intership and port operations; national use varies',
  ),
  MarineChannelDefinition(
    name: 'INT 11',
    receiveMhz: 156.550,
    transmitMhz: 156.550,
    purpose: 'Port operations',
  ),
  MarineChannelDefinition(
    name: 'INT 12',
    receiveMhz: 156.600,
    transmitMhz: 156.600,
    purpose: 'Port operations',
  ),
  MarineChannelDefinition(
    name: 'INT 13',
    receiveMhz: 156.650,
    transmitMhz: 156.650,
    purpose: 'Bridge-to-bridge navigation safety',
  ),
  MarineChannelDefinition(
    name: 'INT 14',
    receiveMhz: 156.700,
    transmitMhz: 156.700,
    purpose: 'Port operations and pilot communications',
  ),
  MarineChannelDefinition(
    name: 'INT 15',
    receiveMhz: 156.750,
    transmitMhz: 156.750,
    purpose: 'On-board and operational working; normally 1 W',
  ),
  MarineChannelDefinition(
    name: 'INT 16',
    receiveMhz: 156.800,
    transmitMhz: 156.800,
    purpose: 'International distress, safety, and calling',
  ),
  MarineChannelDefinition(
    name: 'INT 17',
    receiveMhz: 156.850,
    transmitMhz: 156.850,
    purpose: 'On-board and operational working; normally 1 W',
  ),
  MarineChannelDefinition(
    name: 'INT 18',
    receiveMhz: 161.500,
    transmitMhz: 156.900,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 19',
    receiveMhz: 161.550,
    transmitMhz: 156.950,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 20',
    receiveMhz: 161.600,
    transmitMhz: 157.000,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 21',
    receiveMhz: 161.650,
    transmitMhz: 157.050,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 22',
    receiveMhz: 161.700,
    transmitMhz: 157.100,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 23',
    receiveMhz: 161.750,
    transmitMhz: 157.150,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 24',
    receiveMhz: 161.800,
    transmitMhz: 157.200,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'INT 25',
    receiveMhz: 161.850,
    transmitMhz: 157.250,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'INT 26',
    receiveMhz: 161.900,
    transmitMhz: 157.300,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'INT 27',
    receiveMhz: 161.950,
    transmitMhz: 157.350,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'INT 28',
    receiveMhz: 162.000,
    transmitMhz: 157.400,
    purpose: 'Public correspondence ship-to-shore',
  ),
  MarineChannelDefinition(
    name: 'INT 60',
    receiveMhz: 160.625,
    transmitMhz: 156.025,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 61',
    receiveMhz: 160.675,
    transmitMhz: 156.075,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 62',
    receiveMhz: 160.725,
    transmitMhz: 156.125,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 63',
    receiveMhz: 160.775,
    transmitMhz: 156.175,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 64',
    receiveMhz: 160.825,
    transmitMhz: 156.225,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 65',
    receiveMhz: 160.875,
    transmitMhz: 156.275,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 66',
    receiveMhz: 160.925,
    transmitMhz: 156.325,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 67',
    receiveMhz: 156.375,
    transmitMhz: 156.375,
    purpose: 'Intership and small-ship safety',
  ),
  MarineChannelDefinition(
    name: 'INT 68',
    receiveMhz: 156.425,
    transmitMhz: 156.425,
    purpose: 'Intership and non-commercial working',
  ),
  MarineChannelDefinition(
    name: 'INT 69',
    receiveMhz: 156.475,
    transmitMhz: 156.475,
    purpose: 'Intership and port operations',
  ),
  MarineChannelDefinition(
    name: 'DSC 70',
    receiveMhz: 156.525,
    purpose: 'Digital Selective Calling; voice transmission prohibited',
  ),
  MarineChannelDefinition(
    name: 'INT 71',
    receiveMhz: 156.575,
    transmitMhz: 156.575,
    purpose: 'Intership and port operations',
  ),
  MarineChannelDefinition(
    name: 'INT 72',
    receiveMhz: 156.625,
    transmitMhz: 156.625,
    purpose: 'Intership working',
  ),
  MarineChannelDefinition(
    name: 'INT 73',
    receiveMhz: 156.675,
    transmitMhz: 156.675,
    purpose: 'Intership and port operations',
  ),
  MarineChannelDefinition(
    name: 'INT 74',
    receiveMhz: 156.725,
    transmitMhz: 156.725,
    purpose: 'Intership and port operations',
  ),
  MarineChannelDefinition(
    name: 'AIS LR1',
    receiveMhz: 156.775,
    purpose: 'Long-range AIS messages; receive only',
  ),
  MarineChannelDefinition(
    name: 'AIS LR2',
    receiveMhz: 156.825,
    purpose: 'Long-range AIS messages; receive only',
  ),
  MarineChannelDefinition(
    name: 'INT 77',
    receiveMhz: 156.875,
    transmitMhz: 156.875,
    purpose: 'Intership working',
  ),
  MarineChannelDefinition(
    name: 'INT 78',
    receiveMhz: 161.525,
    transmitMhz: 156.925,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 79',
    receiveMhz: 161.575,
    transmitMhz: 156.975,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 80',
    receiveMhz: 161.625,
    transmitMhz: 157.025,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 81',
    receiveMhz: 161.675,
    transmitMhz: 157.075,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 82',
    receiveMhz: 161.725,
    transmitMhz: 157.125,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 83',
    receiveMhz: 161.775,
    transmitMhz: 157.175,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 84',
    receiveMhz: 161.825,
    transmitMhz: 157.225,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 85',
    receiveMhz: 161.875,
    transmitMhz: 157.275,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 86',
    receiveMhz: 161.925,
    transmitMhz: 157.325,
    purpose: 'International ship-to-shore pair',
  ),
  MarineChannelDefinition(
    name: 'INT 87',
    receiveMhz: 157.375,
    transmitMhz: 157.375,
    purpose: 'Ship-side simplex; 161.975 MHz is AIS only',
  ),
  MarineChannelDefinition(
    name: 'INT 88',
    receiveMhz: 157.425,
    transmitMhz: 157.425,
    purpose: 'Ship-side commercial simplex; 162.025 MHz is AIS only',
  ),
  MarineChannelDefinition(
    name: 'AIS 1',
    receiveMhz: 161.975,
    purpose: 'Automatic Identification System; receive only',
  ),
  MarineChannelDefinition(
    name: 'AIS 2',
    receiveMhz: 162.025,
    purpose: 'Automatic Identification System; receive only',
  ),
];
