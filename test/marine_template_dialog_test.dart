import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/marine_channels.dart';
import 'package:newchirp/widgets/marine_template_dialog.dart';

void main() {
  testWidgets('marine dialog defaults to receive-only and selects a plan', (
    tester,
  ) async {
    MarineTemplateSelection? selection;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                selection = await showDialog<MarineTemplateSelection>(
                  context: context,
                  builder: (context) => const MarineTemplateDialog(),
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
    expect(find.text('Marine VHF channel template'), findsOneWidget);
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const ValueKey('marine-program-transmit')),
          )
          .value,
      isFalse,
    );
    expect(
      find.textContaining('56 channels: 40 transmit-capable, 16 receive-only'),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('marine-plan-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('International (ITU)').last);
    await tester.pumpAndSettle();
    expect(find.textContaining('ITU Radio Regulations'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('marine-program-transmit')));
    await tester.pump();
    expect(
      find.textContaining('Most amateur transceivers are not type-accepted'),
      findsOneWidget,
    );
    await tester.tap(find.byKey(const ValueKey('marine-template-continue')));
    await tester.pumpAndSettle();

    expect(selection?.plan, MarineChannelPlan.international);
    expect(selection?.programTransmit, isTrue);
  });
}
