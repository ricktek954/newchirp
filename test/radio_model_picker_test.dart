import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/widgets/radio_model_picker.dart';

void main() {
  testWidgets('radio model picker filters and selects matching models', (
    tester,
  ) async {
    String? selectedModel = 'Yaesu_FTM-150R';
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) => Padding(
              padding: const EdgeInsets.all(24),
              child: RadioModelPicker(
                models: const [
                  'Baofeng_UV-5R',
                  'Connect_Systems_CS750',
                  'Radtel_RT-950',
                  'Yaesu_FTM-150R',
                ],
                selectedModel: selectedModel,
                onSelected: (model) {
                  setState(() => selectedModel = model);
                },
              ),
            ),
          ),
        ),
      ),
    );

    final field = find.byKey(const ValueKey('radio-model-typeahead-field'));
    await tester.tap(field);
    await tester.enterText(field, 'connect cs750');
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('radio-model-option-Connect_Systems_CS750')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('radio-model-option-Yaesu_FTM-150R')),
      findsNothing,
    );

    await tester.tap(
      find.byKey(const ValueKey('radio-model-option-Connect_Systems_CS750')),
    );
    await tester.pumpAndSettle();

    expect(selectedModel, 'Connect_Systems_CS750');
    expect(find.text('Connect Systems CS750'), findsOneWidget);
  });

  testWidgets('radio model picker supports compact type-ahead queries', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: const [
              'Baofeng_UV-5R',
              'Connect_Systems_CS750',
              'Radtel_RT-950',
            ],
            selectedModel: 'Radtel_RT-950',
            onSelected: (_) {},
          ),
        ),
      ),
    );

    final field = find.byKey(const ValueKey('radio-model-typeahead-field'));
    await tester.tap(field);
    await tester.enterText(field, 'uv5r');
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('radio-model-option-Baofeng_UV-5R')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('radio-model-option-Radtel_RT-950')),
      findsNothing,
    );
  });

  testWidgets('radio model picker reports when a search has no matches', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: const ['Baofeng_UV-5R', 'Yaesu_FTM-150R'],
            selectedModel: 'Baofeng_UV-5R',
            onSelected: (_) {},
          ),
        ),
      ),
    );

    final field = find.byKey(const ValueKey('radio-model-typeahead-field'));
    await tester.tap(field);
    await tester.enterText(field, 'not-a-radio');
    await tester.pumpAndSettle();

    expect(find.text('No radio models match this search.'), findsOneWidget);
  });

  testWidgets('radio model picker supports keyboard selection', (tester) async {
    String? selectedModel;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: const ['Baofeng_UV-5R', 'Yaesu_FTM-150R'],
            selectedModel: 'Baofeng_UV-5R',
            onSelected: (model) => selectedModel = model,
          ),
        ),
      ),
    );

    final field = find.byKey(const ValueKey('radio-model-typeahead-field'));
    await tester.tap(field);
    await tester.enterText(field, 'ftm150');
    await tester.pumpAndSettle();
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();

    expect(selectedModel, 'Yaesu_FTM-150R');
  });
}
