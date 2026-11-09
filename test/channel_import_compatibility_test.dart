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
      String? firmware,
      List<RadioZone> zones,
      List<RadioMappingModel> mappings,
      int? zone,
    })
  >
  imageInfo(String imagePath) async => (
    firmware: null,
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
  String path;

  @override
  Future<XFile?> openFile({
    List<XTypeGroup>? acceptedTypeGroups,
    String? initialDirectory,
    String? confirmButtonText,
  }) async => XFile(path);
}

class _WritingBridge extends _AnalogBridge {
  final imageChannels = [
    for (var location = 1; location <= 3; location++)
      RadioChannel(
        location: location,
        name: 'Original $location',
        frequency: 145.5,
      ),
  ];
  List<RadioChannel>? uploaded;
  List<int>? clearedLocations;
  int imageReads = 0;

  @override
  Future<List<SerialPortInfo>> serialPortDetails() async => const [
    SerialPortInfo(port: 'TEST-NO-HARDWARE'),
  ];

  @override
  Future<RadioInstructions> instructions(String model) async =>
      const RadioInstructions(
        info: null,
        experimental: null,
        preDownload: null,
        preUpload: null,
      );

  @override
  Future<
    ({
      List<RadioChannel> channels,
      String model,
      String imagePath,
      String? firmware,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
      List<RadioMappingModel> mappings,
      int? zone,
    })
  >
  readImage(String imagePath, {int? zone}) async {
    imageReads++;
    return (
      channels: imageChannels.map((channel) => channel.copy()).toList(),
      model: _model,
      imagePath: imagePath,
      firmware: null,
      capabilities: (await imageInfo(imagePath)).capabilities,
      zones: const <RadioZone>[],
      mappings: const <RadioMappingModel>[],
      zone: null,
    );
  }

  @override
  Future<
    ({List<Map<String, dynamic>> adjustments, List<RadioMappingModel> mappings})
  >
  upload({
    required String model,
    required String port,
    required String imagePath,
    required List<RadioChannel> channels,
    required List<int> cleared,
    List<RadioMappingModel>? mappings,
    int? zone,
    void Function(RadioProgress)? onProgress,
  }) async {
    expect(port, 'TEST-NO-HARDWARE');
    uploaded = channels.map((channel) => channel.copy()).toList();
    clearedLocations = [...cleared];
    for (final channel in channels) {
      imageChannels.removeWhere(
        (stored) => stored.location == channel.location,
      );
      imageChannels.add(channel.copy());
    }
    imageChannels.removeWhere((channel) => cleared.contains(channel.location));
    return (
      adjustments: <Map<String, dynamic>>[],
      mappings: <RadioMappingModel>[],
    );
  }
}

void main() {
  testWidgets(
    'skip and write never sends flagged rows to the bridge and keeps them unsaved',
    (tester) async {
      tester.view.physicalSize = const Size(1440, 1000);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final temp = Directory.systemTemp.createTempSync('newchirp-skip-write-');
      addTearDown(() async {
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.runAsync(() => temp.delete(recursive: true));
      });
      final image = File('${temp.path}/source.img')
        ..writeAsStringSync('fake image');
      final tooLong = 'X' * 31;
      final incoming = [
        RadioChannel(location: 1, name: 'Compatible edit', frequency: 146.52),
        RadioChannel(location: 2, name: tooLong, frequency: 146.6),
        RadioChannel(
          location: 3,
          name: 'Digital',
          frequency: 433.45,
          mode: 'DMR',
        ),
        RadioChannel(location: 4, name: tooLong, frequency: 146.7),
      ];
      final csv = File('${temp.path}/channels.csv')
        ..writeAsStringSync(ChirpCsv.encode(incoming));
      final selector = _CsvSelector(image.path);
      final previousSelector = FileSelectorPlatform.instance;
      FileSelectorPlatform.instance = selector;
      addTearDown(() => FileSelectorPlatform.instance = previousSelector);
      final bridge = _WritingBridge();
      await tester.pumpWidget(
        NewChirpApp(
          radioBridge: bridge,
          radioImageStore: RadioImageStore(
            rootDirectory: Directory('${temp.path}/images'),
          ),
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
      Future<void> openFile() async {
        await tester.runAsync(() async {
          await tester.tap(find.text('Open channel file').first);
          await Future<void>.delayed(const Duration(milliseconds: 100));
        });
        await tester.pumpAndSettle();
      }

      await openFile();
      expect(find.text('Original 2'), findsOneWidget);
      selector.path = csv.path;
      await openFile();
      await tester.runAsync(() async {
        await tester.tap(find.text('Apply'));
        await Future<void>.delayed(Duration.zero);
      });
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<Text>(find.byKey(const Key('channel-library-write-issues')))
            .data,
        contains('3 channels need attention'),
        reason: tester
            .widgetList<Text>(find.byType(Text))
            .map((text) => text.data)
            .join('\n'),
      );
      await tester.tap(find.byKey(const Key('channel-library-write')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('upload-skip-incompatible')));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('This will program 1 channels'),
        findsOneWidget,
      );
      await tester.tap(find.text('Write to radio'));
      await tester.pumpAndSettle();

      // Assert the actual bridge boundary, before it can truncate/filter names.
      expect(bridge.uploaded!.map((channel) => channel.location), [1]);
      expect(bridge.clearedLocations, isEmpty);
      expect(
        bridge.imageChannels
            .firstWhere((channel) => channel.location == 1)
            .name,
        'Compatible edit',
      );
      expect(
        bridge.imageChannels
            .firstWhere((channel) => channel.location == 2)
            .name,
        'Original 2',
      );
      expect(
        bridge.imageChannels
            .firstWhere((channel) => channel.location == 3)
            .name,
        'Original 3',
      );
      expect(
        bridge.imageChannels.any((channel) => channel.location == 4),
        isFalse,
      );
      expect(bridge.imageReads, 2); // Import, then the image actually written.
      expect(
        find.textContaining('Channel 2 $tooLong could not be written'),
        findsOneWidget,
      );
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();
      expect(find.text('Unsaved radio changes'), findsOneWidget);
      expect(find.text(tooLong), findsNWidgets(2));
      expect(
        tester
            .widget<FilledButton>(
              find.byKey(const Key('channel-library-write')),
            )
            .onPressed,
        isNotNull,
      );
      expect(find.byKey(const ValueKey('channel-issues-2')), findsOneWidget);
      expect(find.byKey(const ValueKey('channel-issues-3')), findsOneWidget);
      expect(find.byKey(const ValueKey('channel-issues-4')), findsOneWidget);
      await tester.tap(find.text('New'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Blank configuration'));
      await tester.pumpAndSettle();
      expect(
        find.textContaining('Any unsaved changes will be lost'),
        findsOneWidget,
      );
      await tester.tap(find.text('Keep current list'));
      await tester.pumpAndSettle();
    },
  );
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
      expect(
        tester
            .widget<Text>(find.byKey(const Key('channel-library-write-issues')))
            .data,
        contains('2 channels need attention'),
      );
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
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.textContaining('Mode DMR is not supported'),
        ),
        findsNWidgets(2),
      );
      expect(source.readAsStringSync(), csv);
    },
  );
}
