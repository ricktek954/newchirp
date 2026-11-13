import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/main.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/models/repeater_search.dart';
import 'package:newchirp/services/column_layout_store.dart';
import 'package:newchirp/services/file_save_warning_store.dart';
import 'package:newchirp/services/mygmrs_client.dart';
import 'package:newchirp/services/radio_bridge.dart';
import 'package:newchirp/services/repeater_search_preferences_store.dart';
import 'package:newchirp/services/update_checker.dart';

import 'chirp_test_source.dart';

import 'package:newchirp/services/update_installer.dart';

var _layoutTest = 0;
NewChirpApp testApp({
  UpdateChecker? updateChecker,
  UpdateInstaller? updateInstaller,
  Future<void> Function()? exitForUpdate,
  bool checkForUpdatesOnStartup = false,
}) {
  final id = _layoutTest++;
  return NewChirpApp(
    columnLayoutStore: ColumnLayoutStore(
      path: '${Directory.systemTemp.path}/newchirp-widget-layout-$pid-$id.json',
    ),
    fileSaveWarningStore: FileSaveWarningStore(
      path:
          '${Directory.systemTemp.path}/newchirp-widget-save-warning-$pid-$id.json',
    ),
    updateChecker: updateChecker,
    updateInstaller: updateInstaller,
    exitForUpdate: exitForUpdate,
    checkForUpdatesOnStartup: checkForUpdatesOnStartup,
  );
}

class _FakeUpdateChecker extends UpdateChecker {
  _FakeUpdateChecker(this.result);

  final UpdateCheckResult result;

  @override
  Future<UpdateCheckResult> check(String currentVersion) async => result;
}

class _FailingUpdateChecker extends UpdateChecker {
  @override
  Future<UpdateCheckResult> check(String currentVersion) async {
    throw UpdateCheckException('Update service unavailable.');
  }
}

class _FakeUpdateInstaller extends UpdateInstaller {
  int downloadCount = 0;
  int installCount = 0;
  UpdateCheckResult? downloaded;
  DownloadedUpdate? installed;

  @override
  Future<DownloadedUpdate> download(
    UpdateCheckResult update, {
    UpdateProgressCallback? onProgress,
  }) async {
    downloadCount++;
    downloaded = update;
    onProgress?.call(
      const UpdateDownloadProgress(receivedBytes: 50, totalBytes: 100),
    );
    return DownloadedUpdate(
      path: '/tmp/NewChirp-linux-x64-${update.latestVersion}.deb',
      platform: 'linux',
      version: update.latestVersion,
    );
  }

  @override
  Future<void> install(DownloadedUpdate update) async {
    installCount++;
    installed = update;
  }
}

class _FakeRepeaterBridge extends RadioBridge {
  _FakeRepeaterBridge({this.emptyResults = false});

  final bool emptyResults;
  String? lastCountry;
  String? lastState;
  String? lastService;
  String? lastFilter;
  double? lastLatitude;
  double? lastLongitude;
  double? lastDistance;
  bool? lastFmOnly;
  bool? lastOpenOnly;

  @override
  Future<RepeaterSearchResults> searchRepeaters({
    required String country,
    required String state,
    required String service,
    String filter = '',
    double? latitude,
    double? longitude,
    double? distance,
    bool fmOnly = false,
    bool openOnly = false,
    void Function(RadioProgress)? onProgress,
  }) async {
    lastCountry = country;
    lastState = state;
    lastService = service;
    lastFilter = filter;
    lastLatitude = latitude;
    lastLongitude = longitude;
    lastDistance = distance;
    lastFmOnly = fmOnly;
    lastOpenOnly = openOnly;
    if (emptyResults) {
      return const RepeaterSearchResults(
        source: 'RepeaterBook',
        sourceUrl: 'https://repeaterbook.com',
        totalMatches: 0,
        results: [],
      );
    }
    final channel = RadioChannel(
      location: 1,
      name: 'Buffalo',
      frequency: 146.865,
      duplex: '-',
      offset: 0.6,
      tone: 'Tone',
      txTone: 151.4,
    );
    final secondChannel = RadioChannel(
      location: 2,
      name: 'Point of Americas',
      frequency: 444,
      duplex: '+',
      offset: 5,
      tone: 'TSQL',
      txTone: 88.5,
      rxTone: 110.9,
    );
    return RepeaterSearchResults(
      source: 'RepeaterBook',
      sourceUrl: 'https://repeaterbook.com',
      totalMatches: 2,
      results: [
        RepeaterSearchResult(
          channel: channel,
          callsign: 'WB2ECR',
          city: 'Buffalo',
          county: 'Erie',
          state: state,
          use: 'OPEN',
          service: 'Amateur',
          latitude: 42.8864,
          longitude: -78.8784,
        ),
        RepeaterSearchResult(
          channel: secondChannel,
          callsign: 'W4BUG',
          city: 'Fort Lauderdale',
          county: 'Broward',
          state: state,
          use: 'OPEN',
          service: 'Amateur',
          latitude: 26.1224,
          longitude: -80.1373,
        ),
      ],
    );
  }
}

class _FakeRepeaterSearchPreferencesStore
    extends RepeaterSearchPreferencesStore {
  _FakeRepeaterSearchPreferencesStore([
    this.preferences = const RepeaterSearchPreferences(),
  ]);

  RepeaterSearchPreferences preferences;

  @override
  Future<RepeaterSearchPreferences> load() async => preferences;

  @override
  Future<void> save(RepeaterSearchPreferences next) async {
    preferences = next;
  }
}

class _FakeMyGmrsService implements MyGmrsService {
  bool _signedIn = false;
  int signInCalls = 0;
  int cancelCalls = 0;
  Completer<void>? _pendingSignIn;

  @override
  bool get signedIn => _signedIn;

  @override
  Future<void> signIn() {
    signInCalls++;
    _pendingSignIn = Completer<void>();
    return _pendingSignIn!.future;
  }

  @override
  void cancelSignIn() {
    cancelCalls++;
    final pending = _pendingSignIn;
    if (pending != null && !pending.isCompleted) {
      pending.completeError(
        const MyGmrsException('myGMRS sign-in was cancelled.'),
      );
    }
  }

  @override
  Future<void> signOut() async {
    _signedIn = false;
  }

  @override
  Future<RepeaterSearchResults> searchRepeaters({
    required String state,
    String query = '',
    double? latitude,
    double? longitude,
    double? distanceKm,
    bool openOnly = false,
    int limit = 100,
  }) async {
    return const RepeaterSearchResults(
      source: 'myGMRS',
      sourceUrl: 'https://mygmrs.com',
      totalMatches: 0,
      results: [],
    );
  }
}

