import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/widgets/radio_model_picker.dart';

const _vendors = {
  'AOR': ['AOR_AR8200'],
  'Baofeng': ['Baofeng_UV-5R', 'Baofeng_UV-9R'],
  'Connect Systems': ['Connect_Systems_CS750'],
  'Icom': ['Icom_ID-50', 'Icom_ID-52'],
  'Yaesu': ['Yaesu_FT-60', 'Yaesu_FTM-150R'],
};

List<String> get _models => _vendors.values.expand((models) => models).toList();

void main() {
  testWidgets('selected model does not hide the rest of the catalog', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: _models,
            vendorModels: _vendors,
            selectedModel: 'Baofeng_UV-5R',
            onSelected: (_) {},
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();

    expect(find.text('Choose your radio'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('radio-model-vendor-Icom')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('radio-model-option-Baofeng_UV-9R')),
      findsOneWidget,
    );
    await tester.enterText(
      find.byKey(const ValueKey('radio-model-search')),
      'yaesu',
    );
    await tester.pumpAndSettle();
    expect(
      find.byKey(const ValueKey('radio-model-option-Yaesu_FTM-150R')),
      findsOneWidget,
    );
  });

  testWidgets('search selects across manufacturer and model', (tester) async {
    String? selectedModel = 'Yaesu_FTM-150R';
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) => RadioModelPicker(
              models: _models,
              vendorModels: _vendors,
              selectedModel: selectedModel,
              onSelected: (model) {
                setState(() => selectedModel = model);
              },
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('radio-model-search')),
      'connect cs750',
    );
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

  testWidgets('vendor browse makes model selection deliberate', (tester) async {
    String? selectedModel = 'AOR_AR8200';
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) => RadioModelPicker(
              models: _models,
              vendorModels: _vendors,
              selectedModel: selectedModel,
              onSelected: (model) {
                setState(() => selectedModel = model);
              },
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();
    final icomVendor = find.byKey(const ValueKey('radio-model-vendor-Icom'));
    await tester.ensureVisible(icomVendor);
    await tester.pumpAndSettle();
    await tester.tap(icomVendor);
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('radio-model-option-Icom_ID-52')),
      findsOneWidget,
    );
    await tester.tap(
      find.byKey(const ValueKey('radio-model-option-Icom_ID-52')),
    );
    await tester.pumpAndSettle();

    expect(selectedModel, 'Icom_ID-52');
    expect(find.text('Icom ID-52'), findsOneWidget);
  });

  testWidgets('search reports when no models match', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: _models,
            vendorModels: _vendors,
            selectedModel: 'Baofeng_UV-5R',
            onSelected: (_) {},
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('radio-model-search')),
      'not-a-radio',
    );
    await tester.pumpAndSettle();

    expect(find.text('No radio models match this search.'), findsOneWidget);
  });

  testWidgets('search supports keyboard selection', (tester) async {
    String? selectedModel;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: _models,
            vendorModels: _vendors,
            selectedModel: 'Baofeng_UV-5R',
            onSelected: (model) => selectedModel = model,
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('radio-model-search')),
      'ftm150',
    );
    await tester.pumpAndSettle();
    await tester.testTextInput.receiveAction(TextInputAction.search);
    await tester.pumpAndSettle();

    expect(selectedModel, 'Yaesu_FTM-150R');
  });

  testWidgets('full catalog remains scrollable', (tester) async {
    debugDefaultTargetPlatformOverride = TargetPlatform.macOS;

    final models = List<String>.generate(
      574,
      (index) => 'Vendor${index}_RT-${index.toString().padLeft(3, '0')}',
    );
    final groups = {
      for (var group = 0; group < 89; group++)
        'Vendor$group': [
          for (var index = group; index < models.length; index += 89)
            models[index],
        ],
    };
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: models,
            vendorModels: groups,
            selectedModel: null,
            onSelected: (_) {},
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();
    final results = find.byKey(const ValueKey('radio-model-results-list'));
    for (var index = 0; index < 8; index++) {
      await tester.drag(results, const Offset(0, -600));
      await tester.pump();
    }
    await tester.pumpAndSettle();

    final exception = tester.takeException();
    debugDefaultTargetPlatformOverride = null;
    expect(exception, isNull);
  });

  testWidgets('large filtered catalog scrolls on macOS', (tester) async {
    debugDefaultTargetPlatformOverride = TargetPlatform.macOS;

    final icomModels = List<String>.generate(
      106,
      (index) => 'Icom_R${index.toString().padLeft(3, '0')}',
    );
    final models = <String>[
      for (var index = 0; index < 468; index++)
        'Vendor${index % 88}_Other-${index.toString().padLeft(3, '0')}',
      ...icomModels,
    ];
    final groups = <String, List<String>>{
      for (var group = 0; group < 88; group++) 'Vendor$group': <String>[],
      'Icom': icomModels,
    };
    for (final model in models.take(468)) {
      final group = model.substring(0, model.indexOf('_'));
      groups[group]!.add(model);
    }

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioModelPicker(
            models: models,
            vendorModels: groups,
            selectedModel: null,
            onSelected: (_) {},
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('radio-model-picker-field')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('radio-model-search')),
      'icom',
    );
    await tester.pumpAndSettle();
    final results = find.byKey(const ValueKey('radio-model-results-list'));
    for (var index = 0; index < 5; index++) {
      await tester.drag(results, const Offset(0, -500));
      await tester.pump();
    }
    await tester.pumpAndSettle();

    final exception = tester.takeException();
    debugDefaultTargetPlatformOverride = null;
    expect(exception, isNull);
  });
}
