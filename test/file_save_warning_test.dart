import 'dart:io';

import 'package:file_selector_platform_interface/file_selector_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/main.dart';
import 'package:newchirp/services/column_layout_store.dart';
import 'package:newchirp/services/file_save_warning_store.dart';

const _warning =
    'Saving this file does not write these changes to your radio. '
    'You must write your changes to the radio for them to take effect.';

void main() {
  test(
    'file save warning stays hidden only after an explicit choice',
    () async {
      final path =
          '${Directory.systemTemp.path}/newchirp-save-warning-$pid-store.json';
      final file = File(path);
      if (file.existsSync()) file.deleteSync();
      addTearDown(() {
        if (file.existsSync()) file.deleteSync();
      });
      final store = FileSaveWarningStore(path: path);

      expect(await store.isHidden(), isFalse);

      await file.writeAsString('not json');
      expect(await store.isHidden(), isFalse);

      await file.writeAsString('{"hideFileSaveWarning": false}');
      expect(await store.isHidden(), isFalse);

      await store.hide();
      expect(await store.isHidden(), isTrue);
    },
  );

  testWidgets('Save and Save as warn before writing a file', (tester) async {
    final harness = await _pumpLibrary(tester);

    await _chooseSave(tester);
    expect(find.text(_warning), findsOneWidget);
    expect(find.text('Do not show me this message again'), findsOneWidget);
    await tester.tap(find.widgetWithText(TextButton, 'Cancel'));
    await tester.pumpAndSettle();

    expect(find.text(_warning), findsNothing);
    expect(harness.store.hidden, isFalse);
    expect(harness.selector.calls, 0);

    await _chooseSave(tester, saveAs: true);
    expect(find.text(_warning), findsOneWidget);
    await tester.tap(find.text('Do not show me this message again'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(TextButton, 'Cancel'));
    await tester.pumpAndSettle();
    expect(harness.store.hidden, isFalse);
    expect(harness.selector.calls, 0);
  });

  testWidgets('the warning can be dismissed for later saves', (tester) async {
    final harness = await _pumpLibrary(tester);

    await _chooseSave(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'OK'));
    await tester.pumpAndSettle();

    expect(find.text(_warning), findsNothing);
    expect(harness.store.hidden, isFalse);
    expect(harness.selector.calls, 1);

    await _chooseSave(tester);
    expect(find.text(_warning), findsOneWidget);
    await tester.tap(find.text('Do not show me this message again'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'OK'));
    await tester.pumpAndSettle();

    expect(find.text(_warning), findsNothing);
    expect(harness.store.hidden, isTrue);
    expect(harness.selector.calls, 2);

    await _chooseSave(tester);
    expect(find.text(_warning), findsNothing);
    expect(harness.selector.calls, 3);
  });
}

class _Harness {
  _Harness(this.store, this.selector);

  final _MemorySaveWarningStore store;
  final _SavePathSelector selector;
}

Future<_Harness> _pumpLibrary(WidgetTester tester) async {
  tester.view.physicalSize = const Size(1440, 900);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);

  final selector = _SavePathSelector();
  final previous = FileSelectorPlatform.instance;
  FileSelectorPlatform.instance = selector;
  addTearDown(() => FileSelectorPlatform.instance = previous);

  final id = DateTime.now().microsecondsSinceEpoch;
  final store = _MemorySaveWarningStore();
  final layoutPath =
      '${Directory.systemTemp.path}/newchirp-save-warning-layout-$id.json';
  addTearDown(() {
    final file = File(layoutPath);
    if (file.existsSync()) file.deleteSync();
  });

  await tester.pumpWidget(
    NewChirpApp(
      columnLayoutStore: ColumnLayoutStore(path: layoutPath),
      fileSaveWarningStore: store,
      checkForUpdatesOnStartup: false,
    ),
  );
  await tester.pumpAndSettle();
  await tester.tap(find.text('New'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('GMRS starter template'));
  await tester.pumpAndSettle();
  return _Harness(store, selector);
}

Future<void> _chooseSave(WidgetTester tester, {bool saveAs = false}) async {
  await tester.tap(find.widgetWithText(FilledButton, 'Save'));
  await tester.pumpAndSettle();
  await tester.tap(
    saveAs
        ? find.text('Save as…')
        : find.widgetWithText(MenuItemButton, 'Save'),
  );
  await tester.pumpAndSettle();
}

class _MemorySaveWarningStore extends FileSaveWarningStore {
  _MemorySaveWarningStore() : super(path: 'memory-only');

  bool hidden = false;

  @override
  Future<bool> isHidden() async => hidden;

  @override
  Future<void> hide() async {
    hidden = true;
  }
}

class _SavePathSelector extends FileSelectorPlatform {
  int calls = 0;

  @override
  Future<FileSaveLocation?> getSaveLocation({
    List<XTypeGroup>? acceptedTypeGroups,
    SaveDialogOptions options = const SaveDialogOptions(),
  }) async {
    calls += 1;
    return null;
  }
}
