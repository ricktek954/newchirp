import 'dart:io';

import 'package:file_selector_platform_interface/file_selector_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/main.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/models/radio_mapping.dart';
import 'package:newchirp/services/chirp_csv.dart';
import 'package:newchirp/services/column_layout_store.dart';
import 'package:newchirp/services/radio_bridge.dart';
import 'package:newchirp/services/radio_image_store.dart';
import 'package:newchirp/services/radio_selection_store.dart';

const _model = 'Test_Analog';

class _RememberedSelection extends RadioSelectionStore {
  @override
  Future<RadioSelection?> load() async => const RadioSelection(model: _model);
}

class _AnalogBridge extends RadioBridge {
  @override
  Future<List<SerialPortInfo>> serialPortDetails() async => const [];

  @override
  Future<RadioModelCatalog> modelCatalog() async =>
      const RadioModelCatalog(models: [_model], groups: []);

  @override
  Future<
    ({
      RadioCapabilities capabilities,
      List<RadioZone> zones,
      List<RadioMappingModel> mappings,
      int? zone,
    })
  >
  imageInfo(String imagePath) async => (
    capabilities: RadioCapabilities.fromJson({
      'modes': ['FM', 'NFM', 'AM'],
      'nameLength': 30,
      'hasTuningStep': false,
      'memoryStart': 1,
      'memoryEnd': 999,
    }),
    zones: const <RadioZone>[],
    mappings: const <RadioMappingModel>[],
    zone: null,
  );
}

class _CsvSelector extends FileSelectorPlatform {
  _CsvSelector(this.path);
  final String path;

  @override
  Future<XFile?> openFile({
    List<XTypeGroup>? acceptedTypeGroups,
    String? initialDirectory,
    String? confirmButtonText,
  }) async => XFile(path);
}

void main() {
  testWidgets(
    'opening CSV retains radio rules, flags both DMR rows and explains each issue',
    (tester) async {
      tester.view.physicalSize = const Size(1440, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final temp = Directory.systemTemp.createTempSync('newchirp-validation-');
      addTearDown(() async {
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.runAsync(() => temp.delete(recursive: true));
      });
      final images = RadioImageStore(rootDirectory: temp);
      File(images.pathForModel(_model)).writeAsStringSync('fake image');
      final csv = ChirpCsv.encode([
        RadioChannel(
          location: 1,
          name: 'Barrio El Remanso',
          frequency: 145.135,
          comment: 'RepeaterBook Amateur: location and free-form notes',
        ),
        RadioChannel(
          location: 2,
          name: 'Digital one',
          frequency: 433.45,
          mode: 'DMR',
        ),
        RadioChannel(
          location: 3,
          name: 'Digital two',
          frequency: 433.55,
          mode: 'DMR',
        ),
      ]);
      final source = File('${temp.path}/channels.csv')..writeAsStringSync(csv);
      final previousSelector = FileSelectorPlatform.instance;
      FileSelectorPlatform.instance = _CsvSelector(source.path);
      addTearDown(() => FileSelectorPlatform.instance = previousSelector);
      await tester.pumpWidget(
        NewChirpApp(
          radioBridge: _AnalogBridge(),
          radioImageStore: images,
          radioSelectionStore: _RememberedSelection(),
          columnLayoutStore: ColumnLayoutStore(
            path: '${temp.path}/layout.json',
          ),
          checkForUpdatesOnStartup: false,
        ),
      );
      await tester.runAsync(
        () => Future<void>.delayed(const Duration(milliseconds: 100)),
      );
      await tester.pumpAndSettle();
      await tester.runAsync(() async {
        await tester.tap(find.text('Open channel file').first);
        await Future<void>.delayed(const Duration(milliseconds: 100));
      });
      await tester.pumpAndSettle();
      expect(find.textContaining('2 channels need attention'), findsOneWidget);
      expect(find.byKey(const ValueKey('channel-issues-1')), findsNothing);
      expect(find.byKey(const ValueKey('channel-issues-2')), findsOneWidget);
      expect(find.byKey(const ValueKey('channel-issues-3')), findsOneWidget);
      expect(
        find.byKey(const Key('channel-library-compatibility-unknown')),
        findsNothing,
      );
      final row = tester.widget<Container>(
        find.byKey(const ValueKey('channel-row-2')),
      );
      expect(row.color, const Color(0xFFFFF4E5));
      await tester.tap(find.byKey(const Key('channel-library-review-issues')));
      await tester.pumpAndSettle();
      expect(find.text('Channel 2 — Digital one'), findsOneWidget);
      expect(find.text('Channel 3 — Digital two'), findsOneWidget);
      expect(
        find.textContaining('Mode DMR is not supported'),
        findsNWidgets(2),
      );
      expect(source.readAsStringSync(), csv);
    },
  );
}
