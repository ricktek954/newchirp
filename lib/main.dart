import 'dart:async';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:screen_retriever/screen_retriever.dart';
import 'package:window_manager/window_manager.dart';

import 'l10n/l10n.dart';
import 'models/channel_image_baseline.dart';
import 'models/frequency_reference.dart';
import 'models/gm32_channel.dart';
import 'models/marine_channels.dart';
import 'models/radio_channel.dart';
import 'models/radio_mapping.dart';
import 'models/repeater_regions.dart';
import 'models/repeater_search.dart';
import 'services/app_language.dart';
import 'services/channel_list_pdf.dart';
import 'services/chirp_csv.dart';
import 'services/column_layout_store.dart';
import 'services/diagnostic_log.dart';
import 'services/file_save_warning_store.dart';
import 'services/local_file_opener.dart';
import 'services/radio_image_store.dart';
import 'services/repeater_search_preferences_store.dart';
import 'services/radio_selection_store.dart';
import 'services/module_sandbox.dart';
import 'services/mototrbo_cps2_xml.dart';
import 'services/mygmrs_client.dart';
import 'services/library_metrics_store.dart';
import 'services/radio_bridge.dart';
import 'services/update_checker.dart';
import 'services/update_installer.dart';
import 'services/window_state_store.dart';
import 'widgets/channel_library_image_bar.dart';
import 'widgets/file_save_warning_dialog.dart';
import 'widgets/error_report_dialog.dart';
import 'widgets/marine_template_dialog.dart';
import 'widgets/radio_model_picker.dart';
import 'widgets/radio_mapping_dialog.dart';

const _menuChannel = MethodChannel('newchirp/menu');

const String _newChirpVersion = '1.0.77';
const bool _enableMyGmrsDirectory = true;

bool radioModelSelectionReady(List<String> models, String? model) {
  return model != null && models.contains(model);
}

bool shouldLoadRadioCatalogForRestoredSelection(
  List<String> models,
  String? model,
) {
  return model != null && models.isEmpty;
}

String _formatBytes(int bytes) {
  if (bytes < 1024) return '$bytes B';
  final kilobytes = bytes / 1024;
  if (kilobytes < 1024) return '${kilobytes.toStringAsFixed(1)} KB';
  final megabytes = kilobytes / 1024;
  if (megabytes < 1024) return '${megabytes.toStringAsFixed(1)} MB';
  return '${(megabytes / 1024).toStringAsFixed(2)} GB';
}

String adaptRadioPromptButton(String message, String buttonLabel) {
  final normalized = message
      .replaceAll(RegExp(r'<br\s*/?>', caseSensitive: false), '\n')
      .replaceAll(RegExp(r'<[^>]+>'), '');
  final adapted = normalized.replaceAllMapped(
    RegExp(
      r'\b(Click|Clicking|Press|Pressing)\s+(?:the\s+)?["“]?OK["”]?(?:\s+button)?',
      caseSensitive: false,
    ),
    (match) {
      final original = match.group(1)!;
      final action = original.toLowerCase();
      final cased = original[0] == original[0].toUpperCase()
          ? '${action[0].toUpperCase()}${action.substring(1)}'
          : action;
      return '$cased "$buttonLabel"';
    },
  );
  if (!adapted.contains('[PTT]')) {
    return _waitForSendKeyCue(adapted, buttonLabel);
  }
  return adapted.replaceFirst(
    RegExp(
      r',\s*hold the \[PTT\] switch for one second'
      r'(?: to send (?:the )?image)?\.',
      caseSensitive: false,
    ),
    ', wait until the transfer window says "Listening for the radio", '
    'then hold the [PTT] switch for one second to send the image.',
  );
}

/// For radios that start a clone read from their own control ("After
/// clicking OK, press the [BAND] key", "press the DIAL knob", "press
/// \"SET MHz\""), tell the user to wait for the bridge's ready cue. NewChirp
/// opens the port only after the dialog closes, so an early press sends the
/// image to nobody or arrives out of step (2026-11-21 FT-1D, 2026-11-22
/// FTM-300DR reports). Every such cue from `scripts/chirp_bridge.py` starts
/// with [_sendKeyCuePrefix].
const _sendKeyCuePrefix = 'Radio is ready - press';

String _waitForSendKeyCue(String message, String buttonLabel) {
  if (buttonLabel != 'Radio is ready') return message;
  final label = RegExp.escape(buttonLabel);
  final step = RegExp(
    '(after\\s+clicking\\s+"$label"(?:\\s+here)?(?:\\s+in\\s+chirp)?,\\s*)'
    r'((?:(?!\n\s*\d+\.).)*?\bpress)',
    caseSensitive: false,
    dotAll: true,
  );
  final match = step.firstMatch(message);
  if (match == null) return message;
  return message.replaceRange(
    match.start,
    match.start + match.group(1)!.length,
    '${match.group(1)}wait until the transfer window says '
    '"$_sendKeyCuePrefix...", then ',
  );
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final diagnosticLog = DiagnosticLog();
  unawaited(diagnosticLog.initialize());
  diagnosticLog.record(
    'app',
    'NewChirp started',
    context: {
      'version': _newChirpVersion,
      'os': Platform.operatingSystemVersion,
      if (Platform.isLinux) ...{
        'session': Platform.environment['XDG_SESSION_TYPE'] ?? '',
        'gdkBackend': Platform.environment['GDK_BACKEND'] ?? '',
      },
    },
  );
  FlutterError.onError = (details) {
    diagnosticLog.recordError(
      'flutter',
      details.exception,
      details.stack ?? StackTrace.current,
      context: {'library': details.library ?? ''},
    );
    FlutterError.presentError(details);
  };
  ui.PlatformDispatcher.instance.onError = (error, stack) {
    diagnosticLog.recordError('platform', error, stack);
    return false;
  };
  LicenseRegistry.addLicense(() async* {
    yield LicenseEntryWithLineBreaks(const [
      'CHIRP',
    ], await rootBundle.loadString('assets/licenses/CHIRP-GPL-3.0.txt'));
    yield LicenseEntryWithLineBreaks(
      const ['pySerial'],
      await rootBundle.loadString('assets/licenses/PYSERIAL-BSD-3-CLAUSE.txt'),
    );
    yield LicenseEntryWithLineBreaks(const [
      'libusb',
    ], await rootBundle.loadString('assets/licenses/LIBUSB-LGPL-2.1.txt'));
  });
  appLocale.value = localeForLanguageCode(await AppLanguageStore().load());
  if (Platform.isLinux) {
    runApp(NewChirpApp(diagnosticLog: diagnosticLog));
    return;
  }
  await windowManager.ensureInitialized();
  final windowStateStore = WindowStateStore();
  final saved = await _clampWindowState(await windowStateStore.load());
  final windowOptions = WindowOptions(
    size: Size(saved?.width ?? 1280, saved?.height ?? 720),
    minimumSize: const Size(900, 600),
    center: saved == null,
  );
  final windowStateManager = _WindowStateManager(windowStateStore, saved);
  await windowManager.waitUntilReadyToShow(windowOptions, () async {
    if (saved != null) {
      await windowManager.setPosition(Offset(saved.x, saved.y));
      if (saved.maximized) {
        await windowManager.maximize();
      }
    }
    await windowManager.show();
    await windowManager.focus();
    windowStateManager.start();
  });
  runApp(NewChirpApp(diagnosticLog: diagnosticLog));
}

Future<WindowState?> _clampWindowState(WindowState? state) async {
  if (state == null) return null;
  try {
    final displays = await screenRetriever.getAllDisplays();
    if (displays.isEmpty) return state;
    final primary = await screenRetriever.getPrimaryDisplay();
    return normalizeWindowStateForDisplays(
      state: state,
      displays: displays.map(_windowDisplayArea).toList(),
      primary: _windowDisplayArea(primary),
      centerOnMixedScale: Platform.isWindows,
    );
  } on Exception {
    return state;
  }
}

WindowDisplayArea _windowDisplayArea(Display display) {
  return WindowDisplayArea(
    left: display.visiblePosition?.dx ?? 0.0,
    top: display.visiblePosition?.dy ?? 0.0,
    width: display.visibleSize?.width ?? display.size.width,
    height: display.visibleSize?.height ?? display.size.height,
    scaleFactor: display.scaleFactor?.toDouble() ?? 1.0,
  );
}

class _WindowStateManager with WindowListener {
  _WindowStateManager(this._store, this._initial);

  final WindowStateStore _store;
  final WindowState? _initial;
  Rect _normalBounds = const Rect.fromLTWH(0, 0, 1280, 720);
  bool _maximized = false;
  Timer? _saveTimer;

  void start() {
    final initial = _initial;
    if (initial != null) {
      _normalBounds = Rect.fromLTWH(
        initial.x,
        initial.y,
        initial.width,
        initial.height,
      );
      _maximized = initial.maximized;
    }
    windowManager.addListener(this);
  }

  @override
  void onWindowResized() => _scheduleSave();

  @override
  void onWindowMoved() => _scheduleSave();

  @override
  void onWindowMaximize() {
    _maximized = true;
    _scheduleSave();
  }

  @override
  void onWindowUnmaximize() {
    _maximized = false;
    _scheduleSave();
  }

  @override
  void onWindowClose() {
    _saveTimer?.cancel();
    unawaited(_save());
  }

  void _scheduleSave() {
    _saveTimer?.cancel();
    _saveTimer = Timer(const Duration(milliseconds: 400), _save);
  }

  Future<void> _save() async {
    try {
      final maximized = await windowManager.isMaximized();
      _maximized = maximized;
      if (!maximized) {
        _normalBounds = await windowManager.getBounds();
      }
      await _store.save(
        WindowState(
          width: _normalBounds.width,
          height: _normalBounds.height,
          x: _normalBounds.left,
          y: _normalBounds.top,
          maximized: _maximized,
        ),
      );
    } on Exception {
      // Window persistence should never interrupt the app.
    }
  }
}

class NewChirpApp extends StatelessWidget {
  const NewChirpApp({
    super.key,
    this.columnLayoutStore,
    this.radioSelectionStore,
    this.fileSaveWarningStore,
    this.libraryMetricsStore,
    this.repeaterSearchPreferencesStore,
    this.myGmrsService,
    this.updateChecker,
    this.updateInstaller,
    this.exitForUpdate,
    this.diagnosticLog,
    this.checkForUpdatesOnStartup = true,
  });

  final ColumnLayoutStore? columnLayoutStore;
  final RadioSelectionStore? radioSelectionStore;
  final FileSaveWarningStore? fileSaveWarningStore;
  final LibraryMetricsStore? libraryMetricsStore;
  final RepeaterSearchPreferencesStore? repeaterSearchPreferencesStore;
  final MyGmrsService? myGmrsService;
  final UpdateChecker? updateChecker;
  final UpdateInstaller? updateInstaller;
  final Future<void> Function()? exitForUpdate;
  final DiagnosticLog? diagnosticLog;
  final bool checkForUpdatesOnStartup;

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xFF15211D);
    const green = Color(0xFF1F7455);
    return ValueListenableBuilder<Locale?>(
      valueListenable: appLocale,
      builder: (context, locale, _) => _buildApp(locale, ink, green),
    );
  }

  Widget _buildApp(Locale? locale, Color ink, Color green) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NewChirp',
      locale: locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: green,
          brightness: Brightness.light,
          surface: const Color(0xFFF8FAF8),
        ),
        scaffoldBackgroundColor: const Color(0xFFF1F4F1),
        textTheme: ThemeData.light().textTheme.apply(
          bodyColor: ink,
          displayColor: ink,
          fontFamily: Platform.isMacOS ? '.AppleSystemUIFont' : null,
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderSide: BorderSide(color: Color(0xFFD8DEDA)),
          ),
          enabledBorder: OutlineInputBorder(
            borderSide: BorderSide(color: Color(0xFFD8DEDA)),
          ),
          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        ),
        cardTheme: const CardThemeData(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(14)),
            side: BorderSide(color: Color(0xFFDEE4E0)),
          ),
        ),
      ),
      home: NewChirpHome(
        columnLayoutStore: columnLayoutStore,
        radioSelectionStore: radioSelectionStore,
        fileSaveWarningStore: fileSaveWarningStore,
        libraryMetricsStore: libraryMetricsStore,
        repeaterSearchPreferencesStore: repeaterSearchPreferencesStore,
        myGmrsService: myGmrsService,
        updateChecker: updateChecker,
        updateInstaller: updateInstaller,
        exitForUpdate: exitForUpdate,
        diagnosticLog: diagnosticLog,
        checkForUpdatesOnStartup: checkForUpdatesOnStartup,
      ),
    );
  }
}

class NewChirpHome extends StatefulWidget {
  const NewChirpHome({
    super.key,
    this.columnLayoutStore,
    this.radioSelectionStore,
    this.fileSaveWarningStore,
    this.libraryMetricsStore,
    this.repeaterSearchPreferencesStore,
    this.myGmrsService,
    this.updateChecker,
    this.updateInstaller,
    this.exitForUpdate,
    this.diagnosticLog,
    this.checkForUpdatesOnStartup = true,
  });

  final ColumnLayoutStore? columnLayoutStore;
  final RadioSelectionStore? radioSelectionStore;
  final FileSaveWarningStore? fileSaveWarningStore;
  final LibraryMetricsStore? libraryMetricsStore;
  final RepeaterSearchPreferencesStore? repeaterSearchPreferencesStore;
  final MyGmrsService? myGmrsService;
  final UpdateChecker? updateChecker;
  final UpdateInstaller? updateInstaller;
  final Future<void> Function()? exitForUpdate;
  final DiagnosticLog? diagnosticLog;
  final bool checkForUpdatesOnStartup;

  @override
  State<NewChirpHome> createState() => _NewChirpHomeState();
}

typedef _ChannelMappingMembership = ({int modelIndex, String mappingIndex});

class _NewChirpHomeState extends State<NewChirpHome> {
  final _bridge = RadioBridge();
  late final _columnLayoutStore =
      widget.columnLayoutStore ?? ColumnLayoutStore();
  late final _radioSelectionStore =
      widget.radioSelectionStore ?? RadioSelectionStore();
  late final _fileSaveWarningStore =
      widget.fileSaveWarningStore ?? FileSaveWarningStore();
  late final _libraryMetricsStore =
      widget.libraryMetricsStore ?? LibraryMetricsStore();
  bool _libraryMetricsCollapsed = false;
  late final _repeaterSearchPreferencesStore =
      widget.repeaterSearchPreferencesStore ?? RepeaterSearchPreferencesStore();
  late final MyGmrsService _myGmrsService =
      widget.myGmrsService ?? MyGmrsClient();
  late final _updateChecker = widget.updateChecker ?? UpdateChecker();
  late final _updateInstaller =
      widget.updateInstaller ?? const UpdateInstaller();
  late final _diagnosticLog = widget.diagnosticLog ?? DiagnosticLog();
  final _imageStore = RadioImageStore();
  Future<void>? _radioSelectionLoad;
  final _searchController = TextEditingController();
  final _channelTableKey = GlobalKey<_ChannelTableState>();
  final _settingsScrollController = ScrollController();
  List<RadioChannel> _channels = [];
  int _selected = -1;
  final Set<int> _extraSelectedLocations = {};
  int? _selectionAnchorLocation;
  int _page = 0;
  int _frequencyReferenceIndex = -1;
  String _query = '';
  final Map<String, String> _columnFilters = {};
  String _libraryName = 'NewChirp';
  String? _libraryPath;
  bool _libraryOpen = false;
  bool _dirty = false;
  bool _busy = false;
  bool _checkingForUpdates = false;
  String _status = 'Ready';
  List<SerialPortInfo> _ports = [];
  List<String> _models = [];
  Map<String, List<String>> _modelGroups = {};
  String? _port;
  String? _model;
  String? _radioImage;
  String? _radioFirmware;
  String? _chirpModuleName;
  RadioCapabilities? _capabilities;
  List<RadioZone> _radioZones = [];
  List<RadioMappingModel> _radioMappings = [];
  int? _selectedZone;
  bool _transferActive = false;
  bool _transferCancelling = false;
  String _transferLabel = '';
  bool _transferWriting = false;
  // Transfer heartbeat (2026-11-24, DM-32UV on KDE Wayland, ledger
  // w-20261121-ab4d): the write finished but the window stopped redrawing at
  // 18% while the app used 98% CPU and 4.9 GB. Logging frames and memory
  // every few seconds during transfers shows whether the window is still
  // drawing.
  Timer? _transferHeartbeat;
  int _framesDrawn = 0;
  bool _frameCounterInstalled = false;
  double? _transferFraction;
  String _transferDetail = '';
  RadioSettings? _radioSettings;
  bool _settingsLoading = false;
  String? _settingsError;
  bool _settingsDirty = false;
  bool _settingsLoadedFromRadio = false;
  String? _settingsLoadedModel;
  String? _settingsLoadedImage;
  int _settingsGeneration = 0;
  List<String> _columnOrder = [];
  final Map<String, double> _columnWidths = {};
  bool _showEmptySlots = false;
  bool _columnLayoutTouched = false;
  Future<void>? _fileSaveWarningLoad;
  bool _hideFileSaveWarning = false;
  bool _savingLibrary = false;
  List<RadioChannel> _channelClipboard = [];
  List<List<_ChannelMappingMembership>> _channelClipboardMappings = [];
  final Set<int> _clearedLocations = {};
  ChannelImageBaseline? _channelImageBaseline;
  final ChannelLibraryStatsCache _channelStats = ChannelLibraryStatsCache();
  final List<_LibraryState> _undoStack = [];
  final List<_LibraryState> _redoStack = [];

  RadioChannel? get _current => _selected >= 0 && _selected < _channels.length
      ? _channels[_selected]
      : null;

  Set<int> get _selectedChannelLocations {
    final selectedLocations = <int>{};
    final current = _current;
    if (current != null && !current.cleared) {
      selectedLocations.add(current.location);
    }
    for (final location in _extraSelectedLocations) {
      for (final channel in _channels) {
        if (channel.location == location) {
          if (!channel.cleared) selectedLocations.add(location);
          break;
        }
      }
    }
    return selectedLocations;
  }

  bool get _radioModelSelectedForTransfer =>
      radioModelSelectionReady(_models, _model);

  List<RadioChannel> get _activeChannels =>
      _channels.where((channel) => !channel.cleared).toList();

  List<MapEntry<int, RadioChannel>> _channelTableRows() {
    final needle = _query.trim().toLowerCase();
    bool matchesColumnFilters(RadioChannel channel) {
      for (final filter in _columnFilters.entries) {
        final value = filter.value.trim();
        if (value.isEmpty) continue;
        final columnValue = _channelColumnFilterValue(channel, filter.key);
        if (_numericColumnFilter(filter.key)) {
          final number = double.tryParse(value);
          if (number != null && number.toStringAsFixed(6) != columnValue) {
            return false;
          }
        } else if (!columnValue.toLowerCase().contains(value.toLowerCase())) {
          return false;
        }
      }
      return true;
    }

    bool matchesQuery(RadioChannel channel) {
      if (needle.isEmpty) return true;
      if (channel.name.toLowerCase().contains(needle) ||
          channel.comment.toLowerCase().contains(needle)) {
        return true;
      }
      final numeric = double.tryParse(needle);
      if (numeric != null && RegExp(r'^\d+(?:\.\d+)?$').hasMatch(needle)) {
        final exact = numeric.toStringAsFixed(6);
        if (channel.frequency.toStringAsFixed(6) == exact ||
            channel.offset.toStringAsFixed(6) == exact ||
            channel.location.toString().contains(needle)) {
          return true;
        }
        return false;
      }
      return channel.frequency.toString().contains(needle) ||
          channel.location.toString().contains(needle);
    }

    if (needle.isNotEmpty) {
      return _channels
          .where(
            (channel) =>
                !channel.cleared &&
                matchesQuery(channel) &&
                matchesColumnFilters(channel),
          )
          .map((channel) => MapEntry(channel.location, channel))
          .toList()
        ..sort((left, right) => left.key.compareTo(right.key));
    }

    final byLocation = {
      for (final channel in _channels) channel.location: channel,
    };
    if (!_showEmptySlots) {
      return byLocation.entries
          .where(
            (entry) =>
                !entry.value.cleared && matchesColumnFilters(entry.value),
          )
          .map((entry) => MapEntry(entry.key, entry.value))
          .toList()
        ..sort((left, right) => left.key.compareTo(right.key));
    }

    int? minimum = _capabilities?.memoryStart;
    int? maximum = _capabilities?.memoryEnd;
    if (minimum == null || maximum == null || maximum < minimum) {
      if (byLocation.isEmpty) return [];
      final locations = byLocation.keys.toList()..sort();
      minimum = locations.first;
      maximum = locations.last;
    }

    return [
      for (var location = minimum; location <= maximum; location++)
        if (matchesColumnFilters(
          byLocation[location] ??
              RadioChannel(
                location: location,
                name: '',
                frequency: 0,
                cleared: true,
              ),
        ))
          MapEntry(
            location,
            byLocation[location] ??
                RadioChannel(
                  location: location,
                  name: '',
                  frequency: 0,
                  cleared: true,
                ),
          ),
    ];
  }

  bool _numericColumnFilter(String columnId) =>
      columnId == 'RX FREQUENCY' || columnId == 'OFFSET / TX FREQ';

  String _channelColumnFilterValue(RadioChannel channel, String columnId) {
    if (columnId == 'BANK') {
      return _bankLabelsByLocation()[channel.location] ?? '';
    }
    if (columnId.startsWith('extra:')) {
      final name = columnId.substring('extra:'.length);
      final match = channel.extras.where((field) => field.name == name);
      if (match.isEmpty) return '';
      final value = match.first.value;
      return '${value is bool ? (value ? 'On' : 'Off') : value ?? ''}';
    }
    return switch (columnId) {
      '#' => channelNumberLabel(_model, channel.location),
      'NAME' => channel.name,
      'RX FREQUENCY' => channel.frequency.toStringAsFixed(6),
      'TONE MODE' => channel.tone.isEmpty ? 'None' : channel.tone,
      'TX TONE' =>
        effectiveTransmitCtcssTone(channel)?.toStringAsFixed(1) ?? '',
      'RX TONE' => effectiveReceiveCtcssTone(channel)?.toStringAsFixed(1) ?? '',
      'DTCS' => channel.dtcs.toString().padLeft(3, '0'),
      'RX DTCS' =>
        (channel.tone == 'DTCS' ? channel.dtcs : channel.rxDtcs)
            .toString()
            .padLeft(3, '0'),
      'DTCS POL' => channel.dtcsPolarity,
      'DUPLEX' => channel.duplex.isEmpty ? 'Simplex' : channel.duplex,
      'OFFSET / TX FREQ' => channel.offset.toStringAsFixed(6),
      'CROSS MODE' => channel.crossMode,
      'MODE' => channel.mode,
      'STEP' => channel.step.toStringAsFixed(2),
      'POWER' => channel.power,
      'SCAN' => scanLabel(channel.skip),
      'COMMENT' => channel.comment,
      _ => '',
    };
  }

  Map<int, String> _bankLabelsByLocation() {
    final labels = <int, Set<String>>{};
    for (final model in _radioMappings) {
      for (final mapping in model.mappings) {
        for (final location in mapping.channelLocations) {
          labels.putIfAbsent(location, () => <String>{}).add(mapping.name);
        }
      }
    }
    return {
      for (final entry in labels.entries)
        entry.key: (entry.value.toList()..sort()).join(' / '),
    };
  }

  /// Whether Ctrl/Cmd+A should select every visible channel row.
  ///
  /// Only on the channel library, and never while a text field has focus,
  /// so the shortcut still selects text inside search and edit fields.
  bool get _canSelectAllChannels {
    if (_page != 0 || !_libraryOpen || _busy) return false;
    final focusContext = FocusManager.instance.primaryFocus?.context;
    if (focusContext == null) return true;
    if (focusContext.widget is EditableText) return false;
    return focusContext.findAncestorWidgetOfExactType<EditableText>() == null;
  }

  void _selectAllChannels() {
    final locations = [
      for (final row in _channelTableRows())
        if (!row.value.cleared) row.key,
    ];
    if (locations.isEmpty) return;
    final first = locations.first;
    final index = _channels.indexWhere((channel) => channel.location == first);
    if (index < 0) return;
    setState(() {
      _selected = index;
      _extraSelectedLocations
        ..clear()
        ..addAll(locations.skip(1));
      _selectionAnchorLocation = first;
    });
  }

  void _selectChannelAtLocation(int location, _ChannelSelectionMode mode) {
    final index = _channels.indexWhere(
      (channel) => channel.location == location,
    );
    if (index < 0) return;

    if (mode == _ChannelSelectionMode.range) {
      final rows = _channelTableRows();
      final clickedRow = rows.indexWhere((entry) => entry.key == location);
      final anchorRow = rows.indexWhere(
        (entry) => entry.key == _selectionAnchorLocation,
      );
      if (clickedRow < 0) return;
      final anchorIndex = anchorRow < 0 ? clickedRow : anchorRow;
      final start = anchorIndex < clickedRow ? anchorIndex : clickedRow;
      final end = anchorIndex < clickedRow ? clickedRow : anchorIndex;
      final range = {for (var row = start; row <= end; row++) rows[row].key};
      setState(() {
        _selected = index;
        _extraSelectedLocations
          ..clear()
          ..addAll(range.where((selected) => selected != location));
        _selectionAnchorLocation ??= location;
      });
      return;
    }

    if (mode == _ChannelSelectionMode.toggle) {
      final selected = _selectedChannelLocations;
      if (selected.contains(location)) {
        final remaining = selected.toSet()..remove(location);
        if (remaining.isEmpty) return;
        if (_current?.location == location) {
          final nextPrimary = remaining.first;
          final nextIndex = _channels.indexWhere(
            (channel) => channel.location == nextPrimary,
          );
          setState(() {
            _selected = nextIndex;
            _extraSelectedLocations
              ..clear()
              ..addAll(remaining.where((selected) => selected != nextPrimary));
            if (_selectionAnchorLocation == location) {
              _selectionAnchorLocation = nextPrimary;
            }
          });
        } else {
          setState(() => _extraSelectedLocations.remove(location));
        }
      } else if (_current == null) {
        setState(() {
          _selected = index;
          _selectionAnchorLocation = location;
        });
      } else {
        setState(() => _extraSelectedLocations.add(location));
      }
      return;
    }

    setState(() {
      _selected = index;
      _extraSelectedLocations.clear();
      _selectionAnchorLocation = location;
    });
  }

