import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/models/radio_mapping.dart';
import 'package:newchirp/widgets/radio_mapping_dialog.dart';

const _dm32Zones = RadioMappingModel(
  index: 0,
  name: 'Zones',
  editable: true,
  multiple: true,
  mappings: [
    RadioMappingEntry(
      index: '1',
      name: 'Analog',
      channelLocations: [1],
      nameEditable: true,
    ),
    RadioMappingEntry(
      index: '2',
      name: 'Digital',
      channelLocations: [10],
      nameEditable: true,
    ),
    RadioMappingEntry(
      index: '3',
      name: 'New zone',
      channelLocations: [],
      nameEditable: true,
    ),
  ],
);

class _DialogResult {
  List<RadioMappingModel>? value;
}

Future<_DialogResult> _showDialog(
  WidgetTester tester, {
  RadioMappingModel model = _dm32Zones,
}) async {
  final result = _DialogResult();
  await tester.binding.setSurfaceSize(const Size(1200, 900));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: Builder(
          builder: (context) => FilledButton(
            onPressed: () async {
              result.value = await showDialog<List<RadioMappingModel>>(
                context: context,
                builder: (context) => RadioMappingDialog(
                  models: [model],
                  channels: [
                    RadioChannel(location: 1, name: 'Local', frequency: 146.52),
                    RadioChannel(
                      location: 10,
                      name: 'DMR',
                      frequency: 444.0,
                      mode: 'DMR',
                    ),
                  ],
                  radioName: 'Baofeng DM-32UV',
                ),
              );
            },
            child: const Text('Open'),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('Open'));
  await tester.pumpAndSettle();
  return result;
}

void main() {
  testWidgets('creates and names a zone from the spare entry', (tester) async {
    final captured = await _showDialog(tester);

    await tester.tap(find.text('New zone'));
    await tester.pump();
    await tester.enterText(
      find.byKey(const ValueKey('radio-mapping-name')),
      'Local',
    );
    await tester.tap(find.byKey(const ValueKey('radio-mapping-channel-10')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('apply-radio-mappings')));
    await tester.pumpAndSettle();

    expect(find.byType(RadioMappingDialog), findsNothing);
    final local = captured.value!.single.mappings[2];
    expect(local.name, 'Local');
    expect(local.channelLocations, [10]);
  });

  testWidgets('allows a channel in multiple zones', (tester) async {
    final captured = await _showDialog(tester);

    await tester.tap(find.text('New zone'));
    await tester.pump();
    await tester.enterText(
      find.byKey(const ValueKey('radio-mapping-name')),
      'Local',
    );
    await tester.tap(find.byKey(const ValueKey('radio-mapping-channel-1')));
    await tester.pump();
    await tester.tap(find.byKey(const ValueKey('apply-radio-mappings')));
    await tester.pumpAndSettle();

    expect(find.byType(RadioMappingDialog), findsNothing);
    expect(captured.value!.single.mappings[0].channelLocations, [1]);
    expect(captured.value!.single.mappings[2].channelLocations, [1]);
  });
}
