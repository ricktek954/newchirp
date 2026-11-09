import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/marine_channels.dart';

void main() {
  test('US marine template is receive-only by default', () {
    final channels = marineTemplateChannels(
      const MarineTemplateSelection(
        plan: MarineChannelPlan.unitedStates,
        programTransmit: false,
      ),
    );

    expect(channels, hasLength(56));
    expect(channels.every((channel) => channel.duplex == 'off'), isTrue);
    expect(
      channels.map((channel) => channel.name),
      containsAll(['SEA 01', 'SEA 16', 'SEA 24', 'DSC 70', 'AIS 1', 'WX 7']),
    );
    expect(channels.map((channel) => channel.name), isNot(contains('SEA 03')));
  });

  test('US marine transmit pairs use the coast receive frequency', () {
    final channels = marineTemplateChannels(
      const MarineTemplateSelection(
        plan: MarineChannelPlan.unitedStates,
        programTransmit: true,
      ),
    );
    final channel24 = channels.firstWhere(
      (channel) => channel.name == 'SEA 24',
    );
    final channel16 = channels.firstWhere(
      (channel) => channel.name == 'SEA 16',
    );
    final dsc = channels.firstWhere((channel) => channel.name == 'DSC 70');
    final ais = channels.firstWhere((channel) => channel.name == 'AIS 1');
    final weather = channels.firstWhere((channel) => channel.name == 'WX 1');

    expect(channel24.frequency, 161.800);
    expect(channel24.duplex, '-');
    expect(channel24.offset, closeTo(4.6, 0.000001));
    expect(channel24.transmitFrequency, closeTo(157.200, 0.000001));
    expect(channel16.frequency, 156.800);
    expect(channel16.duplex, isEmpty);
    expect(channel16.transmitFrequency, closeTo(156.800, 0.000001));
    expect(dsc.transmitFrequency, isNull);
    expect(ais.transmitFrequency, isNull);
    expect(weather.transmitFrequency, isNull);
  });

  test('international plan uses ITU ship and coast pairs', () {
    final channels = marineTemplateChannels(
      const MarineTemplateSelection(
        plan: MarineChannelPlan.international,
        programTransmit: true,
      ),
    );
    final channel1 = channels.firstWhere((channel) => channel.name == 'INT 01');
    final channel60 = channels.firstWhere(
      (channel) => channel.name == 'INT 60',
    );
    final channel87 = channels.firstWhere(
      (channel) => channel.name == 'INT 87',
    );
    final ais2 = channels.firstWhere((channel) => channel.name == 'AIS 2');

    expect(channel1.frequency, 160.650);
    expect(channel1.transmitFrequency, closeTo(156.050, 0.000001));
    expect(channel60.frequency, 160.625);
    expect(channel60.transmitFrequency, closeTo(156.025, 0.000001));
    expect(channel87.frequency, 157.375);
    expect(channel87.transmitFrequency, closeTo(157.375, 0.000001));
    expect(ais2.frequency, 162.025);
    expect(ais2.transmitFrequency, isNull);
  });

  test('marine templates have safe identifiers and transmit frequencies', () {
    for (final plan in MarineChannelPlan.values) {
      final definitions = marineChannelDefinitionsFor(plan);
      final names = definitions.map((channel) => channel.name).toList();
      expect(names.toSet(), hasLength(names.length), reason: plan.label);
      expect(
        names.every((name) => name.length <= 8),
        isTrue,
        reason: '${plan.label} names must fit an eight-character radio',
      );
      for (final channel in definitions) {
        expect(channel.receiveMhz, inInclusiveRange(156.0, 162.550));
        if (channel.transmitMhz != null) {
          expect(channel.transmitMhz, inInclusiveRange(156.025, 157.425));
        }
      }
    }
  });
}