  Future<void> _showBulkChannelEditor() async {
    final selectedLocations = _selectedChannelLocations;
    if (selectedLocations.length < 2) return;
    final channels =
        _channels
            .where(
              (channel) =>
                  selectedLocations.contains(channel.location) &&
                  !channel.cleared,
            )
            .toList()
          ..sort((left, right) => left.location.compareTo(right.location));
    final source = channels.first.copy();
    final initial = source.copy();
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => Dialog(
          child: SizedBox(
            width: 760,
            height: MediaQuery.sizeOf(context).height * 0.82,
            child: _ChannelEditor(
              channel: source,
              radioModel: _model,
              capabilities: _capabilities,
              title: context.l10n.editorBulkTitle(channels.length),
              notice: context.l10n.uiDefaultsComeFromChannelOnlyFields(
                channelNumberLabel(_model, channels.first.location),
              ),
              saveLabel: context.l10n.editorBulkSave(channels.length),
              showLocation: false,
              canDelete: false,
              canSave: () => _bulkChannelDraftChanged(initial, source),
              onChanged: (update) => setDialogState(update),
              onClose: () => Navigator.pop(dialogContext),
              onDelete: () {},
              onSave: () {
                final proposed = [
                  for (final channel in channels)
                    channel.copy()..location = channel.location,
                ];
                for (final channel in proposed) {
                  _applyBulkChannelDraft(initial, source, channel);
                  if (isBaofengGm32(_model)) applyGm32Rules(channel);
                }
                final issues = <String>[];
                for (final channel in proposed) {
                  final channelIssues = [
                    ...channel.validate(
                      minimumLocation: _capabilities?.memoryStart,
                      maximumLocation: _capabilities?.memoryEnd,
                      maximumNameLength: _capabilities?.nameLength,
                      validTuningSteps:
                          _capabilities?.frequencyGridSteps ?? const [],
                      validBands: _capabilities?.validBands ?? const [],
                      validModes: _capabilities?.modes ?? const [],
                      hasTuningStep: _capabilities?.hasTuningStep ?? true,
                      radioModel: _model,
                    ),
                    if (isBaofengGm32(_model))
                      ...gm32ChannelIssues(_model, channel),
                  ];
                  if (channelIssues.isNotEmpty) {
                    issues.add(
                      'Channel '
                      '${channelNumberLabel(_model, channel.location)}: '
                      '${channelIssues.join(' ')}',
                    );
                  }
                }
                if (issues.isNotEmpty) {
                  unawaited(
                    showDialog<void>(
                      context: context,
                      builder: (context) => AlertDialog(
                        title: Text(context.l10n.uiSelectedChannelsNeedChanges),
                        content: SingleChildScrollView(
                          child: Text(issues.join('\n\n')),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(context),
                            child: Text(context.l10n.uiBackToEditor),
                          ),
                        ],
                      ),
                    ),
                  );
                  return;
                }

                _recordHistory(preserveMultiSelection: true);
                setState(() {
                  for (final channel in proposed) {
                    final index = _channels.indexWhere(
                      (existing) => existing.location == channel.location,
                    );
                    if (index >= 0) _channels[index] = channel;
                  }
                  _dirty = true;
                  _markChannelLibraryDirty();
                });
                Navigator.pop(dialogContext);
                ScaffoldMessenger.of(this.context)
                  ..hideCurrentSnackBar()
                  ..showSnackBar(
                    SnackBar(
                      content: Text(
                        context.l10n.uiUpdatedSelectedChannels(channels.length),
                      ),
                      behavior: SnackBarBehavior.floating,
                      duration: const Duration(seconds: 2),
                    ),
                  );
              },
            ),
          ),
        ),
      ),
    );
  }

  bool _bulkChannelDraftChanged(RadioChannel initial, RadioChannel draft) {
    if (initial.name != draft.name ||
        initial.frequency != draft.frequency ||
        initial.duplex != draft.duplex ||
        initial.offset != draft.offset ||
        initial.tone != draft.tone ||
        initial.txTone != draft.txTone ||
        initial.rxTone != draft.rxTone ||
        initial.dtcs != draft.dtcs ||
        initial.dtcsPolarity != draft.dtcsPolarity ||
        initial.rxDtcs != draft.rxDtcs ||
        initial.crossMode != draft.crossMode ||
        initial.mode != draft.mode ||
        initial.step != draft.step ||
        initial.skip != draft.skip ||
        initial.power != draft.power ||
        initial.comment != draft.comment) {
      return true;
    }
    for (final field in draft.extras) {
      ChannelExtraField? original;
      for (final candidate in initial.extras) {
        if (candidate.name == field.name) {
          original = candidate;
          break;
        }
      }
      if (original == null || !mapEquals(original.toJson(), field.toJson())) {
        return true;
      }
    }
    return false;
  }

  void _applyBulkChannelDraft(
    RadioChannel initial,
    RadioChannel draft,
    RadioChannel target,
  ) {
    if (draft.name != initial.name) target.name = draft.name;
    if (draft.frequency != initial.frequency) {
      target.frequency = draft.frequency;
    }
    if (draft.duplex != initial.duplex) target.duplex = draft.duplex;
    if (draft.offset != initial.offset) target.offset = draft.offset;
    if (draft.tone != initial.tone) target.tone = draft.tone;
    if (draft.txTone != initial.txTone) target.txTone = draft.txTone;
    if (draft.rxTone != initial.rxTone) target.rxTone = draft.rxTone;
    if (draft.dtcs != initial.dtcs) target.dtcs = draft.dtcs;
    if (draft.dtcsPolarity != initial.dtcsPolarity) {
      target.dtcsPolarity = draft.dtcsPolarity;
    }
    if (draft.rxDtcs != initial.rxDtcs) target.rxDtcs = draft.rxDtcs;
    if (draft.crossMode != initial.crossMode) {
      target.crossMode = draft.crossMode;
    }
    if (draft.mode != initial.mode) target.mode = draft.mode;
    if (draft.step != initial.step) target.step = draft.step;
    if (draft.skip != initial.skip) target.skip = draft.skip;
    if (draft.power != initial.power) target.power = draft.power;
    if (draft.comment != initial.comment) target.comment = draft.comment;

    for (final draftField in draft.extras) {
      ChannelExtraField? initialField;
      for (final candidate in initial.extras) {
        if (candidate.name == draftField.name) {
          initialField = candidate;
          break;
        }
      }
      if (initialField != null &&
          mapEquals(initialField.toJson(), draftField.toJson())) {
        continue;
      }
      for (final targetField in target.extras) {
        if (targetField.name == draftField.name && targetField.mutable) {
          targetField.value = draftField.value;
          break;
        }
      }
    }
  }

  ChannelLibrarySnapshot get _channelLibrarySnapshot => _channelStats.read(
    imagePath: _radioImage,
    zone: _selectedZone,
    channels: _channels,
    cleared: _clearedLocations,
    mappingSignature: radioMappingsSignature(_radioMappings),
    baseline: _channelImageBaseline,
    memoryStart: _capabilities?.memoryStart,
    memoryEnd: _capabilities?.memoryEnd,
    maximumNameLength: _capabilities?.nameLength,
    radioModel: _model,
    validTuningSteps: _capabilities?.frequencyGridSteps ?? const [],
    validBands: _capabilities?.validBands ?? const [],
    validModes: _capabilities?.modes ?? const [],
    validToneModes: _capabilities?.toneModes ?? const [],
    validCrossModes: _capabilities?.crossModes ?? const [],
    hasTuningStep: _capabilities?.hasTuningStep ?? true,
  );

  ChannelImageMatch get _channelImageMatch => _channelLibrarySnapshot.match;

  void _markChannelLibraryDirty() {
    _channelStats.markDirty();
  }

  void _remapRadioMappingChannels(Map<int, int?> changes) {
    if (_radioMappings.isEmpty || changes.isEmpty) return;
    _radioMappings = remapRadioMappingLocations(_radioMappings, changes);
  }

  List<_ChannelMappingMembership> _mappingMembershipsAt(int location) {
    return [
      for (var modelIndex = 0; modelIndex < _radioMappings.length; modelIndex++)
        for (final mapping in _radioMappings[modelIndex].mappings)
          if (mapping.channelLocations.contains(location))
            (modelIndex: modelIndex, mappingIndex: mapping.index),
    ];
  }

  ({int start, int end})? _bankRangeAt(int location) {
    return mappingRangeAt(_radioMappings, location);
  }

  void _restoreMappingMembershipsAt(
    int location,
    List<_ChannelMappingMembership> memberships,
  ) {
    if (memberships.isEmpty) return;
    final membershipSet = memberships.toSet();
    _radioMappings = [
      for (var modelIndex = 0; modelIndex < _radioMappings.length; modelIndex++)
        if (!_radioMappings[modelIndex].editable)
          _radioMappings[modelIndex]
        else
          _radioMappings[modelIndex].copyWith(
            mappings: [
              for (final mapping in _radioMappings[modelIndex].mappings)
                mapping.copyWith(
                  channelLocations: () {
                    final locations = mapping.channelLocations
                        .where((value) => value != location)
                        .toList();
                    if (membershipSet.contains((
                      modelIndex: modelIndex,
                      mappingIndex: mapping.index,
                    ))) {
                      locations.add(location);
                    }
                    return locations;
                  }(),
                ),
            ],
          ),
    ];
  }

  void _rememberChannelImageBaseline({required bool fromRadio}) {
    _markChannelLibraryDirty();
    final image = _radioImage;
    if (image == null) {
      _channelImageBaseline = null;
      return;
    }
    _channelImageBaseline = ChannelImageBaseline(
      imagePath: image,
      zone: _selectedZone,
      signature: channelListSignature(_channels, _clearedLocations),
      mappingSignature: radioMappingsSignature(_radioMappings),
      loadedFromRadio: fromRadio,
    );
  }

  bool get _settingsHaveInvalidValues {
    bool invalid(RadioSettingNode node) {
      if (node.isGroup) return node.children.any(invalid);
      return node.invalid;
    }

    return _radioSettings?.items.any(invalid) ?? false;
  }

  @override
  void initState() {
    super.initState();
    _menuChannel.setMethodCallHandler((call) async {
      switch (call.method) {
        case 'undo':
          _undo();
          break;
        case 'redo':
          _redo();
          break;
      }
    });
    _syncMenuState();
    _loadColumnLayout();
    _fileSaveWarningLoad = _loadFileSaveWarning();
    _radioSelectionLoad = _loadRadioSelection();
    unawaited(_loadLibraryMetricsCollapsed());
    unawaited(_prepareRestoredRadio());
    if (widget.checkForUpdatesOnStartup) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) unawaited(_checkForUpdates(startup: true));
      });
    }
    final simulatedWrite = int.tryParse(
      Platform.environment['NEWCHIRP_SIMULATE_WRITE'] ?? '',
    );
    if (simulatedWrite != null && simulatedWrite > 0) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) unawaited(_simulateWrite(simulatedWrite));
      });
    }
  }

  void _startTransferHeartbeat(String label) {
    if (!_frameCounterInstalled) {
      _frameCounterInstalled = true;
      SchedulerBinding.instance.addTimingsCallback((timings) {
        _framesDrawn += timings.length;
      });
    }
    _transferHeartbeat?.cancel();
    final elapsed = Stopwatch()..start();
    var lastFrames = _framesDrawn;
    _transferHeartbeat = Timer.periodic(const Duration(seconds: 5), (_) {
      final frames = _framesDrawn - lastFrames;
      lastFrames = _framesDrawn;
      _diagnosticLog.record(
        'transfer',
        'Transfer heartbeat',
        context: {
          'label': label,
          'seconds': elapsed.elapsed.inSeconds,
          'framesLast5s': frames,
          'rssMB': ProcessInfo.currentRss ~/ (1024 * 1024),
          'fraction': _transferFraction ?? -1,
        },
      );
    });
  }

  void _stopTransferHeartbeat() {
    _transferHeartbeat?.cancel();
    _transferHeartbeat = null;
  }

  /// Debug aid: `NEWCHIRP_SIMULATE_WRITE=<seconds>` runs the write progress
  /// window with the DM-32UV's real progress messages and no radio, so a
  /// display freeze can be reproduced on any desktop session. See
  /// docs/LINUX_WAYLAND_FREEZE_TEST.md.
  Future<void> _simulateWrite(int seconds) async {
    _diagnosticLog.record(
      'radio',
      'Simulated write started',
      context: {
        'seconds': seconds,
        'session': Platform.environment['XDG_SESSION_TYPE'] ?? '',
        'gdkBackend': Platform.environment['GDK_BACKEND'] ?? '',
        'desktop': Platform.environment['XDG_CURRENT_DESKTOP'] ?? '',
      },
    );
    const writeLabel =
        'Writing to radio - this takes about a minute. Keep the cable '
        'connected and do not cancel';
    final total = Duration(seconds: seconds);
    final scanEnd = total * 0.3;
    const pages = 120;
    await _transferTask(context.l10n.writingProgress, () async {
      final clock = Stopwatch()..start();
      _reportTransferProgress(
        const RadioProgress(label: 'Scanning flash pages', fraction: 0.10),
      );
      while (clock.elapsed < scanEnd) {
        await Future<void>.delayed(const Duration(milliseconds: 250));
        final part = clock.elapsed.inMilliseconds / scanEnd.inMilliseconds;
        _reportTransferProgress(
          RadioProgress(
            label: 'Scanning flash pages',
            fraction: 0.10 + 0.08 * part.clamp(0.0, 1.0),
          ),
        );
      }
      final pageTime = (total - scanEnd) ~/ pages;
      for (var page = 1; page <= pages; page++) {
        await Future<void>.delayed(pageTime);
        _reportTransferProgress(
          RadioProgress(
            label: '$writeLabel (memory page $page)',
            fraction: 0.18 + 0.80 * page / pages,
          ),
        );
      }
    });
    _diagnosticLog.record(
      'radio',
      'Simulated write completed',
      context: {
        'seconds': seconds,
        'rssMB': ProcessInfo.currentRss ~/ (1024 * 1024),
      },
    );
  }

  Future<void> _loadColumnLayout() async {
    final layout = await _columnLayoutStore.load();
    if (!mounted || layout == null || _columnLayoutTouched) return;
    setState(() {
      _columnOrder = layout.order;
      _columnWidths
        ..clear()
        ..addAll(layout.widths);
      _showEmptySlots = layout.showEmptySlots;
    });
  }

  Future<void> _saveColumnLayout() async {
    try {
      await _columnLayoutStore.save(
        ColumnLayout(
          order: _columnOrder,
          widths: Map.of(_columnWidths),
          showEmptySlots: _showEmptySlots,
        ),
      );
    } on FileSystemException {
      // Layout persistence should never interrupt editing the radio.
    }
  }

  _LibraryState _snapshotLibrary() => _LibraryState(
    channels: _channels.map((channel) => channel.copy()).toList(),
    selected: _selected,
    libraryName: _libraryName,
    libraryPath: _libraryPath,
    libraryOpen: _libraryOpen,
    dirty: _dirty,
    capabilities: _capabilities,
    zones: List.of(_radioZones),
    mappings: List.of(_radioMappings),
    selectedZone: _selectedZone,
    clearedLocations: Set.of(_clearedLocations),
  );

  void _restoreLibrary(_LibraryState state) {
    setState(() {
      _channels = state.channels.map((channel) => channel.copy()).toList();
      _selected = state.selected;
      _extraSelectedLocations.clear();
      _selectionAnchorLocation = _current?.location;
      _libraryName = state.libraryName;
      _libraryPath = state.libraryPath;
      _libraryOpen = state.libraryOpen;
      _dirty = state.dirty;
      _capabilities = state.capabilities;
      _radioZones = List.of(state.zones);
      _radioMappings = List.of(state.mappings);
      _selectedZone = state.selectedZone;
      _clearedLocations
        ..clear()
        ..addAll(state.clearedLocations);
      _markChannelLibraryDirty();
    });
  }

  void _recordHistory({bool preserveMultiSelection = false}) {
    if (!preserveMultiSelection) {
      _extraSelectedLocations.clear();
    }
    _undoStack.add(_snapshotLibrary());
    if (_undoStack.length > 200) _undoStack.removeAt(0);
    _redoStack.clear();
    _syncMenuState();
  }

  void _undo() {
    if (_undoStack.isEmpty) return;
    _redoStack.add(_snapshotLibrary());
    _restoreLibrary(_undoStack.removeLast());
    _syncMenuState();
  }

  void _redo() {
    if (_redoStack.isEmpty) return;
    _undoStack.add(_snapshotLibrary());
    _restoreLibrary(_redoStack.removeLast());
    _syncMenuState();
  }

  void _syncMenuState() {
    unawaited(
      _menuChannel
          .invokeMethod<void>('setUndoState', {
            'undo': _undoStack.isNotEmpty,
            'redo': _redoStack.isNotEmpty,
          })
          .catchError((Object _) {}),
    );
  }

  Future<void> _loadRadioSelection() async {
    final selection = await _radioSelectionStore.load();
    if (!mounted || selection == null) return;
    String? storedImage;
    setState(() {
      _model = selection.model;
      _port = selection.port;
      _radioFirmware = null;
      _capabilities = null;
      _radioZones = [];
      _radioMappings = [];
      _selectedZone = null;
      final model = selection.model;
      if (model != null && _imageStore.hasForModel(model)) {
        _radioImage = _imageStore.pathForModel(model);
        storedImage = _radioImage;
      }
      _markChannelLibraryDirty();
    });
    if (storedImage != null) {
      unawaited(_loadImageCapabilities(storedImage!));
    }
  }

  Future<void> _loadImageCapabilities(String imagePath) async {
    try {
      final info = await _bridge.imageInfo(imagePath);
      if (!mounted || _radioImage != imagePath) return;
      setState(() {
        _radioFirmware = info.firmware;
        _capabilities = info.capabilities;
        _radioZones = info.zones;
        _radioMappings = info.mappings;
        _selectedZone = info.zone;
        _markChannelLibraryDirty();
      });
    } catch (_) {
      // Stored images still support transfer; capabilities are an enhancement.
    }
  }

  Future<void> _switchRadioZone(int zoneIndex) async {
    final image = _radioImage;
    final model = _model;
    final zone = _radioZones
        .where((item) => item.index == zoneIndex)
        .firstOrNull;
    if (image == null || model == null || zone == null) return;
    if (_selectedZone == zoneIndex) return;
    if (_dirty) {
      final proceed = await _confirmReplaceLibrary(
        destination: 'zone ${zone.name}',
      );
      if (!proceed) return;
    }
    // A live radio's snapshot holds only the band that was read, so the
    // other band has to come from the radio (IC-9700 430 band report,
    // 2026-11-19: the snapshot failed with "Unknown file format").
    final RadioInstructions info;
    try {
      info = await _bridge.instructions(model);
    } catch (error) {
      if (mounted) await _showActionError(error);
      return;
    }
    if (!mounted) return;
    if (info.liveRadio) {
      if (_port == null) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(
            SnackBar(
              content: Text(
                context.l10n.uiConnectTheAndChooseItsPort(
                  displayRadioModelName(model),
                  zone.name,
                ),
              ),
            ),
          );
        return;
      }
      await _downloadRadio(liveZone: zoneIndex);
      return;
    }
    late final ({
      List<RadioChannel> channels,
      String model,
      String imagePath,
      String? firmware,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
      List<RadioMappingModel> mappings,
      int? zone,
    })
    imported;
    try {
      imported = await _bridge.readImage(image, zone: zoneIndex);
    } catch (error) {
      if (mounted) await _showActionError(error);
      return;
    }
    if (!mounted || _radioImage != image) return;
    _recordHistory();
    setState(() {
      _channels = [...imported.channels]
        ..sort((left, right) => left.location.compareTo(right.location));
      _selected = _channels.isEmpty ? -1 : 0;
      _clearedLocations.clear();
      _radioFirmware = imported.firmware;
      _capabilities = imported.capabilities;
      _radioZones = imported.zones;
      _radioMappings = imported.mappings;
      _selectedZone = imported.zone;
      _libraryName = '${displayRadioModelName(model)} — ${zone.name}';
      _libraryPath = null;
      _libraryOpen = true;
      _dirty = false;
      _page = 0;
      _rememberChannelImageBaseline(fromRadio: false);
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  Future<void> _editRadioMappings() async {
    if (_busy || _radioMappings.isEmpty) return;
    final edited = await showDialog<List<RadioMappingModel>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => RadioMappingDialog(
        models: _radioMappings,
        channels: _activeChannels,
        radioName: (_model == null
            ? 'this radio'
            : displayRadioModelName(_model!)),
      ),
    );
    if (!mounted || edited == null) return;
    if (radioMappingsSignature(edited) ==
        radioMappingsSignature(_radioMappings)) {
      return;
    }
    _recordHistory();
    setState(() {
      _radioMappings = edited;
      _dirty = true;
      _markChannelLibraryDirty();
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(context.l10n.uiBankAndZoneChangesAreReady),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 3),
        ),
      );
  }

  Future<void> _saveRadioSelection() async {
    try {
      await _radioSelectionStore.save(
        RadioSelection(model: _model, port: _port),
      );
    } on FileSystemException {
      // Selection persistence should never interrupt radio setup.
    }
  }

  void _setColumnOrder(List<String> order) {
    setState(() {
      _columnLayoutTouched = true;
      _columnOrder = order;
    });
    unawaited(_saveColumnLayout());
  }

  void _setColumnWidth(String id, double width) {
    setState(() {
      _columnLayoutTouched = true;
      _columnWidths[id] = width;
    });
    unawaited(_saveColumnLayout());
  }

  void _setShowEmptySlots(bool show) {
    setState(() {
      _columnLayoutTouched = true;
      _showEmptySlots = show;
    });
    unawaited(_saveColumnLayout());
  }

  @override
  void dispose() {
    _stopTransferHeartbeat();
    _searchController.dispose();
    _settingsScrollController.dispose();
    super.dispose();
  }

  Future<void> _refreshPorts() async {
    final ports = await _bridge.serialPortDetails();
    if (!mounted) return;
    setState(() {
      _ports = ports;
      if (!_ports.any((port) => port.port == _port)) {
        _port = _ports.firstOrNull?.port;
      }
    });
  }

  Future<void> _loadModels() async {
    final radioSelectionLoad = _radioSelectionLoad;
    if (radioSelectionLoad != null) await radioSelectionLoad;
    String? storedImage;
    if (!mounted) return;
    await _task(context.l10n.uiLoadingRadioCatalog, () async {
      final catalog = await _bridge.modelCatalog();
      final models = catalog.models;
      setState(() {
        _models = models;
        _modelGroups = {
          for (final group in catalog.groups) group.name: group.models,
        };
        if (_model != null && !models.contains(_model)) _model = null;
        _radioFirmware = null;
        _capabilities = null;
        _radioZones = [];
        _radioMappings = [];
        _selectedZone = null;
        final model = _model;
        if (model != null && _imageStore.hasForModel(model)) {
          _radioImage = _imageStore.pathForModel(model);
          storedImage = _radioImage;
        }
        _markChannelLibraryDirty();
      });
    });
    if (storedImage != null) {
      unawaited(_loadImageCapabilities(storedImage!));
    }
  }

  Future<void> _prepareRestoredRadio() async {
    final radioSelectionLoad = _radioSelectionLoad;
    if (radioSelectionLoad != null) await radioSelectionLoad;
    if (!mounted) return;
    await _refreshPorts();
    if (!mounted) return;
    if (shouldLoadRadioCatalogForRestoredSelection(_models, _model)) {
      await _loadModels();
    }
  }

  void _selectRadioModel(String model) {
    _diagnosticLog.record(
      'radio',
      'Radio model selected',
      context: {'model': model, 'port': _port ?? ''},
    );
    String? storedImage;
    setState(() {
      _model = model;
      _radioFirmware = null;
      _capabilities = null;
      _radioZones = [];
      _radioMappings = [];
      _selectedZone = null;
      _radioImage = _imageStore.hasForModel(model)
          ? _imageStore.pathForModel(model)
          : null;
      storedImage = _radioImage;
      _radioSettings = null;
      _settingsDirty = false;
      _settingsLoadedFromRadio = false;
      _settingsLoadedModel = null;
      _settingsLoadedImage = null;
      _settingsError = null;
      _markChannelLibraryDirty();
    });
    if (storedImage != null) {
      unawaited(_loadImageCapabilities(storedImage!));
    }
    unawaited(_saveRadioSelection());
  }

  Future<void> _task(String label, Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _status = label;
    });
    try {
      await action();
      if (mounted) setState(() => _status = 'Ready');
    } catch (error) {
      if (mounted) {
        setState(() => _status = context.l10n.uiActionFailed);
        await _showActionError(error);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _friendlyActionError(Object error) {
    final message = error.toString();
    if (Platform.isMacOS &&
        error is FileSystemException &&
        (error.osError?.errorCode == 1 ||
            message.contains('Operation not permitted'))) {
      return context.l10n.uiMacosBlockedNewchirpFromWritingTo(message);
    }
    if (Platform.isLinux &&
        (message.contains('Permission denied') ||
            message.contains('Errno 13')) &&
        (message.contains('/dev/tty') ||
            message.contains('could not open port'))) {
      return context.l10n.uiOnLinuxThisUsuallyMeansYour(message);
    }
    return message;
  }

  ({String summary, String? technical}) _actionErrorPresentation(Object error) {
    final message = _friendlyActionError(error).trim();
    const traceMarker = '\n\nRadio communication trace:\n';
    final traceIndex = message.indexOf(traceMarker);
    final coreMessage = traceIndex < 0
        ? message
        : message.substring(0, traceIndex).trim();
    final lines = coreMessage
        .split('\n')
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .toList();
    final hasTechnicalNoise = lines.any((line) {
      return line.contains('Warning:') ||
          line.startsWith('Traceback (most recent call last)') ||
          line.startsWith('File "') ||
          RegExp(r'^.+\.py:\d+:').hasMatch(line);
    });
    if (!hasTechnicalNoise && traceIndex < 0) {
      return (summary: message, technical: null);
    }
    final readable = lines
        .where(
          (line) =>
              !line.contains('Warning:') &&
              !line.startsWith('Traceback (most recent call last)') &&
              !line.startsWith('File "') &&
              !RegExp(r'^.+\.py:\d+:').hasMatch(line),
        )
        .toList();
    var summary = readable.isNotEmpty ? readable.last : lines.last;
    final nameError = RegExp(
      r"Channel (\d+): Name character `(.+)' not supported",
    ).firstMatch(summary);
    if (nameError != null) {
      summary =
          'Channel ${nameError.group(1)} contains the character '
          '“${nameError.group(2)}”, which this radio does not support.';
    }
    return (summary: summary, technical: message == summary ? null : message);
  }

  Future<void> _showActionError(Object error) {
    final presentation = _actionErrorPresentation(error);
    _diagnosticLog.recordError(
      'action-error',
      error,
      StackTrace.current,
      context: {
        'page': _page,
        'radio': _model ?? '',
        'port': _port ?? '',
        'library': _libraryName,
      },
    );
    return showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.uiCouldnTCompleteThatAction),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 620),
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                SelectableText(
                  presentation.summary,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    height: 1.35,
                  ),
                ),
                if (presentation.technical != null) ...[
                  const SizedBox(height: 12),
                  Theme(
                    data: Theme.of(
                      context,
                    ).copyWith(dividerColor: Colors.transparent),
                    child: ExpansionTile(
                      tilePadding: EdgeInsets.zero,
                      childrenPadding: const EdgeInsets.only(top: 4, bottom: 8),
                      title: Text(
                        context.l10n.uiMoreInfo,
                        style: TextStyle(
                          color: Colors.black54,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      children: [
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF3F5F4),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: SelectableText(
                            presentation.technical!,
                            style: const TextStyle(
                              color: Colors.black54,
                              fontFamily: 'monospace',
                              fontSize: 11.5,
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.close),
          ),
          FilledButton.icon(
            onPressed: () {
              Navigator.pop(dialogContext);
              unawaited(
                _showErrorReport(
                  summary: presentation.summary,
                  technical: presentation.technical,
                ),
              );
            },
            icon: const Icon(Icons.bug_report_outlined),
            label: Text(context.l10n.uiSubmitBugReport),
          ),
        ],
      ),
    );
  }

  Future<void> _showErrorReport({required String summary, String? technical}) {
    _diagnosticLog.record(
      'report',
      'Error report dialog opened',
      context: {
        'radio': _model ?? '',
        'page': _page,
        'firmware': _radioFirmware ?? '',
      },
    );
    return showDialog<void>(
      context: context,
      builder: (context) => ErrorReportDialog(
        diagnosticLog: _diagnosticLog,
        summary: summary,
        technical: technical,
        radio: _model ?? 'No radio selected',
        firmware: _radioFirmware ?? 'Not available',
        version: _newChirpVersion,
        cable: _port == null ? 'No serial port selected' : 'Serial port $_port',
        imagePath: _reportImagePath(summary, technical),
      ),
    );
  }

  /// The radio image a report should offer: the one a failed read saved
  /// (its path is in the error text), else the current radio's stored image.
  String? _reportImagePath(String summary, String? technical) {
    final text = '$summary\n${technical ?? ''}';
    for (final match in RegExp(
      r'^\s*(.+\.img)\s*$',
      multiLine: true,
    ).allMatches(text)) {
      final path = match.group(1)!.trim();
      if (File(path).existsSync()) return path;
    }
    final stored = _radioImage;
    if (stored != null && File(stored).existsSync()) return stored;
    return null;
  }

  Future<void> _openLibraryFile() async {
    const type = XTypeGroup(
      label: 'CHIRP images, CSV, or MOTOTRBO XML',
      extensions: ['csv', 'img', 'icf', 'itm', 'd72', 'xml'],
    );
    final file = await openFile(acceptedTypeGroups: const [type]);
    if (file == null) return;
    final lowerPath = file.path.toLowerCase();
    _diagnosticLog.record(
      'file',
      'Open channel file selected',
      context: {'name': file.name},
    );
    final isXml = lowerPath.endsWith('.xml');
    if (!lowerPath.endsWith('.csv') && !isXml) {
      await _importChirpImage(file);
      return;
    }
    late final List<RadioChannel> channels;
    try {
      final bytes = await file.readAsBytes();
      channels = isXml
          ? MototrboCps2Xml.decode(ChirpCsv.decodeText(bytes))
          : ChirpCsv.decodeBytes(bytes);
    } catch (error) {
      if (mounted) await _showActionError(error);
      return;
    }
    if (channels.isEmpty) {
      if (mounted) {
        await _showActionError(
          const FormatException('No channel rows were found.'),
        );
      }
      return;
    }
    if (!mounted) return;

    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: isXml
                ? context.l10n.uiMototrboCpsChannels
                : context.l10n.uiCsvChannels,
            count: channels.length,
          )
        : const _ChannelApplyMode(replaceAll: true, startAt: 1);
    if (mode == null || !mounted) return;

    await _task('Importing ${file.name}…', () async {
      _recordHistory();
      _applyChannels(
        channels,
        mode,
        libraryName: file.name.replaceFirst(
          RegExp(r'\.(?:csv|xml)$', caseSensitive: false),
          '',
        ),
        libraryPath: file.path,
      );
    });
  }

  Future<void> _loadChirpModule() async {
    final blocker = await moduleSandboxBlocker();
    if (!mounted) return;
    if (blocker != null) {
      await _showActionError(RadioBridgeException(blocker));
      return;
    }
    const type = XTypeGroup(
      label: 'CHIRP driver modules',
      extensions: ['py', 'mod'],
    );
    final file = await openFile(acceptedTypeGroups: const [type]);
    if (file == null || !mounted) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.l10n.uiLoadExperimentalChirpModule),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(context.l10n.uiChirpModulesAreExecutablePythonCode),
              SizedBox(height: 12),
              Text(context.l10n.uiOnlyLoadAModuleFromA),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFF9B3D2E),
            ),
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.uiLoadModule),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    await _task('Loading ${file.name}…', () async {
      final models = await _bridge.loadModule(file.path);
      if (!mounted) return;
      setState(() {
        _chirpModuleName = file.name;
        _models = models;
        _modelGroups = {};
        _model = null;
        _radioFirmware = null;
        _capabilities = null;
        _radioZones = [];
        _radioMappings = [];
        _selectedZone = null;
        _radioImage = null;
        _radioSettings = null;
        _settingsDirty = false;
        _settingsLoadedFromRadio = false;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _settingsError = null;
        _markChannelLibraryDirty();
      });
      await _saveRadioSelection();
    });
  }

  Future<void> _unloadChirpModule() async {
    _bridge.unloadModule();
    await _task(context.l10n.uiRefreshingRadioCatalog, () async {
      final catalog = await _bridge.modelCatalog();
      final models = catalog.models;
      if (!mounted) return;
      setState(() {
        _chirpModuleName = null;
        _models = models;
        _modelGroups = {
          for (final group in catalog.groups) group.name: group.models,
        };
        _model = null;
        _radioFirmware = null;
        _capabilities = null;
        _radioZones = [];
        _radioMappings = [];
        _selectedZone = null;
        _radioImage = null;
        _radioSettings = null;
        _settingsDirty = false;
        _settingsLoadedFromRadio = false;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _settingsError = null;
        _markChannelLibraryDirty();
      });
      await _saveRadioSelection();
    });
  }

  Future<void> _importChirpImage(XFile file) async {
    late final ({
      List<RadioChannel> channels,
      String model,
      String imagePath,
      String? firmware,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
      List<RadioMappingModel> mappings,
      int? zone,
    })
    imported;
    try {
      imported = await _bridge.readImage(file.path);
    } catch (error) {
      if (mounted) await _showActionError(error);
      return;
    }
    if (!mounted) return;
    final proceed = await _confirmReplaceLibrary(
      destination: context.l10n.uiThisChirpImage,
    );
    if (!proceed || !mounted) return;

    await _task('Opening ${file.name}…', () async {
      String storedImage;
      try {
        storedImage = await _imageStore.saveForModel(
          imported.model,
          imported.imagePath,
        );
      } catch (error) {
        if (mounted) await _showActionError(error);
        return;
      }
      if (!mounted) return;
      _recordHistory();
      _applyChannels(
        imported.channels,
        const _ChannelApplyMode(replaceAll: true, startAt: 1),
        libraryName: file.name.replaceFirst(RegExp(r'\.[^.]+$'), ''),
        clearRemovedLocations: false,
      );
      setState(() {
        _model = imported.model;
        _radioImage = storedImage;
        _radioFirmware = imported.firmware;
        _capabilities = imported.capabilities;
        _radioZones = imported.zones;
        _radioMappings = imported.mappings;
        _selectedZone = imported.zone;
        if (!_models.contains(imported.model)) {
          _models = [..._models, imported.model]..sort();
        }
        _radioSettings = null;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _settingsError = null;
        _rememberChannelImageBaseline(fromRadio: false);
      });
      unawaited(_saveRadioSelection());
    });
    await _reportUndecodedChannels();
  }

  Future<_ChannelApplyMode?> _chooseChannelApplyMode({
    required String label,
    required int count,
  }) async {
    return showDialog<_ChannelApplyMode>(
      context: context,
      barrierDismissible: false,
      builder: (context) => _ChannelApplyDialog(
        label: label,
        count: count,
        initialStart: _nextChannelLocation() ?? _capabilities?.memoryStart ?? 1,
        zoneName: _keepsRadioZoneOnReplace
            ? _radioZones
                  .where((zone) => zone.index == _selectedZone)
                  .firstOrNull
                  ?.name
            : null,
      ),
    );
  }

  // Replacing the list while a zoned radio image is open must keep the zone:
  // dropping it sent the next write to the driver's default zone 1 and
  // cleared zone 1's other channels (UV-5RM Plus v2, INBOX:924).
  bool get _keepsRadioZoneOnReplace =>
      _radioImage != null && _selectedZone != null;

  void _applyChannels(
    List<RadioChannel> incoming,
    _ChannelApplyMode mode, {
    required String libraryName,
    String? libraryPath,
    bool clearRemovedLocations = true,
  }) {
    if (mode.replaceAll) {
      final sorted = [...incoming]
        ..sort((left, right) => left.location.compareTo(right.location));
      final replacementClears = clearRemovedLocations
          ? clearedLocationsAfterReplacement(
              previousChannels: _channels,
              previousCleared: _clearedLocations,
              replacementChannels: sorted,
            )
          : <int>{};
      final keepZone = _keepsRadioZoneOnReplace;
      setState(() {
        _channels = sorted;
        _selected = sorted.isEmpty ? -1 : 0;
        _libraryName = libraryName;
        _libraryPath = libraryPath;
        _libraryOpen = true;
        _page = 0;
        _dirty = keepZone;
        if (!keepZone) {
          _radioZones = [];
          _radioMappings = [];
          _selectedZone = null;
        }
        _clearedLocations
          ..clear()
          ..addAll(replacementClears);
        _markChannelLibraryDirty();
      });
      return;
    }

    final shifted = <RadioChannel>[];
    for (var i = 0; i < incoming.length; i++) {
      shifted.add(incoming[i].copy()..location = mode.startAt + i);
    }
    final last = mode.startAt + incoming.length - 1;
    final kept = _channels
        .where((c) => c.location < mode.startAt || c.location > last)
        .toList();
    final merged = [...kept, ...shifted]
      ..sort((a, b) => a.location.compareTo(b.location));
    setState(() {
      _channels = merged;
      _selected = merged.isEmpty ? -1 : 0;
      _libraryOpen = true;
      _dirty = true;
      for (var location = mode.startAt; location <= last; location++) {
        _clearedLocations.remove(location);
      }
      _markChannelLibraryDirty();
    });
  }

  int? _nextChannelLocation() => RadioChannel.nextAvailableLocation(
    _channels,
    minimum: _capabilities?.memoryStart ?? 1,
    maximum: _capabilities?.memoryEnd,
  );

  List<String> _channelIssues(RadioChannel channel) => channel.validate(
    minimumLocation: _capabilities?.memoryStart,
    maximumLocation: _capabilities?.memoryEnd,
    maximumNameLength: _capabilities?.nameLength,
    radioModel: _model,
    validTuningSteps: _capabilities?.frequencyGridSteps ?? const [],
    validBands: _capabilities?.validBands ?? const [],
    validModes: _capabilities?.modes ?? const [],
    validToneModes: _capabilities?.toneModes ?? const [],
    validCrossModes: _capabilities?.crossModes ?? const [],
    hasTuningStep: _capabilities?.hasTuningStep ?? true,
  );

  Future<void> _reviewChannelIssues(RadioChannel channel) async {
    final index = _channels.indexOf(channel);
    if (index < 0) return;
    setState(() {
      _selected = index;
      _extraSelectedLocations.clear();
      _selectionAnchorLocation = channel.location;
    });
    await _showChannelEditorAtLocation(channel.location);
  }

  List<RadioChannel> _channelsWithLongNames() {
    final limit = _capabilities?.nameLength;
    if (limit == null || limit <= 0) return const [];
    return _activeChannels
        .where((channel) => channel.name.length > limit)
        .toList();
  }

  /// Cut every channel name that is longer than the radio allows, after the
  /// operator confirms a preview. One undo step restores all of them.
  Future<void> _shortenLongNames() async {
    final limit = _capabilities?.nameLength;
    final long = _channelsWithLongNames();
    if (limit == null || long.isEmpty) return;
    String shortened(String name) => name.substring(0, limit).trimRight();
    final shortNames = {
      for (final channel in _activeChannels)
        channel.location: channel.name.length > limit
            ? shortened(channel.name)
            : channel.name,
    };
    final counts = <String, int>{};
    for (final name in shortNames.values) {
      if (name.isEmpty) continue;
      counts[name] = (counts[name] ?? 0) + 1;
    }
    final duplicates = long
        .where((channel) => (counts[shortNames[channel.location]] ?? 0) > 1)
        .length;
    final l10n = context.l10n;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.shortenNamesTitle(limit)),
        content: SizedBox(
          width: 460,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(l10n.shortenNamesBody(long.length, limit)),
              const SizedBox(height: 12),
              for (final channel in long.take(6))
                Text(
                  '${channelNumberLabel(_model, channel.location)}: '
                  '${channel.name}  →  ${shortNames[channel.location]}',
                  style: const TextStyle(fontFamily: 'monospace'),
                ),
              if (long.length > 6) Text(l10n.shortenNamesMore(long.length - 6)),
              if (duplicates > 0) ...[
                const SizedBox(height: 12),
                Text(
                  l10n.shortenNamesDuplicates(duplicates),
                  style: const TextStyle(color: Color(0xFF8A4C0E)),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            key: const Key('confirm-shorten-names'),
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.shortenNamesAction(long.length)),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    _recordHistory(preserveMultiSelection: true);
    setState(() {
      for (final channel in long) {
        channel.name = shortNames[channel.location]!;
      }
      _dirty = true;
      _markChannelLibraryDirty();
    });
    _diagnosticLog.record(
      'library',
      'Shortened long channel names',
      context: {'count': long.length, 'limit': limit, 'radio': _model ?? ''},
    );
  }

  void _sortChannelsByLocation() {
    _channels.sort((left, right) => left.location.compareTo(right.location));
  }

  void _moveChannel(int fromIndex, int toIndex) {
    if (_query.isNotEmpty ||
        fromIndex == toIndex ||
        fromIndex < 0 ||
        toIndex < 0 ||
        fromIndex >= _channels.length ||
        toIndex >= _channels.length ||
        _channels[fromIndex].cleared) {
      return;
    }

    final slots = _channels.map((channel) => channel.location).toList();
    final representedSlots = slots.toSet();
    final deletedSlots = _clearedLocations
        .where((location) => !representedSlots.contains(location))
        .toSet();
    final moved = _channels[fromIndex];
    final oldLocations = {
      for (final channel in _channels) channel: channel.location,
    };

    _recordHistory();
    setState(() {
      _channels.removeAt(fromIndex);
      _channels.insert(toIndex, moved);
      for (var index = 0; index < _channels.length; index++) {
        _channels[index].location = slots[index];
      }
      _clearedLocations
        ..clear()
        ..addAll(deletedSlots)
        ..addAll(
          _channels
              .where((channel) => channel.cleared)
              .map((channel) => channel.location),
        );
      _remapRadioMappingChannels({
        for (final channel in _channels)
          oldLocations[channel]!: channel.location,
      });
      _selected = toIndex;
      _dirty = true;
      _markChannelLibraryDirty();
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            context.l10n.uiMovedToChannel(moved.name, moved.location),
          ),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  void _moveChannelToLocation(int fromIndex, int targetLocation) {
    if (_query.isNotEmpty ||
        fromIndex < 0 ||
        fromIndex >= _channels.length ||
        _channels[fromIndex].cleared) {
      return;
    }
    final moved = _channels[fromIndex];
    final previousLocation = moved.location;
    if (previousLocation == targetLocation) return;

    _recordHistory();
    setState(() {
      final locationChanges = <int, int?>{
        previousLocation: targetLocation,
        targetLocation: null,
      };
      _channels.removeWhere(
        (channel) =>
            channel.location == targetLocation &&
            channel.cleared &&
            !identical(channel, moved),
      );
      moved.location = targetLocation;
      _remapRadioMappingChannels(locationChanges);
      _clearedLocations
        ..remove(targetLocation)
        ..add(previousLocation);
      _sortChannelsByLocation();
      _selected = _channels.indexOf(moved);
      _dirty = true;
      _markChannelLibraryDirty();
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            context.l10n.uiMovedToChannel(moved.name, targetLocation),
          ),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  void _insertEmptySlotBefore(int location) {
    if (_query.isNotEmpty) return;
    if (showsMidlandChannelNumbers(_model)) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(context.l10n.uiThisRadioHasFixedChannelLocations),
            behavior: SnackBarBehavior.floating,
          ),
        );
      return;
    }
    final maximum = _capabilities?.memoryEnd;
    final bankRange = _bankRangeAt(location);
    final shiftEnd = bankRange?.end ?? maximum;
    if (maximum != null &&
        bankRange == null &&
        _channels.any((channel) => channel.location >= maximum)) {
      _showNoEmptyChannelSlot();
      return;
    }
    if (bankRange != null &&
        _channels.any(
          (channel) => channel.location == bankRange.end && !channel.cleared,
        )) {
      _showNoEmptyChannelSlot();
      return;
    }

    final selectedChannel = _current;
    _recordHistory();
    setState(() {
      final locationChanges = <int, int?>{};
      for (final channel in _channels) {
        if (channel.location >= location &&
            (shiftEnd == null || channel.location <= shiftEnd)) {
          locationChanges[channel.location] = channel.location + 1;
          channel.location += 1;
        }
      }
      if (!locationChanges.containsKey(location)) {
        locationChanges[location] = null;
      }
      _remapRadioMappingChannels(locationChanges);
      final shiftedClears =
          _clearedLocations
              .map(
                (cleared) =>
                    cleared < location ||
                        (shiftEnd != null && cleared > shiftEnd)
                    ? cleared
                    : shiftEnd != null && cleared == shiftEnd
                    ? shiftEnd
                    : cleared + 1,
              )
              .toSet()
            ..add(location);
      _clearedLocations
        ..clear()
        ..addAll(shiftedClears);
      _sortChannelsByLocation();
      _selected = selectedChannel == null
          ? -1
          : _channels.indexOf(selectedChannel);
      _dirty = true;
      _markChannelLibraryDirty();
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            context.l10n.uiInsertedAnEmptySlotBeforeChannel(location),
          ),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
  }

  void _removeEmptySlot(int location) {
    if (_query.isNotEmpty) return;
    if (showsMidlandChannelNumbers(_model)) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(context.l10n.uiThisRadioHasFixedChannelLocations2),
            behavior: SnackBarBehavior.floating,
          ),
        );
      return;
    }

    final selectedChannel = _current;
    final shiftEnd = _bankRangeAt(location)?.end;
    _recordHistory();
    setState(() {
      final shiftedClears = clearedLocationsAfterEmptySlotRemoval(
        channels: _channels,
        clearedLocations: _clearedLocations,
        location: location,
        rangeEnd: shiftEnd,
      );
      final locationChanges = <int, int?>{};
      for (final channel in _channels) {
        if (channel.location >= location &&
            (shiftEnd == null || channel.location <= shiftEnd)) {
          locationChanges[channel.location] = channel.location - 1;
        }
      }
      _channels.removeWhere((channel) => channel.location == location);
      for (final channel in _channels) {
        if (channel.location > location &&
            (shiftEnd == null || channel.location <= shiftEnd)) {
          channel.location -= 1;
        }
      }
      _remapRadioMappingChannels(locationChanges);
      _clearedLocations
        ..clear()
        ..addAll(shiftedClears);
      _sortChannelsByLocation();
      _selected = selectedChannel == null
          ? -1
          : _channels.indexOf(selectedChannel);
      _dirty = true;
      _markChannelLibraryDirty();
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(context.l10n.uiRemovedEmptySlot(location)),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
  }

  Future<void> _findRepeaters() async {
    final channels = await showDialog<List<RadioChannel>>(
      context: context,
      builder: (context) => RepeaterBookDialog(
        bridge: _bridge,
        preferencesStore: _repeaterSearchPreferencesStore,
        myGmrsService: _myGmrsService,
      ),
    );
    if (channels == null || channels.isEmpty || !mounted) return;
    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: context.l10n.uiRepeaterbookResults,
            count: channels.length,
          )
        : const _ChannelApplyMode(replaceAll: true, startAt: 1);
    if (mode == null || !mounted) return;
    _recordHistory();
    _applyChannels(channels, mode, libraryName: 'RepeaterBook Repeaters');
  }

  void _showNoEmptyChannelSlot() {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            _capabilities?.memoryEnd == null
                ? context.l10n.uiNoEmptyChannelSlotIsAvailable
                : context.l10n.uiNoEmptyChannelSlotsAreAvailable,
          ),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 3),
        ),
      );
  }

  Future<void> _loadFileSaveWarning() async {
    final hidden = await _fileSaveWarningStore.isHidden();
    if (!mounted) return;
    _hideFileSaveWarning = hidden;
  }

  Future<bool> _confirmFileSaveDoesNotWriteRadio() async {
    await _fileSaveWarningLoad;
    if (!mounted || _hideFileSaveWarning) {
      return mounted && _hideFileSaveWarning;
    }
    final hideNextTime = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => const FileSaveWarningDialog(),
    );
    if (hideNextTime == null || !mounted) return false;
    if (hideNextTime) {
      _hideFileSaveWarning = true;
      try {
        await _fileSaveWarningStore.hide();
      } on FileSystemException {
        // Remembering the choice should not block the file save.
        _hideFileSaveWarning = false;
      }
    }
    return mounted;
  }

  Future<void> _saveCsv({bool saveAs = false}) async {
    if (_savingLibrary) return;
    _savingLibrary = true;
    try {
      await _saveCsvNow(saveAs: saveAs);
    } finally {
      _savingLibrary = false;
    }
  }

  Future<void> _saveCsvNow({required bool saveAs}) async {
    if (!await _confirmFileSaveDoesNotWriteRadio()) return;
    if (!mounted) return;
    var path = _libraryPath;
    if (saveAs || path == null) {
      const type = XTypeGroup(label: 'CHIRP CSV', extensions: ['csv']);
      final location = await getSaveLocation(
        initialDirectory: _libraryPath == null
            ? null
            : File(_libraryPath!).parent.path,
        suggestedName: '${_libraryName.replaceAll(' ', '_')}.csv',
        acceptedTypeGroups: const [type],
      );
      path = location?.path;
    }
    if (path == null) return;
    var savePath = path.endsWith('.csv') ? path : '$path.csv';
    setState(() {
      _busy = true;
      _status = context.l10n.uiSavingChannelLibrary;
    });
    try {
      try {
        await File(savePath).writeAsString(ChirpCsv.encode(_activeChannels));
      } on FileSystemException catch (error) {
        if (!Platform.isMacOS ||
            (error.osError?.errorCode != 1 &&
                !error.toString().contains('Operation not permitted'))) {
          rethrow;
        }
        if (!mounted) rethrow;
        final chooseAnother = await showDialog<bool>(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            icon: const Icon(
              Icons.folder_off_outlined,
              color: Color(0xFFC46A15),
            ),
            title: Text(context.l10n.uiMacosBlockedTheSaveLocation),
            content: Text(context.l10n.uiNewchirpDoesNotHavePermissionTo),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: Text(context.l10n.cancel),
              ),
              FilledButton.icon(
                onPressed: () => Navigator.pop(context, true),
                icon: const Icon(Icons.folder_open_outlined),
                label: Text(context.l10n.uiChooseAnotherFolder),
              ),
            ],
          ),
        );
        if (!mounted) return;
        if (chooseAnother != true) {
          setState(() => _status = context.l10n.uiSaveCanceled);
          return;
        }
        const type = XTypeGroup(label: 'CHIRP CSV', extensions: ['csv']);
        final location = await getSaveLocation(
          suggestedName: File(savePath).uri.pathSegments.last,
          acceptedTypeGroups: const [type],
        );
        if (!mounted) return;
        if (location == null) {
          setState(() => _status = context.l10n.uiSaveCanceled);
          return;
        }
        savePath = location.path.endsWith('.csv')
            ? location.path
            : '${location.path}.csv';
        await File(savePath).writeAsString(ChirpCsv.encode(_activeChannels));
      }
      if (mounted) {
        setState(() {
          _libraryPath = savePath;
          _dirty = false;
          _status = 'Ready';
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() => _status = context.l10n.uiActionFailed);
        await _showActionError(error);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<bool> _confirmReplaceLibrary({required String destination}) async {
    if (!_libraryOpen) return true;
    final discard = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: Color(0xFFC46A15)),
        title: Text(context.l10n.uiStart(destination)),
        content: Text(
          _dirty
              ? context.l10n.uiDiscardTheCurrentChannelListAny
              : context.l10n.uiCloseTheCurrentChannelListAnd(destination),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.uiKeepCurrentList),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.uiDiscardAndContinue),
          ),
        ],
      ),
    );
    return discard == true && mounted;
  }

  Future<void> _newLibrary() async {
    if (!await _confirmReplaceLibrary(
      destination: context.l10n.uiANewBlankConfiguration,
    )) {
      return;
    }
    _recordHistory();
    setState(() {
      _channels = [];
      _selected = -1;
      _clearedLocations.clear();
      _libraryName = 'Untitled Library';
      _libraryPath = null;
      _libraryOpen = true;
      _page = 0;
      _dirty = false;
      _capabilities = null;
      _radioZones = [];
      _radioMappings = [];
      _selectedZone = null;
      _markChannelLibraryDirty();
    });
  }

  Future<void> _useGmrsStarter() async {
    final template = gmrsStarterChannels();
    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: context.l10n.newGmrs,
            count: template.length,
          )
        : const _ChannelApplyMode(replaceAll: true, startAt: 1);
    if (mode == null || !mounted) return;
    _recordHistory();
    _applyChannels(template, mode, libraryName: 'GMRS Starter Library');
  }

  Future<void> _useMarineTemplate() async {
    final selection = await showDialog<MarineTemplateSelection>(
      context: context,
      builder: (context) => const MarineTemplateDialog(),
    );
    if (selection == null || !mounted) return;
    final template = marineTemplateChannels(selection);
    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: context.l10n.uiMarineVhfTemplate(selection.plan.label),
            count: template.length,
          )
        : const _ChannelApplyMode(replaceAll: true, startAt: 1);
    if (mode == null || !mounted) return;
    _recordHistory();
    _applyChannels(template, mode, libraryName: selection.plan.libraryName);
  }

  Future<void> _restoreStockChannels() async {
    final source = _bridge.chirpSource;
    final stockFile = File(
      '$source/chirp/stock_configs/US FRS and GMRS Channels.csv',
    );
    if (!await stockFile.exists()) {
      if (mounted) {
        await _showActionError(
          const FileSystemException(
            'The CHIRP stock channels file was not found.',
          ),
        );
      }
      return;
    }
    late final List<RadioChannel> channels;
    try {
      channels = ChirpCsv.decodeBytes(await stockFile.readAsBytes());
    } catch (error) {
      if (mounted) await _showActionError(error);
      return;
    }
    if (channels.isEmpty) {
      if (mounted) {
        await _showActionError(
          const FormatException('No stock channels were found.'),
        );
      }
      return;
    }
    if (!mounted) return;

    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: context.l10n.uiStockChannels,
            count: channels.length,
          )
        : const _ChannelApplyMode(replaceAll: true, startAt: 1);
    if (mode == null || !mounted) return;
    _recordHistory();
    _applyChannels(channels, mode, libraryName: 'Stock Channels');
  }

  void _openRadioConnection() {
    setState(() => _page = 1);
    if (_models.isEmpty) unawaited(_loadModels());
  }

  void _selectPage(int page) {
    if (page == 4) {
      unawaited(_openRadioSettings());
      return;
    }
    setState(() => _page = page);
  }

  Future<void> _openRadioSettings() async {
    setState(() => _page = 4);
    final selectionLoad = _radioSelectionLoad;
    if (selectionLoad != null) await selectionLoad;
    if (_models.isEmpty) await _loadModels();
  }

  Future<void> _loadRadioSettings({bool force = false}) async {
    final model = _model;
    final image = _radioImage;
    if (_settingsLoading || model == null || image == null) return;
    if (!force &&
        _radioSettings != null &&
        _settingsLoadedModel == model &&
        _settingsLoadedImage == image) {
      return;
    }
    setState(() {
      _settingsLoading = true;
      _settingsError = null;
    });
    try {
      final settings = await _bridge.readSettings(
        model: model,
        imagePath: image,
      );
      if (!mounted || _model != model || _radioImage != image) return;
      setState(() {
        _radioSettings = settings;
        _settingsLoadedModel = model;
        _settingsLoadedImage = image;
        _settingsLoadedFromRadio = false;
        _settingsDirty = false;
        _settingsGeneration++;
      });
    } catch (error) {
      if (mounted) {
        setState(() => _settingsError = _friendlyActionError(error));
      }
    } finally {
      if (mounted) setState(() => _settingsLoading = false);
    }
  }

  Future<void> _useSavedRadioSnapshot() async {
    if (_settingsLoading || _busy) return;
    if (_settingsDirty) {
      final discard = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: Text(context.l10n.uiDiscardUnsavedSettingsChanges),
          content: Text(context.l10n.uiUsingTheSavedRadioSnapshotWill),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(context.l10n.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(context.l10n.uiUseSavedSnapshot),
            ),
          ],
        ),
      );
      if (discard != true || !mounted) return;
    }
    await _loadRadioSettings(force: true);
  }

  Future<void> _readRadioSettings() async {
    final model = _model;
    final port = _port;
    if (_settingsLoading || _busy || model == null || port == null) return;
    if (_settingsDirty) {
      final discard = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: Text(context.l10n.uiReplaceUnsavedSettingsChanges),
          content: Text(context.l10n.uiReadingSettingsFromTheRadioWill),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(context.l10n.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(context.l10n.uiReadSettings),
            ),
          ],
        ),
      );
      if (discard != true || !mounted) return;
    }
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: false) ||
        !mounted) {
      return;
    }
    setState(() {
      _settingsLoading = true;
      _settingsError = null;
    });
    try {
      await _transferTask(
        context.l10n.uiReadingRadioSettingsDoNotDisconnect,
        () async {
          final settings = await _bridge.readSettings(
            model: model,
            port: port,
            onProgress: _reportTransferProgress,
          );
          final sourceImage = settings.imagePath;
          final storedImage = sourceImage == null
              ? null
              : await _imageStore.saveForModel(model, sourceImage);
          if (!mounted || _model != model || _port != port) return;
          setState(() {
            _radioSettings = settings;
            _radioFirmware = settings.firmware ?? _radioFirmware;
            _settingsLoadedModel = model;
            if (storedImage != null) {
              _radioImage = storedImage;
              _markChannelLibraryDirty();
            }
            _settingsLoadedImage = _radioImage;
            _settingsLoadedFromRadio = settings.hasSettings;
            _settingsDirty = false;
            _settingsGeneration++;
          });
        },
      );
    } finally {
      if (mounted) setState(() => _settingsLoading = false);
    }
  }

  void _markRadioSettingsChanged(RadioSettingNode node) {
    node.changed = true;
    setState(() => _settingsDirty = true);
  }

  List<Map<String, Object?>> _radioSettingChanges() {
    final changes = <Map<String, Object?>>[];
    void walk(RadioSettingNode node) {
      if (node.isGroup) {
        for (final child in node.children) {
          walk(child);
        }
      } else if (node.changed && node.mutable && node.kind != 'unsupported') {
        changes.add(node.toChangeJson());
      }
    }

    for (final item in _radioSettings?.items ?? const <RadioSettingNode>[]) {
      walk(item);
    }
    return changes;
  }

  Future<void> _writeRadioSettings() async {
    if (await _writeBlockedByDriver() || !mounted) return;
    final model = _model;
    final port = _port;
    final image = _radioImage;
    if (model == null || port == null || image == null) return;
    if (_settingsHaveInvalidValues) return;
    final changes = _radioSettingChanges();
    // With nothing edited, write the same snapshot again so several
    // identical radios can be programmed in a row (email INBOX:931).
    final repeat = changes.isEmpty;
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(
          Icons.warning_amber_rounded,
          color: Color(0xFFC46A15),
          size: 32,
        ),
        title: Text(
          repeat
              ? context.l10n.writeSameSettingsTitle
              : context.l10n.writeSettingsTitle,
        ),
        content: Text(
          repeat
              ? context.l10n.writeSameSettingsBody(model, port)
              : context.l10n.writeSettingsBody(changes.length, model, port),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.writeSettingsButton),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: true) ||
        !mounted) {
      return;
    }
    final succeeded = await _transferTask(
      context.l10n.writingSettingsProgress,
      () async {
        await _bridge.writeSettings(
          model: model,
          port: port,
          imagePath: image,
          changes: changes,
          onProgress: _reportTransferProgress,
        );
      },
    );
    if (!mounted || !succeeded) return;
    setState(() => _settingsDirty = false);
    await _loadRadioSettings(force: true);
  }

  RadioChannel _newChannelAt(int location) {
    final midland = showsMidlandChannelNumbers(_model);
    final gm32 = isBaofengGm32(_model);
    final specializedReceive = midland || gm32;
    return RadioChannel(
      location: location,
      name: 'NEW $location',
      frequency: specializedReceive ? 0 : 146.52,
      duplex: '',
      offset: specializedReceive ? 0 : 0.6,
    );
  }

  int? _endInsertionLocation() {
    final minimum = _capabilities?.memoryStart ?? 1;
    final maximum = _capabilities?.memoryEnd;
    final active = _activeChannels;
    final location = active.isEmpty
        ? minimum
        : active
                  .map((channel) => channel.location)
                  .reduce((left, right) => left > right ? left : right) +
              1;
    if (maximum != null && location > maximum) return null;
    return location;
  }

  Future<_AddChannelPlacement?> _chooseAddChannelPlacement() {
    final selected = _current;
    final endLocation = _endInsertionLocation();
    final canInsertAround =
        selected != null && !showsMidlandChannelNumbers(_model);
    final selectedLabel = selected == null
        ? context.l10n.uiSelectAChannelFirst
        : 'Channel ${channelNumberLabel(_model, selected.location)}';
    final aroundSubtitle = selected == null
        ? selectedLabel
        : showsMidlandChannelNumbers(_model)
        ? context.l10n.uiThisRadioHasFixedChannelLocations4
        : context.l10n.uiAndFollowingChannelsMoveDownOne(selectedLabel);
    return showDialog<_AddChannelPlacement>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.l10n.uiWhereShouldTheNewChannelGo),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              key: const ValueKey('add-channel-at-end'),
              enabled: endLocation != null,
              leading: const Icon(Icons.last_page),
              title: Text(context.l10n.uiAtTheEnd),
              subtitle: Text(
                endLocation == null
                    ? 'No free slot follows the final channel.'
                    : context.l10n.uiUseChannelAfterTheFinalChannel(
                        endLocation,
                      ),
              ),
              onTap: () => Navigator.pop(context, _AddChannelPlacement.end),
            ),
            ListTile(
              key: const ValueKey('add-channel-before-selected'),
              enabled: canInsertAround,
              leading: const Icon(Icons.vertical_align_top),
              title: Text(context.l10n.uiBeforeTheSelectedChannel),
              subtitle: Text(aroundSubtitle),
              onTap: () =>
                  Navigator.pop(context, _AddChannelPlacement.beforeSelected),
            ),
            ListTile(
              key: const ValueKey('add-channel-after-selected'),
              enabled: canInsertAround,
              leading: const Icon(Icons.vertical_align_bottom),
              title: Text(context.l10n.uiAfterTheSelectedChannel),
              subtitle: Text(aroundSubtitle),
              onTap: () =>
                  Navigator.pop(context, _AddChannelPlacement.afterSelected),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(context.l10n.cancel),
          ),
        ],
      ),
    );
  }

  void _insertChannelAt(int location) {
    final minimum = _capabilities?.memoryStart;
    final maximum = _capabilities?.memoryEnd;
    if (maximum != null && location > maximum) {
      _showNoEmptyChannelSlot();
      return;
    }
    if (minimum != null && location < minimum) {
      _showNoEmptyChannelSlot();
      return;
    }
    final occupied = _channels.any(
      (channel) => channel.location == location && !channel.cleared,
    );
    if (occupied &&
        maximum != null &&
        _channels.any((channel) => channel.location >= maximum)) {
      _showNoEmptyChannelSlot();
      return;
    }

    final channel = _newChannelAt(location);
    _recordHistory();
    setState(() {
      final locationChanges = <int, int?>{location: null};
      if (occupied) {
        locationChanges.addAll({
          for (final existing in _channels)
            if (existing.location >= location)
              existing.location: existing.location + 1,
        });
        for (final existing in _channels) {
          if (existing.location >= location) existing.location += 1;
        }
        final shiftedClears = _clearedLocations
            .map((cleared) => cleared >= location ? cleared + 1 : cleared)
            .toSet();
        _clearedLocations
          ..clear()
          ..addAll(shiftedClears);
      } else {
        _channels.removeWhere(
          (existing) => existing.location == location && existing.cleared,
        );
      }
      _clearedLocations.remove(location);
      _remapRadioMappingChannels(locationChanges);
      _channels.add(channel);
      _sortChannelsByLocation();
      _searchController.clear();
      _query = '';
      _selected = _channels.indexOf(channel);
      _dirty = true;
      _markChannelLibraryDirty();
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(context.l10n.uiChannelAdded(location)),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  Future<void> _addChannel() async {
    final placement = await _chooseAddChannelPlacement();
    if (!mounted || placement == null) return;
    if (placement != _AddChannelPlacement.end &&
        showsMidlandChannelNumbers(_model)) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(context.l10n.uiThisRadioHasFixedChannelLocations3),
            behavior: SnackBarBehavior.floating,
          ),
        );
      return;
    }
    final selected = _current;
    final location = switch (placement) {
      _AddChannelPlacement.end => _endInsertionLocation(),
      _AddChannelPlacement.beforeSelected => selected?.location,
      _AddChannelPlacement.afterSelected =>
        selected == null ? null : selected.location + 1,
    };
    if (location == null) {
      _showNoEmptyChannelSlot();
      return;
    }
    _insertChannelAt(location);
  }

  void _duplicateChannel() {
    if (_selected < 0 || _selected >= _channels.length) return;
    _duplicateChannelAt(_selected);
  }

  void _duplicateChannelAt(int index) {
    if (index < 0 || index >= _channels.length) return;
    if (_channels[index].cleared) return;
    final location = _nextChannelLocation();
    if (location == null) {
      _showNoEmptyChannelSlot();
      return;
    }
    _recordHistory();
    final copy = _channels[index].copy()..location = location;
    setState(() {
      _clearedLocations.remove(copy.location);
      _channels.add(copy);
      _sortChannelsByLocation();
      _selected = _channels.indexOf(copy);
      _dirty = true;
      _markChannelLibraryDirty();
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  List<RadioChannel> _channelsAtLocations(Iterable<int> locations) {
    final wanted = locations.toSet();
    return _channels
        .where(
          (channel) => wanted.contains(channel.location) && !channel.cleared,
        )
        .toList()
      ..sort((left, right) => left.location.compareTo(right.location));
  }

  void _copyChannelsAtLocations(Iterable<int> locations) {
    final channels = _channelsAtLocations(locations);
    if (channels.isEmpty) return;
    setState(() {
      _channelClipboard = [for (final channel in channels) channel.copy()];
      _channelClipboardMappings = [
        for (final _ in channels) <_ChannelMappingMembership>[],
      ];
    });
  }

  void _cutChannelsAtLocations(Iterable<int> locations) {
    final channels = _channelsAtLocations(locations);
    if (channels.isEmpty) return;
    final protectedChannels = channels
        .where((channel) => isMidlandRepeaterRow(_model, channel.location))
        .toList();
    final clearableChannels = channels
        .where((channel) => !isMidlandRepeaterRow(_model, channel.location))
        .toList();
    _recordHistory(preserveMultiSelection: true);
    setState(() {
      _channelClipboard = [for (final channel in channels) channel.copy()];
      _channelClipboardMappings = [
        for (final channel in channels) _mappingMembershipsAt(channel.location),
      ];
      for (final channel in protectedChannels) {
        _keepMidlandRepeater(channel);
      }
      if (clearableChannels.isNotEmpty) {
        final clearedLocations = [
          for (final channel in clearableChannels) channel.location,
        ];
        for (final channel in clearableChannels) {
          channel.clear();
        }
        _remapRadioMappingChannels({
          for (final location in clearedLocations) location: null,
        });
        _clearedLocations.addAll(clearedLocations);
      }
      _selected = _channels.indexWhere(
        (channel) => channel.location == channels.first.location,
      );
      _selectionAnchorLocation = channels.first.location;
      _extraSelectedLocations.clear();
      _dirty = true;
      _markChannelLibraryDirty();
    });
    for (final channel in protectedChannels) {
      _noteRepeaterRowKept(channel);
    }
  }

  Future<void> _pasteChannelsAtLocation(int location) async {
    if (_channelClipboard.isEmpty) return;
    final finalLocation = location + _channelClipboard.length - 1;
    final minimum = _capabilities?.memoryStart;
    final maximum = _capabilities?.memoryEnd;
    if ((minimum != null && location < minimum) ||
        (maximum != null && finalLocation > maximum)) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(
              _channelClipboard.length == 1
                  ? context.l10n.uiTheCopiedChannelDoesNotFit
                  : context.l10n.uiTheCopiedChannelsDoNotFit,
            ),
            behavior: SnackBarBehavior.floating,
          ),
        );
      return;
    }

    final byLocation = {
      for (final channel in _channels) channel.location: channel,
    };
    final occupiedTargets = [
      for (var offset = 0; offset < _channelClipboard.length; offset++)
        if (byLocation[location + offset] case final target?
            when !target.cleared)
          target,
    ];
    if (occupiedTargets.isNotEmpty) {
      final confirmed = await _confirmOverwriteChannels(occupiedTargets);
      if (!confirmed || !mounted) return;
    }

    final destinations = [
      for (var offset = 0; offset < _channelClipboard.length; offset++)
        location + offset,
    ];
    final pastedChannels = [
      for (var index = 0; index < _channelClipboard.length; index++)
        _channelClipboard[index].copy()..location = destinations[index],
    ];
    _recordHistory(preserveMultiSelection: true);
    setState(() {
      for (var index = 0; index < pastedChannels.length; index++) {
        final pasted = pastedChannels[index];
        final targetIndex = _channels.indexWhere(
          (channel) => channel.location == pasted.location,
        );
        if (targetIndex >= 0) {
          _channels[targetIndex] = pasted;
        } else {
          _channels.add(pasted);
        }
        _restoreMappingMembershipsAt(
          pasted.location,
          _channelClipboardMappings[index],
        );
      }
      _clearedLocations.removeAll(destinations);
      _sortChannelsByLocation();
      _selected = _channels.indexWhere(
        (channel) => channel.location == location,
      );
      _selectionAnchorLocation = location;
      _extraSelectedLocations
        ..clear()
        ..addAll(destinations.skip(1));
      _dirty = true;
      _markChannelLibraryDirty();
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  Future<bool> _confirmOverwriteChannels(List<RadioChannel> channels) async {
    if (channels.length == 1) return _confirmOverwriteChannel(channels.single);
    final first = channels.first;
    final last = channels.last;
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: Color(0xFFC46A15)),
        title: Text(context.l10n.uiOverwriteChannels(channels.length)),
        content: Text(
          context.l10n.uiTheDestinationRangeThroughContainsChannels(
            channelNumberLabel(_model, first.location),
            channelNumberLabel(_model, last.location),
            channels.length,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.uiOverwriteChannels2),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  Future<bool> _confirmOverwriteChannel(RadioChannel channel) async {
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: Color(0xFFC46A15)),
        title: Text(
          context.l10n.uiOverwriteChannel(
            channelNumberLabel(_model, channel.location),
          ),
        ),
        content: Text(
          channel.name.isEmpty
              ? context.l10n.uiThisChannelContainsDataPastingWill
              : context.l10n.uiContainsDataPastingWillReplaceIt(channel.name),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.uiOverwriteChannel2),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  void _deleteChannelAt(int index) {
    if (index < 0 || index >= _channels.length) return;
    final channel = _channels[index];
    if (isMidlandRepeaterRow(_model, channel.location)) {
      _recordHistory();
      setState(() {
        _keepMidlandRepeater(channel);
        _dirty = true;
        _markChannelLibraryDirty();
      });
      _noteRepeaterRowKept(channel);
      return;
    }
    final location = channel.location;
    final wasCleared = channel.cleared;
    _recordHistory();
    setState(() {
      _channels.removeAt(index);
      _remapRadioMappingChannels({location: null});
      if (wasCleared) {
        _clearedLocations.remove(location);
      } else {
        _clearedLocations.add(location);
      }
      _selected = _channels.isEmpty ? -1 : index.clamp(0, _channels.length - 1);
      _dirty = true;
      _markChannelLibraryDirty();
    });
  }

  void _clearChannelsAtLocations(Iterable<int> locations) {
    final channels = _channelsAtLocations(locations);
    if (channels.isEmpty) return;
    final protectedChannels = channels
        .where((channel) => isMidlandRepeaterRow(_model, channel.location))
        .toList();
    final clearableChannels = channels
        .where((channel) => !isMidlandRepeaterRow(_model, channel.location))
        .toList();
    if (clearableChannels.isEmpty) {
      _recordHistory(preserveMultiSelection: true);
      setState(() {
        for (final channel in protectedChannels) {
          _keepMidlandRepeater(channel);
        }
        _dirty = true;
        _markChannelLibraryDirty();
      });
      for (final channel in protectedChannels) {
        _noteRepeaterRowKept(channel);
      }
      return;
    }

    _recordHistory(preserveMultiSelection: true);
    final firstClearIndex = _channels.indexWhere(
      (channel) => channel.location == clearableChannels.first.location,
    );
    setState(() {
      for (final channel in protectedChannels) {
        _keepMidlandRepeater(channel);
      }
      final clearedLocations = [
        for (final channel in clearableChannels) channel.location,
      ];
      for (final channel in clearableChannels) {
        channel.clear();
      }
      _remapRadioMappingChannels({
        for (final location in clearedLocations) location: null,
      });
      _clearedLocations.addAll(clearedLocations);
      if (_showEmptySlots) {
        _selected = firstClearIndex;
      } else {
        var replacement = -1;
        for (var next = firstClearIndex + 1; next < _channels.length; next++) {
          if (!_channels[next].cleared) {
            replacement = next;
            break;
          }
        }
        if (replacement < 0) {
          for (var previous = firstClearIndex - 1; previous >= 0; previous--) {
            if (!_channels[previous].cleared) {
              replacement = previous;
              break;
            }
          }
        }
        _selected = replacement;
      }
      _extraSelectedLocations.clear();
      _selectionAnchorLocation = _current?.location;
      _dirty = true;
      _markChannelLibraryDirty();
    });
    if (clearableChannels.length > 1) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            content: Text(
              context.l10n.uiClearedChannelsUseCmdCtrlZ(
                clearableChannels.length,
              ),
            ),
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 3),
          ),
        );
    }
    for (final channel in protectedChannels) {
      _noteRepeaterRowKept(channel);
    }
  }

  void _keepMidlandRepeater(RadioChannel channel) {
    channel.restorePlainMidlandRepeater();
    _clearedLocations.remove(channel.location);
  }

  void _noteRepeaterRowKept(RadioChannel channel) {
    final label = channelNumberLabel(_model, channel.location);
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(context.l10n.uiStaysInTheRadioTheName(label)),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 3),
        ),
      );
  }

  Future<void> _downloadRadio({int? liveZone}) async {
    if (_port == null || !_radioModelSelectedForTransfer) return;
    // A live-radio zone switch has already confirmed replacing the list.
    if (liveZone == null && _libraryOpen && _channels.isNotEmpty) {
      final replace = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          icon: const Icon(
            Icons.warning_amber_rounded,
            color: Color(0xFFC46A15),
          ),
          title: Text(context.l10n.readReplaceTitle),
          content: Text(context.l10n.readReplaceBody),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(context.l10n.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(context.l10n.readChannels),
            ),
          ],
        ),
      );
      if (replace != true || !mounted) return;
    }
    _diagnosticLog.record(
      'radio',
      'Radio read started',
      context: {
        'model': _model!,
        'port': _port!,
        'zone': liveZone ?? _selectedZone ?? '',
        'firmware': _radioFirmware ?? '',
      },
    );
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: false) ||
        !mounted) {
      return;
    }
    await _transferTask(context.l10n.readingProgress, () async {
      final result = await _bridge.download(
        model: _model!,
        port: _port!,
        zone: liveZone ?? _selectedZone,
        onProgress: _reportTransferProgress,
      );
      final storedImage = await _imageStore.saveForModel(
        _model!,
        result.imagePath,
      );
      setState(() {
        _channels = [...result.channels]
          ..sort((left, right) => left.location.compareTo(right.location));
        _clearedLocations.clear();
        _selected = _channels.isEmpty ? -1 : 0;
        _radioImage = storedImage;
        _radioFirmware = result.firmware;
        _capabilities = result.capabilities;
        _radioZones = result.zones;
        _radioMappings = result.mappings;
        _selectedZone = result.zone;
        _libraryName = displayRadioModelName(_model!);
        _libraryOpen = true;
        _dirty = false;
        _page = 0;
        _radioSettings = null;
        _settingsDirty = false;
        _settingsLoadedFromRadio = false;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _rememberChannelImageBaseline(fromRadio: true);
      });
      _diagnosticLog.record(
        'radio',
        'Radio read completed',
        context: {
          'model': _model!,
          'port': _port!,
          'channels': result.channels.length,
          'firmware': result.firmware ?? '',
        },
      );
    });
    await _reportUndecodedChannels();
  }

  Future<bool> _confirmRadioInstructions(
    RadioInstructions instructions, {
    required bool writing,
  }) async {
    final readyLabel = writing
        ? context.l10n.radioReadyToReceive
        : context.l10n.radioReady;
    final messages =
        (writing ? instructions.writeMessages : instructions.readMessages)
            .map((message) => message.trim())
            .where((message) => message.isNotEmpty)
            .map((message) => adaptRadioPromptButton(message, readyLabel))
            .toList();
    if (messages.isEmpty) return true;
    final ready = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: Icon(
          instructions.experimental == null
              ? Icons.cable
              : Icons.warning_amber_rounded,
          color: instructions.experimental == null
              ? const Color(0xFF1F7455)
              : const Color(0xFFC46A15),
        ),
        title: Text(
          writing
              ? context.l10n.beforeWriting(displayRadioModelName(_model!))
              : context.l10n.beforeReading(displayRadioModelName(_model!)),
        ),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: SelectableText(messages.join('\n\n')),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(readyLabel),
          ),
        ],
      ),
    );
    return ready == true && mounted;
  }

  Future<RadioInstructions?> _loadRadioInstructions() async {
    setState(() {
      _busy = true;
      _status = context.l10n.uiLoadingRadioInstructions;
    });
    try {
      return await _bridge.instructions(_model!);
    } catch (error) {
      if (mounted) {
        setState(() => _status = context.l10n.uiActionFailed);
        await _showActionError(error);
      }
      return null;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _discardChannelLibraryChanges() async {
    final image = _radioImage;
    if (_busy ||
        image == null ||
        _channelImageMatch != ChannelImageMatch.differs) {
      return;
    }
    final zone = _channelImageBaseline?.zone;
    await _task(context.l10n.uiRestoringChannelsFromTheStoredRadio, () async {
      final imported = await _bridge.readImage(image, zone: zone);
      if (!mounted || _radioImage != image) return;
      _recordHistory();
      setState(() {
        _channels = [...imported.channels]
          ..sort((left, right) => left.location.compareTo(right.location));
        _selected = _channels.isEmpty ? -1 : 0;
        _clearedLocations.clear();
        _radioFirmware = imported.firmware ?? _radioFirmware;
        _capabilities = imported.capabilities;
        _radioZones = imported.zones;
        _radioMappings = imported.mappings;
        _selectedZone = imported.zone;
        _libraryOpen = true;
        _dirty = false;
        _rememberChannelImageBaseline(fromRadio: false);
      });
    });
  }

  /// Explains, before any write work starts, that this radio is read-only.
  /// Returns true when the write must not continue.
  Future<bool> _writeBlockedByDriver() async {
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return true;
    if (!instructions.writeDisabled) return false;
    final model = displayRadioModelName(_model ?? 'this radio');
    _diagnosticLog.record(
      'radio',
      'Write blocked: driver is read-only',
      context: {'model': _model ?? ''},
    );
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.l10n.writeUnavailableTitle(model)),
        content: Text(context.l10n.writeUnavailableBody),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: Text(context.l10n.ok),
          ),
        ],
      ),
    );
    return true;
  }

  Future<void> _uploadRadio() async {
    if (_port == null ||
        !_radioModelSelectedForTransfer ||
        _radioImage == null) {
      return;
    }
    if (await _writeBlockedByDriver() || !mounted) return;
    final mappingSignature = radioMappingsSignature(_radioMappings);
    final mappingsChanged =
        _radioMappings.isNotEmpty &&
        mappingSignature != (_channelImageBaseline?.mappingSignature ?? '');
    _diagnosticLog.record(
      'radio',
      'Radio write started',
      context: {
        'model': _model!,
        'port': _port!,
        'channels': _activeChannels.length,
        'mappingsChanged': mappingsChanged,
        'firmware': _radioFirmware ?? '',
      },
    );
    final invalidChannels = _activeChannels
        .where((channel) => _channelIssues(channel).isNotEmpty)
        .toList();
    var channelsToWrite = _activeChannels;
    final compatibleCount = _activeChannels.length - invalidChannels.length;
    final issues = _activeChannels
        .expand(
          (channel) => _channelIssues(channel).map(
            (issue) =>
                '${channelNumberLabel(_model, channel.location)}: $issue',
          ),
        )
        .toList();
    if (issues.isNotEmpty) {
      final skipIncompatible = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(context.l10n.incompatibleTitle),
          content: SingleChildScrollView(
            child: Text(
              '${context.l10n.incompatibleSummary(invalidChannels.length, _activeChannels.length)}\n\n'
              '${issues.take(8).join('\n')}'
              '${issues.length > 8 ? '\n${context.l10n.incompatibleMore(issues.length - 8)}' : ''}'
              '${compatibleCount > 0 ? '\n\n${context.l10n.incompatibleSkipHint(compatibleCount)}' : ''}',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(context.l10n.reviewChannels),
            ),
            if (compatibleCount > 0)
              FilledButton(
                key: const ValueKey('upload-skip-incompatible'),
                onPressed: () => Navigator.pop(context, true),
                child: Text(context.l10n.skipAndWriteRemaining),
              ),
          ],
        ),
      );
      if (skipIncompatible != true) return;
      if (!mounted) return;
      channelsToWrite = compatibleChannelsForUpload(
        _activeChannels,
        _channelIssues,
      );
    }
    final activeLocations = channelsToWrite
        .map((channel) => channel.location)
        .toSet();
    final uppercasesNames =
        _capabilities?.uppercaseNames == true &&
        channelsToWrite.any(
          (channel) => channel.name != channel.name.toUpperCase(),
        );
    final receiveOnlyNote = receiveOnlyWriteNote(
      channelsToWrite,
      (location) => channelNumberLabel(_model, location),
    );
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(
          Icons.warning_amber_rounded,
          color: Color(0xFFC46A15),
          size: 32,
        ),
        title: Text(
          mappingsChanged
              ? context.l10n.writeChangesTitle
              : context.l10n.writeChannelsTitle,
        ),
        content: Text(
          context.l10n.writeConfirmBody(compatibleCount, _model!, _port!) +
              (mappingsChanged
                  ? '\n\n${context.l10n.writeConfirmMappings}'
                  : '') +
              (invalidChannels.isNotEmpty
                  ? '\n\n${context.l10n.writeConfirmIncompatible(invalidChannels.length)}'
                  : '') +
              (uppercasesNames
                  ? '\n\n${context.l10n.writeConfirmUppercase}'
                  : '') +
              (receiveOnlyNote.isEmpty ? '' : '\n\n$receiveOnlyNote'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.writeToRadio),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: true) ||
        !mounted) {
      return;
    }
    final incompatibleChanges = <Map<String, dynamic>>[
      for (final channel in invalidChannels)
        {
          'location': channel.location,
          'name': channel.name,
          'reason': _channelIssues(channel).join('; '),
          'skipped': true,
        },
    ];
    var changes = <Map<String, dynamic>>[];
    final clearedForUpload = clearedLocationsForUpload(
      channels: _activeChannels,
      existingCleared: _clearedLocations,
      minimum: _capabilities?.memoryStart,
      maximum: _capabilities?.memoryEnd,
    );
    if (!mounted) return;
    await _transferTask(context.l10n.writingProgress, () async {
      final result = await _bridge.upload(
        model: _model!,
        port: _port!,
        imagePath: _radioImage!,
        channels: channelsToWrite,
        cleared: clearedForUpload.toList(),
        mappings: mappingsChanged
            ? _radioMappings
                  .map((model) => model.retainingChannels(activeLocations))
                  .toList()
            : null,
        zone: _selectedZone,
        onProgress: _reportTransferProgress,
      );
      changes = [...incompatibleChanges, ...result.adjustments];
      final nameChanges = changes.where((entry) {
        final from = entry['nameFrom'];
        final to = entry['nameTo'];
        return from != null && to != null && '$from' != '$to';
      }).toList();
      if (nameChanges.isNotEmpty) _recordHistory();
      setState(() {
        for (final entry in nameChanges) {
          final location = (entry['location'] as num?)?.toInt();
          final name = entry['nameTo']?.toString();
          if (location == null || name == null) continue;
          final index = _channels.indexWhere(
            (channel) => channel.location == location,
          );
          if (index >= 0) _channels[index].name = name;
        }
        _radioMappings = result.mappings;
        _dirty = false;
        _rememberChannelImageBaseline(fromRadio: false);
      });
      _diagnosticLog.record(
        'radio',
        'Radio write completed',
        context: {
          'model': _model!,
          'port': _port!,
          'adjustments': changes.length,
          'firmware': _radioFirmware ?? '',
        },
      );
    });
    if (changes.isNotEmpty && mounted) {
      final skippedCount = changes
          .where((entry) => entry['skipped'] == true)
          .length;
      final adjustedCount = changes.length - skippedCount;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(
            skippedCount > 0
                ? context.l10n.uiSomeChannelsWereNotWritten
                : context.l10n.uiSomeChannelValuesWereAdjusted,
          ),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  skippedCount > 0 && adjustedCount > 0
                      ? context.l10n.uiTheWriteFinishedChannelsWereAdjusted(
                          adjustedCount,
                          skippedCount,
                        )
                      : skippedCount > 0
                      ? context.l10n.uiTheCompatibleChannelsWereWrittenBut(
                          skippedCount,
                        )
                      : context.l10n.uiTheWriteFinishedButNewchirpAdjusted,
                ),
                const SizedBox(height: 12),
                for (final entry in changes.take(20))
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(() {
                      final location = entry['location'];
                      final name = entry['name'];
                      final reason = entry['reason'];
                      if (reason != null) {
                        if (entry['skipped'] == true) {
                          return context.l10n.uiChannelCouldNotBeWritten(
                            location,
                            name,
                            reason,
                          );
                        }
                        return 'Channel $location $name: $reason.';
                      }
                      final notes = <String>[];
                      final nameFrom = entry['nameFrom'];
                      final nameTo = entry['nameTo'];
                      if (nameFrom != null &&
                          nameTo != null &&
                          '$nameFrom' != '$nameTo') {
                        notes.add(
                          context.l10n.uiNameChangedFromTo(nameFrom, nameTo),
                        );
                      }
                      final fields = (entry['fields'] as List? ?? const [])
                          .join(', ');
                      if (fields.isNotEmpty) {
                        notes.add(
                          context.l10n.uiLockedFieldSEverythingElseWas(fields),
                        );
                      }
                      return 'Channel $location $name: ${notes.join('; ')}.';
                    }()),
                  ),
                if (changes.length > 20)
                  Text(
                    context.l10n.uiAndMoreChannels(changes.length - 20),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                Text(context.l10n.uiNamesAreConvertedOnlyWhenThe),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(context.l10n.close),
            ),
          ],
        ),
      );
    }
  }

  Future<bool> _transferTask(
    String label,
    Future<void> Function() action,
  ) async {
    setState(() {
      _busy = true;
      _transferActive = true;
      _transferCancelling = false;
      _transferLabel = label;
      _transferWriting = label.startsWith('Writing');
      _transferFraction = null;
      _transferDetail = '';
      _status = label;
    });
    _startTransferHeartbeat(label);
    Object? failure;
    var succeeded = false;
    try {
      await action();
      succeeded = true;
      if (mounted) setState(() => _status = 'Ready');
    } catch (error) {
      if (!_transferCancelling) failure = error;
      if (mounted) {
        setState(
          () => _status = _transferCancelling
              ? 'Cancelled'
              : context.l10n.uiActionFailed,
        );
      }
    } finally {
      _stopTransferHeartbeat();
      if (mounted) {
        setState(() {
          _busy = false;
          _transferActive = false;
          _transferCancelling = false;
        });
      }
    }
    if (failure != null && mounted) await _showActionError(failure);
    return succeeded;
  }

  void _reportTransferProgress(RadioProgress progress) {
    if (!mounted) return;
    setState(() {
      _transferDetail = progress.label;
      if (progress.fraction != null) {
        _transferFraction = progress.fraction;
      }
    });
  }

  Future<void> _cancelTransfer() async {
    if (!_transferActive || _transferCancelling) return;
    if (_transferWriting) {
      // 2026-11-21 DM-32UV report: two writes that were still working were
      // cancelled; stopping mid-write can leave a flash page half-written.
      final stop = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          icon: const Icon(
            Icons.warning_amber_rounded,
            color: Color(0xFFC46A15),
          ),
          title: Text(context.l10n.uiStopWritingTheRadio),
          content: Text(context.l10n.uiTheRadioIsBeingWrittenNow),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(context.l10n.uiStopAnyway),
            ),
            FilledButton(
              autofocus: true,
              onPressed: () => Navigator.pop(context, false),
              child: Text(context.l10n.uiKeepWriting),
            ),
          ],
        ),
      );
      if (stop != true || !mounted) return;
      if (!_transferActive || _transferCancelling) return;
    }
    setState(() {
      _transferCancelling = true;
      _transferLabel = context.l10n.uiCancellingSafely;
    });
    _bridge.cancelActive();
  }

  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: const {
        SingleActivator(LogicalKeyboardKey.keyA, meta: true):
            _SelectAllChannelsIntent(),
        SingleActivator(LogicalKeyboardKey.keyA, control: true):
            _SelectAllChannelsIntent(),
      },
      child: Actions(
        actions: {
          _SelectAllChannelsIntent: _SelectAllChannelsAction(
            enabled: () => _canSelectAllChannels,
            onInvoke: _selectAllChannels,
          ),
        },
        child: CallbackShortcuts(
          bindings: {
            const SingleActivator(LogicalKeyboardKey.keyZ, meta: true): _undo,
            const SingleActivator(
              LogicalKeyboardKey.keyZ,
              meta: true,
              shift: true,
            ): _redo,
            const SingleActivator(LogicalKeyboardKey.keyY, meta: true): _redo,
            const SingleActivator(LogicalKeyboardKey.keyZ, control: true):
                _undo,
            const SingleActivator(
              LogicalKeyboardKey.keyZ,
              control: true,
              shift: true,
            ): _redo,
            const SingleActivator(LogicalKeyboardKey.keyY, control: true):
                _redo,
          },
          child: Focus(
            autofocus: true,
            child: Scaffold(
              body: Stack(
                children: [
                  SafeArea(
                    child: Row(
                      children: [
                        _Sidebar(
                          page: _page,
                          onPage: _selectPage,
                          onFindRepeaters: _findRepeaters,
                        ),
                        Expanded(
                          child: Column(
                            children: [
                              _TopBar(
                                libraryName: _libraryName,
                                dirty: _dirty,
                                busy: _busy,
                                status: _status,
                                chirpModuleName: _chirpModuleName,
                                moduleLoadingAvailable: canLoadChirpModules(
                                  currentSandboxPlatform(),
                                ),
                                checkingForUpdates: _checkingForUpdates,
                                onCheckForUpdates: () => _checkForUpdates(),
                                onReportProblem: () => _showErrorReport(
                                  summary: 'General problem report',
                                ),
                                onLoadChirpModule: _loadChirpModule,
                                onUnloadChirpModule: _unloadChirpModule,
                                onNew: _newLibrary,
                                onGmrsStarter: _useGmrsStarter,
                                onMarineTemplate: _useMarineTemplate,
                                onRestoreStock: _restoreStockChannels,
                                onOpen: _openLibraryFile,
                                onSave: () => _saveCsv(),
                                onSaveAs: () => _saveCsv(saveAs: true),
                                onPrintChannels: () =>
                                    unawaited(_printChannelList()),
                                canSave: _libraryOpen,
                                minimalMode:
                                    _page == 2 || _page == 3 || _page == 4,
                                minimalTitle: switch (_page) {
                                  2 => context.l10n.navAbout,
                                  3 => context.l10n.freqRefTitle,
                                  _ => context.l10n.navRadioSettings,
                                },
                                minimalSubtitle: switch (_page) {
                                  2 => context.l10n.aboutSubtitle,
                                  3 =>
                                    _frequencyReferenceIndex < 0
                                        ? context.l10n.freqRefUsSubtitle
                                        : internationalFrequencyReferencePlans[_frequencyReferenceIndex]
                                              .subtitle,
                                  _ => context.l10n.settingsSubtitle,
                                },
                                showPrint: _page == 3,
                                onPrint: _printFrequencyReference,
                              ),
                              Expanded(
                                child: switch (_page) {
                                  0 =>
                                    _libraryOpen
                                        ? _buildLibrary()
                                        : _buildWelcome(),
                                  1 => _buildRadio(),
                                  2 => _buildAbout(),
                                  4 => _buildRadioSettings(),
                                  _ => _buildFrequencyReference(),
                                },
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (_transferActive)
                    _TransferOverlay(
                      label: _transferLabel,
                      detail: _transferDetail,
                      fraction: _transferFraction,
                      cancelling: _transferCancelling,
                      onCancel: _cancelTransfer,
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildWelcome() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 900),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                context.l10n.welcomeTitle,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                context.l10n.welcomeSubtitle,
                style: Theme.of(
                  context,
                ).textTheme.bodyLarge?.copyWith(color: Colors.black54),
              ),
              const SizedBox(height: 24),
              LayoutBuilder(
                builder: (context, constraints) {
                  const gap = 14.0;
                  final cardWidth = constraints.maxWidth >= 620
                      ? (constraints.maxWidth - gap) / 2
                      : constraints.maxWidth;
                  return Wrap(
                    spacing: gap,
                    runSpacing: gap,
                    children: [
                      _WelcomeAction(
                        width: cardWidth,
                        icon: Icons.folder_open_outlined,
                        title: context.l10n.welcomeLoadTitle,
                        description: context.l10n.welcomeLoadBody,
                        buttonLabel: context.l10n.openChannelFile,
                        onPressed: _openLibraryFile,
                        help: context.l10n.welcomeLoadHelp,
                      ),
                      _WelcomeAction(
                        width: cardWidth,
                        icon: Icons.settings_input_antenna,
                        title: context.l10n.welcomeReadTitle,
                        description: context.l10n.welcomeReadBody,
                        buttonLabel: context.l10n.welcomeConnect,
                        onPressed: _openRadioConnection,
                        help: context.l10n.welcomeReadHelp,
                      ),
                      _WelcomeAction(
                        width: cardWidth,
                        icon: Icons.travel_explore,
                        title: context.l10n.welcomeRepeatersTitle,
                        description: context.l10n.welcomeRepeatersBody,
                        buttonLabel: context.l10n.navFindRepeaters,
                        onPressed: _findRepeaters,
                        help: context.l10n.welcomeRepeatersHelp,
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 22),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.lightbulb_outline,
                        color: Color(0xFF1F7455),
                      ),
                      const SizedBox(width: 12),
                      Expanded(child: Text(context.l10n.welcomeTip)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _checkForUpdates({bool startup = false}) async {
    if (_checkingForUpdates) return;
    setState(() => _checkingForUpdates = true);
    try {
      final result = await _updateChecker.check(_newChirpVersion);
      if (!mounted) return;
      if (result.updateAvailable) {
        await _showUpdateAvailable(result);
      } else if (!startup) {
        await _showUpToDate(result);
      }
    } on UpdateCheckException catch (error) {
      if (!mounted || startup) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(context.l10n.updateCheckFailed),
          content: Text(
            '${error.message}\n\n${context.l10n.updateCheckFailedHint}',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(context.l10n.close),
            ),
          ],
        ),
      );
    } finally {
      if (mounted) setState(() => _checkingForUpdates = false);
    }
  }

  Future<void> _showUpdateAvailable(UpdateCheckResult result) {
    final installerUrl = trustedUpdateArtifactUrl(result.downloadUrl);
    final downloadPageUrl = trustedDownloadUrl(result.releaseUrl);
    return showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          installerUrl == null
              ? context.l10n.uiUpdateAvailable
              : context.l10n.uiNewchirpIsReady(result.latestVersion),
        ),
        content: Text(
          installerUrl == null
              ? context.l10n.uiNewchirpIsAvailableYouAreRunning(
                  result.latestVersion,
                  result.currentVersion,
                )
              : context.l10n.uiYouAreRunningNewchirpCanDownload(
                  result.currentVersion,
                  result.latestVersion,
                ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.uiLater),
          ),
          if (installerUrl == null)
            FilledButton.icon(
              onPressed: () {
                Navigator.pop(dialogContext);
                unawaited(_openDownloadPage(downloadPageUrl));
              },
              icon: const Icon(Icons.open_in_new),
              label: Text(context.l10n.uiOpenDownloadPage),
            )
          else
            FilledButton.icon(
              onPressed: () {
                Navigator.pop(dialogContext);
                unawaited(_downloadAndInstallUpdate(result));
              },
              icon: const Icon(Icons.system_update_alt),
              label: Text(context.l10n.uiDownloadAndInstall),
            ),
        ],
      ),
    );
  }

  Future<void> _downloadAndInstallUpdate(UpdateCheckResult result) async {
    final l10n = context.l10n;
    if (_busy || _transferActive || _savingLibrary) {
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(l10n.uiFinishTheCurrentOperationFirst),
          content: Text(l10n.uiWaitForTheCurrentRadioOr),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(l10n.close),
            ),
          ],
        ),
      );
      return;
    }

    if (_settingsDirty) {
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(l10n.uiSaveRadioSettingsFirst),
          content: Text(l10n.uiYouHaveRadioSettingChangesThat),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(l10n.close),
            ),
          ],
        ),
      );
      return;
    }

    if (_dirty) {
      final save = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(l10n.uiSaveYourChannelChangesFirst),
          content: Text(l10n.uiNewchirpWillCloseToInstallThe),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(l10n.uiLater),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(l10n.uiSaveAndContinue),
            ),
          ],
        ),
      );
      if (save != true || !mounted) return;
      await _saveCsv();
      if (!mounted || _dirty) return;
    }

    final status = ValueNotifier<String>(l10n.uiPreparingTheUpdateDownload);
    final progress = ValueNotifier<UpdateDownloadProgress>(
      const UpdateDownloadProgress(receivedBytes: 0),
    );
    NavigatorState? progressNavigator;
    final progressDialog = showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        progressNavigator = Navigator.of(dialogContext);
        return AlertDialog(
          title: Text(l10n.uiInstallingNewchirpUpdate),
          content: SizedBox(
            width: 430,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ValueListenableBuilder<String>(
                  valueListenable: status,
                  builder: (context, value, _) => Text(value),
                ),
                const SizedBox(height: 16),
                ValueListenableBuilder<UpdateDownloadProgress>(
                  valueListenable: progress,
                  builder: (context, value, _) => LinearProgressIndicator(
                    value: value.fraction,
                    minHeight: 8,
                  ),
                ),
                const SizedBox(height: 10),
                ValueListenableBuilder<UpdateDownloadProgress>(
                  valueListenable: progress,
                  builder: (context, value, _) => Text(
                    value.totalBytes == null
                        ? _formatBytes(value.receivedBytes)
                        : '${_formatBytes(value.receivedBytes)} of '
                              '${_formatBytes(value.totalBytes!)}',
                    style: const TextStyle(color: Colors.black54),
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  l10n.uiNewchirpWillCloseAndReopenAutomatically,
                  style: TextStyle(color: Colors.black54),
                ),
              ],
            ),
          ),
        );
      },
    );
    await Future<void>.delayed(Duration.zero);

    try {
      final downloaded = await _updateInstaller.download(
        result,
        onProgress: (value) {
          progress.value = value;
          status.value = l10n.uiDownloadingNewchirp(result.latestVersion);
        },
      );
      status.value = l10n.uiVerifiedStartingTheInstallerAndRestarting;
      await _updateInstaller.install(downloaded);
      progressNavigator?.pop();
      await (widget.exitForUpdate ?? _exitForUpdate)();
      await progressDialog;
    } catch (error) {
      progressNavigator?.pop();
      await progressDialog;
      final message = error is UpdateInstallException
          ? error.message
          : l10n.uiNewchirpCouldNotPrepareTheUpdate;
      if (!mounted) return;
      final downloadPageUrl = trustedDownloadUrl(result.releaseUrl);
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text(l10n.uiUpdateCouldNotBeInstalled),
          content: Text(l10n.uiYouCanStillDownloadTheLatest(message)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(l10n.close),
            ),
            FilledButton.icon(
              onPressed: () {
                Navigator.pop(context);
                unawaited(_openDownloadPage(downloadPageUrl));
              },
              icon: const Icon(Icons.open_in_new),
              label: Text(l10n.uiOpenDownloadPage),
            ),
          ],
        ),
      );
    } finally {
      status.dispose();
      progress.dispose();
    }
  }

  Future<void> _exitForUpdate() async {
    exit(0);
  }

  /// Opens [url] in the browser and keeps the link reachable if that fails.
  Future<void> _openDownloadPage(String url) async {
    if (await openExternalUrl(url)) return;
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(context.l10n.uiCouldnTOpenYourBrowser),
        content: Text(context.l10n.uiNewchirpCouldNotStartTheBrowser(url)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: Text(context.l10n.close),
          ),
          FilledButton.icon(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: url));
              if (dialogContext.mounted) Navigator.pop(dialogContext);
            },
            icon: const Icon(Icons.copy),
            label: Text(context.l10n.uiCopyLink),
          ),
        ],
      ),
    );
  }

  /// Tells the user which slots the driver could not decode, logs the
  /// details for the bug report, and offers to send one.
  Future<void> _reportUndecodedChannels() async {
    final undecoded = _bridge.lastUndecodedChannels;
    if (undecoded.isEmpty || !mounted) return;
    for (final channel in undecoded) {
      _diagnosticLog.record(
        'radio',
        'Channel could not be decoded',
        context: {
          'model': _model ?? '',
          'location': channel.location,
          'error': channel.error,
        },
      );
    }
    final locations = undecoded.map((channel) => channel.location).join(', ');
    final technical = undecoded
        .map(
          (channel) =>
              'Channel ${channel.location}: ${channel.error}\n${channel.raw}',
        )
        .join('\n\n');
    final send = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.l10n.uiUndecodedChannelsTitle),
        content: Text(context.l10n.uiUndecodedChannelsBody(locations)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.close),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(context.l10n.uiSendReport),
          ),
        ],
      ),
    );
    if (send == true && mounted) {
      await _showErrorReport(
        summary: context.l10n.uiUndecodedChannelsTitle,
        technical: technical,
      );
    }
  }

  Future<void> _showUpToDate(UpdateCheckResult result) => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(context.l10n.uiYouReUpToDate),
      content: Text(
        context.l10n.uiNewchirpIsTheLatestVersion(result.currentVersion),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(context.l10n.close),
        ),
      ],
    ),
  );

  Widget _buildAbout() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(28),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 880),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const _Logo(),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'NewChirp',
                          style: Theme.of(context).textTheme.headlineMedium
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        Text(
                          context.l10n.aboutTagline(_newChirpVersion),
                          style: const TextStyle(color: Colors.black54),
                        ),
                        const SizedBox(height: 3),
                        _ProgrammerCredit(
                          roleLine:
                              'Rick Lopez · ${context.l10n.sidebarLeadProgrammer}',
                          email: 'rick@newchirp.net',
                        ),
                        const SizedBox(height: 8),
                        _ProgrammerCredit(
                          roleLine:
                              'Randolpho Cafe · ${context.l10n.contributor}',
                          email: '[redacted-email]',
                        ),
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: OutlinedButton.icon(
                            onPressed: _checkingForUpdates
                                ? null
                                : _checkForUpdates,
                            icon: _checkingForUpdates
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(Icons.system_update_alt_outlined),
                            label: Text(
                              _checkingForUpdates
                                  ? context.l10n.checkingUpdates
                                  : context.l10n.checkUpdates,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 28),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        context.l10n.chirpLayerTitle,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(context.l10n.chirpLayerBody1),
                      const SizedBox(height: 12),
                      Text(context.l10n.chirpLayerBody2),
                      const SizedBox(height: 12),
                      // License notice: kept in English, as the authoritative text.
                      const Text(
                        'CHIRP is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.',
                      ),
                      const SizedBox(height: 12),
                      SelectableText(
                        context.l10n.chirpSource(
                          'https://github.com/kk7ds/chirp',
                        ),
                        style: const TextStyle(color: Color(0xFF1F7455)),
                      ),
                      const SizedBox(height: 6),
                      SelectableText(
                        context.l10n.newchirpSource(
                          'https://github.com/ricktek954/newchirp',
                        ),
                        style: const TextStyle(color: Color(0xFF1F7455)),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.balance_outlined,
                        color: Color(0xFF1F7455),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.l10n.licensesTitle,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(context.l10n.licensesBody),
                            const SizedBox(height: 16),
                            OutlinedButton.icon(
                              onPressed: () => showLicensePage(
                                context: context,
                                applicationName: 'NewChirp',
                                applicationVersion: _newChirpVersion,
                                applicationLegalese:
                                    'CHIRP is licensed under GPL-3.0-or-later. NewChirp is not affiliated with or endorsed by the CHIRP project.',
                              ),
                              icon: const Icon(Icons.description_outlined),
                              label: Text(context.l10n.viewLicenses),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                context.l10n.notAffiliated,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.black54, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showChannelEditorAtLocation(int location) async {
    final initialIndex = _channels.indexWhere(
      (channel) => channel.location == location,
    );
    final existing = initialIndex >= 0 ? _channels[initialIndex] : null;
    final draft = existing != null && !existing.cleared
        ? existing.copy()
        : _newChannelAt(location);
    var enterFrequency = false;
    if (showsMidlandChannelNumbers(_model)) {
      draft.prepareMxt295Editor();
    }
    if (isBaofengGm32(_model)) {
      enterFrequency = gm32NeedsFrequencyBox(draft);
      applyGm32Rules(draft);
    }
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          void changed(VoidCallback update) => setDialogState(() => update());

          Future<void> save() async {
            final saved = draft.copy()..cleared = false;
            final occupied = saved.location == location
                ? null
                : _channels
                      .where(
                        (channel) =>
                            channel.location == saved.location &&
                            !channel.cleared,
                      )
                      .firstOrNull;
            final conflictAction = occupied == null
                ? null
                : await _chooseChannelLocationConflictAction(
                    sourceLocation: location,
                    target: occupied,
                  );
            if (occupied != null && conflictAction == null) return;
            if (!dialogContext.mounted) return;
            _saveEditedChannel(
              saved,
              originalLocation: location,
              conflictAction: conflictAction,
            );
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (mounted) {
                _channelTableKey.currentState?.revealSelectedChannel();
              }
            });
            Navigator.pop(dialogContext);
          }

          return Dialog(
            child: SizedBox(
              width: 760,
              height: MediaQuery.sizeOf(context).height * 0.82,
              child: _ChannelEditor(
                channel: draft,
                radioModel: _model,
                capabilities: _capabilities,
                canDelete: existing != null,
                enteringFrequency: enterFrequency,
                onEnteringFrequency: (value) => enterFrequency = value,
                onChanged: changed,
                onSave: save,
                onClose: () => Navigator.pop(dialogContext),
                onDelete: () async {
                  final currentIndex = _channels.indexWhere(
                    (channel) => channel.location == location,
                  );
                  if (currentIndex < 0) {
                    Navigator.pop(dialogContext);
                    return;
                  }
                  final confirmed = await _confirmDeleteChannel(
                    _channels[currentIndex],
                  );
                  if (confirmed && dialogContext.mounted) {
                    _deleteChannelAt(currentIndex);
                    Navigator.pop(dialogContext);
                  }
                },
              ),
            ),
          );
        },
      ),
    );
  }

  Future<_ChannelLocationConflictAction?> _chooseChannelLocationConflictAction({
    required int sourceLocation,
    required RadioChannel target,
  }) {
    final source = _channels
        .where(
          (channel) => channel.location == sourceLocation && !channel.cleared,
        )
        .firstOrNull;
    return showDialog<_ChannelLocationConflictAction>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.swap_horiz),
        title: Text(context.l10n.uiChannelIsOccupied(target.location)),
        content: Text(
          context.l10n.occupiedBody(
            target.name.isEmpty ? context.l10n.anExistingChannel : target.name,
            target.location,
            source?.name.isNotEmpty == true
                ? source!.name
                : context.l10n.thisChannel,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(context.l10n.cancel),
          ),
          TextButton(
            onPressed: () =>
                Navigator.pop(context, _ChannelLocationConflictAction.replace),
            child: Text(context.l10n.uiReplace),
          ),
          if (source != null)
            TextButton(
              onPressed: () =>
                  Navigator.pop(context, _ChannelLocationConflictAction.swap),
              child: Text(context.l10n.uiSwap),
            ),
          FilledButton(
            onPressed: () =>
                Navigator.pop(context, _ChannelLocationConflictAction.move),
            child: Text(context.l10n.uiMoveAndShift),
          ),
        ],
      ),
    );
  }

  void _saveEditedChannel(
    RadioChannel saved, {
    required int originalLocation,
    _ChannelLocationConflictAction? conflictAction,
  }) {
    _recordHistory();
    setState(() {
      final sourceIndex = _channels.indexWhere(
        (channel) => channel.location == originalLocation && !channel.cleared,
      );
      final source = sourceIndex < 0 ? null : _channels[sourceIndex];
      final targetIndex = _channels.indexWhere(
        (channel) =>
            channel.location == saved.location &&
            !channel.cleared &&
            !identical(channel, source),
      );
      final oldClears = Set<int>.of(_clearedLocations);
      final locationChanges = <int, int?>{};

      if (saved.location == originalLocation || targetIndex < 0) {
        if (saved.location != originalLocation) {
          locationChanges[originalLocation] = saved.location;
        }
        if (sourceIndex >= 0) {
          _channels[sourceIndex] = saved;
        } else {
          _channels.add(saved);
        }
      } else {
        switch (conflictAction) {
          case _ChannelLocationConflictAction.move:
            if (saved.location > originalLocation) {
              for (
                var location = originalLocation + 1;
                location <= saved.location;
                location++
              ) {
                locationChanges[location] = location - 1;
              }
            } else {
              for (
                var location = saved.location;
                location < originalLocation;
                location++
              ) {
                locationChanges[location] = location + 1;
              }
            }
            locationChanges[originalLocation] = saved.location;
            for (final channel in _channels) {
              if (identical(channel, source)) continue;
              final next = locationChanges[channel.location];
              if (locationChanges.containsKey(channel.location) &&
                  next != null) {
                channel.location = next;
              }
            }
            if (sourceIndex >= 0) {
              _channels[sourceIndex] = saved;
            } else {
              _channels.add(saved);
            }
          case _ChannelLocationConflictAction.swap:
            if (sourceIndex < 0) return;
            final destination = _channels[targetIndex];
            locationChanges[originalLocation] = saved.location;
            locationChanges[saved.location] = originalLocation;
            _channels[sourceIndex] = saved;
            destination.location = originalLocation;
          case _ChannelLocationConflictAction.replace:
            locationChanges[originalLocation] = saved.location;
            locationChanges[saved.location] = null;
            _channels.removeAt(targetIndex);
            final replacementIndex = targetIndex < sourceIndex
                ? sourceIndex - 1
                : sourceIndex;
            if (replacementIndex >= 0) {
              _channels[replacementIndex] = saved;
            } else {
              _channels.add(saved);
            }
          case null:
            return;
        }
      }

      final remappedClears = <int>{};
      for (final cleared in oldClears) {
        final next = locationChanges.containsKey(cleared)
            ? locationChanges[cleared]
            : cleared;
        if (next != null) remappedClears.add(next);
      }
      if (saved.location != originalLocation) {
        remappedClears.add(originalLocation);
      }
      final activeLocations = _channels
          .where((channel) => !channel.cleared)
          .map((channel) => channel.location)
          .toSet();
      remappedClears.removeAll(activeLocations);
      _clearedLocations
        ..clear()
        ..addAll(remappedClears);
      _remapRadioMappingChannels(locationChanges);
      _sortChannelsByLocation();
      _selected = _channels.indexOf(saved);
      _dirty = true;
      _markChannelLibraryDirty();
    });
  }

  Future<bool> _confirmDeleteChannel(RadioChannel channel) async {
    final kept = isMidlandRepeaterRow(_model, channel.location);
    final label = channelNumberLabel(_model, channel.location);
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: Icon(
          kept ? Icons.restart_alt : Icons.delete_outline,
          color: kept ? null : const Color(0xFF9B3D34),
        ),
        title: Text(
          kept ? 'Reset $label?' : context.l10n.uiDeleteChannel(label),
        ),
        content: Text(
          kept
              ? context.l10n.uiRepeaterRowsThroughStayInThe
              : channel.name.isEmpty
              ? context.l10n.uiThisChannelWillBeRemovedFrom
              : context.l10n.uiWillBeRemovedFromTheCurrent(channel.name),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(context.l10n.cancel),
          ),
          FilledButton(
            style: kept
                ? null
                : FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF9B3D34),
                  ),
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              kept
                  ? context.l10n.tipResetRepeater
                  : context.l10n.tipDeleteChannel,
            ),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  Future<void> _loadLibraryMetricsCollapsed() async {
    final collapsed = await _libraryMetricsStore.isCollapsed();
    if (mounted && collapsed != _libraryMetricsCollapsed) {
      setState(() => _libraryMetricsCollapsed = collapsed);
    }
  }

  void _setLibraryMetricsCollapsed(bool collapsed) {
    setState(() => _libraryMetricsCollapsed = collapsed);
    unawaited(_libraryMetricsStore.setCollapsed(collapsed));
  }

  Widget _buildLibrary() {
    final visible = _channelTableRows();
    final selectedChannelCount = _selectedChannelLocations.length;
    final libraryStats = _channelLibrarySnapshot;
    final invalid = libraryStats.needsAttention;
    final imageMatch = libraryStats.match;
    final storedImageReady =
        _model != null &&
        _radioImage != null &&
        _radioImage == _imageStore.pathForModel(_model!);
    final channelsNeedingAttention = _activeChannels
        .where((channel) => _channelIssues(channel).isNotEmpty)
        .toList();
    final channelIssueDetails = [
      for (final channel in channelsNeedingAttention)
        for (final issue in _channelIssues(channel))
          '${channelNumberLabel(_model, channel.location)}: $issue',
    ];
    final longNameCount = _channelsWithLongNames().length;
    final firstChannelNeedingAttention = channelsNeedingAttention.isEmpty
        ? null
        : channelsNeedingAttention.first;
    return Padding(
      padding: const EdgeInsets.all(22),
      child: Column(
        children: [
          if (_libraryMetricsCollapsed)
            Row(
              key: const Key('library-metrics-collapsed'),
              children: [
                Expanded(
                  child: Text(
                    context.l10n.uiChannelsScanEnabledNeedAttention(
                      libraryStats.activeCount,
                      libraryStats.scanEnabledCount,
                      invalid,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.black54, fontSize: 12),
                  ),
                ),
                IconButton(
                  key: const Key('library-metrics-expand'),
                  tooltip: context.l10n.showSummary,
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.expand_more),
                  onPressed: () => _setLibraryMetricsCollapsed(false),
                ),
              ],
            )
          else
            Row(
              children: [
                _Metric(
                  label: context.l10n.metricChannels,
                  value: '${libraryStats.activeCount}',
                  icon: Icons.radio,
                ),
                const SizedBox(width: 12),
                _Metric(
                  label: context.l10n.metricScan,
                  value: '${libraryStats.scanEnabledCount}',
                  icon: Icons.radar,
                ),
                const SizedBox(width: 12),
                _Metric(
                  label: context.l10n.metricAttention,
                  value: '$invalid',
                  icon: invalid == 0
                      ? Icons.check_circle_outline
                      : Icons.error_outline,
                ),
                IconButton(
                  key: const Key('library-metrics-collapse'),
                  tooltip: context.l10n.hideSummary,
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.expand_less),
                  onPressed: () => _setLibraryMetricsCollapsed(true),
                ),
              ],
            ),
          if (invalid > 0) ...[
            const SizedBox(height: 12),
            DecoratedBox(
              key: const Key('channel-attention-banner'),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF3E7),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFE7C9A5)),
              ),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(14, 10, 8, 10),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: Color(0xFF9B5B18)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            context.l10n.channelsNeedAttention(invalid),
                            style: const TextStyle(
                              color: Color(0xFF8A4C0E),
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          if (channelIssueDetails.isNotEmpty) ...[
                            const SizedBox(height: 3),
                            Text(
                              channelIssueDetails.first,
                              style: const TextStyle(
                                color: Color(0xFF8A4C0E),
                                fontSize: 12,
                              ),
                            ),
                            if (channelIssueDetails.length > 1)
                              Text(
                                context.l10n.moreValidationIssues(
                                  channelIssueDetails.length - 1,
                                ),
                                style: const TextStyle(
                                  color: Color(0xFF8A4C0E),
                                  fontSize: 12,
                                ),
                              ),
                          ],
                        ],
                      ),
                    ),
                    if (longNameCount > 0)
                      TextButton(
                        key: const Key('shorten-long-names'),
                        onPressed: () => unawaited(_shortenLongNames()),
                        child: Text(
                          context.l10n.shortenNamesButton(
                            longNameCount,
                            _capabilities!.nameLength,
                          ),
                        ),
                      ),
                    if (firstChannelNeedingAttention != null)
                      TextButton(
                        key: const Key('review-channel-attention'),
                        onPressed: () => unawaited(
                          _reviewChannelIssues(firstChannelNeedingAttention),
                        ),
                        child: Text(context.l10n.uiReview),
                      ),
                  ],
                ),
              ),
            ),
          ],
          if (_radioImage == null) ...[
            const SizedBox(height: 12),
            DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xFFFFF7EC),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFE7C9A5)),
              ),
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Row(
                  children: [
                    Icon(Icons.shield_outlined, color: Color(0xFF9B5B18)),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(context.l10n.uiNoRadioImageLoadedEditingAnd),
                    ),
                  ],
                ),
              ),
            ),
          ] else ...[
            const SizedBox(height: 12),
            DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xFFEAF4EF),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFB9D8C8)),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 10,
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.verified_user_outlined,
                      color: Color(0xFF1F7455),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        storedImageReady
                            ? context.l10n.uiStoredImageReadyForYouCan(
                                displayRadioModelName(_model!),
                              )
                            : context.l10n.uiARadioImageIsLoadedFrom,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          if (_radioMappings.any((model) => model.mappings.isNotEmpty)) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(
                  Icons.account_tree_outlined,
                  color: Color(0xFF1F7455),
                ),
                const SizedBox(width: 10),
                OutlinedButton.icon(
                  key: const ValueKey('edit-radio-mappings'),
                  onPressed: _busy ? null : _editRadioMappings,
                  icon: const Icon(Icons.edit_outlined),
                  label: Text(context.l10n.editBanksZones),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _radioMappings
                        .map(
                          (model) => '${model.name}: ${model.mappings.length}',
                        )
                        .join('  •  '),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                _HelpButton(
                  title: context.l10n.banksZonesTitle,
                  details: context.l10n.banksZonesHelp,
                ),
              ],
            ),
          ],
          if (_radioZones.isNotEmpty) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(
                  Icons.account_tree_outlined,
                  color: Color(0xFF1F7455),
                ),
                const SizedBox(width: 10),
                SizedBox(
                  width: 300,
                  child: DropdownButtonFormField<int>(
                    key: ValueKey('radio-zone-$_selectedZone-$_radioImage'),
                    initialValue: _selectedZone,
                    decoration: InputDecoration(
                      labelText: context.l10n.radioSection,
                      isDense: true,
                    ),
                    items: _radioZones
                        .map(
                          (zone) => DropdownMenuItem(
                            value: zone.index,
                            child: Text(
                              context.l10n.zoneChannelCount(
                                zone.name,
                                zone.channelCount,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: _busy
                        ? null
                        : (value) {
                            if (value != null) {
                              unawaited(_switchRadioZone(value));
                            }
                          },
                  ),
                ),
                const SizedBox(width: 8),
                _HelpButton(
                  title: context.l10n.radioSectionsTitle,
                  details: context.l10n.radioSectionsHelp,
                ),
              ],
            ),
          ],
          const SizedBox(height: 16),
          Expanded(
            child: Card(
              clipBehavior: Clip.antiAlias,
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(14),
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        // Longer Spanish/French labels need room sooner.
                        final labelScale =
                            Localizations.localeOf(context).languageCode == 'en'
                            ? 1.0
                            : 1.4;
                        final compact = constraints.maxWidth < 780 * labelScale;
                        return Row(
                          children: [
                            Expanded(
                              child: TextField(
                                key: const ValueKey('channel-search-field'),
                                controller: _searchController,
                                onChanged: (value) =>
                                    setState(() => _query = value),
                                decoration: InputDecoration(
                                  prefixIcon: const Icon(Icons.search),
                                  hintText: compact
                                      ? context.l10n.search
                                      : context.l10n.searchHint,
                                  suffixIcon: _searchController.text.isEmpty
                                      ? null
                                      : IconButton(
                                          key: const ValueKey(
                                            'channel-search-clear',
                                          ),
                                          tooltip:
                                              context.l10n.clearChannelSearch,
                                          onPressed: () {
                                            _searchController.clear();
                                            setState(() => _query = '');
                                          },
                                          icon: const Icon(Icons.clear),
                                        ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            if (compact) ...[
                              if (selectedChannelCount > 1)
                                IconButton(
                                  key: const ValueKey('bulk-edit-channels'),
                                  onPressed: _showBulkChannelEditor,
                                  tooltip: context.l10n.bulkEditTip(
                                    selectedChannelCount,
                                  ),
                                  icon: const Icon(Icons.edit_note_outlined),
                                ),
                              if (selectedChannelCount > 1)
                                IconButton(
                                  key: const ValueKey(
                                    'clear-selected-channels',
                                  ),
                                  onPressed: () => _clearChannelsAtLocations(
                                    _selectedChannelLocations,
                                  ),
                                  tooltip: context.l10n.clearSelectedTip(
                                    selectedChannelCount,
                                  ),
                                  color: const Color(0xFF9B3D34),
                                  icon: const Icon(Icons.delete_sweep_outlined),
                                ),
                              IconButton(
                                onPressed: _duplicateChannel,
                                tooltip: context.l10n.duplicateChannel,
                                icon: const Icon(Icons.copy_outlined),
                              ),
                              IconButton.filled(
                                onPressed: _addChannel,
                                tooltip: context.l10n.addChannel,
                                icon: const Icon(Icons.add),
                              ),
                              const SizedBox(width: 4),
                              FilterChip(
                                key: const ValueKey('show-empty-slots-toggle'),
                                selected: _showEmptySlots,
                                onSelected: _setShowEmptySlots,
                                avatar: const Icon(Icons.space_bar, size: 17),
                                label: Text(context.l10n.slots),
                                tooltip: context.l10n.showEmptySlotsTip,
                              ),
                              if (_columnFilters.values.any(
                                (value) => value.trim().isNotEmpty,
                              ))
                                IconButton(
                                  key: const ValueKey(
                                    'clear-channel-column-filters',
                                  ),
                                  tooltip: context.l10n.clearColumnFilters,
                                  onPressed: () =>
                                      setState(_columnFilters.clear),
                                  icon: const Icon(
                                    Icons.filter_alt_off_outlined,
                                  ),
                                ),
                            ] else ...[
                              if (selectedChannelCount > 1) ...[
                                OutlinedButton.icon(
                                  key: const ValueKey('bulk-edit-channels'),
                                  onPressed: _showBulkChannelEditor,
                                  icon: const Icon(Icons.edit_note_outlined),
                                  label: Text(
                                    context.l10n.editSelected(
                                      selectedChannelCount,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                IconButton(
                                  key: const ValueKey(
                                    'clear-selected-channels',
                                  ),
                                  onPressed: () => _clearChannelsAtLocations(
                                    _selectedChannelLocations,
                                  ),
                                  tooltip: context.l10n.clearSelectedTip(
                                    selectedChannelCount,
                                  ),
                                  color: const Color(0xFF9B3D34),
                                  icon: const Icon(Icons.delete_sweep_outlined),
                                ),
                                const SizedBox(width: 8),
                              ],
                              OutlinedButton.icon(
                                onPressed: _duplicateChannel,
                                icon: const Icon(Icons.copy_outlined),
                                label: Text(context.l10n.duplicate),
                              ),
                              const SizedBox(width: 8),
                              FilledButton.icon(
                                onPressed: _addChannel,
                                icon: const Icon(Icons.add),
                                label: Text(context.l10n.addChannel),
                              ),
                              const SizedBox(width: 8),
                              FilterChip(
                                key: const ValueKey('show-empty-slots-toggle'),
                                selected: _showEmptySlots,
                                onSelected: _setShowEmptySlots,
                                avatar: const Icon(Icons.space_bar, size: 17),
                                label: Text(context.l10n.showEmptySlots),
                                tooltip: context.l10n.showEmptySlotsTip,
                              ),
                              if (_columnFilters.values.any(
                                (value) => value.trim().isNotEmpty,
                              )) ...[
                                const SizedBox(width: 8),
                                TextButton.icon(
                                  key: const ValueKey(
                                    'clear-channel-column-filters',
                                  ),
                                  onPressed: () =>
                                      setState(_columnFilters.clear),
                                  icon: const Icon(
                                    Icons.filter_alt_off_outlined,
                                  ),
                                  label: Text(context.l10n.clearFilters),
                                ),
                              ],
                            ],
                            const SizedBox(width: 2),
                            _HelpButton(
                              title: context.l10n.uiChannelEditing,
                              details: context.l10n.uiAddLetsYouPlaceANew,
                            ),
                          ],
                        );
                      },
                    ),
                  ),
                  Expanded(
                    child: visible.isEmpty
                        ? const _EmptyLibrary()
                        : _ChannelTable(
                            key: _channelTableKey,
                            entries: visible,
                            selected: _current?.location ?? -1,
                            selectedLocations: _selectedChannelLocations,
                            radioModel: _model,
                            capabilities: _capabilities,
                            columnOrder: _columnOrder,
                            columnWidths: _columnWidths,
                            onColumnOrderChanged: _setColumnOrder,
                            onColumnWidthChanged: _setColumnWidth,
                            filterValues: _columnFilters,
                            onFilterChanged: (id, value) => setState(() {
                              if (value.trim().isEmpty) {
                                _columnFilters.remove(id);
                              } else {
                                _columnFilters[id] = value;
                              }
                            }),
                            bankLabels: _bankLabelsByLocation(),
                            onSelect: _selectChannelAtLocation,
                            clipboardCount: _channelClipboard.length,
                            onCopy: (location) {
                              final selected = _selectedChannelLocations;
                              _copyChannelsAtLocations(
                                selected.contains(location)
                                    ? selected
                                    : {location},
                              );
                            },
                            onCut: (location) {
                              final selected = _selectedChannelLocations;
                              _cutChannelsAtLocations(
                                selected.contains(location)
                                    ? selected
                                    : {location},
                              );
                            },
                            onPaste: _pasteChannelsAtLocation,
                            onDuplicate: (location) {
                              final index = _channels.indexWhere(
                                (channel) => channel.location == location,
                              );
                              if (index >= 0) _duplicateChannelAt(index);
                            },
                            onClear: (location) {
                              final selected = _selectedChannelLocations;
                              _clearChannelsAtLocations(
                                selected.contains(location)
                                    ? selected
                                    : {location},
                              );
                            },
                            onMove: (fromLocation, toLocation) {
                              final fromIndex = _channels.indexWhere(
                                (channel) => channel.location == fromLocation,
                              );
                              final toIndex = _channels.indexWhere(
                                (channel) => channel.location == toLocation,
                              );
                              if (fromIndex < 0) return;
                              if (toIndex >= 0 && !_channels[toIndex].cleared) {
                                _moveChannel(fromIndex, toIndex);
                              } else {
                                _moveChannelToLocation(fromIndex, toLocation);
                              }
                            },
                            onInsertEmptyBefore: _insertEmptySlotBefore,
                            onRemoveEmpty: _removeEmptySlot,
                            onBulkEdit: _showBulkChannelEditor,
                            reorderEnabled:
                                _query.isEmpty &&
                                !_columnFilters.values.any(
                                  (value) => value.trim().isNotEmpty,
                                ),
                            reorderDisabledMessage:
                                _query.isNotEmpty ||
                                    _columnFilters.values.any(
                                      (value) => value.trim().isNotEmpty,
                                    )
                                ? context.l10n.uiClearSearchAndColumnFiltersTo
                                : context.l10n.uiRearrangeChannels,
                            onOpen: (location) {
                              final index = _channels.indexWhere(
                                (channel) => channel.location == location,
                              );
                              if (index >= 0) {
                                setState(() {
                                  _selected = index;
                                  _extraSelectedLocations.clear();
                                  _selectionAnchorLocation = location;
                                });
                              }
                              unawaited(_showChannelEditorAtLocation(location));
                            },
                          ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          ChannelLibraryImageBar(
            match: imageMatch,
            canDiscard: imageMatch == ChannelImageMatch.differs && !_busy,
            canWrite: channelLibraryWriteReady(
              match: imageMatch,
              busy: _busy,
              invalidCount: invalid,
              hasPort: _port != null,
              hasRadioModel: _radioModelSelectedForTransfer,
              hasRadioImage: _radioImage != null,
            ),
            showConnect: _port == null,
            onDiscard: () => unawaited(_discardChannelLibraryChanges()),
            onWrite: () => unawaited(_uploadRadio()),
            onConnect: _openRadioConnection,
          ),
        ],
      ),
    );
  }

  Future<void> _printFrequencyReference() async {
    final temp = File(
      '${Directory.systemTemp.path}/newchirp-frequency-reference.pdf',
    );
    final asset = _frequencyReferenceIndex < 0
        ? 'assets/GMRS_FRS_Frequency_Chart.pdf'
        : internationalFrequencyReferencePlans[_frequencyReferenceIndex]
              .pdfAsset;
    var prepared = false;
    await _task(context.l10n.uiPreparingFrequencyReference, () async {
      final data = await rootBundle.load(asset);
      await temp.writeAsBytes(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
      );
      prepared = true;
    });

    if (!mounted || !prepared) return;
    await _printPdfFile(
      temp,
      noun: 'reference',
      taskLabel: context.l10n.uiPrintingFrequencyReference,
      sentText: context.l10n.uiTheGmrsFrsReference,
    );
  }

  Future<void> _printChannelList() async {
    final rows = channelListRows(_channels, radioModel: _model);
    final title = _model == null
        ? context.l10n.uiNewchirpChannelList
        : context.l10n.uiNewchirpChannelList2(displayRadioModelName(_model!));
    final today = DateTime.now().toIso8601String().substring(0, 10);
    final subtitle =
        '$_libraryName · ${rows.length} channel${rows.length == 1 ? '' : 's'}'
        ' · printed $today';
    final locale = Platform.localeName.toUpperCase();
    final letter = locale.contains('_US') || locale.contains('_CA');
    final temp = File('${Directory.systemTemp.path}/newchirp-channel-list.pdf');
    var prepared = false;
    await _task(context.l10n.uiPreparingChannelList, () async {
      await temp.writeAsBytes(
        buildChannelListPdf(
          title: title,
          subtitle: subtitle,
          rows: rows,
          letter: letter,
        ),
      );
      prepared = true;
    });
    if (!mounted || !prepared) return;
    await _printPdfFile(
      temp,
      noun: context.l10n.uiChannelList,
      taskLabel: context.l10n.uiPrintingChannelList,
      sentText: context.l10n.uiTheChannelList,
    );
  }

  /// Open [pdf] in the PDF viewer (Windows, or no printers) or send it to a
  /// chosen CUPS printer.
  Future<void> _printPdfFile(
    File pdf, {
    required String noun,
    required String taskLabel,
    required String sentText,
  }) async {
    final temp = pdf;

    Future<void> openInPdfViewer({required bool noPrinters}) async {
      try {
        await openLocalFile(temp.path);
      } catch (error) {
        if (mounted) await _showActionError(error);
        return;
      }
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          icon: const Icon(Icons.print_outlined, color: Color(0xFFC46A15)),
          title: Text(
            noPrinters
                ? context.l10n.uiNoPrintersFound
                : '${noun[0].toUpperCase()}${noun.substring(1)} opened',
          ),
          content: Text(
            noPrinters
                ? context.l10n.uiNewchirpCouldNotFindAnySystem(noun)
                : context.l10n.uiThePdfWasOpenedInYour(noun),
          ),
          actions: [
            FilledButton(
              onPressed: () => Navigator.pop(context),
              child: Text(context.l10n.close),
            ),
          ],
        ),
      );
    }

    if (Platform.isWindows) {
      await openInPdfViewer(noPrinters: false);
      return;
    }

    final printers = await _systemPrinters();
    if (printers.isEmpty) {
      await openInPdfViewer(noPrinters: true);
      return;
    }

    final defaultPrinter = await _defaultPrinterName();
    if (!mounted) return;
    String? selectedPrinter = printers.contains(defaultPrinter)
        ? defaultPrinter
        : printers.first;
    final chosenPrinter = await showDialog<String>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          icon: const Icon(Icons.print_outlined, color: Color(0xFF1F7455)),
          title: Text(context.l10n.uiChooseAPrinter),
          content: SizedBox(
            width: 460,
            height: 320,
            child: RadioGroup<String>(
              groupValue: selectedPrinter,
              onChanged: (value) {
                setDialogState(() => selectedPrinter = value);
              },
              child: ListView(
                children: [
                  for (final printer in printers)
                    RadioListTile<String>(
                      value: printer,
                      title: Text(
                        printer == defaultPrinter
                            ? '$printer (default)'
                            : printer,
                      ),
                    ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: Text(context.l10n.cancel),
            ),
            FilledButton(
              onPressed: selectedPrinter == null
                  ? null
                  : () => Navigator.pop(dialogContext, selectedPrinter),
              child: Text(context.l10n.print),
            ),
          ],
        ),
      ),
    );

    if (chosenPrinter == null || !mounted) return;

    var printSent = false;
    await _task(taskLabel, () async {
      final result = await Process.run('/usr/bin/lp', [
        '-d',
        chosenPrinter,
        temp.path,
      ]);
      if (result.exitCode != 0) {
        throw Exception(
          'Could not send the $noun to $chosenPrinter:\n'
          '${result.stderr.toString().trim()}',
        );
      }
      printSent = true;
    });

    if (mounted && printSent) {
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          icon: const Icon(
            Icons.check_circle_outline,
            color: Color(0xFF1F7455),
          ),
          title: Text(context.l10n.uiPrintJobSent),
          content: Text(context.l10n.uiWasSentTo(sentText, chosenPrinter)),
          actions: [
            FilledButton(
              onPressed: () => Navigator.pop(context),
              child: Text(context.l10n.close),
            ),
          ],
        ),
      );
    }
  }

  Future<List<String>> _systemPrinters() async {
    try {
      final result = await Process.run('/usr/bin/lpstat', ['-p']);
      final lines = result.stdout.toString().split('\n');
      return [
        for (final line in lines)
          if (line.trim().startsWith('printer '))
            RegExp(r'^printer\s+(\S+)').firstMatch(line.trim())!.group(1)!,
      ];
    } catch (_) {
      return [];
    }
  }

  Future<String?> _defaultPrinterName() async {
    try {
      final result = await Process.run('/usr/bin/lpstat', ['-d']);
      final text = result.stdout.toString();
      const prefix = 'system default destination:';
      if (!text.contains(prefix)) return null;
      final name = text.substring(text.indexOf(prefix) + prefix.length).trim();
      return name == 'no system default destination' ? null : name;
    } catch (_) {
      return null;
    }
  }

  Widget _buildFrequencyReference() {
    final plan = _frequencyReferenceIndex < 0
        ? null
        : internationalFrequencyReferencePlans[_frequencyReferenceIndex];
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 8),
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ChoiceChip(
                key: const ValueKey('frequency-plan-us'),
                selected: plan == null,
                onSelected: (_) =>
                    setState(() => _frequencyReferenceIndex = -1),
                avatar: const Icon(Icons.public, size: 17),
                label: Text(context.l10n.uiUsFrsGmrs),
              ),
              for (
                var index = 0;
                index < internationalFrequencyReferencePlans.length;
                index++
              )
                ChoiceChip(
                  key: ValueKey(
                    'frequency-plan-${internationalFrequencyReferencePlans[index].id}',
                  ),
                  selected: _frequencyReferenceIndex == index,
                  onSelected: (_) =>
                      setState(() => _frequencyReferenceIndex = index),
                  label: Text(
                    internationalFrequencyReferencePlans[index].title,
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: plan == null
              ? _buildUsFrequencyReference()
              : _buildInternationalFrequencyReference(plan),
        ),
      ],
    );
  }

  Widget _buildInternationalFrequencyReference(FrequencyReferencePlan plan) {
    const green = Color(0xFF1F7455);
    const ink = Color(0xFF15211D);
    const muted = Color(0xFF56615B);
    const grid = Color(0xFFD8DEDA);

    Widget cell(String text, {bool header = false}) => Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
      child: Text(
        text,
        style: TextStyle(
          color: header ? Colors.white : ink,
          fontSize: 11,
          fontWeight: header ? FontWeight.w700 : FontWeight.w400,
        ),
      ),
    );

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1040),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                plan.title,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: green,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                plan.subtitle,
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: muted),
              ),
              for (final group in plan.groups) ...[
                const SizedBox(height: 18),
                Text(
                  group.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: green,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 4),
                Text(group.note, style: const TextStyle(color: muted)),
                const SizedBox(height: 10),
                Card(
                  clipBehavior: Clip.antiAlias,
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Table(
                      border: TableBorder.all(color: grid, width: 0.6),
                      columnWidths: const {
                        0: FixedColumnWidth(90),
                        1: FixedColumnWidth(140),
                        2: FixedColumnWidth(520),
                      },
                      children: [
                        TableRow(
                          decoration: const BoxDecoration(color: green),
                          children: [
                            cell('Channel', header: true),
                            cell(context.l10n.uiFrequencyMhz, header: true),
                            cell(context.l10n.uiUseNotes, header: true),
                          ],
                        ),
                        for (final row in group.rows)
                          TableRow(
                            children: [
                              cell(row.channel),
                              cell(row.frequency),
                              cell(row.notes),
                            ],
                          ),
                      ],
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 18),
              Text(
                context.l10n.uiReferenceSourceVerifyCurrentNationalRules(
                  plan.source,
                ),
                style: const TextStyle(color: muted, fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUsFrequencyReference() {
    const green = Color(0xFF1F7455);
    const ink = Color(0xFF15211D);
    const muted = Color(0xFF56615B);
    const grid = Color(0xFFD8DEDA);
    const band1 = Color(0xFFEAF3FA);
    const band2 = Color(0xFFFFF4E0);
    const band3 = Color(0xFFEAF4EF);
    const repeater = Color(0xFFF2ECF8);

    final mainRows = <List<String>>[
      [
        '1',
        '462.5625',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '2',
        '462.5875',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '3',
        '462.6125',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '4',
        '462.6375',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '5',
        '462.6625',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '6',
        '462.6875',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '7',
        '462.7125',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        context.l10n.uiSharedMhzInterstitial,
      ],
      [
        '8',
        '467.5625',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '9',
        '467.5875',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '10',
        '467.6125',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '11',
        '467.6375',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '12',
        '467.6625',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '13',
        '467.6875',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '14',
        '467.7125',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        context.l10n.uiHandheldOnly,
      ],
      [
        '15',
        '462.5500',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '16',
        '462.5750',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '17',
        '462.6000',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '18',
        '462.6250',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '19',
        '462.6500',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '20',
        '462.6750',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '21',
        '462.7000',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
      [
        '22',
        '462.7250',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        context.l10n.uiMainRepeaterOutput,
      ],
    ];

    final repeaterRows = <List<String>>[
      ['RPT15', '467.5500', '462.5500'],
      ['RPT16', '467.5750', '462.5750'],
      ['RPT17', '467.6000', '462.6000'],
      ['RPT18', '467.6250', '462.6250'],
      ['RPT19', '467.6500', '462.6500'],
      ['RPT20', '467.6750', '462.6750'],
      ['RPT21', '467.7000', '462.7000'],
      ['RPT22', '467.7250', '462.7250'],
    ];

    Color rowColor(int channel) {
      if (channel <= 7) return band1;
      if (channel <= 14) return band2;
      return band3;
    }

    Widget cell(
      String text, {
      Color color = ink,
      FontWeight weight = FontWeight.w400,
      TextAlign align = TextAlign.left,
    }) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
        child: Text(
          text,
          textAlign: align,
          style: TextStyle(color: color, fontWeight: weight, fontSize: 11),
        ),
      );
    }

    Widget headerCell(String text, {TextAlign align = TextAlign.left}) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        child: Text(
          text,
          textAlign: align,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
            fontSize: 11,
          ),
        ),
      );
    }

    Widget legendItem(Color color, String label) {
      return Padding(
        padding: const EdgeInsets.only(right: 18, bottom: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 13,
              height: 13,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(3),
                border: Border.all(color: grid),
              ),
            ),
            const SizedBox(width: 7),
            Text(label, style: const TextStyle(color: ink, fontSize: 11)),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 980),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                context.l10n.uiGmrsFrsFrequencyReference,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: green,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                context.l10n.uiUnitedStatesPartChannelPlanColor,
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: muted),
              ),
              const SizedBox(height: 14),
              Wrap(
                children: [
                  legendItem(band1, context.l10n.uiChMhzInterstitial),
                  legendItem(band2, context.l10n.uiChMhzInterstitial2),
                  legendItem(band3, context.l10n.uiChMhzMain),
                ],
              ),
              const SizedBox(height: 16),
              Card(
                clipBehavior: Clip.antiAlias,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Table(
                    border: TableBorder.all(color: grid, width: 0.6),
                    columnWidths: const {
                      0: FixedColumnWidth(36),
                      1: FixedColumnWidth(118),
                      2: FixedColumnWidth(72),
                      3: FixedColumnWidth(72),
                      4: FixedColumnWidth(108),
                      5: FixedColumnWidth(82),
                      6: FixedColumnWidth(196),
                    },
                    children: [
                      TableRow(
                        decoration: const BoxDecoration(color: green),
                        children: [
                          headerCell('Ch', align: TextAlign.center),
                          headerCell(
                            context.l10n.uiFrequencyMhz,
                            align: TextAlign.center,
                          ),
                          headerCell(
                            context.l10n.uiFrsPower,
                            align: TextAlign.center,
                          ),
                          headerCell('FRS BW', align: TextAlign.center),
                          headerCell(
                            context.l10n.uiGmrsPower,
                            align: TextAlign.center,
                          ),
                          headerCell('GMRS BW', align: TextAlign.center),
                          headerCell('Notes'),
                        ],
                      ),
                      for (final row in mainRows)
                        TableRow(
                          decoration: BoxDecoration(
                            color: rowColor(int.parse(row.first)),
                          ),
                          children: [
                            cell(row[0], align: TextAlign.center),
                            cell(row[1], align: TextAlign.center),
                            cell(row[2], align: TextAlign.center),
                            cell(row[3], align: TextAlign.center),
                            cell(row[4], align: TextAlign.center),
                            cell(row[5], align: TextAlign.center),
                            cell(row[6]),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text(
                context.l10n.uiRepeaterPairsGmrsOnly,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: green,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Card(
                clipBehavior: Clip.antiAlias,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Table(
                    border: TableBorder.all(color: grid, width: 0.6),
                    columnWidths: const {
                      0: FixedColumnWidth(92),
                      1: FixedColumnWidth(150),
                      2: FixedColumnWidth(150),
                      3: FixedColumnWidth(220),
                    },
                    children: [
                      TableRow(
                        decoration: const BoxDecoration(color: green),
                        children: [
                          headerCell('Repeater'),
                          headerCell(
                            context.l10n.uiInputYouTransmit,
                            align: TextAlign.center,
                          ),
                          headerCell(
                            context.l10n.uiOutputYouListen,
                            align: TextAlign.center,
                          ),
                          headerCell('Notes'),
                        ],
                      ),
                      for (final row in repeaterRows)
                        TableRow(
                          decoration: const BoxDecoration(color: repeater),
                          children: [
                            cell(row[0]),
                            cell(row[1], align: TextAlign.center),
                            cell(row[2], align: TextAlign.center),
                            cell(context.l10n.uiInputOutputMhz),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              DecoratedBox(
                decoration: BoxDecoration(
                  color: Color(0xFFF5F8F5),
                  borderRadius: BorderRadius.all(Radius.circular(10)),
                ),
                child: Padding(
                  padding: EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        context.l10n.uiKeyNotes,
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        context.l10n.uiAllFrequenciesAreInMhzGmrs,
                        style: TextStyle(
                          color: Color(0xFF56615B),
                          height: 1.45,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _settingsMessage({
    required IconData icon,
    required String title,
    required String body,
    Widget? action,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: const Color(0xFF39725C)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 5),
                  Text(body, style: const TextStyle(color: Colors.black54)),
                  if (action != null) ...[const SizedBox(height: 12), action],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRadioSettings() {
    final model = _model;
    final hasImage = model != null && _radioImage != null;
    final canReadRadio = model != null && _port != null;
    final settings = _radioSettings;
    final hasSettings =
        settings != null && settings.hasSettings && settings.items.isNotEmpty;
    final settingsUnsupported = settings != null && !settings.hasSettings;
    return Scrollbar(
      controller: _settingsScrollController,
      thumbVisibility: true,
      child: SingleChildScrollView(
        controller: _settingsScrollController,
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        padding: const EdgeInsets.fromLTRB(22, 22, 22, 40),
        child: Align(
          alignment: Alignment.topCenter,
          child: SizedBox(
            width: 900,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  context.l10n.navRadioSettings,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  context.l10n.settingsIntro,
                  style: Theme.of(
                    context,
                  ).textTheme.bodyLarge?.copyWith(color: Colors.black54),
                ),
                const SizedBox(height: 20),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(
                          children: [
                            const Icon(
                              Icons.settings_input_antenna,
                              color: Color(0xFF39725C),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                model == null
                                    ? context.l10n.settingsNoModel
                                    : '${displayRadioModelName(model)}  |  '
                                          '${_port ?? context.l10n.settingsNoCable}'
                                          '${_settingsLoadedFromRadio
                                              ? '  |  ${context.l10n.settingsReadFromRadio}'
                                              : hasImage
                                              ? '  |  ${context.l10n.settingsSnapshotAvailable}'
                                              : ''}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        RadioSettingsSourceActions(
                          canReadRadio: canReadRadio && !settingsUnsupported,
                          hasSavedSnapshot: hasImage && !settingsUnsupported,
                          enabled: !_settingsLoading && !_busy,
                          onReadRadio: _readRadioSettings,
                          onUseSavedSnapshot: _useSavedRadioSnapshot,
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                if (_settingsLoading)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Row(
                        children: [
                          const SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          const SizedBox(width: 14),
                          Text(context.l10n.settingsLoading),
                        ],
                      ),
                    ),
                  )
                else if (settingsUnsupported)
                  _settingsMessage(
                    icon: Icons.tune,
                    title: context.l10n.settingsUnsupportedTitle,
                    body: context.l10n.settingsUnsupportedBody,
                  )
                else if (_settingsError != null)
                  _settingsMessage(
                    icon: Icons.error_outline,
                    title: context.l10n.settingsLoadError,
                    body: _settingsError!,
                  )
                else if (!hasImage)
                  _settingsMessage(
                    icon: Icons.info_outline,
                    title: context.l10n.settingsReadTitle,
                    body: canReadRadio
                        ? context.l10n.settingsReadBodyConnected
                        : context.l10n.settingsReadBodyDisconnected,
                    action: canReadRadio
                        ? null
                        : FilledButton.icon(
                            onPressed: _openRadioConnection,
                            icon: const Icon(Icons.settings_input_antenna),
                            label: Text(context.l10n.openRadioConnection),
                          ),
                  )
                else if (settings == null)
                  _settingsMessage(
                    icon: Icons.tune,
                    title: context.l10n.settingsNotLoadedTitle,
                    body: canReadRadio
                        ? context.l10n.settingsNotLoadedConnected
                        : context.l10n.settingsNotLoadedSnapshot,
                  )
                else if (!hasSettings)
                  _settingsMessage(
                    icon: Icons.tune,
                    title: context.l10n.settingsUnsupportedTitle,
                    body: context.l10n.settingsUnsupportedBody,
                  )
                else ...[
                  for (final item in settings.items)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 14),
                      child: item.isGroup
                          ? _buildRadioSettingsGroup(item)
                          : Card(
                              child: Padding(
                                padding: const EdgeInsets.all(18),
                                child: _RadioSettingField(
                                  key: ValueKey(
                                    'setting-$_settingsGeneration-'
                                    '${item.id.join('-')}',
                                  ),
                                  node: item,
                                  onChanged: _markRadioSettingsChanged,
                                ),
                              ),
                            ),
                    ),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              _settingsDirty
                                  ? context.l10n.settingsUnsaved
                                  : _settingsLoadedFromRadio
                                  ? context.l10n.settingsMatchRadio
                                  : context.l10n.settingsMatchSnapshot,
                              style: TextStyle(
                                color: _settingsDirty
                                    ? const Color(0xFFC46A15)
                                    : Colors.black54,
                                fontWeight: _settingsDirty
                                    ? FontWeight.w700
                                    : FontWeight.w400,
                              ),
                            ),
                          ),
                          TextButton(
                            onPressed: _settingsDirty
                                ? () => _loadRadioSettings(force: true)
                                : null,
                            child: Text(context.l10n.discardChanges),
                          ),
                          const SizedBox(width: 10),
                          if (_port == null)
                            OutlinedButton.icon(
                              onPressed: _openRadioConnection,
                              icon: const Icon(Icons.cable),
                              label: Text(context.l10n.connectRadioToWrite),
                            )
                          else
                            FilledButton.icon(
                              onPressed:
                                  _radioImage != null &&
                                      !_settingsHaveInvalidValues
                                  ? _writeRadioSettings
                                  : null,
                              icon: const Icon(Icons.save_outlined),
                              label: Text(context.l10n.writeSettingsToRadio),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRadioSettingsGroup(
    RadioSettingNode group, {
    bool nested = false,
  }) {
    final content = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Icon(
              nested ? Icons.subdirectory_arrow_right : Icons.tune,
              size: nested ? 18 : 21,
              color: const Color(0xFF39725C),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                group.label,
                style: TextStyle(
                  fontSize: nested ? 14 : 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
        if (group.documentation != null) ...[
          const SizedBox(height: 5),
          Text(
            group.documentation!,
            style: const TextStyle(color: Colors.black54, fontSize: 12),
          ),
        ],
        if (group.children.isEmpty)
          Padding(
            padding: EdgeInsets.only(top: 10),
            child: Text(
              context.l10n.uiNoEditableOptionsInThisGroup,
              style: TextStyle(color: Colors.black45),
            ),
          )
        else
          for (final child in group.children)
            if (child.isGroup)
              Padding(
                padding: const EdgeInsets.only(top: 14, left: 10),
                child: _buildRadioSettingsGroup(child, nested: true),
              )
            else
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: _RadioSettingField(
                  key: ValueKey(
                    'setting-$_settingsGeneration-${child.id.join('-')}',
                  ),
                  node: child,
                  onChanged: _markRadioSettingsChanged,
                ),
              ),
      ],
    );
    if (nested) {
      return DecoratedBox(
        decoration: BoxDecoration(
          color: const Color(0xFFF5F8F5),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Padding(padding: const EdgeInsets.all(14), child: content),
      );
    }
    return Card(
      child: Padding(padding: const EdgeInsets.all(18), child: content),
    );
  }

  Widget _buildRadio() {
    final storedImageReady =
        _model != null &&
        _radioImage != null &&
        _radioImage == _imageStore.pathForModel(_model!);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(22),
      child: Align(
        alignment: Alignment.topCenter,
        child: SizedBox(
          width: 820,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                context.l10n.navRadioConnection,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                context.l10n.connIntro,
                style: Theme.of(
                  context,
                ).textTheme.bodyLarge?.copyWith(color: Colors.black54),
              ),
              const SizedBox(height: 20),
              if (_chirpModuleName != null) ...[
                Container(
                  padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF4E5),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFE9BE84)),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.extension_outlined,
                        color: Color(0xFF9B5B18),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          context.l10n.moduleLoaded(_chirpModuleName!),
                          style: const TextStyle(
                            color: Color(0xFF73420F),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: _busy ? null : _unloadChirpModule,
                        child: Text(context.l10n.unload),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
              ],
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _StepTitle(
                        number: '1',
                        title: context.l10n.step1Title,
                        help: context.l10n.step1Help,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              key: ValueKey(
                                'radio-interface-${_port ?? 'none'}-'
                                '${_ports.map((port) => port.port).join('|')}',
                              ),
                              initialValue:
                                  _ports.any((port) => port.port == _port)
                                  ? _port
                                  : null,
                              isExpanded: true,
                              decoration: InputDecoration(
                                labelText: context.l10n.programmingInterface,
                                prefixIcon: const Icon(Icons.cable),
                              ),
                              items: _ports
                                  .map(
                                    (p) => DropdownMenuItem(
                                      value: p.port,
                                      child: Text(
                                        p.label,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ),
                                  )
                                  .toList(),
                              onChanged: (value) {
                                setState(() => _port = value);
                                unawaited(_saveRadioSelection());
                              },
                            ),
                          ),
                          const SizedBox(width: 10),
                          IconButton.filledTonal(
                            onPressed: _refreshPorts,
                            tooltip: context.l10n.refreshInterfaces,
                            icon: const Icon(Icons.refresh),
                          ),
                          const SizedBox(width: 2),
                          _HelpButton(
                            title: context.l10n.refreshInterfaces,
                            details: context.l10n.refreshHelp,
                          ),
                        ],
                      ),
                      if (_ports.isEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text(
                            context.l10n.noInterface,
                            style: const TextStyle(color: Color(0xFF9B5B18)),
                          ),
                        ),
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 22),
                        child: Divider(),
                      ),
                      _StepTitle(
                        number: '2',
                        title: context.l10n.step2Title,
                        help: context.l10n.step2Help,
                      ),
                      const SizedBox(height: 12),
                      if (_models.isEmpty)
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton.icon(
                                onPressed: _busy ? null : _loadModels,
                                icon: const Icon(
                                  Icons.download_for_offline_outlined,
                                ),
                                label: Text(context.l10n.loadCatalog),
                              ),
                            ),
                            const SizedBox(width: 2),
                            _HelpButton(
                              title: context.l10n.loadCatalog,
                              details: context.l10n.loadCatalogHelp,
                            ),
                          ],
                        )
                      else
                        RadioModelPicker(
                          models: _models,
                          vendorModels: _modelGroups,
                          selectedModel: _models.contains(_model)
                              ? _model
                              : null,
                          enabled: !_busy,
                          onSelected: _selectRadioModel,
                        ),
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 22),
                        child: Divider(),
                      ),
                      _StepTitle(
                        number: '3',
                        title: context.l10n.step3Title,
                        help: context.l10n.step3Help,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton.icon(
                              onPressed:
                                  _busy ||
                                      _port == null ||
                                      !_radioModelSelectedForTransfer
                                  ? null
                                  : _downloadRadio,
                              icon: const Icon(Icons.south),
                              label: Padding(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 12,
                                ),
                                child: Text(context.l10n.readChannelsFromRadio),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed:
                                  _busy ||
                                      _port == null ||
                                      !_radioModelSelectedForTransfer ||
                                      _radioImage == null
                                  ? null
                                  : _uploadRadio,
                              icon: const Icon(Icons.north),
                              label: Padding(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 12,
                                ),
                                child: Text(context.l10n.writeToRadio),
                              ),
                            ),
                          ),
                          const SizedBox(width: 2),
                          _HelpButton(
                            title: context.l10n.step3Title,
                            details: context.l10n.step3Help,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      DecoratedBox(
                        decoration: BoxDecoration(
                          color: const Color(0xFFF5F8F5),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              Icon(
                                _radioImage == null
                                    ? Icons.shield_outlined
                                    : Icons.verified_user_outlined,
                                color: const Color(0xFF39725C),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  _radioImage == null
                                      ? context.l10n.imageNone
                                      : storedImageReady
                                      ? context.l10n.imageStored(
                                          displayRadioModelName(_model!),
                                        )
                                      : context.l10n.imageSession,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Sidebar extends StatelessWidget {
  const _Sidebar({
    required this.page,
    required this.onPage,
    required this.onFindRepeaters,
  });
  final int page;
  final ValueChanged<int> onPage;
  final VoidCallback onFindRepeaters;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('left-menu-rail'),
      width: 216,
      color: const Color(0xFF172C24),
      padding: const EdgeInsets.fromLTRB(14, 22, 14, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 10),
            child: Row(
              children: [
                _Logo(),
                SizedBox(width: 11),
                Expanded(
                  child: Text(
                    'NewChirp',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          _NavItem(
            label: context.l10n.navRadioConnection,
            icon: Icons.settings_input_antenna,
            selected: page == 1,
            onTap: () => onPage(1),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: context.l10n.navChannelLibrary,
            icon: Icons.table_rows_outlined,
            selected: page == 0,
            onTap: () => onPage(0),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: context.l10n.navRadioSettings,
            icon: Icons.tune,
            selected: page == 4,
            onTap: () => onPage(4),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: context.l10n.navFindRepeaters,
            icon: Icons.travel_explore,
            selected: false,
            onTap: onFindRepeaters,
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: context.l10n.navFrequencyReference,
            icon: Icons.table_chart_outlined,
            selected: page == 3,
            onTap: () => onPage(3),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: context.l10n.navAbout,
            icon: Icons.info_outline,
            selected: page == 2,
            onTap: () => onPage(2),
          ),
          const Spacer(),
          const _LanguageMenu(),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Text(
              '${context.l10n.sidebarDesktopProgrammer}\n'
              'Rick Lopez · ${context.l10n.sidebarLeadProgrammer}\n'
              'rick@newchirp.net\n'
              '${context.l10n.sidebarVersion(_newChirpVersion)}',
              style: const TextStyle(
                color: Color(0xFF8FA59B),
                fontSize: 10,
                height: 1.6,
                letterSpacing: 0.8,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LanguageMenu extends StatelessWidget {
  const _LanguageMenu();

  @override
  Widget build(BuildContext context) {
    final current = appLocale.value?.languageCode ?? 'system';
    final label = current == 'system'
        ? context.l10n.languageSystem
        : languageNativeNames[current] ?? current;
    return Tooltip(
      message: context.l10n.languageBetaNote,
      child: PopupMenuButton<String>(
        key: const Key('language-menu'),
        tooltip: '',
        initialValue: current,
        onSelected: (code) {
          appLocale.value = localeForLanguageCode(code);
          unawaited(AppLanguageStore().save(code));
        },
        itemBuilder: (context) => [
          PopupMenuItem(
            value: 'system',
            child: Text(context.l10n.languageSystem),
          ),
          for (final code in supportedLanguageCodes)
            PopupMenuItem(value: code, child: Text(languageNativeNames[code]!)),
        ],
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.translate, color: Color(0xFF9CB0A8), size: 18),
              const SizedBox(width: 11),
              Expanded(
                child: Text(
                  '${context.l10n.languageLabel}: $label',
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFFB7C6C0),
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ProgrammerCredit extends StatelessWidget {
  const _ProgrammerCredit({required this.roleLine, required this.email});

  final String roleLine;
  final String email;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          roleLine,
          style: const TextStyle(
            color: Color(0xFF1F7455),
            fontWeight: FontWeight.w600,
          ),
        ),
        SelectableText(email, style: const TextStyle(color: Colors.black54)),
      ],
    );
  }
}

class _Logo extends StatelessWidget {
  const _Logo();
  @override
  Widget build(BuildContext context) => Container(
    width: 36,
    height: 36,
    decoration: BoxDecoration(
      color: const Color(0xFFDAF2E5),
      borderRadius: BorderRadius.circular(10),
    ),
    child: const Icon(Icons.graphic_eq, color: Color(0xFF1D6B4E)),
  );
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Material(
    color: selected ? const Color(0xFF29493D) : Colors.transparent,
    borderRadius: BorderRadius.circular(9),
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(9),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
        child: Row(
          children: [
            Icon(
              icon,
              color: selected ? Colors.white : const Color(0xFF9CB0A8),
              size: 20,
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Text(
                label,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: selected ? Colors.white : const Color(0xFFB7C6C0),
                  fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

class _TransferOverlay extends StatefulWidget {
  const _TransferOverlay({
    required this.label,
    required this.detail,
    required this.fraction,
    required this.cancelling,
    required this.onCancel,
  });

  final String label;
  final String detail;
  final double? fraction;
  final bool cancelling;
  final VoidCallback onCancel;

  @override
  State<_TransferOverlay> createState() => _TransferOverlayState();
}

class _TransferOverlayState extends State<_TransferOverlay> {
  final Stopwatch _elapsed = Stopwatch();
  Timer? _ticker;

  @override
  void initState() {
    super.initState();
    _elapsed.start();
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }

  String get _elapsedText {
    final seconds = _elapsed.elapsed.inSeconds;
    final minutes = seconds ~/ 60;
    final remainder = seconds % 60;
    return minutes > 0
        ? '${minutes}m ${remainder.toString().padLeft(2, '0')}s'
        : '${remainder}s';
  }

  @override
  Widget build(BuildContext context) {
    final fraction = widget.fraction;
    final percent = fraction == null ? null : (fraction * 100).round();
    return Positioned.fill(
      child: ColoredBox(
        color: Colors.black54,
        child: Center(
          child: Card(
            child: SizedBox(
              width: 390,
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: 58,
                      height: 58,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          CircularProgressIndicator(
                            value: fraction,
                            strokeWidth: 4,
                          ),
                          if (percent != null)
                            Text(
                              '$percent%',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      widget.label,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.detail.isEmpty
                          ? context.l10n.uiPreparingTransfer
                          : widget.detail,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: Color(0xFF39725C),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 14),
                    LinearProgressIndicator(value: fraction),
                    const SizedBox(height: 10),
                    Text(
                      percent == null
                          ? context.l10n.uiWaitingForTheRadioToReport
                          : context.l10n.uiCompleteElapsed(
                              percent,
                              _elapsedText,
                            ),
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.black54),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      context.l10n.uiKeepTheRadioPoweredOnAnd,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.black54),
                    ),
                    const SizedBox(height: 22),
                    OutlinedButton.icon(
                      onPressed: widget.cancelling ? null : widget.onCancel,
                      icon: const Icon(Icons.stop_circle_outlined),
                      label: Text(
                        widget.cancelling ? 'Cancelling...' : 'Cancel',
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class RadioSettingsSourceActions extends StatelessWidget {
  const RadioSettingsSourceActions({
    super.key,
    required this.canReadRadio,
    required this.hasSavedSnapshot,
    required this.enabled,
    required this.onReadRadio,
    required this.onUseSavedSnapshot,
  });

  final bool canReadRadio;
  final bool hasSavedSnapshot;
  final bool enabled;
  final VoidCallback onReadRadio;
  final VoidCallback onUseSavedSnapshot;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.end,
      spacing: 8,
      runSpacing: 8,
      children: [
        if (canReadRadio)
          FilledButton.tonalIcon(
            onPressed: enabled ? onReadRadio : null,
            icon: const Icon(Icons.cable),
            label: Text(context.l10n.readSettingsFromRadio),
          ),
        if (hasSavedSnapshot)
          OutlinedButton.icon(
            onPressed: enabled ? onUseSavedSnapshot : null,
            icon: const Icon(Icons.history),
            label: Text(context.l10n.useSavedSnapshot),
          ),
      ],
    );
  }
}

class _RadioSettingField extends StatefulWidget {
  const _RadioSettingField({
    super.key,
    required this.node,
    required this.onChanged,
  });

  final RadioSettingNode node;
  final ValueChanged<RadioSettingNode> onChanged;

  @override
  State<_RadioSettingField> createState() => _RadioSettingFieldState();
}

class _RadioSettingFieldState extends State<_RadioSettingField> {
  late final TextEditingController _controller;
  late final FocusNode _focusNode;
  String? _error;

  String get _textValue => '${widget.node.value ?? ''}';

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: _textValue);
    _focusNode = FocusNode();
  }

  @override
  void didUpdateWidget(covariant _RadioSettingField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.node != widget.node) {
      _controller.text = _textValue;
      _error = null;
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  String? get _rangeHint {
    final node = widget.node;
    if (node.min == null || node.max == null) return null;
    return '${node.min} - ${node.max}';
  }

  void _changed(String text) {
    final node = widget.node;
    String? error;
    if (node.kind == 'integer') {
      final parsed = int.tryParse(text.trim());
      if (parsed == null) {
        error = context.l10n.uiEnterAWholeNumber;
      } else if (node.min != null && parsed < node.min!) {
        error = context.l10n.uiValueMustBeAtLeast('${node.min}');
      } else if (node.max != null && parsed > node.max!) {
        error = context.l10n.uiValueMustBeAtMost('${node.max}');
      } else {
        node.value = parsed;
      }
    } else if (node.kind == 'number') {
      final parsed = double.tryParse(text.trim());
      if (parsed == null) {
        error = 'Enter a number';
      } else if (node.min != null && parsed < node.min!) {
        error = context.l10n.uiValueMustBeAtLeast('${node.min}');
      } else if (node.max != null && parsed > node.max!) {
        error = context.l10n.uiValueMustBeAtMost('${node.max}');
      } else {
        node.value = parsed;
      }
    } else {
      final length = text.length;
      if (node.minLength != null && length < node.minLength!) {
        error = context.l10n.uiUseAtLeastCharacters('${node.minLength}');
      } else if (node.maxLength != null && length > node.maxLength!) {
        error = context.l10n.uiUseAtMostCharacters('${node.maxLength}');
      } else {
        node.value = text;
      }
    }
    node.invalid = error != null;
    setState(() => _error = error);
    widget.onChanged(node);
  }

  @override
  Widget build(BuildContext context) {
    final node = widget.node;
    final documentation = node.documentation;
    if (node.kind == 'boolean') {
      return SwitchListTile(
        contentPadding: EdgeInsets.zero,
        title: Text(node.label),
        subtitle: documentation == null ? null : Text(documentation),
        value: node.value == true,
        onChanged: node.mutable
            ? (value) {
                node.value = value;
                node.invalid = false;
                widget.onChanged(node);
              }
            : null,
      );
    }
    if (node.kind == 'choice') {
      final choices = [...node.options];
      final current = _textValue;
      if (current.isNotEmpty && !choices.contains(current)) {
        choices.insert(0, current);
      }
      return DropdownButtonFormField<String>(
        initialValue: current.isEmpty ? null : current,
        decoration: InputDecoration(
          labelText: node.label,
          helperText: documentation,
        ),
        items: choices
            .map(
              (choice) => DropdownMenuItem(value: choice, child: Text(choice)),
            )
            .toList(),
        onChanged: node.mutable
            ? (value) {
                if (value == null) return;
                node.value = value;
                node.invalid = false;
                widget.onChanged(node);
              }
            : null,
      );
    }
    if (node.kind == 'unsupported') {
      return Text(
        context.l10n.uiThisSettingTypeIsNotSupported(node.label),
        style: const TextStyle(color: Color(0xFF9B5B18)),
      );
    }
    return TextField(
      controller: _controller,
      focusNode: _focusNode,
      enabled: node.mutable,
      keyboardType: node.kind == 'string'
          ? TextInputType.text
          : TextInputType.number,
      inputFormatters:
          node.kind == 'string' && node.maxLength != null && node.maxLength! > 0
          ? [LengthLimitingTextInputFormatter(node.maxLength)]
          : null,
      decoration: InputDecoration(
        labelText: node.label,
        helperText: documentation,
        errorText: _error,
        suffixText: _rangeHint,
      ),
      onChanged: _changed,
    );
  }
}

List<(String, String)> _glossaryTerms(AppLocalizations l10n) => [
  ('FRS', l10n.glossFrs),
  ('GMRS', l10n.glossGmrs),
  ('RX', l10n.glossRx),
  ('TX', l10n.glossTx),
  ('CTCSS', l10n.glossCtcss),
  ('TSQL', l10n.glossTsql),
  ('DCS', l10n.glossDcs),
  ('DTCS', l10n.glossDtcs),
  ('DTCS POL', l10n.glossDtcsPol),
  ('FM', l10n.glossFm),
  ('NFM', l10n.glossNfm),
  ('AM', l10n.glossAm),
  ('DUPLEX', l10n.glossDuplex),
  ('OFFSET', l10n.glossOffset),
  ('SPLIT', l10n.glossSplit),
  ('STEP', l10n.glossStep),
  ('SCAN', l10n.glossScan),
  ('BCL', l10n.glossBcl),
  ('PTT ID', l10n.glossPttId),
  ('S-CODE', l10n.glossSCode),
];

Future<void> _showAbbreviationGlossary(BuildContext context) {
  return showDialog<void>(
    context: context,
    builder: (context) => const _GlossaryDialog(),
  );
}

class _GlossaryDialog extends StatefulWidget {
  const _GlossaryDialog();

  @override
  State<_GlossaryDialog> createState() => _GlossaryDialogState();
}

class _GlossaryDialogState extends State<_GlossaryDialog> {
  final _controller = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final query = _query.trim().toLowerCase();
    final terms = _glossaryTerms(context.l10n)
        .where(
          (entry) =>
              query.isEmpty ||
              entry.$1.toLowerCase().contains(query) ||
              entry.$2.toLowerCase().contains(query),
        )
        .toList();
    return AlertDialog(
      title: Text(context.l10n.tipAbbreviations),
      content: SizedBox(
        width: 640,
        height: 520,
        child: Column(
          children: [
            TextField(
              controller: _controller,
              autofocus: true,
              onChanged: (value) => setState(() => _query = value),
              decoration: InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: context.l10n.uiSearchAbbreviationsOrDefinitions,
              ),
            ),
            const SizedBox(height: 14),
            Expanded(
              child: terms.isEmpty
                  ? Center(child: Text(context.l10n.uiNoMatchingTerms))
                  : ListView.separated(
                      itemCount: terms.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final term = terms[index];
                        return ListTile(
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 4,
                          ),
                          title: Text(
                            term.$1,
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          subtitle: Text(term.$2),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
      actions: [
        FilledButton(
          onPressed: () => Navigator.pop(context),
          child: Text(context.l10n.close),
        ),
      ],
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({
    required this.libraryName,
    required this.dirty,
    required this.busy,
    required this.status,
    required this.chirpModuleName,
    required this.moduleLoadingAvailable,
    required this.checkingForUpdates,
    required this.onCheckForUpdates,
    required this.onReportProblem,
    required this.onLoadChirpModule,
    required this.onUnloadChirpModule,
    required this.onNew,
    required this.onGmrsStarter,
    required this.onMarineTemplate,
    required this.onRestoreStock,
    required this.onOpen,
    required this.onSave,
    required this.onSaveAs,
    required this.onPrintChannels,
    required this.canSave,
    required this.minimalMode,
    required this.minimalTitle,
    required this.minimalSubtitle,
    required this.showPrint,
    required this.onPrint,
  });
  final String libraryName;
  final bool dirty;
  final bool busy;
  final String status;
  final String? chirpModuleName;
  final bool moduleLoadingAvailable;
  final bool checkingForUpdates;
  final VoidCallback onCheckForUpdates;
  final VoidCallback onReportProblem;
  final VoidCallback onLoadChirpModule;
  final VoidCallback onUnloadChirpModule;
  final VoidCallback onNew;
  final VoidCallback onGmrsStarter;
  final VoidCallback onMarineTemplate;
  final VoidCallback onRestoreStock;
  final VoidCallback onOpen;
  final VoidCallback onSave;
  final VoidCallback onSaveAs;
  final VoidCallback onPrintChannels;
  final bool canSave;
  final bool minimalMode;
  final String minimalTitle;
  final String minimalSubtitle;
  final bool showPrint;
  final VoidCallback onPrint;
  @override
  Widget build(BuildContext context) {
    if (minimalMode) {
      return Container(
        height: 72,
        color: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 22),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    minimalTitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    minimalSubtitle,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.black45, fontSize: 12),
                  ),
                ],
              ),
            ),
            if (showPrint)
              TextButton.icon(
                onPressed: onPrint,
                icon: const Icon(Icons.print_outlined),
                label: Text(context.l10n.print),
              ),
            const SizedBox(width: 8),
            _buildHelpMenu(context, iconOnly: false),
          ],
        ),
      );
    }

    return Container(
      height: 72,
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 22),
      child: LayoutBuilder(
        builder: (context, constraints) {
          // Spanish and French labels run about a third longer than
          // English, so they switch to compact and icon-only layouts sooner.
          final english = Localizations.localeOf(context).languageCode == 'en';
          final labelScale = english ? 1.0 : 1.4;
          final iconOnly = constraints.maxWidth < 760 * labelScale;
          final compactLabels = constraints.maxWidth < 1120 * labelScale;
          return Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: Text(
                            libraryName,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        if (dirty)
                          Padding(
                            padding: const EdgeInsets.only(left: 7),
                            child: Text(
                              context.l10n.edited,
                              style: const TextStyle(
                                color: Color(0xFFC46A15),
                                fontSize: 12,
                              ),
                            ),
                          ),
                      ],
                    ),
                    if (busy || chirpModuleName != null)
                      Text(
                        busy
                            ? status
                            : context.l10n.moduleActive(chirpModuleName!),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: busy
                              ? const Color(0xFF1F7455)
                              : const Color(0xFF9B5B18),
                          fontSize: 12,
                        ),
                      ),
                  ],
                ),
              ),
              MenuAnchor(
                builder: (context, controller, child) {
                  void toggle() => controller.isOpen
                      ? controller.close()
                      : controller.open();
                  if (iconOnly) {
                    return IconButton(
                      tooltip: context.l10n.menuNew,
                      onPressed: busy ? null : toggle,
                      icon: const Icon(Icons.note_add_outlined),
                    );
                  }
                  return TextButton.icon(
                    onPressed: busy ? null : toggle,
                    icon: const Icon(Icons.note_add_outlined),
                    label: Text(context.l10n.menuNew),
                  );
                },
                menuChildren: [
                  MenuItemButton(
                    onPressed: onNew,
                    leadingIcon: const Icon(Icons.note_add_outlined),
                    child: Text(context.l10n.newBlank),
                  ),
                  MenuItemButton(
                    onPressed: onGmrsStarter,
                    leadingIcon: const Icon(Icons.view_list_outlined),
                    child: Text(context.l10n.newGmrs),
                  ),
                  MenuItemButton(
                    onPressed: onMarineTemplate,
                    leadingIcon: const Icon(Icons.sailing_outlined),
                    child: Text(context.l10n.newMarine),
                  ),
                  MenuItemButton(
                    onPressed: onRestoreStock,
                    leadingIcon: const Icon(Icons.restore),
                    child: Text(context.l10n.newRestoreStock),
                  ),
                ],
              ),
              if (iconOnly)
                IconButton(
                  tooltip: context.l10n.openChannelFile,
                  onPressed: busy ? null : onOpen,
                  icon: const Icon(Icons.folder_open_outlined),
                )
              else
                TextButton.icon(
                  onPressed: busy ? null : onOpen,
                  icon: const Icon(Icons.folder_open_outlined),
                  label: Text(
                    compactLabels && !english
                        ? context.l10n.openShort
                        : context.l10n.openChannelFile,
                  ),
                ),
              if (moduleLoadingAvailable || chirpModuleName != null)
                if (iconOnly)
                  IconButton(
                    tooltip: chirpModuleName == null
                        ? context.l10n.loadModule
                        : context.l10n.unloadModule,
                    onPressed: busy
                        ? null
                        : chirpModuleName == null
                        ? onLoadChirpModule
                        : onUnloadChirpModule,
                    icon: Icon(
                      chirpModuleName == null
                          ? Icons.extension_outlined
                          : Icons.extension_off_outlined,
                    ),
                  )
                else
                  TextButton.icon(
                    onPressed: busy
                        ? null
                        : chirpModuleName == null
                        ? onLoadChirpModule
                        : onUnloadChirpModule,
                    icon: Icon(
                      chirpModuleName == null
                          ? Icons.extension_outlined
                          : Icons.extension_off_outlined,
                    ),
                    label: Text(
                      chirpModuleName != null
                          ? context.l10n.unloadModule
                          : compactLabels
                          ? context.l10n.loadModuleShort
                          : context.l10n.loadModule,
                    ),
                  ),
              MenuAnchor(
                builder: (context, controller, child) {
                  void toggle() => controller.isOpen
                      ? controller.close()
                      : controller.open();
                  if (iconOnly) {
                    return IconButton.filled(
                      tooltip: context.l10n.save,
                      onPressed: busy || !canSave ? null : toggle,
                      icon: const Icon(Icons.save_outlined),
                    );
                  }
                  return FilledButton.icon(
                    onPressed: busy || !canSave ? null : toggle,
                    icon: const Icon(Icons.save_outlined),
                    label: Text(context.l10n.save),
                  );
                },
                menuChildren: [
                  MenuItemButton(
                    onPressed: onSave,
                    child: Text(context.l10n.save),
                  ),
                  MenuItemButton(
                    onPressed: onSaveAs,
                    child: Text(context.l10n.saveAs),
                  ),
                  MenuItemButton(
                    key: const ValueKey('print-channel-list'),
                    onPressed: onPrintChannels,
                    leadingIcon: const Icon(Icons.print_outlined),
                    child: Text(context.l10n.printChannelList),
                  ),
                ],
              ),
              const SizedBox(width: 8),
              _buildHelpMenu(context, iconOnly: iconOnly),
            ],
          );
        },
      ),
    );
  }

  Widget _buildHelpMenu(BuildContext context, {required bool iconOnly}) {
    return MenuAnchor(
      builder: (context, controller, child) {
        void toggle() =>
            controller.isOpen ? controller.close() : controller.open();
        if (iconOnly) {
          return IconButton(
            tooltip: context.l10n.help,
            onPressed: toggle,
            icon: const Icon(Icons.help_outline),
          );
        }
        return TextButton.icon(
          onPressed: toggle,
          icon: const Icon(Icons.help_outline),
          label: Text(context.l10n.help),
        );
      },
      menuChildren: [
        MenuItemButton(
          onPressed: onReportProblem,
          leadingIcon: const Icon(Icons.bug_report_outlined),
          child: Text(context.l10n.reportProblem),
        ),
        const Divider(height: 1),
        MenuItemButton(
          onPressed: () => _showAbbreviationGlossary(context),
          leadingIcon: const Icon(Icons.menu_book_outlined),
          child: Text(context.l10n.tipAbbreviations),
        ),
        const Divider(height: 1),
        MenuItemButton(
          onPressed: checkingForUpdates ? null : onCheckForUpdates,
          leadingIcon: checkingForUpdates
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.system_update_alt_outlined),
          child: Text(
            checkingForUpdates
                ? context.l10n.checkingUpdates
                : context.l10n.checkUpdates,
          ),
        ),
      ],
    );
  }
}

class _ChannelApplyMode {
  const _ChannelApplyMode({required this.replaceAll, required this.startAt});

  final bool replaceAll;
  final int startAt;
}

class _LibraryState {
  const _LibraryState({
    required this.channels,
    required this.selected,
    required this.libraryName,
    required this.libraryPath,
    required this.libraryOpen,
    required this.dirty,
    required this.capabilities,
    required this.zones,
    required this.mappings,
    required this.selectedZone,
    required this.clearedLocations,
  });

  final List<RadioChannel> channels;
  final int selected;
  final String libraryName;
  final String? libraryPath;
  final bool libraryOpen;
  final bool dirty;
  final RadioCapabilities? capabilities;
  final List<RadioZone> zones;
  final List<RadioMappingModel> mappings;
  final int? selectedZone;
  final Set<int> clearedLocations;
}

class _ErrorReportDialog extends StatefulWidget {
  const _ErrorReportDialog({
    required this.diagnosticLog,
    required this.summary,
    required this.technical,
    required this.radio,
    required this.version,
    required this.cable,
  });

  final DiagnosticLog diagnosticLog;
  final String summary;
  final String? technical;
  final String radio;
  final String version;
  final String cable;

  @override
  State<_ErrorReportDialog> createState() => _ErrorReportDialogState();
}

class _ErrorReportDialogState extends State<_ErrorReportDialog> {
  final _emailController = TextEditingController();
  final _descriptionController = TextEditingController();
  bool _sending = false;
  bool _sent = false;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    if (!email.contains('@') || email.startsWith('@') || email.endsWith('@')) {
      setState(() => _error = context.l10n.uiEnterAValidEmailAddress);
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    final notes = _descriptionController.text.trim();
    final description = [
      'Reported error: ${widget.summary}',
      if (widget.technical != null && widget.technical!.trim().isNotEmpty)
        'Technical details:\n${widget.technical}',
      if (notes.isNotEmpty) 'Reporter notes:\n$notes',
    ].join('\n\n');
    try {
      await widget.diagnosticLog.submit(
        email: email,
        description: description,
        radio: widget.radio,
        firmware: 'Not available',
        version: widget.version,
        cable: widget.cable,
      );
      widget.diagnosticLog.record(
        'report',
        'Error report submitted',
        context: {'radio': widget.radio, 'version': widget.version},
      );
      if (mounted) setState(() => _sent = true);
    } on DiagnosticReportException catch (error) {
      widget.diagnosticLog.record(
        'report',
        'Error report submission failed: $error',
      );
      if (mounted) setState(() => _error = error.message);
    } on Object {
      if (mounted) {
        setState(() => _error = context.l10n.uiCouldNotSendTheErrorReport);
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final diagnosticPreview = widget.diagnosticLog.buildReport(
      maxCharacters: 6000,
    );
    return AlertDialog(
      title: Text(
        _sent
            ? context.l10n.uiErrorReportSent
            : context.l10n.uiSubmitErrorReport,
      ),
      content: SizedBox(
        width: 620,
        child: SingleChildScrollView(
          child: _sent
              ? Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.check_circle_outline,
                        color: Color(0xFF1F7455),
                        size: 44,
                      ),
                      SizedBox(height: 14),
                      Text(
                        context.l10n.uiThanksTheDiagnosticLogAndError,
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      widget.summary,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      autocorrect: false,
                      decoration: InputDecoration(
                        labelText: context.l10n.uiYourEmail,
                        helperText: context.l10n.uiUsedOnlyIfTheDeveloperNeeds,
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _descriptionController,
                      minLines: 3,
                      maxLines: 6,
                      maxLength: 3500,
                      decoration: InputDecoration(
                        labelText: context.l10n.uiWhatWereYouTryingToDo,
                        alignLabelWithHint: true,
                      ),
                    ),
                    Text(
                      context.l10n.uiTheReportIncludesAppAndOperating,
                      style: TextStyle(color: Colors.black54, height: 1.4),
                    ),
                    const SizedBox(height: 8),
                    ExpansionTile(
                      tilePadding: EdgeInsets.zero,
                      title: Text(
                        context.l10n.uiPreviewDiagnosticEvents(
                          widget.diagnosticLog.entryCount,
                        ),
                        style: const TextStyle(fontSize: 13),
                      ),
                      childrenPadding: const EdgeInsets.only(bottom: 8),
                      children: [
                        Container(
                          width: double.infinity,
                          constraints: const BoxConstraints(maxHeight: 220),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF3F5F4),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: SingleChildScrollView(
                            child: SelectableText(
                              diagnosticPreview.isEmpty
                                  ? context.l10n.uiNoDiagnosticEventsRecorded
                                  : diagnosticPreview,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 10.5,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 10),
                      Text(
                        _error!,
                        style: const TextStyle(color: Color(0xFF9B3D34)),
                      ),
                    ],
                  ],
                ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _sending ? null : () => Navigator.pop(context),
          child: Text(_sent ? 'Close' : 'Cancel'),
        ),
        if (!_sent)
          FilledButton.icon(
            onPressed: _sending ? null : _submit,
            icon: _sending
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send_outlined),
            label: Text(_sending ? 'Sending…' : context.l10n.uiSendReport),
          ),
      ],
    );
  }
}

class _ChannelApplyDialog extends StatefulWidget {
  const _ChannelApplyDialog({
    required this.label,
    required this.count,
    required this.initialStart,
    this.zoneName,
  });

  final String label;
  final int count;
  final int initialStart;
  final String? zoneName;

  @override
  State<_ChannelApplyDialog> createState() => _ChannelApplyDialogState();
}

class _ChannelApplyDialogState extends State<_ChannelApplyDialog> {
  late final TextEditingController _startController;
  bool _replaceAll = true;
  String? _startError;

  @override
  void initState() {
    super.initState();
    _startController = TextEditingController(text: '${widget.initialStart}');
  }

  @override
  void dispose() {
    _startController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      icon: const Icon(Icons.merge_type),
      title: Text(context.l10n.applyTitle(widget.label)),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(context.l10n.applyIntro),
          const SizedBox(height: 12),
          RadioGroup<bool>(
            groupValue: _replaceAll,
            onChanged: (value) => setState(() {
              _replaceAll = value ?? true;
              _startError = null;
            }),
            child: Column(
              children: [
                RadioListTile<bool>(
                  value: true,
                  title: Text(
                    widget.zoneName == null
                        ? context.l10n.applyReplaceList
                        : context.l10n.applyReplaceZone(widget.zoneName!),
                  ),
                  subtitle: Text(
                    widget.zoneName == null
                        ? context.l10n.applyReplaceListNote
                        : context.l10n.applyReplaceZoneNote,
                  ),
                ),
                RadioListTile<bool>(
                  value: false,
                  title: Text(context.l10n.applyInsertAt),
                  subtitle: Text(context.l10n.applyInsertNote(widget.count)),
                ),
              ],
            ),
          ),
          if (!_replaceAll) ...[
            const SizedBox(height: 8),
            TextField(
              controller: _startController,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: false,
              ),
              decoration: InputDecoration(
                labelText: context.l10n.applyStartLabel,
                errorText: _startError,
              ),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(context.l10n.cancel),
        ),
        FilledButton(onPressed: _apply, child: Text(context.l10n.apply)),
      ],
    );
  }

  void _apply() {
    if (_replaceAll) {
      Navigator.pop(
        context,
        const _ChannelApplyMode(replaceAll: true, startAt: 1),
      );
      return;
    }
    final start = int.tryParse(_startController.text);
    if (start == null || start < 1) {
      setState(() => _startError = context.l10n.applyStartError);
      return;
    }
    Navigator.pop(
      context,
      _ChannelApplyMode(replaceAll: false, startAt: start),
    );
  }
}

enum _AddChannelPlacement { end, beforeSelected, afterSelected }

enum _ChannelLocationConflictAction { move, swap, replace }

enum _RepeaterProvider { repeaterBook, myGmrs }

class _SearchableRegionField extends StatelessWidget {
  const _SearchableRegionField({
    required this.value,
    required this.options,
    required this.enabled,
    required this.onSelected,
  });

  final String value;
  final List<String> options;
  final bool enabled;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Autocomplete<String>(
      key: ValueKey('repeater-region-$enabled-$value'),
      initialValue: TextEditingValue(text: value),
      displayStringForOption: (option) => option,
      optionsBuilder: (textEditingValue) {
        if (!enabled) return const Iterable<String>.empty();
        final query = textEditingValue.text.trim().toLowerCase();
        if (query.isEmpty) return options;
        return options.where((option) => option.toLowerCase().contains(query));
      },
      onSelected: onSelected,
      fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) =>
          TextFormField(
            key: const ValueKey('repeater-region-field'),
            controller: controller,
            focusNode: focusNode,
            enabled: enabled,
            decoration: InputDecoration(
              labelText: options.length == 1 ? 'Region' : 'State or province',
              helperText: enabled ? 'Type to search' : null,
              suffixIcon: const Icon(Icons.search),
            ),
            onFieldSubmitted: (_) {
              final query = controller.text.trim().toLowerCase();
              final matches = options
                  .where(
                    (option) =>
                        query.isEmpty || option.toLowerCase().contains(query),
                  )
                  .toList();
              if (matches.length == 1) {
                onSelected(matches.single);
              } else {
                onFieldSubmitted();
              }
            },
          ),
      optionsViewBuilder: (context, selectOption, matches) => Align(
        alignment: Alignment.topLeft,
        child: Material(
          elevation: 8,
          borderRadius: BorderRadius.circular(8),
          clipBehavior: Clip.antiAlias,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxHeight: 240, minWidth: 260),
            child: ListView.builder(
              padding: EdgeInsets.zero,
              shrinkWrap: true,
              itemCount: matches.length,
              itemBuilder: (context, index) {
                final option = matches.elementAt(index);
                return ListTile(
                  dense: true,
                  title: Text(option),
                  onTap: () => selectOption(option),
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

class RepeaterBookDialog extends StatefulWidget {
  const RepeaterBookDialog({
    super.key,
    required this.bridge,
    required this.preferencesStore,
    this.myGmrsService,
  });

  final RadioBridge bridge;
  final RepeaterSearchPreferencesStore preferencesStore;
  final MyGmrsService? myGmrsService;

  @override
  State<RepeaterBookDialog> createState() => _RepeaterBookDialogState();
}

class _RepeaterBookDialogState extends State<RepeaterBookDialog> {
  final _filterController = TextEditingController();
  final _latitudeController = TextEditingController();
  final _longitudeController = TextEditingController();
  final _distanceController = TextEditingController();
  final _resultFilterController = TextEditingController();
  final _countyFilterController = TextEditingController();
  String _country = 'United States';
  String _state = 'New York';
  String _service = 'all';
  _RepeaterProvider _provider = _RepeaterProvider.repeaterBook;
  bool _fmOnly = false;
  bool _openOnly = false;
  bool _preferencesLoaded = false;
  bool _preferencesTouched = false;
  late final Future<void> _preferencesLoad;
  Future<void> _preferencesSave = Future.value();
  Timer? _preferencesSaveTimer;
  bool _mapView = false;
  bool _loading = false;
  String _status = '';
  String? _error;
  RepeaterSearchResults? _results;
  final Set<RepeaterSearchResult> _selected = {};
  final Set<String> _selectedCounties = {};
  RepeaterSortOrder _sortOrder = RepeaterSortOrder.source;
  Size? _dialogSize;
  final MapController _mapController = MapController();
  // The results list scrolls on its own inside the dialog's scrolling page;
  // it needs its own controller and bar (2026-11-26 report: the visible
  // scroll bar belonged to the page, so only Tab reached more repeaters).
  final ScrollController _resultsScrollController = ScrollController();
  late final MyGmrsService _myGmrs;
  bool _myGmrsSigningIn = false;
  bool _myGmrsSignInCancelled = false;

  List<String> get _regions => repeaterRegionsForCountry(_country);

  bool get _supportsGmrs => repeaterCountrySupportsGmrs(_country);

  @override
  void initState() {
    super.initState();
    _myGmrs = widget.myGmrsService ?? MyGmrsClient();
    _preferencesLoad = _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final preferences = await widget.preferencesStore.load();
    if (!mounted) return;
    _preferencesLoaded = true;
    if (_preferencesTouched) return;
    final provider = _enumByName(
      _RepeaterProvider.values,
      preferences.provider,
      _RepeaterProvider.repeaterBook,
    );
    var country = repeaterCountryChoices.contains(preferences.country)
        ? preferences.country
        : 'United States';
    if (provider == _RepeaterProvider.myGmrs) {
      country = 'United States';
    }
    final regions = repeaterRegionsForCountry(country);
    final region = regions.contains(preferences.region)
        ? preferences.region
        : regions.first;
    var service = const {'all', 'amateur', 'gmrs'}.contains(preferences.service)
        ? preferences.service
        : 'all';
    if (provider == _RepeaterProvider.myGmrs) {
      service = 'gmrs';
    }
    service = repeaterCountrySupportsGmrs(country) ? service : 'amateur';
    final sortOrder = _enumByName(
      RepeaterSortOrder.values,
      preferences.sortOrder,
      RepeaterSortOrder.source,
    );
    setState(() {
      _provider = provider;
      _country = country;
      _state = region;
      _service = service;
      _sortOrder = sortOrder;
      _filterController.text = preferences.query;
      _latitudeController.text = preferences.latitude;
      _longitudeController.text = preferences.longitude;
      _distanceController.text = preferences.radiusKm;
      _fmOnly = preferences.fmOnly;
      _openOnly = preferences.openOnly;
      _mapView = preferences.mapView;
      if (provider == _RepeaterProvider.myGmrs) {
        _fmOnly = false;
      }
    });
  }

  T _enumByName<T extends Enum>(List<T> values, String name, T fallback) {
    for (final value in values) {
      if (value.name == name) return value;
    }
    return fallback;
  }

  RepeaterSearchPreferences _currentPreferences() {
    return RepeaterSearchPreferences(
      provider: _provider.name,
      country: _country,
      region: _state,
      service: _service,
      sortOrder: _sortOrder.name,
      query: _filterController.text,
      latitude: _latitudeController.text,
      longitude: _longitudeController.text,
      radiusKm: _distanceController.text,
      openOnly: _openOnly,
      fmOnly: _fmOnly,
      mapView: _mapView,
    );
  }

  Future<void> _savePreferencesNow() {
    final preferences = _currentPreferences();
    _preferencesSave = _preferencesSave.then((_) async {
      try {
        await widget.preferencesStore.save(preferences);
      } on FileSystemException {
        // Search preferences should never prevent a repeater query.
      }
    });
    return _preferencesSave;
  }

  void _preferencesChanged() {
    _preferencesTouched = true;
    if (!_preferencesLoaded) return;
    _preferencesSaveTimer?.cancel();
    _preferencesSaveTimer = Timer(const Duration(milliseconds: 250), () {
      if (mounted) unawaited(_savePreferencesNow());
    });
  }

  void _selectCountry(String country) {
    final regions = repeaterRegionsForCountry(country);
    setState(() {
      _preferencesTouched = true;
      _country = country;
      _state = regions.first;
      _service = repeaterCountrySupportsGmrs(country) ? _service : 'amateur';
      _results = null;
      _selected.clear();
      _selectedCounties.clear();
      _error = null;
      _status = '';
    });
    _preferencesChanged();
  }

  void _selectProvider(_RepeaterProvider provider) {
    if (_myGmrsSigningIn) {
      _myGmrs.cancelSignIn();
      _myGmrsSigningIn = false;
    }
    setState(() {
      _preferencesTouched = true;
      _provider = provider;
      _results = null;
      _selected.clear();
      _selectedCounties.clear();
      _error = null;
      _status = '';
      if (provider == _RepeaterProvider.myGmrs) {
        _country = 'United States';
        _service = 'gmrs';
        _fmOnly = false;
      }
    });
    _preferencesChanged();
  }

  Future<void> _signInMyGmrs() async {
    _myGmrsSignInCancelled = false;
    setState(() {
      _loading = true;
      _myGmrsSigningIn = true;
      _error = null;
      _status = context.l10n.uiWaitingForMygmrsSignInYou;
    });
    try {
      await _myGmrs.signIn();
      if (mounted) {
        setState(() => _status = context.l10n.uiSignedInToMygmrsForThis);
      }
    } catch (error) {
      if (mounted && !_myGmrsSignInCancelled) {
        setState(() => _error = '$error');
      }
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _myGmrsSigningIn = false;
        });
      }
    }
  }

  void _cancelMyGmrsSignIn() {
    _myGmrsSignInCancelled = true;
    _myGmrs.cancelSignIn();
    if (mounted) {
      setState(() {
        _loading = false;
        _myGmrsSigningIn = false;
        _status = context.l10n.uiMygmrsSignInCancelled;
        _error = null;
      });
    }
  }

  Future<void> _signOutMyGmrs() async {
    setState(() {
      _loading = true;
      _error = null;
      _status = context.l10n.uiSigningOutOfMygmrs;
    });
    try {
      await _myGmrs.signOut();
      if (mounted) {
        setState(() {
          _status = context.l10n.uiSignedOutOfMygmrs;
          _results = null;
          _selected.clear();
          _selectedCounties.clear();
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() => _error = '$error');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _preferencesSaveTimer?.cancel();
    if (_preferencesTouched) unawaited(_savePreferencesNow());
    _filterController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    _distanceController.dispose();
    _resultFilterController.dispose();
    _countyFilterController.dispose();
    _mapController.dispose();
    _resultsScrollController.dispose();
    if (_myGmrsSigningIn) _myGmrs.cancelSignIn();
    super.dispose();
  }

  Future<void> _search() async {
    await _preferencesLoad;
    if (!mounted) return;
    final filter = _filterController.text.trim();
    final zipSearch = RegExp(r'^\d{5}(?:-\d{4})?$').hasMatch(filter);
    final latitude = double.tryParse(_latitudeController.text.trim());
    final longitude = double.tryParse(_longitudeController.text.trim());
    final distance = double.tryParse(_distanceController.text.trim());
    if ((latitude == null) != (longitude == null)) {
      setState(() => _error = context.l10n.uiEnterBothLatitudeAndLongitudeOr);
      return;
    }
    if (latitude != null && (latitude < -90 || latitude > 90)) {
      setState(() => _error = context.l10n.uiLatitudeMustBeBetweenAnd);
      return;
    }
    if (longitude != null && (longitude < -180 || longitude > 180)) {
      setState(() => _error = context.l10n.uiLongitudeMustBeBetweenAnd);
      return;
    }
    if (zipSearch && latitude != null) {
      setState(() => _error = context.l10n.uiUseEitherAZipCodeOr);
      return;
    }
    if (distance != null && latitude == null && !zipSearch) {
      setState(
        () => _error = context.l10n.uiLatitudeAndLongitudeAreRequiredFor,
      );
      return;
    }
    if (distance != null && distance <= 0) {
      setState(() => _error = context.l10n.uiRadiusMustBeGreaterThanZero);
      return;
    }
    if (_provider == _RepeaterProvider.myGmrs && !_myGmrs.signedIn) {
      setState(() => _error = context.l10n.uiSignInToMygmrsBeforeSearching);
      return;
    }
    _preferencesSaveTimer?.cancel();
    _preferencesTouched = true;
    await _savePreferencesNow();
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
      _results = null;
      _selected.clear();
      _selectedCounties.clear();
      _status = _provider == _RepeaterProvider.myGmrs
          ? context.l10n.uiSigningInToMygmrs
          : context.l10n.uiSearchingRepeaterbook;
    });
    try {
      final results = _provider == _RepeaterProvider.myGmrs
          ? await _myGmrs.searchRepeaters(
              state: _state,
              query: filter,
              latitude: latitude,
              longitude: longitude,
              distanceKm: distance,
              openOnly: _openOnly,
            )
          : await widget.bridge.searchRepeaters(
              country: _country,
              state: _state,
              service: _service,
              filter: _filterController.text.trim(),
              latitude: latitude,
              longitude: longitude,
              distance: distance,
              fmOnly: _fmOnly,
              openOnly: _openOnly,
              onProgress: (progress) {
                if (mounted) setState(() => _status = progress.label);
              },
            );
      if (!mounted) return;
      setState(() {
        _results = results;
        if (results.results.isEmpty) {
          _error = _emptyResultsMessage(results.totalMatches);
        }
      });
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _emptyResultsMessage(int totalMatches) {
    final source = _provider == _RepeaterProvider.myGmrs
        ? 'myGMRS'
        : 'RepeaterBook';
    if (totalMatches > 0) {
      return context.l10n.repeatersNoneImportable(totalMatches, source);
    }
    final hasCoordinates =
        double.tryParse(_latitudeController.text.trim()) != null &&
        double.tryParse(_longitudeController.text.trim()) != null;
    final location = hasCoordinates || _state == 'All'
        ? _country
        : '$_state, $_country';
    final radius = double.tryParse(_distanceController.text.trim());
    final zip = RegExp(
      r'^\d{5}(?:-\d{4})?$',
    ).hasMatch(_filterController.text.trim());
    final effectiveRadius = radius == null && zip ? 50.0 : radius;
    final km = effectiveRadius?.toStringAsFixed(
      effectiveRadius == effectiveRadius.roundToDouble() ? 0 : 1,
    );
    final range = effectiveRadius == null || effectiveRadius <= 0
        ? context.l10n.repeaterRangeIn(location)
        : zip
        ? context.l10n.repeaterRangeZip(
            km!,
            _filterController.text.trim(),
            location,
          )
        : context.l10n.repeaterRangeCoords(km!, location);
    if (_country == 'United States' && _service == 'gmrs') {
      final sourceHint = _provider == _RepeaterProvider.myGmrs
          ? context.l10n.uiMygmrsRequiresAnActiveGmrsLicense2
          : context.l10n.uiRepeaterbookMayNotHaveAGmrs;
      final scopeHint = hasCoordinates
          ? context.l10n.uiCoordinatesAreSearchedWithinTheSelected
          : context.l10n.uiCheckThatCountryAndRegionAre;
      return context.l10n.uiNoMatchingGmrsRepeatersWereFound(
        range,
        sourceHint,
        scopeHint,
      );
    }
    final activeFilters = [
      if (_openOnly) context.l10n.uiOpenUse,
      if (_fmOnly) context.l10n.uiFmAnalog,
    ];
    final filterHint = activeFilters.isEmpty
        ? ''
        : context.l10n.repeaterFilterHint(
            activeFilters.join(context.l10n.listAnd),
          );
    if (zip) {
      return context.l10n.uiNoMatchingRepeatersWereFoundZip(range, filterHint);
    }
    if (hasCoordinates) {
      return context.l10n.uiNoMatchingRepeatersWereFoundCoordinates(
        range,
        filterHint,
      );
    }
    return context.l10n.uiNoMatchingRepeatersWereFoundCheck(range, filterHint);
  }

  List<RadioChannel> get _selectedChannels {
    final results = _selected.toList()
      ..sort(
        (left, right) =>
            left.channel.location.compareTo(right.channel.location),
      );
    return [
      for (var index = 0; index < results.length; index++)
        results[index].channel.copy()..location = index + 1,
    ];
  }

  List<String> get _availableCounties {
    final loadedCounties = {
      for (final result in _results?.results ?? const <RepeaterSearchResult>[])
        if (result.county.trim().isNotEmpty) result.county.trim(),
    };
    return repeaterCountiesForRegion(_country, _state, loadedCounties);
  }

  Future<void> _chooseCounties() async {
    final counties = _availableCounties;
    if (counties.isEmpty) return;
    final selected = Set<String>.of(_selectedCounties);
    _countyFilterController.clear();
    var countyQuery = '';
    final result = await showDialog<Set<String>>(
      context: context,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          final visibleCounties = counties
              .where(
                (county) =>
                    countyQuery.isEmpty ||
                    county.toLowerCase().contains(countyQuery),
              )
              .toList();
          return AlertDialog(
            title: Text(context.l10n.uiFilterCounties(_state)),
            content: SizedBox(
              width: 460,
              height: 420,
              child: Column(
                children: [
                  TextField(
                    key: const ValueKey('county-filter-field'),
                    controller: _countyFilterController,
                    autofocus: true,
                    decoration: InputDecoration(
                      labelText: context.l10n.uiFindACounty,
                      prefixIcon: Icon(Icons.search),
                    ),
                    onChanged: (value) => setDialogState(
                      () => countyQuery = value.trim().toLowerCase(),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Text(
                        context.l10n.uiOfCounties(
                          visibleCounties.length,
                          counties.length,
                        ),
                        style: const TextStyle(
                          color: Colors.black54,
                          fontSize: 12,
                        ),
                      ),
                      const Spacer(),
                      TextButton(
                        onPressed: () => setDialogState(selected.clear),
                        child: Text(context.l10n.uiClearAll),
                      ),
                    ],
                  ),
                  Expanded(
                    child: visibleCounties.isEmpty
                        ? Center(child: Text(context.l10n.uiNoMatchingCounties))
                        : ListView.builder(
                            itemCount: visibleCounties.length,
                            itemBuilder: (context, index) {
                              final county = visibleCounties[index];
                              return CheckboxListTile(
                                dense: true,
                                value: selected.contains(county),
                                title: Text(county),
                                onChanged: (checked) => setDialogState(() {
                                  if (checked == true) {
                                    selected.add(county);
                                  } else {
                                    selected.remove(county);
                                  }
                                }),
                              );
                            },
                          ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: Text(context.l10n.cancel),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, selected),
                child: Text(context.l10n.apply),
              ),
            ],
          );
        },
      ),
    );
    if (!mounted || result == null) return;
    setState(() {
      _selectedCounties
        ..clear()
        ..addAll(result);
    });
  }

  void _searchAmateurInstead() {
    setState(() {
      _preferencesTouched = true;
      _provider = _RepeaterProvider.repeaterBook;
      _service = 'amateur';
    });
    _preferencesChanged();
    _search();
  }

  String _channelDetail(RepeaterSearchResult result) {
    final channel = result.channel;
    final frequency = '${channel.frequency.toStringAsFixed(4)} MHz';
    final tone = channel.tone.isEmpty ? context.l10n.uiNoTone : channel.tone;
    final distance = result.distanceKm == null
        ? ''
        : ' • ${result.distanceKm!.toStringAsFixed(1)} km';
    return '${result.service} • $frequency • ${channel.mode} • $tone$distance'
        '${result.location.isEmpty ? '' : ' • ${result.location}'}';
  }

  void _setResultSelected(RepeaterSearchResult result, bool selected) {
    setState(() {
      if (selected) {
        _selected.add(result);
      } else {
        _selected.remove(result);
      }
    });
  }

  Widget _buildResultsMap(
    BuildContext context,
    List<RepeaterSearchResult> visibleResults,
  ) {
    final points = [
      for (final result in visibleResults)
        if (result.latitude != null && result.longitude != null)
          LatLng(result.latitude!, result.longitude!),
    ];
    final markers = [
      for (final result in visibleResults)
        if (result.latitude != null && result.longitude != null)
          Marker(
            point: LatLng(result.latitude!, result.longitude!),
            width: 24,
            height: 24,
            child: Tooltip(
              message:
                  '${result.callsign} • ${result.channel.frequency.toStringAsFixed(4)} MHz\n'
                  '${result.location}',
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () =>
                    _setResultSelected(result, !_selected.contains(result)),
                child: Icon(
                  Icons.location_on,
                  size: 22,
                  color: _selected.contains(result)
                      ? const Color(0xFF9B3C20)
                      : const Color(0xFF1F7455),
                  shadows: const [Shadow(blurRadius: 4, color: Colors.black45)],
                ),
              ),
            ),
          ),
    ];
    final fallback = points.isEmpty ? const LatLng(39.5, -98.35) : points.first;
    void fitAllPoints() {
      if (!mounted || points.isEmpty) return;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        _mapController.fitCamera(
          CameraFit.bounds(
            bounds: LatLngBounds.fromPoints(points),
            padding: const EdgeInsets.all(52),
            maxZoom: points.length == 1 ? 12 : 11,
          ),
        );
      });
    }

    final mapKey = ValueKey(
      Object.hashAll(
        points.map((point) => '${point.latitude},${point.longitude}'),
      ),
    );
    return Stack(
      children: [
        Positioned.fill(
          child: FlutterMap(
            key: mapKey,
            mapController: _mapController,
            options: MapOptions(
              initialCenter: fallback,
              initialZoom: 9,
              minZoom: 2,
              maxZoom: 18,
              initialCameraFit: points.length > 1
                  ? CameraFit.bounds(
                      bounds: LatLngBounds.fromPoints(points),
                      padding: const EdgeInsets.all(48),
                      maxZoom: 12,
                    )
                  : null,
              onMapReady: fitAllPoints,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.rickext.newchirp',
                maxZoom: 19,
              ),
              CircleLayer(
                circles: [
                  for (final result in visibleResults)
                    if (result.latitude != null && result.longitude != null)
                      CircleMarker(
                        point: LatLng(result.latitude!, result.longitude!),
                        radius: 4,
                        color: _selected.contains(result)
                            ? const Color(0xFFB23A28)
                            : const Color(0xFF19724F),
                        borderStrokeWidth: 1,
                        borderColor: Colors.white,
                      ),
                ],
              ),
              MarkerLayer(markers: markers),
              const RichAttributionWidget(
                attributions: [
                  TextSourceAttribution('OpenStreetMap contributors'),
                ],
              ),
            ],
          ),
        ),
        if (points.isEmpty)
          Positioned.fill(
            child: ColoredBox(
              color: Color(0xCCFFFFFF),
              child: Center(
                child: Text(context.l10n.uiNoCoordinatesAreAvailableForThese),
              ),
            ),
          )
        else
          Positioned(
            top: 8,
            right: 8,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                child: Text(
                  context.l10n.uiMappedTapAPinToSelect(points.length),
                  style: const TextStyle(fontSize: 11),
                ),
              ),
            ),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final results = _results;
    final sortedResults = results == null
        ? const <RepeaterSearchResult>[]
        : sortRepeaterResults(results.results, _sortOrder);
    final visibleResults = filterRepeaterResults(
      sortedResults,
      _resultFilterController.text,
      counties: _selectedCounties,
    );
    final size = MediaQuery.sizeOf(context);
    final maxWidth = size.width - 24;
    final maxHeight = size.height - 24;
    final minWidth = maxWidth < 680 ? maxWidth : 680.0;
    final minHeight = maxHeight < 520 ? maxHeight : 520.0;
    final dialogWidth = (_dialogSize?.width ?? size.width * 0.9)
        .clamp(minWidth, maxWidth)
        .toDouble();
    final dialogHeight = (_dialogSize?.height ?? size.height * 0.9)
        .clamp(minHeight, maxHeight)
        .toDouble();
    final resultsHeight = dialogHeight > 480 ? dialogHeight - 300 : 180.0;
    void resizeBy(double dx, double dy) {
      setState(() {
        _dialogSize = Size(
          (dialogWidth + dx).clamp(minWidth, maxWidth).toDouble(),
          (dialogHeight + dy).clamp(minHeight, maxHeight).toDouble(),
        );
      });
    }

    return Dialog(
      insetPadding: const EdgeInsets.all(12),
      child: SizedBox(
        key: const Key('repeater-book-dialog'),
        width: dialogWidth,
        height: dialogHeight,
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 22),
              child: Column(
                children: [
                  const Icon(
                    Icons.travel_explore,
                    color: Color(0xFF1F7455),
                    size: 30,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    context.l10n.navFindRepeaters,
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 14),
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            context.l10n.uiSearchARepeaterDirectoryAndAdd,
                            style: TextStyle(color: Colors.black54),
                          ),
                          const SizedBox(height: 14),
                          if (_enableMyGmrsDirectory) ...[
                            Row(
                              children: [
                                Expanded(
                                  child:
                                      DropdownButtonFormField<
                                        _RepeaterProvider
                                      >(
                                        key: ValueKey(
                                          'repeater-provider-${_provider.name}',
                                        ),
                                        isExpanded: true,
                                        initialValue: _provider,
                                        decoration: InputDecoration(
                                          labelText: context.l10n.uiDirectory,
                                        ),
                                        items: const [
                                          DropdownMenuItem(
                                            value:
                                                _RepeaterProvider.repeaterBook,
                                            child: Text('RepeaterBook'),
                                          ),
                                          DropdownMenuItem(
                                            value: _RepeaterProvider.myGmrs,
                                            child: Text('myGMRS.com'),
                                          ),
                                        ],
                                        onChanged: _loading
                                            ? null
                                            : (value) {
                                                if (value != null) {
                                                  _selectProvider(value);
                                                }
                                              },
                                      ),
                                ),
                                if (_provider == _RepeaterProvider.myGmrs) ...[
                                  const SizedBox(width: 12),
                                  OutlinedButton.icon(
                                    key: const ValueKey('mygmrs-sign-in'),
                                    onPressed: _myGmrsSigningIn
                                        ? _cancelMyGmrsSignIn
                                        : _loading
                                        ? null
                                        : _myGmrs.signedIn
                                        ? _signOutMyGmrs
                                        : _signInMyGmrs,
                                    icon: Icon(
                                      _myGmrsSigningIn
                                          ? Icons.cancel_outlined
                                          : _myGmrs.signedIn
                                          ? Icons.logout
                                          : Icons.login,
                                    ),
                                    label: Text(
                                      _myGmrsSigningIn
                                          ? context.l10n.uiCancelSignIn
                                          : _myGmrs.signedIn
                                          ? context.l10n.uiSignOut
                                          : context.l10n.uiSignInToMygmrs,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                            if (_provider == _RepeaterProvider.myGmrs) ...[
                              const SizedBox(height: 6),
                              Text(
                                context
                                    .l10n
                                    .uiMygmrsRequiresAnActiveGmrsLicense,
                                style: TextStyle(
                                  color: Colors.black54,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                            const SizedBox(height: 12),
                          ],
                          Row(
                            children: [
                              Expanded(
                                child: DropdownButtonFormField<String>(
                                  key: ValueKey('repeater-country-$_country'),
                                  isExpanded: true,
                                  initialValue: _country,
                                  decoration: InputDecoration(
                                    labelText: context.l10n.uiCountry,
                                  ),
                                  items: repeaterCountryChoices
                                      .map(
                                        (country) => DropdownMenuItem(
                                          value: country,
                                          child: Text(country),
                                        ),
                                      )
                                      .toList(),
                                  onChanged:
                                      _loading ||
                                          _provider == _RepeaterProvider.myGmrs
                                      ? null
                                      : (value) {
                                          if (value != null) {
                                            _selectCountry(value);
                                          }
                                        },
                                ),
                              ),
                              SizedBox(width: 12),
                              SizedBox(
                                width: 165,
                                child:
                                    DropdownButtonFormField<RepeaterSortOrder>(
                                      key: ValueKey(
                                        'repeater-sort-${_sortOrder.name}',
                                      ),
                                      isExpanded: true,
                                      initialValue: _sortOrder,
                                      decoration: InputDecoration(
                                        labelText: context.l10n.uiSortResults,
                                      ),
                                      items: [
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.source,
                                          child: Text(
                                            context.l10n.uiSourceOrder,
                                          ),
                                        ),
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.frequency,
                                          child: Text(context.l10n.uiFrequency),
                                        ),
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.callsignName,
                                          child: Text(
                                            context.l10n.uiCallsignName,
                                          ),
                                        ),
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.city,
                                          child: Text(context.l10n.uiCity),
                                        ),
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.county,
                                          child: Text(context.l10n.uiCounty),
                                        ),
                                      ],
                                      onChanged: (value) {
                                        if (value != null) {
                                          setState(() {
                                            _preferencesTouched = true;
                                            _sortOrder = value;
                                          });
                                          _preferencesChanged();
                                        }
                                      },
                                    ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: _SearchableRegionField(
                                  value: _state,
                                  options: _regions,
                                  enabled: !_loading && _regions.length > 1,
                                  onSelected: (value) {
                                    setState(() {
                                      _preferencesTouched = true;
                                      _state = value;
                                      _results = null;
                                      _selected.clear();
                                      _selectedCounties.clear();
                                    });
                                    _preferencesChanged();
                                  },
                                ),
                              ),
                              SizedBox(width: 12),
                              SizedBox(
                                width: 190,
                                child: DropdownButtonFormField<String>(
                                  key: ValueKey(
                                    'repeater-service-$_country-$_service',
                                  ),
                                  isExpanded: true,
                                  initialValue: _service,
                                  decoration: InputDecoration(
                                    labelText: context.l10n.uiService,
                                  ),
                                  items: [
                                    DropdownMenuItem(
                                      value: 'all',
                                      child: Text(context.l10n.uiAmateurGmrs),
                                    ),
                                    DropdownMenuItem(
                                      value: 'amateur',
                                      child: Text(context.l10n.uiAmateurHam),
                                    ),
                                    DropdownMenuItem(
                                      value: 'gmrs',
                                      child: Text('GMRS'),
                                    ),
                                  ],
                                  onChanged:
                                      _loading ||
                                          !_supportsGmrs ||
                                          _provider == _RepeaterProvider.myGmrs
                                      ? null
                                      : (value) {
                                          if (value != null) {
                                            setState(() {
                                              _preferencesTouched = true;
                                              _service = value;
                                              _results = null;
                                              _selected.clear();
                                              _selectedCounties.clear();
                                            });
                                            _preferencesChanged();
                                          }
                                        },
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            key: const ValueKey('repeater-search-filter'),
                            controller: _filterController,
                            enabled: !_loading,
                            onChanged: (_) {
                              setState(() => _preferencesTouched = true);
                              _preferencesChanged();
                            },
                            onSubmitted: (_) => _search(),
                            decoration: InputDecoration(
                              labelText: _provider == _RepeaterProvider.myGmrs
                                  ? context.l10n.uiRepeaterNameCityOrZipCode
                                  : context
                                        .l10n
                                        .uiCityZipCountyCallsignLandmarkOr,
                              helperText: _provider == _RepeaterProvider.myGmrs
                                  ? context
                                        .l10n
                                        .uiADigitZipSearchesNearbyRepeaters
                                  : context
                                        .l10n
                                        .uiADigitZipSearchesRepeatersWithin,
                              prefixIcon: const Icon(Icons.search),
                              suffixIcon: _filterController.text.isEmpty
                                  ? null
                                  : IconButton(
                                      key: const ValueKey(
                                        'repeater-search-clear',
                                      ),
                                      tooltip:
                                          context.l10n.uiClearRepeaterSearch,
                                      onPressed: () {
                                        setState(() {
                                          _preferencesTouched = true;
                                          _filterController.clear();
                                        });
                                        _preferencesChanged();
                                      },
                                      icon: const Icon(Icons.clear),
                                    ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  key: const ValueKey('repeater-latitude'),
                                  controller: _latitudeController,
                                  enabled: !_loading,
                                  onChanged: (_) => _preferencesChanged(),
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                        signed: true,
                                      ),
                                  decoration: InputDecoration(
                                    labelText: context.l10n.uiLatitudeOptional,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  key: const ValueKey('repeater-longitude'),
                                  controller: _longitudeController,
                                  enabled: !_loading,
                                  onChanged: (_) => _preferencesChanged(),
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                        signed: true,
                                      ),
                                  decoration: InputDecoration(
                                    labelText: context.l10n.uiLongitudeOptional,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  key: const ValueKey('repeater-radius-km'),
                                  controller: _distanceController,
                                  enabled: !_loading,
                                  onChanged: (_) => _preferencesChanged(),
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  decoration: InputDecoration(
                                    labelText: context.l10n.uiRadiusKm,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 18,
                            children: [
                              CheckboxListTile(
                                contentPadding: EdgeInsets.zero,
                                dense: true,
                                controlAffinity:
                                    ListTileControlAffinity.leading,
                                title: Text(context.l10n.uiOpenRepeatersOnly),
                                value: _openOnly,
                                onChanged: _loading
                                    ? null
                                    : (value) {
                                        setState(() {
                                          _preferencesTouched = true;
                                          _openOnly = value ?? false;
                                        });
                                        _preferencesChanged();
                                      },
                              ),
                              CheckboxListTile(
                                contentPadding: EdgeInsets.zero,
                                dense: true,
                                controlAffinity:
                                    ListTileControlAffinity.leading,
                                title: Text(context.l10n.uiFmCapableOnly),
                                value: _fmOnly,
                                onChanged:
                                    _loading ||
                                        _provider == _RepeaterProvider.myGmrs
                                    ? null
                                    : (value) {
                                        setState(() {
                                          _preferencesTouched = true;
                                          _fmOnly = value ?? false;
                                        });
                                        _preferencesChanged();
                                      },
                              ),
                            ],
                          ),
                          if (_loading) ...[
                            const LinearProgressIndicator(),
                            const SizedBox(height: 6),
                          ],
                          if (_status.isNotEmpty) ...[
                            Text(
                              _status,
                              style: const TextStyle(color: Colors.black54),
                            ),
                          ],
                          if (_error != null) ...[
                            const SizedBox(height: 6),
                            Text(
                              _error!,
                              style: const TextStyle(color: Color(0xFF9B3C20)),
                            ),
                            if (_service == 'gmrs' &&
                                _results != null &&
                                _results!.results.isEmpty)
                              TextButton.icon(
                                onPressed: _loading
                                    ? null
                                    : _searchAmateurInstead,
                                icon: const Icon(Icons.search),
                                label: Text(
                                  context.l10n.uiSearchAmateurRepeatersInstead,
                                ),
                              ),
                          ],
                          if (results != null) ...[
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Expanded(
                                  child: TextField(
                                    controller: _resultFilterController,
                                    onChanged: (_) => setState(() {}),
                                    decoration: InputDecoration(
                                      isDense: true,
                                      labelText:
                                          context.l10n.uiFilterLoadedResults,
                                      hintText: context
                                          .l10n
                                          .uiCityCountyCallsignModeServiceOr,
                                      prefixIcon: const Icon(
                                        Icons.filter_alt_outlined,
                                      ),
                                      suffixIcon:
                                          _resultFilterController.text.isEmpty
                                          ? null
                                          : IconButton(
                                              tooltip: context
                                                  .l10n
                                                  .uiClearResultFilter,
                                              onPressed: () => setState(
                                                _resultFilterController.clear,
                                              ),
                                              icon: const Icon(Icons.close),
                                            ),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                OutlinedButton.icon(
                                  onPressed: _availableCounties.isEmpty
                                      ? null
                                      : _chooseCounties,
                                  icon: const Icon(
                                    Icons.location_city_outlined,
                                  ),
                                  label: Text(
                                    _selectedCounties.isEmpty
                                        ? context.l10n.uiAllCounties
                                        : context.l10n.countyCount(
                                            _selectedCounties.length,
                                          ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  results == null
                                      ? context
                                            .l10n
                                            .uiSearchToPreviewRepeaterChannels
                                      : context.l10n.uiShownOfLoadedDataFrom(
                                          visibleResults.length,
                                          results.results.length,
                                          results.source,
                                        ),
                                  style: TextStyle(
                                    color: Colors.black54,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                              if (results != null &&
                                  visibleResults.isNotEmpty) ...[
                                SegmentedButton<bool>(
                                  segments: [
                                    ButtonSegment(
                                      value: false,
                                      icon: Icon(Icons.view_list_outlined),
                                      label: Text(context.l10n.uiList),
                                    ),
                                    ButtonSegment(
                                      value: true,
                                      icon: Icon(Icons.map_outlined),
                                      label: Text(context.l10n.uiMap),
                                    ),
                                  ],
                                  selected: {_mapView},
                                  showSelectedIcon: false,
                                  style: const ButtonStyle(
                                    visualDensity: VisualDensity.compact,
                                  ),
                                  onSelectionChanged: (selection) {
                                    setState(() {
                                      _preferencesTouched = true;
                                      _mapView = selection.first;
                                    });
                                    _preferencesChanged();
                                  },
                                ),
                                const SizedBox(width: 8),
                                TextButton(
                                  onPressed: () => setState(
                                    () => _selected.addAll(visibleResults),
                                  ),
                                  child: Text(context.l10n.uiSelectAll),
                                ),
                                TextButton(
                                  onPressed: () => setState(_selected.clear),
                                  child: Text(context.l10n.uiClear),
                                ),
                              ],
                            ],
                          ),
                          if (results != null &&
                              results.source == 'RepeaterBook')
                            Padding(
                              padding: EdgeInsets.only(top: 2),
                              child: Text(
                                context.l10n.uiDataCourtesyOfRepeaterbookCom,
                                style: TextStyle(
                                  color: Colors.black54,
                                  fontSize: 11,
                                ),
                              ),
                            ),
                          SizedBox(
                            key: const Key('repeater-results-area'),
                            height: resultsHeight,
                            child: results == null
                                ? const Center(
                                    child: Icon(
                                      Icons.travel_explore,
                                      size: 48,
                                      color: Colors.black26,
                                    ),
                                  )
                                : _mapView
                                ? _buildResultsMap(context, visibleResults)
                                : Padding(
                                    // Keep this bar clear of the page's own
                                    // scroll bar at the dialog edge, which
                                    // otherwise caught the drag.
                                    padding: const EdgeInsets.only(right: 16),
                                    child: Scrollbar(
                                      controller: _resultsScrollController,
                                      thumbVisibility: true,
                                      interactive: true,
                                      child: ScrollConfiguration(
                                        behavior: ScrollConfiguration.of(
                                          context,
                                        ).copyWith(scrollbars: false),
                                        child: ListView.separated(
                                          controller: _resultsScrollController,
                                          itemCount: visibleResults.length,
                                          separatorBuilder: (_, _) =>
                                              const Divider(height: 1),
                                          itemBuilder: (context, index) {
                                            final result =
                                                visibleResults[index];
                                            return CheckboxListTile(
                                              dense: true,
                                              contentPadding:
                                                  const EdgeInsets.symmetric(
                                                    horizontal: 4,
                                                  ),
                                              value: _selected.contains(result),
                                              onChanged: (selected) {
                                                setState(() {
                                                  if (selected == true) {
                                                    _selected.add(result);
                                                  } else {
                                                    _selected.remove(result);
                                                  }
                                                });
                                              },
                                              title: Text(
                                                result.callsign.isEmpty
                                                    ? result.channel.name
                                                    : '${result.callsign} — ${result.channel.name}',
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                              subtitle: Text(
                                                _channelDetail(result),
                                                maxLines: 2,
                                                overflow: TextOverflow.ellipsis,
                                              ),
                                            );
                                          },
                                        ),
                                      ),
                                    ),
                                  ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton(
                        onPressed: _loading
                            ? null
                            : () => Navigator.pop(context),
                        child: Text(context.l10n.close),
                      ),
                      const SizedBox(width: 8),
                      FilledButton.tonalIcon(
                        onPressed:
                            _loading ||
                                (_provider == _RepeaterProvider.myGmrs &&
                                    !_myGmrs.signedIn)
                            ? null
                            : _search,
                        icon: const Icon(Icons.search),
                        label: Text(context.l10n.search),
                      ),
                      const SizedBox(width: 8),
                      FilledButton.icon(
                        onPressed: _selected.isEmpty || _loading
                            ? null
                            : () => Navigator.pop(context, _selectedChannels),
                        icon: const Icon(Icons.add),
                        label: Text(
                          _selected.isEmpty
                              ? context.l10n.uiAddSelected
                              : context.l10n.uiAddSelected2(_selected.length),
                        ),
                      ),
                      const SizedBox(width: 18),
                    ],
                  ),
                ],
              ),
            ),
            Positioned(
              top: 36,
              right: 0,
              bottom: 36,
              width: 12,
              child: MouseRegion(
                cursor: SystemMouseCursors.resizeLeftRight,
                child: GestureDetector(
                  key: const Key('repeater-book-width-handle'),
                  behavior: HitTestBehavior.opaque,
                  onHorizontalDragUpdate: (details) =>
                      resizeBy(details.delta.dx, 0),
                  child: Center(
                    child: Container(
                      width: 3,
                      height: 42,
                      decoration: BoxDecoration(
                        color: const Color(0x6639725C),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            Positioned(
              left: 36,
              right: 36,
              bottom: 0,
              height: 12,
              child: MouseRegion(
                cursor: SystemMouseCursors.resizeUpDown,
                child: GestureDetector(
                  key: const Key('repeater-book-height-handle'),
                  behavior: HitTestBehavior.opaque,
                  onVerticalDragUpdate: (details) =>
                      resizeBy(0, details.delta.dy),
                  child: Center(
                    child: Container(
                      width: 42,
                      height: 3,
                      decoration: BoxDecoration(
                        color: const Color(0x6639725C),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            Positioned(
              right: 0,
              bottom: 0,
              child: MouseRegion(
                cursor: SystemMouseCursors.resizeDownRight,
                child: Tooltip(
                  message: context.l10n.uiDragToResize,
                  child: GestureDetector(
                    key: const Key('repeater-book-corner-handle'),
                    behavior: HitTestBehavior.opaque,
                    onPanUpdate: (details) =>
                        resizeBy(details.delta.dx, details.delta.dy),
                    child: Container(
                      width: 30,
                      height: 30,
                      decoration: const BoxDecoration(
                        color: Color(0xEEF1F8F4),
                        borderRadius: BorderRadius.only(
                          topLeft: Radius.circular(8),
                          bottomRight: Radius.circular(12),
                        ),
                      ),
                      child: const Icon(
                        Icons.open_in_full_rounded,
                        size: 18,
                        color: Color(0xFF39725C),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HelpButton extends StatelessWidget {
  const _HelpButton({required this.title, required this.details});

  final String title;
  final String details;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: details,
      waitDuration: const Duration(milliseconds: 400),
      child: IconButton(
        visualDensity: VisualDensity.compact,
        iconSize: 18,
        color: const Color(0xFF39725C),
        icon: const Icon(Icons.help_outline),
        onPressed: () => showDialog<void>(
          context: context,
          builder: (context) => AlertDialog(
            icon: const Icon(Icons.help_outline),
            title: Text(title),
            content: SelectableText(details),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(context.l10n.close),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WelcomeAction extends StatelessWidget {
  const _WelcomeAction({
    required this.width,
    required this.icon,
    required this.title,
    required this.description,
    required this.buttonLabel,
    required this.onPressed,
    this.help,
  });

  final double width;
  final IconData icon;
  final String title;
  final String description;
  final String buttonLabel;
  final VoidCallback onPressed;
  final String? help;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: width,
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                color: const Color(0xFFEAF4EF),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: const Color(0xFF1F7455)),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                if (help != null) _HelpButton(title: title, details: help!),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              description,
              style: const TextStyle(color: Colors.black54, height: 1.4),
            ),
            const SizedBox(height: 18),
            FilledButton.tonal(onPressed: onPressed, child: Text(buttonLabel)),
          ],
        ),
      ),
    ),
  );
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value, required this.icon});
  final String label;
  final String value;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Expanded(
    child: Card(
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Row(
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: const Color(0xFFEAF4EF),
                borderRadius: BorderRadius.circular(9),
              ),
              child: Icon(icon, color: const Color(0xFF1F7455), size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Colors.black54, fontSize: 12),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

enum _ChannelSelectionMode { replace, toggle, range }

class _SelectAllChannelsIntent extends Intent {
  const _SelectAllChannelsIntent();
}

/// Disabled (so the key falls through to text select-all) unless the
/// channel table can take the selection.
class _SelectAllChannelsAction extends Action<_SelectAllChannelsIntent> {
  _SelectAllChannelsAction({required this.enabled, required this.onInvoke});

  final bool Function() enabled;
  final VoidCallback onInvoke;

  @override
  bool isEnabled(_SelectAllChannelsIntent intent) => enabled();

  @override
  Object? invoke(_SelectAllChannelsIntent intent) {
    onInvoke();
    return null;
  }
}

class _ChannelColumn {
  _ChannelColumn(this.label, this.width, this.value, {String? id, this.help})
    : id = id ?? label;
  final String id;
  final String label;
  double width;
  final String Function(RadioChannel) value;
  final String? help;
}

// Column ids stay English: saved column layouts and filters key on them.
String _channelColumnTitle(AppLocalizations l10n, _ChannelColumn column) =>
    switch (column.label) {
      'BANK' => l10n.colBank,
      'NAME' => l10n.colName,
      'RX FREQUENCY' => l10n.colRxFrequency,
      'TONE MODE' => l10n.colToneMode,
      'TX TONE' => l10n.colTxTone,
      'RX TONE' => l10n.colRxTone,
      'DTCS' => l10n.colDtcs,
      'RX DTCS' => l10n.colRxDtcs,
      'DTCS POL' => l10n.colDtcsPol,
      'DUPLEX' => l10n.colDuplex,
      'OFFSET / TX FREQ' => l10n.colOffset,
      'CROSS MODE' => l10n.colCrossMode,
      'MODE' => l10n.colMode,
      'STEP' => l10n.colStep,
      'POWER' => l10n.colPower,
      'SCAN' => l10n.colScan,
      'COMMENT' => l10n.colComment,
      _ => column.label,
    };

String? _channelColumnHelp(AppLocalizations l10n, _ChannelColumn column) {
  final help = column.help;
  if (help == null) return null;
  return switch (help) {
    'Memory channel number or slot stored in the radio.' => l10n.helpNumber,
    'Midland channel number. Repeater rows are labeled RPTR.' =>
      l10n.helpNumberMidland,
    'Bank or zone membership reported by the selected radio. A green boundary marks the start of each bank.' =>
      l10n.helpBank,
    'Channel name stored in the radio memory.' => l10n.helpName,
    'Receive frequency: the frequency the radio listens on.' =>
      l10n.helpRxFrequency,
    'Receive/transmit squelch mode. Tone is CTCSS, TSQL is tone squelch, DTCS is a digital code, and Cross uses different tones.' =>
      l10n.helpToneMode,
    'Transmit CTCSS tone in hertz. TSQL uses the same CTCSS tone for transmit and receive.' =>
      l10n.helpTxTone,
    'Receive CTCSS tone in hertz. Set Tone Mode to TSQL or a matching Cross mode first.' =>
      l10n.helpRxTone,
    'Transmit DTCS digital squelch code.' => l10n.helpDtcs,
    'Receive DTCS digital squelch code.' => l10n.helpRxDtcs,
    'DTCS polarity: normal or inverted for transmit and receive.' =>
      l10n.helpDtcsPol,
    'Transmit/receive relationship. Simplex uses one frequency; offsets or split use different transmit frequencies.' =>
      l10n.helpDuplex,
    'Frequency offset, or the independent transmit frequency for split.' =>
      l10n.helpOffset,
    'Separate receive and transmit tone/code modes used with Cross.' =>
      l10n.helpCrossMode,
    'Voice modulation: FM, narrowband FM, or AM depending on the radio.' =>
      l10n.helpMode,
    'Tuning step size in kHz.' => l10n.helpStep,
    'Selected transmit power level.' => l10n.helpPower,
    'Whether the channel is included in scanning.' => l10n.helpScan,
    'Free-form notes stored with the channel when supported.' =>
      l10n.helpComment,
    'Radio-specific channel setting reported by the CHIRP driver.' =>
      l10n.helpExtra,
    _ => help,
  };
}

class _ChannelTable extends StatefulWidget {
  const _ChannelTable({
    super.key,
    required this.entries,
    required this.selected,
    required this.selectedLocations,
    required this.radioModel,
    required this.capabilities,
    required this.columnOrder,
    required this.columnWidths,
    required this.onColumnOrderChanged,
    required this.onColumnWidthChanged,
    required this.filterValues,
    required this.onFilterChanged,
    required this.bankLabels,
    required this.onSelect,
    required this.clipboardCount,
    required this.onCopy,
    required this.onCut,
    required this.onPaste,
    required this.onDuplicate,
    required this.onClear,
    required this.onMove,
    required this.onInsertEmptyBefore,
    required this.onRemoveEmpty,
    required this.onBulkEdit,
    required this.reorderEnabled,
    required this.reorderDisabledMessage,
    required this.onOpen,
  });

  final List<MapEntry<int, RadioChannel>> entries;
  final int selected;
  final Set<int> selectedLocations;
  final String? radioModel;
  final RadioCapabilities? capabilities;
  final List<String> columnOrder;
  final Map<String, double> columnWidths;
  final ValueChanged<List<String>> onColumnOrderChanged;
  final void Function(String id, double width) onColumnWidthChanged;
  final Map<String, String> filterValues;
  final void Function(String id, String value) onFilterChanged;
  final Map<int, String> bankLabels;
  final void Function(int location, _ChannelSelectionMode mode) onSelect;
  final int clipboardCount;
  final ValueChanged<int> onCopy;
  final ValueChanged<int> onCut;
  final Future<void> Function(int) onPaste;
  final ValueChanged<int> onDuplicate;
  final ValueChanged<int> onClear;
  final void Function(int fromIndex, int toIndex) onMove;
  final ValueChanged<int> onInsertEmptyBefore;
  final ValueChanged<int> onRemoveEmpty;
  final VoidCallback onBulkEdit;
  final bool reorderEnabled;
  final String reorderDisabledMessage;
  final ValueChanged<int> onOpen;

  @override
  State<_ChannelTable> createState() => _ChannelTableState();
}

class _ChannelTableState extends State<_ChannelTable> {
  final _horizontalController = ScrollController();
  final _verticalController = ScrollController();
  final Map<String, double> _workingWidths = {};
  final Map<String, double> _resizeStartX = {};
  final Map<String, double> _resizeStartWidth = {};
  final Map<String, TextEditingController> _filterControllers = {};

  @override
  void didUpdateWidget(covariant _ChannelTable oldWidget) {
    super.didUpdateWidget(oldWidget);
    final ids = {...oldWidget.filterValues.keys, ...widget.filterValues.keys};
    for (final id in ids) {
      final value = widget.filterValues[id] ?? '';
      final controller = _filterControllers[id];
      if (controller != null && controller.text != value) {
        controller.value = TextEditingValue(
          text: value,
          selection: TextSelection.collapsed(offset: value.length),
        );
      }
    }
  }

  void revealSelectedChannel() {
    if (!_verticalController.hasClients) return;
    final position = _verticalController.position;
    final selectedIndex = widget.entries.indexWhere(
      (entry) => entry.key == widget.selected,
    );
    if (selectedIndex < 0) return;
    final rowsAfter = widget.entries.length - selectedIndex - 1;
    final target = rowsAfter < 2
        ? position.maxScrollExtent
        : (selectedIndex * 45.0 - position.viewportDimension + 90)
              .clamp(0.0, position.maxScrollExtent)
              .toDouble();
    if ((position.pixels - target).abs() < 1) return;
    unawaited(
      _verticalController
          .animateTo(
            target,
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeOutCubic,
          )
          .then((_) {
            if (mounted) revealSelectedChannel();
          }),
    );
  }

  @override
  void dispose() {
    _horizontalController.dispose();
    _verticalController.dispose();
    for (final controller in _filterControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  void _showRowMenu(BuildContext context, int index, Offset position) {
    final isCleared = widget.entries.any(
      (entry) => entry.key == index && entry.value.cleared,
    );
    if (!widget.selectedLocations.contains(index)) {
      widget.onSelect(index, _ChannelSelectionMode.replace);
    }
    final multiSelected =
        widget.selectedLocations.length > 1 &&
        widget.selectedLocations.contains(index);
    showMenu<int>(
      context: context,
      position: RelativeRect.fromLTRB(
        position.dx,
        position.dy,
        position.dx,
        position.dy,
      ),
      items: [
        PopupMenuItem(
          value: 7,
          enabled: !isCleared,
          child: Text(
            multiSelected
                ? context.l10n.uiEditSelectedProperties
                : 'Properties',
          ),
        ),
        const PopupMenuDivider(),
        PopupMenuItem(
          value: 0,
          enabled: !isCleared,
          child: Text(
            multiSelected
                ? context.l10n.uiCopyChannels(widget.selectedLocations.length)
                : 'Copy',
          ),
        ),
        PopupMenuItem(
          value: 1,
          enabled: !isCleared,
          child: Text(
            multiSelected
                ? context.l10n.uiCutChannels(widget.selectedLocations.length)
                : 'Cut',
          ),
        ),
        PopupMenuItem(
          value: 2,
          enabled: widget.clipboardCount > 0,
          child: Text(
            widget.clipboardCount > 1
                ? context.l10n.uiPasteChannels(widget.clipboardCount)
                : 'Paste',
          ),
        ),
        PopupMenuItem(
          value: 3,
          enabled: !isCleared,
          child: Text(context.l10n.duplicate),
        ),
        PopupMenuItem(
          value: 5,
          enabled: !isCleared && widget.reorderEnabled,
          child: Text(context.l10n.uiInsertEmptySlotBefore),
        ),
        PopupMenuItem(
          value: 6,
          enabled: isCleared && widget.reorderEnabled,
          child: Text(context.l10n.uiRemoveEmptySlot),
        ),
        PopupMenuItem(
          value: 4,
          enabled: !isCleared,
          child: Text(
            multiSelected
                ? context.l10n.uiClearSelectedChannels(
                    widget.selectedLocations.length,
                  )
                : context.l10n.uiClearChannel,
          ),
        ),
      ],
    ).then((value) {
      switch (value) {
        case 7:
          if (multiSelected) {
            widget.onBulkEdit();
          } else {
            widget.onOpen(index);
          }
          break;
        case 0:
          widget.onCopy(index);
          break;
        case 1:
          widget.onCut(index);
          break;
        case 2:
          unawaited(widget.onPaste(index));
          break;
        case 3:
          widget.onDuplicate(index);
          break;
        case 4:
          widget.onClear(index);
          break;
        case 5:
          widget.onInsertEmptyBefore(index);
          break;
        case 6:
          widget.onRemoveEmpty(index);
          break;
      }
    });
  }

  List<_ChannelColumn> _columns() {
    String inactive(bool active, Object value) => active ? '$value' : '—';
    final showStep = widget.capabilities?.hasTuningStep ?? true;
    final columns = <_ChannelColumn>[
      _ChannelColumn(
        '#',
        showsMidlandChannelNumbers(widget.radioModel) ? 96 : 52,
        (channel) => channelNumberLabel(widget.radioModel, channel.location),
        help: showsMidlandChannelNumbers(widget.radioModel)
            ? 'Midland channel number. Repeater rows are labeled RPTR.'
            : 'Memory channel number or slot stored in the radio.',
      ),
      if (widget.bankLabels.isNotEmpty)
        _ChannelColumn(
          'BANK',
          138,
          (channel) => widget.bankLabels[channel.location] ?? '—',
          help: context.l10n.helpBank,
        ),
      _ChannelColumn(
        'NAME',
        160,
        (channel) => channel.name.isEmpty ? '—' : channel.name,
        help: context.l10n.helpName,
      ),
      _ChannelColumn(
        'RX FREQUENCY',
        126,
        (channel) =>
            channel.frequency <= 0 ? '' : channel.frequency.toStringAsFixed(6),
        help: context.l10n.helpRxFrequency,
      ),
      _ChannelColumn(
        'TONE MODE',
        96,
        (channel) => channel.tone.isEmpty ? 'None' : channel.tone,
        help: context.l10n.helpToneMode,
      ),
      _ChannelColumn('TX TONE', 82, (channel) {
        final tone = effectiveTransmitCtcssTone(channel);
        return tone == null ? '—' : tone.toStringAsFixed(1);
      }, help: context.l10n.helpTxTone),
      _ChannelColumn('RX TONE', 82, (channel) {
        final tone = effectiveReceiveCtcssTone(channel);
        return tone == null ? '—' : tone.toStringAsFixed(1);
      }, help: context.l10n.helpRxTone),
      _ChannelColumn(
        'DTCS',
        66,
        (channel) => inactive(
          channel.tone == 'DTCS' ||
              (channel.tone == 'Cross' && channel.crossMode.startsWith('DTCS')),
          channel.dtcs.toString().padLeft(3, '0'),
        ),
        help: context.l10n.helpDtcs,
      ),
      _ChannelColumn(
        'RX DTCS',
        76,
        (channel) => inactive(
          channel.tone == 'DTCS' ||
              (channel.tone == 'Cross' && channel.crossMode.endsWith('DTCS')),
          (channel.tone == 'DTCS' ? channel.dtcs : channel.rxDtcs)
              .toString()
              .padLeft(3, '0'),
        ),
        help: context.l10n.helpRxDtcs,
      ),
      _ChannelColumn(
        'DTCS POL',
        76,
        (channel) => inactive(
          channel.tone == 'DTCS' ||
              (channel.tone == 'Cross' && channel.crossMode.contains('DTCS')),
          channel.dtcsPolarity,
        ),
        help: context.l10n.helpDtcsPol,
      ),
      _ChannelColumn(
        'DUPLEX',
        82,
        (channel) => channel.duplex.isEmpty ? 'Simplex' : channel.duplex,
        help: context.l10n.helpDuplex,
      ),
      _ChannelColumn(
        'OFFSET / TX FREQ',
        132,
        (channel) => inactive(
          channel.duplex.isNotEmpty && channel.duplex != 'off',
          channel.offset.toStringAsFixed(6),
        ),
        help: context.l10n.helpOffset,
      ),
      _ChannelColumn(
        'CROSS MODE',
        112,
        (channel) => inactive(channel.tone == 'Cross', channel.crossMode),
        help: context.l10n.helpCrossMode,
      ),
      _ChannelColumn(
        'MODE',
        68,
        (channel) => channel.mode,
        help: context.l10n.helpMode,
      ),
      if (showStep)
        _ChannelColumn(
          'STEP',
          68,
          (channel) => channel.step.toStringAsFixed(2),
          help: context.l10n.helpStep,
        ),
      _ChannelColumn(
        'POWER',
        82,
        (channel) => channel.power.isEmpty ? '—' : channel.power,
        help: context.l10n.helpPower,
      ),
      _ChannelColumn(
        'SCAN',
        72,
        (channel) => scanLabel(channel.skip),
        help: context.l10n.helpScan,
      ),
      _ChannelColumn(
        'COMMENT',
        210,
        (channel) => channel.comment.isEmpty ? '—' : channel.comment,
        help: context.l10n.helpComment,
      ),
    ];

    final extras = <String, ChannelExtraField>{};
    for (final entry in widget.entries) {
      for (final field in entry.value.extras) {
        final current = extras[field.name];
        if (current == null ||
            (current.documentation == null && field.documentation != null)) {
          extras[field.name] = field;
        }
      }
    }
    for (final extra in extras.entries) {
      columns.add(
        _ChannelColumn(
          extra.value.label.toUpperCase(),
          96,
          (channel) {
            final matches = channel.extras.where(
              (field) => field.name == extra.key,
            );
            if (matches.isEmpty) return '—';
            final value = matches.first.value;
            if (value is bool) return value ? 'On' : 'Off';
            return value?.toString() ?? '—';
          },
          id: 'extra:${extra.key}',
          help:
              extra.value.documentation ??
              'Radio-specific channel setting reported by the CHIRP driver.',
        ),
      );
    }
    final baseOrder = {
      for (var index = 0; index < columns.length; index++)
        columns[index].id: index,
    };
    final configuredOrder = {
      for (var index = 0; index < widget.columnOrder.length; index++)
        widget.columnOrder[index]: index,
    };
    for (final column in columns) {
      column.width =
          _workingWidths[column.id] ??
          widget.columnWidths[column.id] ??
          column.width;
    }
    columns.sort((left, right) {
      final leftRank = configuredOrder[left.id];
      final rightRank = configuredOrder[right.id];
      if (leftRank != null && rightRank != null) {
        return leftRank.compareTo(rightRank);
      }
      if (leftRank != null) return -1;
      if (rightRank != null) return 1;
      return baseOrder[left.id]!.compareTo(baseOrder[right.id]!);
    });
    return columns;
  }

  void _moveColumn(
    String draggedId,
    String targetId,
    List<_ChannelColumn> columns,
  ) {
    if (draggedId == targetId) return;
    final order = columns.map((column) => column.id).toList();
    order.remove(draggedId);
    final targetIndex = order.indexOf(targetId);
    order.insert(targetIndex < 0 ? order.length : targetIndex, draggedId);
    widget.onColumnOrderChanged(order);
  }

  Widget _headerCell(_ChannelColumn column, List<_ChannelColumn> columns) {
    Widget label({Color? color}) => Container(
      color: color,
      alignment: Alignment.centerLeft,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      child: Text(
        _channelColumnTitle(context.l10n, column),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(fontSize: 12),
      ),
    );

    return DragTarget<String>(
      onWillAcceptWithDetails: (details) => details.data != column.id,
      onAcceptWithDetails: (details) =>
          _moveColumn(details.data, column.id, columns),
      builder: (context, candidates, rejected) => SizedBox(
        width: column.width,
        height: 42,
        child: Stack(
          children: [
            Positioned.fill(
              right: 8,
              child: Tooltip(
                message: _channelColumnHelp(context.l10n, column) == null
                    ? context.l10n.dragToReorder
                    : '${_channelColumnHelp(context.l10n, column)}\n\n'
                          '${context.l10n.dragToReorder}',
                waitDuration: const Duration(milliseconds: 350),
                child: Draggable<String>(
                  data: column.id,
                  axis: Axis.horizontal,
                  feedback: Material(
                    elevation: 4,
                    color: const Color(0xFFE8F3ED),
                    child: SizedBox(
                      width: column.width,
                      height: 42,
                      child: label(),
                    ),
                  ),
                  childWhenDragging: Opacity(opacity: 0.35, child: label()),
                  child: label(
                    color: candidates.isEmpty ? null : const Color(0xFFD7EAE1),
                  ),
                ),
              ),
            ),
            Positioned(
              right: 0,
              top: 0,
              bottom: 0,
              width: 8,
              child: MouseRegion(
                cursor: SystemMouseCursors.resizeColumn,
                child: GestureDetector(
                  key: ValueKey('resize-${column.id}'),
                  behavior: HitTestBehavior.opaque,
                  onHorizontalDragDown: (details) {
                    _resizeStartX[column.id] = details.globalPosition.dx;
                    _resizeStartWidth[column.id] = column.width;
                  },
                  onHorizontalDragUpdate: (details) {
                    final startX =
                        _resizeStartX[column.id] ?? details.globalPosition.dx;
                    final startWidth =
                        _resizeStartWidth[column.id] ?? column.width;
                    final width =
                        (startWidth + details.globalPosition.dx - startX)
                            .clamp(48.0, 480.0)
                            .toDouble();
                    setState(() => _workingWidths[column.id] = width);
                  },
                  onHorizontalDragEnd: (_) {
                    final width = _workingWidths[column.id] ?? column.width;
                    widget.onColumnWidthChanged(column.id, width);
                    _resizeStartX.remove(column.id);
                    _resizeStartWidth.remove(column.id);
                  },
                  child: const Align(
                    alignment: Alignment.centerRight,
                    child: VerticalDivider(
                      width: 1,
                      thickness: 1,
                      color: Color(0xFFD8DEDA),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _channelRow(
    BuildContext context,
    MapEntry<int, RadioChannel> entry,
    List<_ChannelColumn> columns,
    double dragHandleWidth, {
    required bool startsEmptyGroup,
    required bool endsEmptyGroup,
    required bool startsBank,
  }) {
    final isCleared = entry.value.cleared;
    final canDrag = widget.reorderEnabled && !isCleared;
    final dragLabel = entry.value.name.isEmpty
        ? 'Channel ${channelNumberLabel(widget.radioModel, entry.value.location)}'
        : entry.value.name;
    return DragTarget<int>(
      key: ValueKey('channel-slot-${entry.key}'),
      onWillAcceptWithDetails: (details) =>
          widget.reorderEnabled && details.data != entry.key,
      onAcceptWithDetails: (details) => widget.onMove(details.data, entry.key),
      builder: (context, candidates, rejected) {
        final isDropTarget = candidates.isNotEmpty;
        return Listener(
          behavior: HitTestBehavior.opaque,
          onPointerDown: (event) {
            if (event.buttons & kSecondaryMouseButton != 0) return;
            final keyboard = HardwareKeyboard.instance;
            final mode = keyboard.isShiftPressed
                ? _ChannelSelectionMode.range
                : keyboard.isControlPressed || keyboard.isMetaPressed
                ? _ChannelSelectionMode.toggle
                : _ChannelSelectionMode.replace;
            widget.onSelect(entry.key, mode);
          },
          child: GestureDetector(
            onSecondaryTapDown: (details) =>
                _showRowMenu(context, entry.key, details.globalPosition),
            child: Tooltip(
              message: isCleared
                  ? context.l10n.uiEmptyMemorySlotDoubleClickTo
                  : context.l10n.uiDoubleClickToEditChannel,
              child: InkWell(
                onDoubleTap: () => widget.onOpen(entry.key),
                child: Container(
                  height: 45,
                  color: isDropTarget
                      ? const Color(0xFFD7EAE1)
                      : widget.selectedLocations.contains(entry.key)
                      ? const Color(0xFFE8F3ED)
                      : isCleared
                      ? const Color(0xFFFAFAFA)
                      : Colors.white,
                  foregroundDecoration: BoxDecoration(
                    border: Border(
                      top: startsBank
                          ? const BorderSide(color: Color(0xFF1F7455), width: 2)
                          : startsEmptyGroup
                          ? const BorderSide(color: Color(0xFFD8DEDA))
                          : BorderSide.none,
                      bottom: endsEmptyGroup
                          ? const BorderSide(color: Color(0xFFD8DEDA))
                          : BorderSide.none,
                    ),
                  ),
                  child: Row(
                    children: [
                      SizedBox(
                        width: dragHandleWidth,
                        child: Draggable<int>(
                          data: entry.key,
                          maxSimultaneousDrags: canDrag ? 1 : 0,
                          onDragStarted: () => widget.onSelect(
                            entry.key,
                            _ChannelSelectionMode.replace,
                          ),
                          feedback: Material(
                            elevation: 6,
                            color: const Color(0xFF1F7455),
                            borderRadius: BorderRadius.circular(8),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 9,
                              ),
                              child: Text(
                                context.l10n.uiMove(dragLabel),
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                          childWhenDragging: Opacity(
                            opacity: 0.3,
                            child: Icon(
                              Icons.drag_indicator,
                              size: 18,
                              color: Colors.grey.shade500,
                            ),
                          ),
                          child: MouseRegion(
                            cursor: canDrag
                                ? SystemMouseCursors.grab
                                : SystemMouseCursors.basic,
                            child: Tooltip(
                              message: canDrag
                                  ? context.l10n.uiDragToRearrangeChannel
                                  : widget.reorderDisabledMessage,
                              child: Icon(
                                Icons.drag_indicator,
                                size: 18,
                                color: canDrag
                                    ? Colors.black45
                                    : Colors.black26,
                              ),
                            ),
                          ),
                        ),
                      ),
                      for (final column in columns)
                        SizedBox(
                          width: column.width,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 10),
                            child: Align(
                              alignment: Alignment.centerLeft,
                              child: Text(
                                isCleared
                                    ? column.label == '#'
                                          ? column.value(entry.value)
                                          : column.label == 'NAME'
                                          ? context.l10n.uiEmptySlot
                                          : '—'
                                    : column.value(entry.value),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontWeight: column.label == 'NAME'
                                      ? isCleared
                                            ? FontWeight.w400
                                            : FontWeight.w600
                                      : FontWeight.w400,
                                  fontStyle: isCleared && column.label == 'NAME'
                                      ? FontStyle.italic
                                      : null,
                                  color: isCleared
                                      ? Colors.black38
                                      : column.label == '#'
                                      ? Colors.black54
                                      : null,
                                  fontFeatures: column.label == 'RX FREQUENCY'
                                      ? const [FontFeature.tabularFigures()]
                                      : null,
                                ),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    const dragHandleWidth = 30.0;
    final columns = _columns();
    final tableWidth =
        dragHandleWidth +
        columns.fold<double>(0, (sum, column) => sum + column.width);
    return LayoutBuilder(
      builder: (context, constraints) => Scrollbar(
        key: const ValueKey('channel-vertical-scrollbar'),
        controller: _verticalController,
        thumbVisibility: true,
        scrollbarOrientation: ScrollbarOrientation.right,
        notificationPredicate: (notification) =>
            notification.metrics.axis == Axis.vertical,
        child: Scrollbar(
          key: const ValueKey('channel-horizontal-scrollbar'),
          controller: _horizontalController,
          thumbVisibility: true,
          scrollbarOrientation: ScrollbarOrientation.bottom,
          notificationPredicate: (notification) =>
              notification.metrics.axis == Axis.horizontal,
          child: SingleChildScrollView(
            controller: _horizontalController,
            scrollDirection: Axis.horizontal,
            child: SizedBox(
              width: tableWidth,
              height: constraints.maxHeight,
              child: Column(
                children: [
                  ColoredBox(
                    color: const Color(0xFFF3F6F4),
                    child: Row(
                      children: [
                        SizedBox(
                          width: dragHandleWidth,
                          child: Tooltip(
                            message: context.l10n.uiDragRowsToRearrangeChannels,
                            child: Icon(
                              Icons.drag_indicator,
                              size: 18,
                              color: Colors.black45,
                            ),
                          ),
                        ),
                        for (final column in columns)
                          _headerCell(column, columns),
                      ],
                    ),
                  ),
                  ColoredBox(
                    color: const Color(0xFFFAFCFB),
                    child: Row(
                      children: [
                        const SizedBox(
                          width: dragHandleWidth,
                          height: 38,
                          child: Icon(
                            Icons.filter_alt_outlined,
                            size: 16,
                            color: Colors.black45,
                          ),
                        ),
                        for (final column in columns)
                          SizedBox(
                            width: column.width,
                            height: 38,
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(6, 4, 6, 4),
                              child: TextField(
                                key: ValueKey(
                                  'channel-column-filter-${column.id}',
                                ),
                                controller: _filterControllers.putIfAbsent(
                                  column.id,
                                  () => TextEditingController(
                                    text: widget.filterValues[column.id] ?? '',
                                  ),
                                ),
                                onChanged: (value) =>
                                    widget.onFilterChanged(column.id, value),
                                style: const TextStyle(fontSize: 11),
                                decoration: InputDecoration(
                                  isDense: true,
                                  hintText: context.l10n.uiFilter,
                                  contentPadding: EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 7,
                                  ),
                                  border: OutlineInputBorder(),
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: ListView.builder(
                      controller: _verticalController,
                      itemExtent: 45,
                      itemCount: widget.entries.length,
                      itemBuilder: (context, index) {
                        final entry = widget.entries[index];
                        final previous = index > 0
                            ? widget.entries[index - 1].value
                            : null;
                        final next = index + 1 < widget.entries.length
                            ? widget.entries[index + 1].value
                            : null;
                        final bank = widget.bankLabels[entry.key];
                        final previousBank = previous == null
                            ? null
                            : widget.bankLabels[previous.location];
                        return _channelRow(
                          context,
                          entry,
                          columns,
                          dragHandleWidth,
                          startsEmptyGroup:
                              entry.value.cleared &&
                              (previous == null || !previous.cleared),
                          endsEmptyGroup:
                              entry.value.cleared &&
                              (next == null || !next.cleared),
                          startsBank:
                              bank != null &&
                              !entry.value.cleared &&
                              bank != previousBank,
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 10),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ChannelEditor extends StatelessWidget {
  const _ChannelEditor({
    required this.channel,
    required this.radioModel,
    required this.capabilities,
    required this.onChanged,
    required this.onSave,
    required this.onDelete,
    required this.onClose,
    this.title,
    this.notice,
    this.saveLabel,
    this.showLocation = true,
    this.canDelete = true,
    this.canSave,
    this.enteringFrequency = false,
    this.onEnteringFrequency,
  });
  final RadioChannel channel;
  final String? radioModel;
  final RadioCapabilities? capabilities;
  final String? title;
  final String? notice;
  final String? saveLabel;
  final bool showLocation;
  final bool enteringFrequency;
  final ValueChanged<bool>? onEnteringFrequency;
  final void Function(VoidCallback) onChanged;
  final VoidCallback onSave;
  final VoidCallback onDelete;
  final VoidCallback onClose;
  final bool canDelete;
  final bool Function()? canSave;

  @override
  Widget build(BuildContext context) {
    final gm32 = isBaofengGm32(radioModel);
    final narrowLow = gm32 && gm32RequiresNarrowLow(channel);
    final issues = channel.validate(
      minimumLocation: capabilities?.memoryStart,
      maximumLocation: capabilities?.memoryEnd,
      maximumNameLength: capabilities?.nameLength,
      radioModel: radioModel,
      validTuningSteps: capabilities?.frequencyGridSteps ?? const [],
      validBands: capabilities?.validBands ?? const [],
      validModes: capabilities?.modes ?? const [],
      hasTuningStep: capabilities?.hasTuningStep ?? true,
    );
    final midland = showsMidlandChannelNumbers(radioModel);
    final receiveLocked =
        midland && midlandReceiveChannelIsLocked(channel.location);
    final duplexLocked =
        midland &&
        midlandDuplexIsLocked(
          channel.location,
          frequencyMhz: channel.frequency,
        );
    if (gm32 && gm32FrequencyIsUnset(channel.frequency)) {
      issues.removeWhere((issue) => issue.startsWith('Frequency must be'));
    }
    if (gm32) issues.addAll(gm32ChannelIssues(radioModel, channel));
    final receiveValue = gm32
        ? gm32ReceiveValue(channel, enteringFrequency: enteringFrequency)
        : '';
    final showManualFrequency =
        !gm32 || receiveValue == gm32ManualFrequencyValue;
    final receiveOnly =
        gm32 &&
        channel.duplex == 'off' &&
        !gm32FrequencyIsUnset(channel.frequency) &&
        gmrsChannelNumber(channel) == null &&
        !isGmrsRepeaterInputHz((channel.frequency * 1000000).round());
    final blocking = <String>[
      if (midland) ...midlandGmrsIssues(radioModel, channel),
      if (gm32) ...gm32ChannelIssues(radioModel, channel),
    ];
    Map<String, String> choices(
      List<String>? values,
      Map<String, String> fallback, {
      String? emptyLabel,
    }) {
      if (values == null || values.isEmpty) return fallback;
      return {
        for (final value in values)
          value: value.isEmpty ? emptyLabel ?? context.l10n.choiceNone : value,
      };
    }

    final toneModes = choices(capabilities?.toneModes, {
      '': context.l10n.choiceNone,
      'Tone': 'Tone',
      'TSQL': context.l10n.choiceToneSquelch,
      'DTCS': 'DTCS',
      'Cross': 'Cross',
    });
    final availableTones = capabilities?.tones.isNotEmpty == true
        ? capabilities!.tones
        : standardCtcssTones;
    final toneValues = <double>{
      ...availableTones,
      channel.txTone,
      channel.rxTone,
    }.toList()..sort();
    final toneChoices = {
      for (final tone in toneValues)
        tone.toStringAsFixed(1): tone.toStringAsFixed(1),
    };
    final dtcsCodes = {
      ...(capabilities?.dtcsCodes ?? standardDtcsCodes),
      channel.dtcs,
      channel.rxDtcs,
    }.toList()..sort();
    final dtcsChoices = {
      for (final code in dtcsCodes) '$code': code.toString().padLeft(3, '0'),
    };
    final sharedCtcss = hasSharedCtcssTone(channel);
    final usesTxTone =
        channel.tone == 'Tone' ||
        (channel.tone == 'Cross' && channel.crossMode.startsWith('Tone'));
    final usesRxTone =
        channel.tone == 'Cross' && channel.crossMode.endsWith('Tone');
    final usesTxDtcs =
        channel.tone == 'DTCS' ||
        (channel.tone == 'Cross' && channel.crossMode.startsWith('DTCS'));
    final simpleDtcs = channel.tone == 'DTCS';
    final usesRxDtcs =
        channel.tone == 'Cross' && channel.crossMode.endsWith('DTCS');
    final repeaterRow = isMidlandRepeaterRow(radioModel, channel.location);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 16, 10, 12),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    title ?? context.l10n.editorTitle,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => _showAbbreviationGlossary(context),
                  tooltip: context.l10n.tipAbbreviations,
                  icon: const Icon(Icons.menu_book_outlined),
                ),
                if (canDelete)
                  IconButton(
                    onPressed: onDelete,
                    tooltip: repeaterRow
                        ? context.l10n.tipResetRepeater
                        : context.l10n.tipDeleteChannel,
                    icon: Icon(
                      repeaterRow ? Icons.restart_alt : Icons.delete_outline,
                      color: repeaterRow ? null : const Color(0xFF9B3D34),
                    ),
                  ),
                IconButton(
                  onPressed: onClose,
                  tooltip: context.l10n.tipCloseEditor,
                  icon: const Icon(Icons.close),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (notice != null) ...[
                  Container(
                    padding: const EdgeInsets.all(11),
                    decoration: BoxDecoration(
                      color: const Color(0xFFE8F3ED),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(notice!, style: const TextStyle(fontSize: 12)),
                  ),
                  const SizedBox(height: 12),
                ],
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (showLocation) ...[
                      Expanded(
                        child: showsMidlandChannelNumbers(radioModel)
                            ? _TextField(
                                label: context.l10n.fieldChannel,
                                value: channelNumberLabel(
                                  radioModel,
                                  channel.location,
                                ),
                                readOnly: true,
                                onValue: (_) {},
                              )
                            : _NumberField(
                                label: context.l10n.fieldLocation,
                                value: channel.location.toDouble(),
                                decimals: 0,
                                onValue: (v) => onChanged(
                                  () => channel.location = v.toInt(),
                                ),
                              ),
                      ),
                      const SizedBox(width: 10),
                    ],
                    Expanded(
                      flex: showLocation ? 2 : 1,
                      child: _TextField(
                        label: context.l10n.fieldName,
                        value: channel.name,
                        maxLength: capabilities?.nameLength,
                        onValue: (v) => onChanged(() => channel.name = v),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                if (gm32) ...[
                  _ChoiceField(
                    key: ValueKey('gm32-receive-$receiveValue'),
                    label: context.l10n.fieldReceiveChannel,
                    value: receiveValue,
                    choices: gm32ReceiveChoices(
                      channel,
                      enteringFrequency: enteringFrequency,
                    ),
                    onValue: (value) => onChanged(() {
                      final entering = value == gm32ManualFrequencyValue;
                      onEnteringFrequency?.call(entering);
                      if (entering || value.isEmpty) return;
                      final number = int.tryParse(value);
                      if (number != null) {
                        useGm32ReceiveChannel(channel, number);
                      }
                    }),
                  ),
                  const SizedBox(height: 12),
                  if (showManualFrequency)
                    _NumberField(
                      label: context.l10n.fieldReceiveFrequency,
                      value: channel.frequency,
                      decimals: 6,
                      onValue: (v) => onChanged(() {
                        channel.frequency = v;
                        applyGm32Rules(channel);
                      }),
                    ),
                ] else if (midland) ...[
                  _ChoiceField(
                    key: ValueKey(
                      'rx-${channel.location}-${channel.frequency}',
                    ),
                    label: context.l10n.fieldReceiveChannel,
                    value: midlandReceiveChannelValue(
                      channel.location,
                      channel.frequency,
                    ),
                    enabled: !receiveLocked,
                    choices: midlandReceiveChannelChoices(
                      channel.location,
                      channel.frequency,
                    ),
                    onValue: (v) {
                      final picked = int.tryParse(v);
                      if (picked == null) return;
                      onChanged(() => channel.useGmrsReceiveChannel(picked));
                    },
                  ),
                ] else ...[
                  _NumberField(
                    label: context.l10n.fieldReceiveFrequency,
                    value: channel.frequency,
                    decimals: 6,
                    onValue: (v) => onChanged(() => channel.frequency = v),
                  ),
                ],
                const SizedBox(height: 12),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: _ChoiceField(
                        key: midland
                            ? ValueKey(
                                'dup-${channel.location}-${channel.duplex}-${channel.frequency}',
                              )
                            : gm32
                            ? ValueKey(
                                'gm32-duplex-${gm32DuplexChoices(channel).keys.join()}-${channel.duplex}',
                              )
                            : null,
                        label: context.l10n.fieldDuplex,
                        value: channel.duplex,
                        enabled: !duplexLocked,
                        choices: midland
                            ? midlandDuplexChoices(
                                channel.location,
                                channel.duplex,
                                frequencyMhz: channel.frequency,
                              )
                            : gm32
                            ? gm32DuplexChoices(channel)
                            : choices(capabilities?.duplexes, {
                                '': context.l10n.choiceSimplex,
                                '+': context.l10n.choicePlusShift,
                                '-': context.l10n.choiceMinusShift,
                                'split': context.l10n.choiceSplit,
                                'off': context.l10n.choiceTxOff,
                              }, emptyLabel: context.l10n.choiceSimplex),
                        onValue: (v) => onChanged(() {
                          channel.duplex = v;
                          if (midland) channel.offset = v == '+' ? 5 : 0;
                          if (gm32) applyGm32Rules(channel);
                        }),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _NumberField(
                        label: channel.duplex == 'split'
                            ? context.l10n.fieldTxFrequency
                            : context.l10n.fieldOffset,
                        value: channel.offset,
                        decimals: 6,
                        readOnly: midland || gm32,
                        onValue: (v) => onChanged(() => channel.offset = v),
                      ),
                    ),
                  ],
                ),
                if (receiveOnly) ...[
                  const SizedBox(height: 8),
                  Text(
                    context.l10n.gm32ReceiveOnly,
                    style: TextStyle(color: Colors.black54, fontSize: 12),
                  ),
                ],
                const SizedBox(height: 12),
                _ChoiceField(
                  label: context.l10n.fieldToneMode,
                  value: channel.tone,
                  choices: toneModes,
                  onValue: (v) => onChanged(() => channel.tone = v),
                ),
                if (channel.tone == 'Cross') ...[
                  const SizedBox(height: 12),
                  _ChoiceField(
                    label: context.l10n.fieldCrossMode,
                    value: channel.crossMode,
                    choices: choices(capabilities?.crossModes, {
                      'Tone->Tone': 'Tone → Tone',
                      'DTCS->': context.l10n.choiceDtcsToNone,
                      '->DTCS': context.l10n.choiceNoneToDtcs,
                      'Tone->DTCS': 'Tone → DTCS',
                      'DTCS->Tone': 'DTCS → Tone',
                      '->Tone': context.l10n.choiceNoneToTone,
                      'DTCS->DTCS': 'DTCS → DTCS',
                    }),
                    onValue: (v) => onChanged(() => channel.crossMode = v),
                  ),
                ],
                if (sharedCtcss || usesTxTone || usesRxTone) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      if (sharedCtcss)
                        Expanded(
                          child: _ChoiceField(
                            label: context.l10n.fieldCtcssTone,
                            value: channel.rxTone.toStringAsFixed(1),
                            choices: toneChoices,
                            onValue: (v) => onChanged(
                              () => channel.rxTone = double.parse(v),
                            ),
                          ),
                        ),
                      if (usesTxTone)
                        Expanded(
                          child: _ChoiceField(
                            label: context.l10n.fieldTransmitTone,
                            value: channel.txTone.toStringAsFixed(1),
                            choices: toneChoices,
                            onValue: (v) => onChanged(
                              () => channel.txTone = double.parse(v),
                            ),
                          ),
                        ),
                      if (usesTxTone && usesRxTone) const SizedBox(width: 10),
                      if (usesRxTone)
                        Expanded(
                          child: _ChoiceField(
                            label: context.l10n.fieldReceiveTone,
                            value: channel.rxTone.toStringAsFixed(1),
                            choices: toneChoices,
                            onValue: (v) => onChanged(
                              () => channel.rxTone = double.parse(v),
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
                if (usesTxDtcs || usesRxDtcs) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      if (usesTxDtcs)
                        Expanded(
                          child: _ChoiceField(
                            label: simpleDtcs
                                ? context.l10n.fieldDtcsCode
                                : context.l10n.fieldTransmitDtcs,
                            value: '${channel.dtcs}',
                            choices: dtcsChoices,
                            onValue: (v) =>
                                onChanged(() => channel.dtcs = int.parse(v)),
                          ),
                        ),
                      if (usesTxDtcs && usesRxDtcs) const SizedBox(width: 10),
                      if (usesRxDtcs)
                        Expanded(
                          child: _ChoiceField(
                            label: context.l10n.fieldReceiveDtcs,
                            value: '${channel.rxDtcs}',
                            choices: dtcsChoices,
                            onValue: (v) =>
                                onChanged(() => channel.rxDtcs = int.parse(v)),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  _ChoiceField(
                    label: context.l10n.fieldDtcsPolarity,
                    value: channel.dtcsPolarity,
                    choices: {
                      'NN': context.l10n.choiceNormalNormal,
                      'NR': context.l10n.choiceNormalReverse,
                      'RN': context.l10n.choiceReverseNormal,
                      'RR': context.l10n.choiceReverseReverse,
                    },
                    onValue: (v) => onChanged(() => channel.dtcsPolarity = v),
                  ),
                ],
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _ChoiceField(
                        key: narrowLow ? const ValueKey('gm32-mode-nfm') : null,
                        label: context.l10n.fieldMode,
                        value: channel.mode,
                        choices: narrowLow
                            ? const {'NFM': 'NFM'}
                            : choices(capabilities?.modes, {
                                'FM': 'FM',
                                'NFM': 'NFM',
                                'AM': 'AM',
                                'DMR': 'DMR (MOTOTRBO)',
                                'DV': context.l10n.choiceDigitalVoice,
                              }),
                        onValue: (v) => onChanged(() => channel.mode = v),
                      ),
                    ),
                    if (capabilities?.hasTuningStep ?? true) ...[
                      const SizedBox(width: 10),
                      Expanded(
                        child: _ChoiceField(
                          label: context.l10n.fieldStep,
                          value: '${channel.step}',
                          choices: {
                            for (final step
                                in capabilities?.steps ?? [channel.step])
                              '$step': '$step',
                          },
                          onValue: (v) =>
                              onChanged(() => channel.step = double.parse(v)),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 12),
                _ChoiceField(
                  label: context.l10n.fieldScan,
                  value: channel.skip,
                  choices: scanChoices(capabilities?.skips),
                  onValue: (v) => onChanged(() => channel.skip = v),
                ),
                if (shouldShowTransmitPower(
                  channel: channel,
                  availablePowers: capabilities?.powers,
                )) ...[
                  const SizedBox(height: 12),
                  _ChoiceField(
                    key: narrowLow ? const ValueKey('gm32-power-low') : null,
                    label: context.l10n.fieldTransmitPower,
                    value: channel.power,
                    choices: narrowLow
                        ? const {'Low': 'Low'}
                        : choices(capabilities!.powers, const {}),
                    onValue: (v) => onChanged(() => channel.power = v),
                  ),
                ],
                const SizedBox(height: 12),
                _TextField(
                  label: context.l10n.fieldComment,
                  value: channel.comment,
                  maxLines: 3,
                  onValue: (v) => onChanged(() => channel.comment = v),
                ),
                if (channel.extras.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 18),
                    child: Divider(),
                  ),
                  Text(
                    context.l10n.radioSpecificSettings,
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 12),
                  for (final field in channel.extras) ...[
                    ExtraFieldEditor(
                      field: field,
                      onChanged: (value) =>
                          onChanged(() => field.value = value),
                    ),
                    const SizedBox(height: 12),
                  ],
                ],
                if (issues.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(11),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF3E7),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      issues.join('\n'),
                      style: const TextStyle(
                        color: Color(0xFF8A4C0E),
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          const Divider(height: 1),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
            child: Row(
              children: [
                TextButton(
                  onPressed: onClose,
                  child: Text(context.l10n.cancel),
                ),
                const Spacer(),
                FilledButton.icon(
                  onPressed: blocking.isEmpty && (canSave?.call() ?? true)
                      ? onSave
                      : null,
                  icon: const Icon(Icons.check, size: 18),
                  label: Text(saveLabel ?? context.l10n.editorSave),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TextField extends StatefulWidget {
  const _TextField({
    required this.label,
    required this.value,
    required this.onValue,
    this.maxLines = 1,
    this.maxLength,
    this.documentation,
    this.readOnly = false,
  });
  final String label;
  final String value;
  final ValueChanged<String> onValue;
  final int maxLines;
  final int? maxLength;
  final String? documentation;
  final bool readOnly;
  @override
  State<_TextField> createState() => _TextFieldState();
}

class _TextFieldState extends State<_TextField> {
  late final TextEditingController controller;
  @override
  void initState() {
    super.initState();
    controller = TextEditingController(text: widget.value);
  }

  @override
  void didUpdateWidget(covariant _TextField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value && controller.text != widget.value) {
      controller.text = widget.value;
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => TextField(
    controller: controller,
    readOnly: widget.readOnly,
    maxLines: widget.maxLines,
    maxLength: widget.maxLength,
    onChanged: widget.readOnly ? null : widget.onValue,
    decoration: InputDecoration(
      labelText: widget.label,
      suffixIcon: widget.documentation == null
          ? null
          : _ExtraFieldHelp(documentation: widget.documentation!),
    ),
  );
}

class ExtraFieldEditor extends StatelessWidget {
  const ExtraFieldEditor({
    super.key,
    required this.field,
    required this.onChanged,
  });

  final ChannelExtraField field;
  final ValueChanged<dynamic> onChanged;

  @override
  Widget build(BuildContext context) {
    final documentation = field.documentation?.trim();
    late final Widget control;
    if (field.kind == 'boolean') {
      control = Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
        child: Row(
          children: [
            Expanded(
              child: Row(
                children: [
                  Flexible(child: Text(field.label)),
                  if (documentation != null && documentation.isNotEmpty) ...[
                    const SizedBox(width: 6),
                    _ExtraFieldHelp(documentation: documentation),
                  ],
                ],
              ),
            ),
            Switch.adaptive(
              value: field.value == true,
              onChanged: field.mutable ? onChanged : null,
            ),
          ],
        ),
      );
    } else if (field.kind == 'choice' && field.choices.isNotEmpty) {
      control = _ChoiceField(
        label: field.label,
        documentation: documentation,
        value: field.value?.toString() ?? '',
        choices: {for (final choice in field.choices) choice: choice},
        onValue: field.mutable ? onChanged : (_) {},
      );
    } else if (field.kind == 'integer' || field.kind == 'number') {
      control = _NumberField(
        label: field.label,
        documentation: documentation,
        value: (field.value as num?)?.toDouble() ?? 0,
        decimals: field.kind == 'integer' ? 0 : 2,
        onValue: field.mutable
            ? (value) =>
                  onChanged(field.kind == 'integer' ? value.toInt() : value)
            : (_) {},
      );
    } else {
      control = _TextField(
        label: field.label,
        documentation: documentation,
        value: field.value?.toString() ?? '',
        onValue: field.mutable ? onChanged : (_) {},
      );
    }
    return control;
  }
}

class _ExtraFieldHelp extends StatelessWidget {
  const _ExtraFieldHelp({required this.documentation});

  final String documentation;

  @override
  Widget build(BuildContext context) => Tooltip(
    message: documentation,
    waitDuration: const Duration(milliseconds: 300),
    child: const Icon(Icons.info_outline, size: 17, color: Color(0xFF39725C)),
  );
}

class _NumberField extends StatefulWidget {
  const _NumberField({
    required this.label,
    this.documentation,
    required this.value,
    required this.onValue,
    required this.decimals,
    this.readOnly = false,
  });
  final String label;
  final String? documentation;
  final double value;
  final ValueChanged<double> onValue;
  final int decimals;
  final bool readOnly;

  @override
  State<_NumberField> createState() => _NumberFieldState();
}

class _NumberFieldState extends State<_NumberField> {
  late final TextEditingController _controller;
  late final FocusNode _focusNode;

  String get _formattedValue => widget.value.toStringAsFixed(widget.decimals);

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: _formattedValue);
    _focusNode = FocusNode()..addListener(_handleFocusChange);
  }

  @override
  void didUpdateWidget(covariant _NumberField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value == widget.value) return;
    if (double.tryParse(_controller.text) == widget.value) return;
    _replaceText(_formattedValue);
  }

  void _handleFocusChange() {
    if (!_focusNode.hasFocus &&
        double.tryParse(_controller.text) != widget.value) {
      _replaceText(_formattedValue);
    }
  }

  void _replaceText(String text) {
    _controller.value = TextEditingValue(
      text: text,
      selection: TextSelection.collapsed(offset: text.length),
    );
  }

  @override
  void dispose() {
    _focusNode.dispose();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => TextFormField(
    controller: _controller,
    focusNode: _focusNode,
    readOnly: widget.readOnly,
    keyboardType: const TextInputType.numberWithOptions(decimal: true),
    onChanged: widget.readOnly
        ? null
        : (text) {
            final parsed = double.tryParse(text);
            if (parsed != null) widget.onValue(parsed);
          },
    decoration: InputDecoration(
      labelText: widget.label,
      suffixIcon: widget.documentation == null
          ? null
          : _ExtraFieldHelp(documentation: widget.documentation!),
    ),
  );
}

class _ChoiceField extends StatelessWidget {
  const _ChoiceField({
    super.key,
    required this.label,
    this.documentation,
    required this.value,
    required this.choices,
    required this.onValue,
    this.enabled = true,
  });
  final String label;
  final String? documentation;
  final String value;
  final Map<String, String> choices;
  final ValueChanged<String> onValue;
  final bool enabled;
  @override
  Widget build(BuildContext context) {
    final safeValue = choices.containsKey(value) ? value : choices.keys.first;
    return DropdownButtonFormField<String>(
      isExpanded: true,
      initialValue: safeValue,
      decoration: InputDecoration(
        labelText: label,
        suffixIcon: documentation == null
            ? null
            : _ExtraFieldHelp(documentation: documentation!),
      ),
      items: choices.entries
          .map(
            (e) => DropdownMenuItem(
              value: e.key,
              child: Text(e.value, overflow: TextOverflow.ellipsis),
            ),
          )
          .toList(),
      onChanged: enabled
          ? (v) {
              if (v != null) onValue(v);
            }
          : null,
    );
  }
}

class _EmptyLibrary extends StatelessWidget {
  const _EmptyLibrary();
  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.inbox_outlined, size: 42, color: Colors.black26),
        SizedBox(height: 10),
        Text(
          context.l10n.uiNoMatchingChannels,
          style: TextStyle(color: Colors.black45),
        ),
      ],
    ),
  );
}

class _StepTitle extends StatelessWidget {
  const _StepTitle({required this.number, required this.title, this.help});
  final String number;
  final String title;
  final String? help;
  @override
  Widget build(BuildContext context) => Row(
    children: [
      Container(
        width: 28,
        height: 28,
        alignment: Alignment.center,
        decoration: const BoxDecoration(
          color: Color(0xFF1F7455),
          shape: BoxShape.circle,
        ),
        child: Text(
          number,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      const SizedBox(width: 10),
      Text(
        title,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
      ),
      if (help != null) ...[
        const SizedBox(width: 4),
        _HelpButton(title: title, details: help!),
      ],
    ],
  );
}

extension<T> on List<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