Future<void> openGmrsStarter(WidgetTester tester) async {
  await tester.tap(find.text('New'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('GMRS starter template'));
  await tester.pumpAndSettle();
}

void main() {
  test('persisted model does not enable transfer before catalog loads', () {
    expect(radioModelSelectionReady(const [], 'Icom_IC-E90'), isFalse);
    expect(
      radioModelSelectionReady(const ['Icom_IC-E90'], 'Icom_IC-E90'),
      isTrue,
    );
    expect(
      radioModelSelectionReady(const ['Icom_IC-E90'], 'Baofeng_UV-5R'),
      isFalse,
    );
  });

  test(
    'restored model loads the catalog without overriding user selection',
    () {
      expect(
        shouldLoadRadioCatalogForRestoredSelection(const [], 'Icom_IC-E90'),
        isTrue,
      );
      expect(
        shouldLoadRadioCatalogForRestoredSelection(const [
          'Icom_IC-E90',
        ], 'Icom_IC-E90'),
        isFalse,
      );
      expect(
        shouldLoadRadioCatalogForRestoredSelection(const [], null),
        isFalse,
      );
    },
  );

  test('radio prompts use the actual NewChirp ready button', () {
    expect(
      adaptRadioPromptButton(
        '6. Click OK to download image from device.',
        'Radio is ready',
      ),
      '6. Click "Radio is ready" to download image from device.',
    );
    expect(
      adaptRadioPromptButton(
        'Select the settings, then press the OK button.',
        'Radio is ready to receive',
      ),
      'Select the settings, then press "Radio is ready to receive".',
    );
    expect(
      adaptRadioPromptButton(
        '6. <b>After clicking OK</b>, hold the [PTT] switch for one second.',
        'Radio is ready',
      ),
      '6. After clicking "Radio is ready", wait until the transfer window '
      'says "Listening for the radio", then hold the [PTT] switch for one '
      'second to send the image.',
    );
  });

  testWidgets('radio extras only toggle through the switch', (tester) async {
    var value = false;
    final field = ChannelExtraField(
      name: 'bcl',
      label: 'BCL',
      kind: 'boolean',
      value: value,
      documentation: 'Busy Channel Lockout.',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) => ExtraFieldEditor(
              field: field,
              onChanged: (next) => setState(() {
                value = next as bool;
                field.value = value;
              }),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('BCL'));
    await tester.pump();
    expect(value, isFalse);

    await tester.tap(find.byType(Switch));
    await tester.pump();
    expect(value, isTrue);
  });

  testWidgets('RepeaterBook search previews and returns selected channels', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    List<RadioChannel>? selected;
    final bridge = _FakeRepeaterBridge();
    final preferencesStore = _FakeRepeaterSearchPreferencesStore();

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                selected = await showDialog<List<RadioChannel>>(
                  context: context,
                  builder: (context) => RepeaterBookDialog(
                    bridge: bridge,
                    preferencesStore: preferencesStore,
                  ),
                );
              },
              child: const Text('Open repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open repeater search'));
    await tester.pumpAndSettle();
    final searchFilter = find.byKey(const ValueKey('repeater-search-filter'));
    await tester.enterText(searchFilter, 'Buffalo');
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.byKey(const ValueKey('repeater-search-clear')), findsOneWidget);
    expect(preferencesStore.preferences.query, 'Buffalo');
    await tester.tap(find.byKey(const ValueKey('repeater-search-clear')));
    await tester.pump();
    expect(tester.widget<TextField>(searchFilter).controller?.text, isEmpty);

    await tester.tap(find.text('Search'));
    await tester.pumpAndSettle();

    expect(bridge.lastCountry, 'United States');
    expect(bridge.lastService, 'all');
    expect(bridge.lastOpenOnly, isFalse);
    expect(bridge.lastFmOnly, isFalse);
    expect(preferencesStore.preferences.openOnly, isFalse);
    expect(preferencesStore.preferences.fmOnly, isFalse);
    expect(find.text('WB2ECR — Buffalo'), findsOneWidget);
    expect(find.text('W4BUG — Point of Americas'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('repeater-sort-source')));
    await tester.pumpAndSettle();
    expect(find.text('Frequency'), findsOneWidget);
    expect(find.text('Callsign / name'), findsOneWidget);
    await tester.tap(find.text('Callsign / name'));
    await tester.pumpAndSettle();
    expect(
      tester.getTopLeft(find.text('W4BUG — Point of Americas')).dy,
      lessThan(tester.getTopLeft(find.text('WB2ECR — Buffalo')).dy),
    );
    await tester.ensureVisible(find.text('Map'));
    await tester.tap(find.text('Map'));
    await tester.pump();
    final allMarkers = tester.widget<MarkerLayer>(find.byType(MarkerLayer));
    expect(allMarkers.markers, hasLength(2));
    expect(
      allMarkers.markers
          .map((marker) => '${marker.point.latitude},${marker.point.longitude}')
          .toSet(),
      hasLength(2),
    );
    await tester.tap(find.text('List'));
    await tester.pump();

    await tester.tap(find.text('All counties'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('county-filter-field')),
      'Erie',
    );
    await tester.pump();
    await tester.tap(find.text('Erie').last);
    await tester.pump();
    await tester.tap(find.text('Apply'));
    await tester.pumpAndSettle();
    expect(find.text('WB2ECR — Buffalo'), findsOneWidget);
    expect(find.text('W4BUG — Point of Americas'), findsNothing);
    expect(find.text('1 county'), findsOneWidget);

    await tester.tap(find.text('1 county'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Clear all'));
    await tester.pump();
    await tester.enterText(
      find.byKey(const ValueKey('county-filter-field')),
      'Broward',
    );
    await tester.pump();
    await tester.tap(find.text('Broward').last);
    await tester.pump();
    await tester.tap(find.text('Apply'));
    await tester.pumpAndSettle();
    expect(find.text('WB2ECR — Buffalo'), findsNothing);
    expect(find.text('W4BUG — Point of Americas'), findsOneWidget);

    final resultFilter = find.byWidgetPredicate(
      (widget) =>
          widget is TextField &&
          widget.decoration?.labelText == 'Filter loaded results',
    );
    await tester.enterText(resultFilter, 'Broward');
    await tester.pumpAndSettle();
    expect(find.text('WB2ECR — Buffalo'), findsNothing);
    expect(find.text('W4BUG — Point of Americas'), findsOneWidget);
    await tester.tap(find.text('Map'));
    await tester.pump();
    final markerLayer = tester.widget<MarkerLayer>(find.byType(MarkerLayer));
    expect(markerLayer.markers, hasLength(1));
    await tester.tap(find.text('List'));
    await tester.pump();

    final initialDialogSize = tester.getSize(
      find.byKey(const Key('repeater-book-dialog')),
    );
    tester.view.physicalSize = const Size(1300, 820);
    await tester.pumpAndSettle();
    final resizedDialogSize = tester.getSize(
      find.byKey(const Key('repeater-book-dialog')),
    );
    final initialResultsSize = tester.getSize(
      find.byKey(const Key('repeater-results-area')),
    );
    expect(resizedDialogSize.width, greaterThan(initialDialogSize.width));
    expect(resizedDialogSize.height, greaterThan(initialDialogSize.height));
    await tester.drag(
      find.byKey(const Key('repeater-book-width-handle')),
      const Offset(100, 0),
    );
    await tester.pumpAndSettle();
    final widthResizedSize = tester.getSize(
      find.byKey(const Key('repeater-book-dialog')),
    );
    expect(widthResizedSize.width, greaterThan(resizedDialogSize.width));
    expect(widthResizedSize.width, greaterThan(1200));
    expect(widthResizedSize.height, resizedDialogSize.height);
    await tester.drag(
      find.byKey(const Key('repeater-book-height-handle')),
      const Offset(0, 50),
    );
    await tester.pumpAndSettle();
    final heightResizedSize = tester.getSize(
      find.byKey(const Key('repeater-book-dialog')),
    );
    final heightResizedResultsSize = tester.getSize(
      find.byKey(const Key('repeater-results-area')),
    );
    expect(heightResizedSize.width, widthResizedSize.width);
    expect(heightResizedSize.height, greaterThan(widthResizedSize.height));
    expect(
      heightResizedResultsSize.height,
      greaterThan(initialResultsSize.height),
    );

    await tester.ensureVisible(find.text('W4BUG — Point of Americas'));
    await tester.tap(find.text('W4BUG — Point of Americas'));
    await tester.pump();
    expect(find.text('Add 1 selected'), findsOneWidget);
    await tester.tap(find.text('Add 1 selected'));
    await tester.pumpAndSettle();

    expect(selected, hasLength(1));
    expect(selected!.single.frequency, 444);
    expect(selected!.single.location, 1);
  });

  testWidgets('RepeaterBook accepts and remembers a ZIP-code search', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final bridge = _FakeRepeaterBridge();
    final preferencesStore = _FakeRepeaterSearchPreferencesStore();

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                await showDialog<List<RadioChannel>>(
                  context: context,
                  builder: (context) => RepeaterBookDialog(
                    bridge: bridge,
                    preferencesStore: preferencesStore,
                  ),
                );
              },
              child: const Text('Open ZIP repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open ZIP repeater search'));
    await tester.pumpAndSettle();
    expect(
      find.text('A 5-digit ZIP searches repeaters within 50 km by default.'),
      findsOneWidget,
    );

    await tester.enterText(
      find.byKey(const ValueKey('repeater-search-filter')),
      '33004',
    );
    await tester.pump(const Duration(milliseconds: 300));
    await tester.tap(find.text('Search'));
    await tester.pumpAndSettle();

    expect(bridge.lastFilter, '33004');
    expect(bridge.lastLatitude, isNull);
    expect(bridge.lastDistance, isNull);
    expect(preferencesStore.preferences.query, '33004');
  });

  testWidgets('RepeaterBook empty results explain country and filters', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final preferencesStore = _FakeRepeaterSearchPreferencesStore();

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                await showDialog<List<RadioChannel>>(
                  context: context,
                  builder: (context) => RepeaterBookDialog(
                    bridge: _FakeRepeaterBridge(emptyResults: true),
                    preferencesStore: preferencesStore,
                  ),
                );
              },
              child: const Text('Open empty repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open empty repeater search'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Search'));
    await tester.pumpAndSettle();

    expect(
      find.textContaining(
        'No matching repeaters were found in New York, United States.',
      ),
      findsOneWidget,
    );
    expect(
      find.textContaining('Coordinates do not change Country or Region'),
      findsOneWidget,
    );
  });

  testWidgets('RepeaterBook restores saved optional filters', (tester) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final bridge = _FakeRepeaterBridge();
    final preferencesStore = _FakeRepeaterSearchPreferencesStore(
      const RepeaterSearchPreferences(openOnly: true, fmOnly: false),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                await showDialog<List<RadioChannel>>(
                  context: context,
                  builder: (context) => RepeaterBookDialog(
                    bridge: bridge,
                    preferencesStore: preferencesStore,
                  ),
                );
              },
              child: const Text('Open remembered repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open remembered repeater search'));
    await tester.pumpAndSettle();
    final openOnlyTile = tester.widget<CheckboxListTile>(
      find.widgetWithText(CheckboxListTile, 'Open repeaters only'),
    );
    final fmOnlyTile = tester.widget<CheckboxListTile>(
      find.widgetWithText(CheckboxListTile, 'FM-capable only'),
    );
    expect(openOnlyTile.value, isTrue);
    expect(fmOnlyTile.value, isFalse);
    await tester.tap(find.text('Search'));
    await tester.pumpAndSettle();

    expect(bridge.lastOpenOnly, isTrue);
    expect(bridge.lastFmOnly, isFalse);
  });

  testWidgets('repeater search restores all saved criteria', (tester) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final bridge = _FakeRepeaterBridge();
    final preferencesStore = _FakeRepeaterSearchPreferencesStore(
      const RepeaterSearchPreferences(
        country: 'Canada',
        region: 'Ontario',
        service: 'amateur',
        sortOrder: 'city',
        query: 'Toronto',
        latitude: '43.6532',
        longitude: '-79.3832',
        radiusKm: '75',
        openOnly: true,
        fmOnly: true,
        mapView: true,
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () async {
                await showDialog<List<RadioChannel>>(
                  context: context,
                  builder: (context) => RepeaterBookDialog(
                    bridge: bridge,
                    preferencesStore: preferencesStore,
                  ),
                );
              },
              child: const Text('Open full repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open full repeater search'));
    await tester.pumpAndSettle();

    expect(
      tester
          .widget<TextField>(
            find.byKey(const ValueKey('repeater-search-filter')),
          )
          .controller
          ?.text,
      'Toronto',
    );
    expect(
      tester
          .widget<TextField>(find.byKey(const ValueKey('repeater-latitude')))
          .controller
          ?.text,
      '43.6532',
    );
    expect(
      tester
          .widget<TextField>(find.byKey(const ValueKey('repeater-longitude')))
          .controller
          ?.text,
      '-79.3832',
    );
    expect(
      tester
          .widget<TextField>(find.byKey(const ValueKey('repeater-radius-km')))
          .controller
          ?.text,
      '75',
    );
    expect(
      tester
          .widget<DropdownButtonFormField<String>>(
            find.byKey(const ValueKey('repeater-country-Canada')),
          )
          .initialValue,
      'Canada',
    );
    expect(
      tester
          .widget<DropdownButtonFormField<String>>(
            find.byKey(const ValueKey('repeater-region-Canada-Ontario')),
          )
          .initialValue,
      'Ontario',
    );
    expect(
      tester
          .widget<DropdownButtonFormField<String>>(
            find.byKey(const ValueKey('repeater-service-Canada-amateur')),
          )
          .initialValue,
      'amateur',
    );
    expect(
      tester
          .widget<DropdownButtonFormField<RepeaterSortOrder>>(
            find.byKey(const ValueKey('repeater-sort-city')),
          )
          .initialValue,
      RepeaterSortOrder.city,
    );

    await tester.tap(find.text('Search'));
    await tester.pumpAndSettle();

    expect(bridge.lastCountry, 'Canada');
    expect(bridge.lastState, 'Ontario');
    expect(bridge.lastService, 'amateur');
    expect(bridge.lastFilter, 'Toronto');
    expect(bridge.lastLatitude, 43.6532);
    expect(bridge.lastLongitude, -79.3832);
    expect(bridge.lastDistance, 75);
    expect(bridge.lastOpenOnly, isTrue);
    expect(bridge.lastFmOnly, isTrue);
    expect(preferencesStore.preferences.sortOrder, 'city');
    expect(preferencesStore.preferences.query, 'Toronto');
    expect(preferencesStore.preferences.latitude, '43.6532');
    expect(preferencesStore.preferences.longitude, '-79.3832');
    expect(preferencesStore.preferences.radiusKm, '75');
    expect(preferencesStore.preferences.mapView, isTrue);
  });

  testWidgets('myGMRS directory is available after credential approval', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () => showDialog<List<RadioChannel>>(
                context: context,
                builder: (context) => RepeaterBookDialog(
                  bridge: _FakeRepeaterBridge(),
                  preferencesStore: _FakeRepeaterSearchPreferencesStore(),
                ),
              ),
              child: const Text('Open repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open repeater search'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('mygmrs-sign-in')), findsNothing);
    expect(
      find.byKey(const ValueKey('repeater-provider-repeaterBook')),
      findsOneWidget,
    );

    await tester.tap(
      find.byKey(const ValueKey('repeater-provider-repeaterBook')),
    );
    await tester.pumpAndSettle();
    expect(find.text('myGMRS.com'), findsOneWidget);
    await tester.tap(find.text('myGMRS.com').last);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('mygmrs-sign-in')), findsOneWidget);
  });

  testWidgets('myGMRS search requires explicit sign-in and can cancel', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 720);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final myGmrs = _FakeMyGmrsService();

    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) => Scaffold(
            body: TextButton(
              onPressed: () => showDialog<List<RadioChannel>>(
                context: context,
                builder: (context) => RepeaterBookDialog(
                  bridge: _FakeRepeaterBridge(),
                  preferencesStore: _FakeRepeaterSearchPreferencesStore(),
                  myGmrsService: myGmrs,
                ),
              ),
              child: const Text('Open repeater search'),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open repeater search'));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('repeater-provider-repeaterBook')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('myGMRS.com').last);
    await tester.pumpAndSettle();

    final search = find.widgetWithText(FilledButton, 'Search');
    expect(tester.widget<FilledButton>(search).onPressed, isNull);
    await tester.tap(search);
    await tester.pump();
    expect(myGmrs.signInCalls, 0);

    await tester.tap(find.byKey(const ValueKey('mygmrs-sign-in')));
    await tester.pump();
    expect(myGmrs.signInCalls, 1);
    expect(find.text('Cancel sign-in'), findsOneWidget);

    await tester.tap(find.text('Cancel sign-in'));
    await tester.pumpAndSettle();
    expect(myGmrs.cancelCalls, 1);
    expect(find.text('myGMRS sign-in cancelled.'), findsOneWidget);
    expect(find.text('Sign in to myGMRS'), findsOneWidget);
  });

  testWidgets('startup update check offers a newer release', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      testApp(
        updateChecker: _FakeUpdateChecker(
          const UpdateCheckResult(
            currentVersion: '1.0.3',
            latestVersion: '9.9.9',
            releaseUrl: 'https://newchirp.net/#download',
          ),
        ),
        checkForUpdatesOnStartup: true,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Update available'), findsOneWidget);
    expect(find.textContaining('NewChirp 9.9.9 is available'), findsOneWidget);
    expect(find.text('Open download page'), findsOneWidget);
    expect(find.text('Download and install'), findsNothing);
  });

  testWidgets('startup update respects automatic update support', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final installer = _FakeUpdateInstaller();
    var exited = false;
    final extension = updateArtifactExtension();

    await tester.pumpWidget(
      testApp(
        updateChecker: _FakeUpdateChecker(
          UpdateCheckResult(
            currentVersion: '1.0.3',
            latestVersion: '9.9.9',
            releaseUrl: 'https://newchirp.net/#download',
            downloadUrl:
                'https://newchirp.net/downloads/NewChirp-9.9.9${extension ?? '.exe'}',
          ),
        ),
        updateInstaller: installer,
        exitForUpdate: () async => exited = true,
        checkForUpdatesOnStartup: true,
      ),
    );
    await tester.pumpAndSettle();

    if (extension == null) {
      expect(find.text('Update available'), findsOneWidget);
      expect(find.text('Open download page'), findsOneWidget);
      expect(find.text('Download and install'), findsNothing);
      expect(installer.downloadCount, 0);
      expect(installer.installCount, 0);
      expect(exited, isFalse);
      return;
    }

    expect(find.text('NewChirp 9.9.9 is ready'), findsOneWidget);
    expect(find.text('Download and install'), findsOneWidget);

    await tester.tap(find.text('Download and install'));
    await tester.pumpAndSettle();

    expect(installer.downloadCount, 1);
    expect(installer.installCount, 1);
    expect(installer.installed?.version, '9.9.9');
    expect(exited, isTrue);
    expect(find.text('Update available'), findsNothing);
  });

  testWidgets('startup update check hides an off-site download link', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      testApp(
        updateChecker: _FakeUpdateChecker(
          const UpdateCheckResult(
            currentVersion: '1.0.3',
            latestVersion: '9.9.9',
            releaseUrl: 'https://evil.example/setup.exe',
            downloadUrl: 'https://evil.example/NewChirp-linux-x64-9.9.9.deb',
          ),
        ),
        checkForUpdatesOnStartup: true,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Open download page'), findsOneWidget);
    expect(find.text('https://evil.example/setup.exe'), findsNothing);
    expect(find.text('Download and install'), findsNothing);
  });

  testWidgets('startup update failures stay quiet', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      testApp(
        updateChecker: _FailingUpdateChecker(),
        checkForUpdatesOnStartup: true,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Couldn\u2019t check for updates'), findsNothing);
    expect(find.text('What would you like to do?'), findsOneWidget);
  });

  testWidgets('Help menu checks for updates on demand', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      testApp(
        updateChecker: _FakeUpdateChecker(
          const UpdateCheckResult(
            currentVersion: '1.0.3',
            latestVersion: '1.0.3',
            releaseUrl: null,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Open channel file'), findsWidgets);
    expect(find.text('Load CHIRP driver module…'), findsOneWidget);
    final openLeft = tester.getTopLeft(find.text('Open channel file').first);
    final loadLeft = tester.getTopLeft(find.text('Load CHIRP driver module…'));
    expect(loadLeft.dx, greaterThan(openLeft.dx));

    await tester.tap(find.text('Help'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Check for updates'));
    await tester.pumpAndSettle();

    expect(find.text('You\u2019re up to date'), findsOneWidget);
  });

  testWidgets('Help glossary defines radio abbreviations', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Help'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Abbreviations & terms'));
    await tester.pumpAndSettle();

    expect(find.text('CTCSS'), findsOneWidget);
    final search = find.descendant(
      of: find.byType(Dialog),
      matching: find.byType(TextField),
    );
    await tester.enterText(search, 'polarity');
    await tester.pumpAndSettle();

    expect(find.text('DTCS POL'), findsOneWidget);
    expect(find.text('CTCSS'), findsNothing);

    await tester.enterText(search, 'BCL');
    await tester.pumpAndSettle();

    expect(
      find.descendant(of: find.byType(ListTile), matching: find.text('BCL')),
      findsOneWidget,
    );
    expect(find.textContaining('Busy Channel Lockout'), findsOneWidget);
  });

  testWidgets('Help menu can submit a problem report at any time', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Help'));
    await tester.pumpAndSettle();

    expect(find.text('Report a problem…'), findsOneWidget);
    await tester.tap(find.text('Report a problem…'));
    await tester.pumpAndSettle();

    expect(find.text('Submit bug report'), findsOneWidget);
    expect(find.text('Your email'), findsOneWidget);
    expect(find.text('What were you trying to do?'), findsOneWidget);
    expect(find.text('General problem report'), findsOneWidget);
  });

  testWidgets('starts with configuration choices', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();

    expect(find.text('NewChirp'), findsWidgets);
    expect(find.text('What would you like to do?'), findsOneWidget);
    expect(find.text('Start new'), findsNothing);
    expect(find.text('Open channel file'), findsWidgets);
    expect(find.text('Use GMRS template'), findsNothing);
    expect(find.text('Connect radio'), findsOneWidget);
    expect(find.text('GMRS 1'), findsNothing);
  });

  testWidgets('left menu follows read, channels, then settings', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();

    const labels = [
      'Radio connection',
      'Channel library',
      'Radio settings',
      'Find repeaters',
      'Frequency reference',
      'About & licenses',
    ];
    final rail = find.byKey(const Key('left-menu-rail'));
    var previousTop = -1.0;
    for (final label in labels) {
      final item = find.descendant(of: rail, matching: find.text(label));
      expect(item, findsOneWidget);
      final top = tester.getTopLeft(item).dy;
      expect(top, greaterThan(previousTop));
      previousTop = top;
    }
  });

  testWidgets('radio settings distinguish live and saved sources', (
    tester,
  ) async {
    var radioReads = 0;
    var snapshotLoads = 0;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RadioSettingsSourceActions(
            canReadRadio: true,
            hasSavedSnapshot: true,
            enabled: true,
            onReadRadio: () => radioReads++,
            onUseSavedSnapshot: () => snapshotLoads++,
          ),
        ),
      ),
    );

    expect(find.text('Read current settings from radio'), findsOneWidget);
    expect(find.text('Use saved radio snapshot'), findsOneWidget);
    expect(find.text('Reload stored image'), findsNothing);

    await tester.tap(find.text('Read current settings from radio'));
    await tester.tap(find.text('Use saved radio snapshot'));
    expect(radioReads, 1);
    expect(snapshotLoads, 1);
  });

  testWidgets('Find repeaters opens from the left navigation', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Find repeaters').first);
    await tester.pumpAndSettle();

    expect(find.text('Country'), findsOneWidget);
    expect(find.text('State or province'), findsOneWidget);
    expect(find.text('Data from RepeaterBook.com'), findsNothing);
  });

  testWidgets('Radio connection omits implementation-detail information card', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Radio connection').first);
    await tester.pumpAndSettle();

    expect(
      find.textContaining('uses the provided CHIRP driver tree'),
      findsNothing,
    );
  });

  testWidgets('channel library shows a locked radio image bar', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    expect(
      find.text(
        'No stored radio image. Read the radio before writing channels.',
      ),
      findsOneWidget,
    );
    expect(
      tester
          .widget<TextButton>(find.byKey(const Key('channel-library-discard')))
          .onPressed,
      isNull,
    );
    expect(find.text('Connect radio to write'), findsOneWidget);
    expect(find.text('Write channels to radio'), findsNothing);
  });

  testWidgets('channel search has a one-click clear control', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final search = find.byKey(const ValueKey('channel-search-field'));
    await tester.enterText(search, 'GMRS 1');
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('channel-search-clear')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('channel-search-clear')));
    await tester.pumpAndSettle();

    expect(tester.widget<TextField>(search).controller?.text, isEmpty);
    expect(find.text('GMRS 1'), findsOneWidget);
    expect(find.byKey(const ValueKey('channel-search-clear')), findsNothing);
  });

  testWidgets('Shift and Ctrl click select channels for bulk editing', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 1').first);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.tap(find.text('GMRS 4').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.pump();

    expect(find.text('Edit 4 selected'), findsOneWidget);
    expect(find.byKey(const ValueKey('bulk-edit-channels')), findsOneWidget);

    await tester.sendKeyDownEvent(LogicalKeyboardKey.metaLeft);
    await tester.tap(find.text('GMRS 6').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.metaLeft);
    await tester.pump();

    expect(find.text('Edit 5 selected'), findsOneWidget);
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.tap(find.text('GMRS 7').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pump();

    expect(find.text('Edit 6 selected'), findsOneWidget);
    final propertiesMenu = await tester.startGesture(
      tester.getCenter(find.text('GMRS 7').first),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await propertiesMenu.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Edit selected properties'));
    await tester.pumpAndSettle();

    expect(find.text('Edit 6 channels'), findsOneWidget);
    expect(
      find.textContaining('Only fields you change here are applied'),
      findsOneWidget,
    );
    final bulkName = find.descendant(
      of: find.byType(Dialog),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == 'Name',
      ),
    );
    tester.widget<TextField>(bulkName).onChanged!('BULK');
    await tester.pump();
    tester
        .widget<DropdownButtonFormField<String>>(
          find.descendant(
            of: find.byType(Dialog),
            matching: find.byWidgetPredicate(
              (widget) =>
                  widget is DropdownButtonFormField<String> &&
                  widget.decoration.labelText == 'Scan',
            ),
          ),
        )
        .onChanged!('S');
    await tester.pump();
    await tester.tap(find.text('Update 6'));
    await tester.pumpAndSettle();

    for (final location in [1, 2, 3, 4, 6, 7]) {
      expect(
        find.descendant(
          of: find.byKey(ValueKey('channel-slot-$location')),
          matching: find.text('Skip'),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byKey(ValueKey('channel-slot-$location')),
          matching: find.text('BULK'),
        ),
        findsOneWidget,
      );
    }
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-5')),
        matching: find.text('Include'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-5')),
        matching: find.text('GMRS 5'),
      ),
      findsOneWidget,
    );
  });

  testWidgets('opens the GMRS starter only when selected', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    expect(find.text('GMRS Starter Library'), findsOneWidget);
    expect(find.text('Add channel'), findsOneWidget);
    expect(find.text('GMRS 1'), findsWidgets);
    expect(find.text('TX TONE'), findsOneWidget);
    expect(find.text('RX DTCS'), findsOneWidget);
    expect(find.text('DTCS POL'), findsOneWidget);
    expect(find.text('POWER'), findsOneWidget);
    expect(find.text('COMMENT'), findsOneWidget);
    expect(
      find.byTooltip(
        'Receive frequency: the frequency the radio listens on.\n\n'
        'Drag to reorder column',
      ),
      findsOneWidget,
    );
  });

  testWidgets('adding a channel reveals it and confirms creation', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final verticalList = find.byWidgetPredicate(
      (widget) =>
          widget is Scrollable && widget.axisDirection == AxisDirection.down,
    );
    final before = tester.state<ScrollableState>(verticalList).position;
    final beforePixels = before.pixels;
    expect(beforePixels, lessThan(before.maxScrollExtent));

    await tester.tap(find.text('Add channel'));
    await tester.pumpAndSettle();
    expect(find.text('Where should the new channel go?'), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('add-channel-at-end')));
    await tester.pumpAndSettle();

    final after = tester.state<ScrollableState>(verticalList).position;
    expect(after.pixels, greaterThan(beforePixels));
    expect(after.pixels, lessThanOrEqualTo(after.maxScrollExtent));
    expect(find.text('NEW 23'), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(SnackBar),
        matching: find.text('Channel 23 added'),
      ),
      findsOneWidget,
    );

    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();
  });

  testWidgets('adding before or after selected shifts memory locations', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('GMRS 2'));
    await tester.pump();

    await tester.tap(find.text('Add channel'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('add-channel-before-selected')));
    await tester.pumpAndSettle();

    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-2')),
        matching: find.text('NEW 2'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-3')),
        matching: find.text('GMRS 2'),
      ),
      findsOneWidget,
    );

    await tester.tap(find.text('Add channel'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('add-channel-after-selected')));
    await tester.pumpAndSettle();

    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-3')),
        matching: find.text('NEW 3'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-4')),
        matching: find.text('GMRS 2'),
      ),
      findsOneWidget,
    );

    final clearedRow = await tester.startGesture(
      tester.getCenter(find.text('NEW 3')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await clearedRow.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Clear channel'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('channel-slot-3')), findsNothing);
    expect(find.text('Empty slot'), findsNothing);

    await tester.tap(find.byKey(const ValueKey('show-empty-slots-toggle')));
    await tester.pumpAndSettle();
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-3')),
        matching: find.text('Empty slot'),
      ),
      findsOneWidget,
    );
  });

  testWidgets('double-clicking a channel opens the modal editor', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('GMRS 1').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 1').first);
    await tester.pumpAndSettle();

    expect(find.text('Channel details'), findsOneWidget);
    expect(find.byTooltip('Close editor'), findsOneWidget);
    expect(find.text('Receive frequency (MHz)'), findsOneWidget);
  });

  testWidgets('editor provides standard tones without radio metadata', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('GMRS 1').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 1').first);
    await tester.pumpAndSettle();

    Finder dropdown(String label) => find.descendant(
      of: find.byType(Dialog),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is DropdownButtonFormField<String> &&
            widget.decoration.labelText == label,
      ),
    );

    tester
        .widget<DropdownButtonFormField<String>>(dropdown('Tone mode'))
        .onChanged!('DTCS');
    await tester.pumpAndSettle();

    final dtcsButton = tester.widget<DropdownButton<String>>(
      find.descendant(
        of: dropdown('DTCS code'),
        matching: find.byWidgetPredicate(
          (widget) => widget is DropdownButton<String>,
        ),
      ),
    );
    final values = dtcsButton.items!.map((item) => item.value).toList();
    expect(values, hasLength(standardDtcsCodes.length));
    expect(values, containsAll(['23', '25', '131', '754']));
    expect(
      find.descendant(
        of: find.byType(Dialog),
        matching: find.text('Receive DTCS'),
      ),
      findsNothing,
    );

    tester
        .widget<DropdownButtonFormField<String>>(dropdown('Tone mode'))
        .onChanged!('Tone');
    await tester.pumpAndSettle();

    final toneButton = tester.widget<DropdownButton<String>>(
      find.descendant(
        of: dropdown('Transmit tone (Hz)'),
        matching: find.byWidgetPredicate(
          (widget) => widget is DropdownButton<String>,
        ),
      ),
    );
    final tones = toneButton.items!.map((item) => item.value).toList();
    expect(tones, hasLength(standardCtcssTones.length));
    expect(tones, containsAll(['88.5', '100.0', '254.1']));
  });

  testWidgets('channel editor save commits and close cancels unsaved changes', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    Future<void> openEditor() async {
      await tester.tap(find.text('GMRS 1').first);
      await tester.pump(const Duration(milliseconds: 50));
      await tester.tap(find.text('GMRS 1').first);
      await tester.pumpAndSettle();
    }

    Finder editorNameField() => find.descendant(
      of: find.byType(Dialog),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == 'Name',
      ),
    );

    await openEditor();
    tester.widget<TextField>(editorNameField()).onChanged!('UNSAVED');
    await tester.pump();
    await tester.tap(find.byTooltip('Close editor'));
    await tester.pumpAndSettle();

    expect(find.text('UNSAVED'), findsNothing);
    expect(find.text('GMRS 1'), findsWidgets);

    await openEditor();
    tester.widget<TextField>(editorNameField()).onChanged!('SAVED');
    await tester.pump();
    await tester.tap(find.text('Save channel'));
    await tester.pumpAndSettle();

    expect(find.text('SAVED'), findsOneWidget);
    expect(find.text('GMRS 1'), findsNothing);
  });

  testWidgets('invalid channel names explain why writing is blocked', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 1').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 1').first);
    await tester.pumpAndSettle();
    final nameField = find.descendant(
      of: find.byType(Dialog),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == 'Name',
      ),
    );
    tester.widget<TextField>(nameField).onChanged!('THIS NAME IS LONG');
    await tester.pump();
    await tester.tap(find.text('Save channel'));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('channel-attention-banner')), findsOneWidget);
    expect(
      find.textContaining(
        '1: Name is 17 characters; many radios allow at most 16.',
      ),
      findsOneWidget,
    );
    await tester.tap(find.byKey(const Key('review-channel-attention')));
    await tester.pumpAndSettle();
    expect(nameField, findsOneWidget);
    expect(
      tester.widget<TextField>(nameField).controller?.text,
      'THIS NAME IS LONG',
    );
    tester.widget<TextField>(nameField).onChanged!('SHORT');
    await tester.pump();
    await tester.tap(find.text('Save channel'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('channel-attention-banner')), findsNothing);
  });

  testWidgets('changing a channel location sorts the table by memory slot', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final verticalList = find.byWidgetPredicate(
      (widget) =>
          widget is Scrollable && widget.axisDirection == AxisDirection.down,
    );
    Finder locationField() => find.descendant(
      of: find.byType(Dialog),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == 'Location',
      ),
    );

    Future<void> openChannel(String name) async {
      await tester.scrollUntilVisible(
        find.text(name).first,
        100,
        scrollable: verticalList,
      );
      await tester.tap(find.text(name).first);
      await tester.pump(const Duration(milliseconds: 50));
      await tester.tap(find.text(name).first);
      await tester.pumpAndSettle();
    }

    Future<void> setLocation(int location) async {
      await tester.tap(locationField());
      await tester.pump();
      tester.testTextInput.enterText('$location');
      await tester.pump();
      await tester.tap(find.text('Save channel'));
      await tester.pumpAndSettle();
    }

    await openChannel('GMRS 1');
    await setLocation(30);

    final gmrs22 = tester.getTopLeft(find.text('GMRS 22'));
    final gmrs1 = tester.getTopLeft(find.text('GMRS 1'));
    expect(gmrs22.dy, lessThan(gmrs1.dy));
  });

  testWidgets('vertical channel scrollbar stays at the visible table edge', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final verticalScrollbar = find.byKey(
      const ValueKey('channel-vertical-scrollbar'),
    );
    final horizontalScrollbar = find.byKey(
      const ValueKey('channel-horizontal-scrollbar'),
    );
    final horizontalViewport = find.descendant(
      of: horizontalScrollbar,
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is SingleChildScrollView &&
            widget.scrollDirection == Axis.horizontal,
      ),
    );

    expect(verticalScrollbar, findsOneWidget);
    expect(
      find.ancestor(
        of: verticalScrollbar,
        matching: find.byWidgetPredicate(
          (widget) =>
              widget is SingleChildScrollView &&
              widget.scrollDirection == Axis.horizontal,
        ),
      ),
      findsNothing,
    );
    expect(horizontalViewport, findsOneWidget);
    expect(
      tester.getRect(verticalScrollbar).right,
      closeTo(tester.getRect(horizontalViewport).right, 1),
    );

    await tester.drag(horizontalViewport, const Offset(-800, 0));
    await tester.pumpAndSettle();

    expect(
      tester.getRect(verticalScrollbar).right,
      closeTo(tester.getRect(horizontalViewport).right, 1),
    );
  });

  testWidgets('dragging a channel rearranges and renumbers the rows', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final handles = find.byTooltip('Drag to rearrange channel');
    expect(handles, findsWidgets);
    final start = tester.getCenter(handles.first);
    final target = tester.getCenter(find.text('GMRS 5').first);
    final gesture = await tester.startGesture(start);
    await tester.pump();
    await gesture.moveTo(target);
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();

    final gmrs2 = tester.getTopLeft(find.text('GMRS 2'));
    final gmrs1 = tester.getTopLeft(find.text('GMRS 1'));
    final gmrs6 = tester.getTopLeft(find.text('GMRS 6'));
    expect(gmrs2.dy, lessThan(gmrs1.dy));
    expect(gmrs1.dy, lessThan(gmrs6.dy));
    expect(find.text('Moved GMRS 1 to channel 5'), findsOneWidget);
  });

  testWidgets('frequency field keeps focus while typing', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('GMRS 1').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 1').first);
    await tester.pumpAndSettle();

    Finder field(String label) => find.descendant(
      of: find.byType(Dialog),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == label,
      ),
    );

    final frequency = field('Receive frequency (MHz)');
    final frequencyInput = find.descendant(
      of: frequency,
      matching: find.byType(EditableText),
    );

    await tester.tap(frequency);
    await tester.pump();
    tester.testTextInput.enterText('');
    await tester.pump();
    tester.testTextInput.enterText('1');
    await tester.pump();

    expect(
      tester.widget<EditableText>(frequencyInput).focusNode.hasFocus,
      isTrue,
    );

    for (final value in ['14', '146', '146.', '146.5', '146.52', '146.520']) {
      tester.testTextInput.enterText(value);
      await tester.pump();
    }

    expect(tester.widget<TextField>(frequency).controller?.text, '146.520');
    expect(tester.widget<TextField>(field('Name')).controller?.text, 'GMRS 1');
    expect(
      tester.widget<EditableText>(frequencyInput).focusNode.hasFocus,
      isTrue,
    );
  });

  testWidgets('channel selection updates on pointer down', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 2')),
    );
    await tester.pump();

    final selectedContainer = find.ancestor(
      of: find.text('GMRS 2'),
      matching: find.byWidgetPredicate(
        (widget) =>
            widget is Container && widget.color == const Color(0xFFE8F3ED),
      ),
    );
    expect(selectedContainer, findsOneWidget);
    await gesture.up();
    await tester.pump(const Duration(milliseconds: 500));
  });

  testWidgets('channel columns can be resized and reordered', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final frequencyBefore = tester.getTopLeft(find.text('RX FREQUENCY')).dx;
    await tester.drag(
      find.byKey(const ValueKey('resize-NAME')),
      const Offset(40, 0),
    );
    await tester.pumpAndSettle();
    final frequencyAfter = tester.getTopLeft(find.text('RX FREQUENCY')).dx;
    expect(frequencyAfter, greaterThan(frequencyBefore + 30));

    final tone = find.text('TONE MODE');
    final name = find.text('NAME');
    final dragOffset = tester.getCenter(name) - tester.getCenter(tone);
    await tester.drag(tone, dragOffset);
    await tester.pumpAndSettle();

    expect(tester.getTopLeft(tone).dx, lessThan(tester.getTopLeft(name).dx));
  });

  testWidgets('New confirms before discarding the current channel list', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('New'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Blank configuration'));
    await tester.pumpAndSettle();

    expect(find.text('Start a new blank configuration?'), findsOneWidget);
    expect(find.text('GMRS 1'), findsWidgets);

    await tester.tap(find.text('Discard and continue'));
    await tester.pumpAndSettle();

    expect(find.text('Untitled Library'), findsOneWidget);
    expect(find.text('GMRS 1'), findsNothing);
  });

  testWidgets('GMRS starter remains available from the New menu', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('New'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS starter template'), findsOneWidget);
    await tester.tap(find.text('GMRS starter template'));
    await tester.pumpAndSettle();
    expect(find.text('Apply GMRS starter template'), findsOneWidget);

    await tester.tap(find.text('Apply'));
    await tester.pumpAndSettle();
    expect(find.text('GMRS Starter Library'), findsOneWidget);
    expect(find.text('GMRS 1'), findsWidgets);
  });

  testWidgets('Marine VHF template applies the selected receive-only plan', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('New'));
    await tester.pumpAndSettle();
    expect(find.text('Marine VHF template'), findsOneWidget);
    await tester.tap(find.text('Marine VHF template'));
    await tester.pumpAndSettle();

    expect(find.text('Marine VHF channel template'), findsOneWidget);
    expect(
      find.textContaining('The channel plan is selected by regulatory region'),
      findsOneWidget,
    );
    expect(
      tester
          .widget<CheckboxListTile>(
            find.byKey(const ValueKey('marine-program-transmit')),
          )
          .value,
      isFalse,
    );

    await tester.tap(find.byKey(const ValueKey('marine-template-continue')));
    await tester.pumpAndSettle();

    expect(find.text('US Marine VHF'), findsOneWidget);
    expect(find.text('SEA 01'), findsWidgets);
    expect(find.text('SEA 05'), findsWidgets);
  });

  testWidgets('GMRS template can be inserted starting at a channel number', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('New'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('GMRS starter template'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Insert starting at channel number'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).last, '23');
    await tester.tap(find.text('Apply'));
    await tester.pumpAndSettle();

    expect(find.text('44'), findsWidgets);
  });

  testWidgets('right-click can copy and paste a channel row', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    var gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 1')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Copy'));
    await tester.pumpAndSettle();

    gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 2')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Paste'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Overwrite channel'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNWidgets(2));
  });

  testWidgets('right-click can copy and paste a selected channel block', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 1').first);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.tap(find.text('GMRS 3').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.pump();
    expect(find.text('Edit 3 selected'), findsOneWidget);

    var gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 3').first),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Copy 3 channels'));
    await tester.pumpAndSettle();

    gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 5').first),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Paste 3 channels'));
    await tester.pumpAndSettle();

    expect(find.text('Overwrite 3 channels?'), findsOneWidget);
    await tester.tap(find.text('Overwrite channels'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNWidgets(2));
    expect(find.text('GMRS 2'), findsNWidgets(2));
    expect(find.text('GMRS 3'), findsNWidgets(2));
    expect(find.text('Edit 3 selected'), findsOneWidget);
  });

  testWidgets('right-click cut clears and copies a selected channel block', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 1').first);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.tap(find.text('GMRS 2').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.pump();

    final gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 2').first),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cut 2 channels'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNothing);
    expect(find.text('GMRS 2'), findsNothing);
  });

  testWidgets('right-click can clear a channel row', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    final gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 1')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Clear channel'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNothing);
  });

  testWidgets('right-click can clear all selected channels', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 1').first);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.tap(find.text('GMRS 3').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.pump();
    expect(find.text('Edit 3 selected'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('clear-selected-channels')),
      findsOneWidget,
    );

    final gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 3').first),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Clear 3 selected channels'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNothing);
    expect(find.text('GMRS 2'), findsNothing);
    expect(find.text('GMRS 3'), findsNothing);
    expect(find.text('GMRS 4'), findsOneWidget);
    expect(find.textContaining('Cleared 3 channels'), findsOneWidget);
  });

  testWidgets('toolbar can clear all selected channels', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 1').first);
    await tester.pump();
    await tester.sendKeyDownEvent(LogicalKeyboardKey.shiftLeft);
    await tester.tap(find.text('GMRS 2').first);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.shiftLeft);
    await tester.pump();

    await tester.tap(find.byKey(const ValueKey('clear-selected-channels')));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNothing);
    expect(find.text('GMRS 2'), findsNothing);
    expect(find.text('GMRS 3'), findsOneWidget);
    expect(find.textContaining('Cleared 2 channels'), findsOneWidget);
  });

  testWidgets('right-click cut clears the row in place and paste can move it', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    var gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 1')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cut'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsNothing);
    expect(find.text('GMRS 2'), findsOneWidget);

    gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 2')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Paste'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Overwrite channel'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS 1'), findsOneWidget);
    expect(find.text('GMRS 2'), findsNothing);
  });

  testWidgets('deleting a channel requires confirmation', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);
    await tester.tap(find.text('GMRS 1').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 1').first);
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Delete channel'));
    await tester.pumpAndSettle();
    expect(find.text('Delete channel 1?'), findsOneWidget);

    await tester.tap(
      find.descendant(
        of: find.byType(AlertDialog),
        matching: find.text('Cancel'),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Channel details'), findsOneWidget);
    expect(find.text('GMRS 1'), findsWidgets);

    await tester.tap(find.byTooltip('Delete channel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete channel'));
    await tester.pumpAndSettle();
    expect(find.text('Channel details'), findsNothing);
    expect(find.text('GMRS 1'), findsNothing);
  });

  testWidgets('empty memory slots can be shown and filled in place', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 3').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 3').first);
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Delete channel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete channel'));
    await tester.pumpAndSettle();

    final emptySlot = find.byKey(const ValueKey('channel-slot-3'));
    expect(emptySlot, findsNothing);

    await tester.tap(find.byKey(const ValueKey('show-empty-slots-toggle')));
    await tester.pumpAndSettle();

    expect(emptySlot, findsOneWidget);
    expect(find.text('Empty slot'), findsOneWidget);

    await tester.tap(emptySlot);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(emptySlot);
    await tester.pumpAndSettle();

    expect(find.text('Channel details'), findsOneWidget);
    expect(find.byTooltip('Delete channel'), findsNothing);
    expect(find.text('NEW 3'), findsOneWidget);

    await tester.tap(find.text('Save channel'));
    await tester.pumpAndSettle();

    expect(emptySlot, findsOneWidget);
    expect(find.text('NEW 3'), findsWidgets);
  });

  testWidgets('channels can be dragged into empty memory slots', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    await tester.tap(find.text('GMRS 3').first);
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('GMRS 3').first);
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Delete channel'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Delete channel'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('show-empty-slots-toggle')));
    await tester.pumpAndSettle();

    final source = find.descendant(
      of: find.byKey(const ValueKey('channel-slot-4')),
      matching: find.byTooltip('Drag to rearrange channel'),
    );
    final target = find.byKey(const ValueKey('channel-slot-3'));
    final gesture = await tester.startGesture(tester.getCenter(source));
    await tester.pump();
    await gesture.moveTo(tester.getCenter(target));
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();

    expect(find.text('Moved GMRS 4 to channel 3'), findsOneWidget);
    expect(
      find.descendant(of: target, matching: find.text('GMRS 4')),
      findsOneWidget,
    );
    expect(
      find.descendant(of: target, matching: find.text('Empty slot')),
      findsNothing,
    );
    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-4')),
        matching: find.text('Empty slot'),
      ),
      findsOneWidget,
    );
  });

  testWidgets('empty slots can be inserted and removed without dragging', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await openGmrsStarter(tester);

    var gesture = await tester.startGesture(
      tester.getCenter(find.text('GMRS 2')),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Insert empty slot before'));
    await tester.pumpAndSettle();

    expect(
      find.descendant(
        of: find.byKey(const ValueKey('channel-slot-3')),
        matching: find.text('GMRS 2'),
      ),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('channel-slot-2')), findsNothing);
    expect(
      find.text('Inserted an empty slot before channel 2'),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('show-empty-slots-toggle')));
    await tester.pumpAndSettle();
    final emptySlot = find.byKey(const ValueKey('channel-slot-2'));
    expect(
      find.descendant(of: emptySlot, matching: find.text('Empty slot')),
      findsOneWidget,
    );

    gesture = await tester.startGesture(
      tester.getCenter(emptySlot),
      buttons: kSecondaryMouseButton,
    );
    await tester.pump();
    await gesture.up();
    await tester.pumpAndSettle();
    await tester.tap(find.text('Remove empty slot'));
    await tester.pumpAndSettle();

    expect(
      find.descendant(of: emptySlot, matching: find.text('GMRS 2')),
      findsOneWidget,
    );
    expect(find.text('Empty slot'), findsNothing);
  });

  testWidgets('welcome screen fits the default macOS window', (tester) async {
    tester.view.physicalSize = const Size(800, 600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('What would you like to do?'), findsOneWidget);
  });

  testWidgets('About screen preserves CHIRP attribution and license notice', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('About & licenses'));
    await tester.pumpAndSettle();

    expect(find.text('CHIRP compatibility layer'), findsOneWidget);
    expect(find.textContaining('GNU General Public License'), findsOneWidget);
    expect(
      find.textContaining(
        'available for incorporation into upstream CHIRP',
      ),
      findsOneWidget,
    );
    expect(find.textContaining('WITHOUT ANY WARRANTY'), findsOneWidget);
    expect(
      find.textContaining('https://github.com/ricktek954/newchirp'),
      findsOneWidget,
    );
    expect(find.text('View complete licenses'), findsOneWidget);
    expect(find.textContaining('not affiliated with'), findsOneWidget);
    expect(find.text('New'), findsNothing);
    expect(find.text('Open channel file'), findsNothing);
    expect(
      find.textContaining('Rick Lopez · Lead Programmer'),
      findsNWidgets(2),
    );
    expect(find.textContaining('rick@newchirp.net'), findsNWidgets(2));
    expect(find.textContaining('Randolpho Cafe · Contributor'), findsOneWidget);
    expect(find.textContaining('randolpho@notarubicon.com'), findsOneWidget);
  });

  testWidgets('frequency reference is available from the sidebar', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Frequency reference'));
    await tester.pumpAndSettle();

    expect(find.text('GMRS & FRS Frequency Reference'), findsNWidgets(2));
    expect(find.text('462.5625'), findsOneWidget);
    expect(find.text('Repeater Pairs (GMRS Only)'), findsOneWidget);
    expect(find.text('467.5500'), findsOneWidget);
    expect(find.text('New'), findsNothing);
    expect(find.text('Open channel file'), findsNothing);
    expect(find.text('Print'), findsOneWidget);
  });

  testWidgets('bundled serial backend loads the CHIRP radio catalog', (
    tester,
  ) async {
    await tester.pumpWidget(testApp());
    await tester.pumpAndSettle();
    final source = requireChirpSourceForTests();
    final models = await tester.runAsync(
      () => RadioBridge(sourcePath: source).models(),
    );
    final instructions = await tester.runAsync(
      () => RadioBridge(sourcePath: source).instructions('Baofeng_UV-5R_Mini'),
    );

    expect(models, contains('Baofeng_UV-5R'));
    expect(models, contains('Yaesu_FT-60'));
    expect(instructions?.experimental, contains('beta version'));
    expect(instructions?.preDownload, contains('Turn off your radio'));

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });
}
