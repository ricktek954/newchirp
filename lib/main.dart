import 'dart:async';
import 'dart:io';

import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:screen_retriever/screen_retriever.dart';
import 'package:window_manager/window_manager.dart';

import 'models/radio_channel.dart';
import 'models/repeater_search.dart';
import 'services/chirp_csv.dart';
import 'services/column_layout_store.dart';
import 'services/radio_image_store.dart';
import 'services/radio_selection_store.dart';
import 'services/radio_bridge.dart';
import 'services/update_checker.dart';
import 'services/window_state_store.dart';
import 'widgets/radio_model_picker.dart';

const _menuChannel = MethodChannel('newchirp/menu');

const String _newChirpVersion = '1.0.20';

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
  if (!adapted.contains('[PTT]')) return adapted;
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

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  LicenseRegistry.addLicense(() async* {
    yield LicenseEntryWithLineBreaks(const [
      'CHIRP',
    ], await rootBundle.loadString('assets/licenses/CHIRP-GPL-3.0.txt'));
    yield LicenseEntryWithLineBreaks(
      const ['pySerial'],
      await rootBundle.loadString('assets/licenses/PYSERIAL-BSD-3-CLAUSE.txt'),
    );
  });
  if (Platform.isLinux) {
    runApp(const NewChirpApp());
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
  runApp(const NewChirpApp());
}

Future<WindowState?> _clampWindowState(WindowState? state) async {
  if (state == null) return null;
  try {
    final rect = Rect.fromLTWH(state.x, state.y, state.width, state.height);
    final displays = await screenRetriever.getAllDisplays();
    if (displays.isEmpty) return state;
    for (final display in displays) {
      final visible = Rect.fromLTWH(
        display.visiblePosition?.dx ?? 0.0,
        display.visiblePosition?.dy ?? 0.0,
        display.visibleSize?.width ?? display.size.width,
        display.visibleSize?.height ?? display.size.height,
      );
      final overlap = rect.intersect(visible);
      if (overlap.width >= 100 && overlap.height >= 100) return state;
    }
    final primary = await screenRetriever.getPrimaryDisplay();
    final visible = Rect.fromLTWH(
      primary.visiblePosition?.dx ?? 0.0,
      primary.visiblePosition?.dy ?? 0.0,
      primary.visibleSize?.width ?? primary.size.width,
      primary.visibleSize?.height ?? primary.size.height,
    );
    final x =
        visible.left +
        (((visible.width - state.width) / 2).clamp(
          0.0,
          double.infinity,
        )).toDouble();
    final y =
        visible.top +
        (((visible.height - state.height) / 2).clamp(
          0.0,
          double.infinity,
        )).toDouble();
    return WindowState(
      width: state.width,
      height: state.height,
      x: x,
      y: y,
      maximized: state.maximized,
    );
  } on Exception {
    return state;
  }
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
    this.updateChecker,
    this.checkForUpdatesOnStartup = true,
  });

  final ColumnLayoutStore? columnLayoutStore;
  final RadioSelectionStore? radioSelectionStore;
  final UpdateChecker? updateChecker;
  final bool checkForUpdatesOnStartup;

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xFF15211D);
    const green = Color(0xFF1F7455);
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'NewChirp',
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
        updateChecker: updateChecker,
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
    this.updateChecker,
    this.checkForUpdatesOnStartup = true,
  });

  final ColumnLayoutStore? columnLayoutStore;
  final RadioSelectionStore? radioSelectionStore;
  final UpdateChecker? updateChecker;
  final bool checkForUpdatesOnStartup;

  @override
  State<NewChirpHome> createState() => _NewChirpHomeState();
}

class _NewChirpHomeState extends State<NewChirpHome> {
  final _bridge = RadioBridge();
  late final _columnLayoutStore =
      widget.columnLayoutStore ?? ColumnLayoutStore();
  late final _radioSelectionStore =
      widget.radioSelectionStore ?? RadioSelectionStore();
  late final _updateChecker = widget.updateChecker ?? UpdateChecker();
  final _imageStore = RadioImageStore();
  Future<void>? _radioSelectionLoad;
  final _searchController = TextEditingController();
  final _channelTableKey = GlobalKey<_ChannelTableState>();
  final _settingsScrollController = ScrollController();
  List<RadioChannel> _channels = [];
  int _selected = -1;
  int _page = 0;
  String _query = '';
  String _libraryName = 'NewChirp';
  String? _libraryPath;
  bool _libraryOpen = false;
  bool _dirty = false;
  bool _busy = false;
  bool _checkingForUpdates = false;
  String _status = 'Ready';
  List<SerialPortInfo> _ports = [];
  List<String> _models = [];
  String? _port;
  String? _model;
  String? _radioImage;
  String? _chirpModuleName;
  RadioCapabilities? _capabilities;
  List<RadioZone> _radioZones = [];
  int? _selectedZone;
  bool _transferActive = false;
  bool _transferCancelling = false;
  String _transferLabel = '';
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
  bool _columnLayoutTouched = false;
  List<RadioChannel> _channelClipboard = [];
  final Set<int> _clearedLocations = {};
  final List<_LibraryState> _undoStack = [];
  final List<_LibraryState> _redoStack = [];

  RadioChannel? get _current => _selected >= 0 && _selected < _channels.length
      ? _channels[_selected]
      : null;

  List<RadioChannel> get _activeChannels =>
      _channels.where((channel) => !channel.cleared).toList();

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
    _radioSelectionLoad = _loadRadioSelection();
    _refreshPorts();
    if (widget.checkForUpdatesOnStartup) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) unawaited(_checkForUpdates(startup: true));
      });
    }
  }

  Future<void> _loadColumnLayout() async {
    final layout = await _columnLayoutStore.load();
    if (!mounted || layout == null || _columnLayoutTouched) return;
    setState(() {
      _columnOrder = layout.order;
      _columnWidths
        ..clear()
        ..addAll(layout.widths);
    });
  }

  Future<void> _saveColumnLayout() async {
    try {
      await _columnLayoutStore.save(
        ColumnLayout(order: _columnOrder, widths: Map.of(_columnWidths)),
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
    selectedZone: _selectedZone,
    clearedLocations: Set.of(_clearedLocations),
  );

  void _restoreLibrary(_LibraryState state) {
    setState(() {
      _channels = state.channels.map((channel) => channel.copy()).toList();
      _selected = state.selected;
      _libraryName = state.libraryName;
      _libraryPath = state.libraryPath;
      _libraryOpen = state.libraryOpen;
      _dirty = state.dirty;
      _capabilities = state.capabilities;
      _radioZones = List.of(state.zones);
      _selectedZone = state.selectedZone;
      _clearedLocations
        ..clear()
        ..addAll(state.clearedLocations);
    });
  }

  void _recordHistory() {
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
      _capabilities = null;
      _radioZones = [];
      _selectedZone = null;
      final model = selection.model;
      if (model != null && _imageStore.hasForModel(model)) {
        _radioImage = _imageStore.pathForModel(model);
        storedImage = _radioImage;
      }
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
        _capabilities = info.capabilities;
        _radioZones = info.zones;
        _selectedZone = info.zone;
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
    late final ({
      List<RadioChannel> channels,
      String model,
      String imagePath,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
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
      _capabilities = imported.capabilities;
      _radioZones = imported.zones;
      _selectedZone = imported.zone;
      _libraryName = '${model.replaceAll('_', ' ')} — ${zone.name}';
      _libraryPath = null;
      _libraryOpen = true;
      _dirty = false;
      _page = 0;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
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

  @override
  void dispose() {
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
    await _task('Loading radio catalog…', () async {
      final models = await _bridge.models();
      setState(() {
        _models = models;
        _model ??= models.firstOrNull;
        _capabilities = null;
        _radioZones = [];
        _selectedZone = null;
        final model = _model;
        if (model != null && _imageStore.hasForModel(model)) {
          _radioImage = _imageStore.pathForModel(model);
          storedImage = _radioImage;
        }
      });
    });
    if (storedImage != null) {
      unawaited(_loadImageCapabilities(storedImage!));
    }
  }

  void _selectRadioModel(String model) {
    String? storedImage;
    setState(() {
      _model = model;
      _capabilities = null;
      _radioZones = [];
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
        setState(() => _status = 'Action failed');
        await _showActionError(error);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _friendlyActionError(Object error) {
    final message = error.toString();
    if (Platform.isLinux &&
        (message.contains('Permission denied') ||
            message.contains('Errno 13')) &&
        (message.contains('/dev/tty') ||
            message.contains('could not open port'))) {
      return '$message\n\n'
          'On Linux, this usually means your user does not have permission '
          'to open the radio programming cable.\n\n'
          'Fix it with:\n'
          '    sudo usermod -aG dialout \$USER\n\n'
          'Then log out and back in, reconnect the cable, and try again.\n\n'
          'For the current terminal session only:\n'
          '    newgrp dialout';
    }
    return message;
  }

  ({String summary, String? technical}) _actionErrorPresentation(Object error) {
    final message = _friendlyActionError(error).trim();
    final lines = message
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
    if (!hasTechnicalNoise) {
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
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Couldn’t complete that action'),
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
                      title: const Text(
                        'More Info:',
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
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Future<void> _openLibraryFile() async {
    const type = XTypeGroup(
      label: 'CHIRP files',
      extensions: ['csv', 'img', 'icf', 'itm', 'd72'],
    );
    final file = await openFile(acceptedTypeGroups: const [type]);
    if (file == null) return;
    if (!file.path.toLowerCase().endsWith('.csv')) {
      await _importChirpImage(file);
      return;
    }
    late final List<RadioChannel> channels;
    try {
      channels = ChirpCsv.decode(await file.readAsString());
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

    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: 'CSV channels',
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
          RegExp(r'\.csv$', caseSensitive: false),
          '',
        ),
        libraryPath: file.path,
      );
    });
  }

  Future<void> _loadChirpModule() async {
    const type = XTypeGroup(
      label: 'CHIRP driver modules',
      extensions: ['py', 'mod'],
    );
    final file = await openFile(acceptedTypeGroups: const [type]);
    if (file == null || !mounted) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Load experimental CHIRP module?'),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: const Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'CHIRP modules are executable Python code. A malicious or '
                'incompatible module could damage your computer, radio, or '
                'both.',
              ),
              SizedBox(height: 12),
              Text(
                'Only load modules from a source you trust. NewChirp cannot '
                'verify that a module is safe. The module remains active only '
                'for this NewChirp session. Select the radio model and read '
                'the radio again before writing.',
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: const Color(0xFF9B3D2E),
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Load module'),
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
        _model = null;
        _capabilities = null;
        _radioZones = [];
        _selectedZone = null;
        _radioImage = null;
        _radioSettings = null;
        _settingsDirty = false;
        _settingsLoadedFromRadio = false;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _settingsError = null;
      });
      await _saveRadioSelection();
    });
  }

  Future<void> _unloadChirpModule() async {
    _bridge.unloadModule();
    await _task('Refreshing radio catalog…', () async {
      final models = await _bridge.models();
      if (!mounted) return;
      setState(() {
        _chirpModuleName = null;
        _models = models;
        _model = null;
        _capabilities = null;
        _radioZones = [];
        _selectedZone = null;
        _radioImage = null;
        _radioSettings = null;
        _settingsDirty = false;
        _settingsLoadedFromRadio = false;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _settingsError = null;
      });
      await _saveRadioSelection();
    });
  }

  Future<void> _importChirpImage(XFile file) async {
    late final ({
      List<RadioChannel> channels,
      String model,
      String imagePath,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
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
      destination: 'this CHIRP image',
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
      );
      setState(() {
        _model = imported.model;
        _radioImage = storedImage;
        _capabilities = imported.capabilities;
        _radioZones = imported.zones;
        _selectedZone = imported.zone;
        if (!_models.contains(imported.model)) {
          _models = [..._models, imported.model]..sort();
        }
        _radioSettings = null;
        _settingsLoadedModel = null;
        _settingsLoadedImage = null;
        _settingsError = null;
      });
      unawaited(_saveRadioSelection());
    });
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
      ),
    );
  }

  void _applyChannels(
    List<RadioChannel> incoming,
    _ChannelApplyMode mode, {
    required String libraryName,
    String? libraryPath,
  }) {
    if (mode.replaceAll) {
      final sorted = [...incoming]
        ..sort((left, right) => left.location.compareTo(right.location));
      setState(() {
        _channels = sorted;
        _selected = sorted.isEmpty ? -1 : 0;
        _libraryName = libraryName;
        _libraryPath = libraryPath;
        _libraryOpen = true;
        _page = 0;
        _dirty = false;
        _capabilities = null;
        _radioZones = [];
        _selectedZone = null;
        _clearedLocations.clear();
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
    radioModel: _model,
  );

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
      _selected = toIndex;
      _dirty = true;
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text('Moved ${moved.name} to channel ${moved.location}'),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  Future<void> _findRepeaters() async {
    final channels = await showDialog<List<RadioChannel>>(
      context: context,
      builder: (context) => RepeaterBookDialog(bridge: _bridge),
    );
    if (channels == null || channels.isEmpty || !mounted) return;
    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: 'RepeaterBook results',
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
                ? 'No empty channel slot is available.'
                : 'No empty channel slots are available for this radio.',
          ),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 3),
        ),
      );
  }

  Future<void> _saveCsv({bool saveAs = false}) async {
    var path = _libraryPath;
    if (saveAs || path == null) {
      const type = XTypeGroup(label: 'CHIRP CSV', extensions: ['csv']);
      final location = await getSaveLocation(
        suggestedName: '${_libraryName.replaceAll(' ', '_')}.csv',
        acceptedTypeGroups: const [type],
      );
      path = location?.path;
    }
    if (path == null) return;
    final savePath = path.endsWith('.csv') ? path : '$path.csv';
    await _task('Saving channel library…', () async {
      await File(savePath).writeAsString(ChirpCsv.encode(_activeChannels));
      setState(() {
        _libraryPath = savePath;
        _dirty = false;
      });
    });
  }

  Future<bool> _confirmReplaceLibrary({required String destination}) async {
    if (!_libraryOpen) return true;
    final discard = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: Color(0xFFC46A15)),
        title: Text('Start $destination?'),
        content: Text(
          _dirty
              ? 'Discard the current channel list? Any unsaved changes will be lost.'
              : 'Close the current channel list and start $destination?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Keep current list'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Discard and continue'),
          ),
        ],
      ),
    );
    return discard == true && mounted;
  }

  Future<void> _newLibrary() async {
    if (!await _confirmReplaceLibrary(
      destination: 'a new blank configuration',
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
      _selectedZone = null;
    });
  }

  Future<void> _useGmrsStarter() async {
    final template = gmrsStarterChannels();
    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: 'GMRS starter template',
            count: template.length,
          )
        : const _ChannelApplyMode(replaceAll: true, startAt: 1);
    if (mode == null || !mounted) return;
    _recordHistory();
    _applyChannels(template, mode, libraryName: 'GMRS Starter Library');
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
      channels = ChirpCsv.decode(await stockFile.readAsString());
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

    final mode = _libraryOpen && _channels.isNotEmpty
        ? await _chooseChannelApplyMode(
            label: 'stock channels',
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

  Future<void> _readRadioSettings() async {
    final model = _model;
    final port = _port;
    if (_settingsLoading || _busy || model == null || port == null) return;
    if (_settingsDirty) {
      final discard = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: const Text('Replace unsaved settings changes?'),
          content: const Text(
            'Reading settings from the radio will replace the unsaved settings '
            'changes shown on this page. The current channel list is not changed.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Read settings'),
            ),
          ],
        ),
      );
      if (discard != true || !mounted) return;
    }
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: false)) return;
    setState(() {
      _settingsLoading = true;
      _settingsError = null;
    });
    try {
      await _transferTask(
        'Reading radio settings - do not disconnect...',
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
            _settingsLoadedModel = model;
            if (storedImage != null) _radioImage = storedImage;
            _settingsLoadedImage = _radioImage;
            _settingsLoadedFromRadio = true;
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
    setState(() => _settingsDirty = true);
  }

  List<Map<String, Object?>> _radioSettingChanges() {
    final changes = <Map<String, Object?>>[];
    void walk(RadioSettingNode node) {
      if (node.isGroup) {
        for (final child in node.children) {
          walk(child);
        }
      } else if (node.mutable && node.kind != 'unsupported') {
        changes.add(node.toChangeJson());
      }
    }

    for (final item in _radioSettings?.items ?? const <RadioSettingNode>[]) {
      walk(item);
    }
    return changes;
  }

  Future<void> _writeRadioSettings() async {
    final model = _model;
    final port = _port;
    final image = _radioImage;
    if (model == null || port == null || image == null) return;
    if (_settingsHaveInvalidValues) return;
    final changes = _radioSettingChanges();
    if (changes.isEmpty) return;
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(
          Icons.warning_amber_rounded,
          color: Color(0xFFC46A15),
          size: 32,
        ),
        title: const Text('Write these radio settings?'),
        content: Text(
          'This will write ${changes.length} radio setting values to '
          '$model through $port. Keep the radio connected and powered on.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Write settings'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: true)) return;
    final succeeded = await _transferTask(
      'Writing radio settings - do not disconnect...',
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

  void _addChannel() {
    final location = _nextChannelLocation();
    if (location == null) {
      _showNoEmptyChannelSlot();
      return;
    }
    final midland = showsMidlandChannelNumbers(_model);
    final channel = RadioChannel(
      location: location,
      name: 'NEW $location',
      frequency: midland ? 0 : 146.52,
      duplex: '',
      offset: midland ? 0 : 0.6,
    );
    _recordHistory();
    setState(() {
      _clearedLocations.remove(location);
      _channels.add(channel);
      _sortChannelsByLocation();
      _searchController.clear();
      _query = '';
      _selected = _channels.indexOf(channel);
      _dirty = true;
    });
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text('Channel $location added'),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
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
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _channelTableKey.currentState?.revealSelectedChannel();
    });
  }

  void _copyChannel(int index) {
    if (index < 0 || index >= _channels.length) return;
    if (_channels[index].cleared) return;
    setState(() {
      _channelClipboard = [_channels[index].copy()];
    });
  }

  void _cutChannel(int index) {
    if (index < 0 || index >= _channels.length) return;
    if (_channels[index].cleared) return;
    final channel = _channels[index];
    if (isMidlandRepeaterRow(_model, channel.location)) {
      _recordHistory();
      setState(() {
        _channelClipboard = [channel.copy()];
        _keepMidlandRepeater(channel);
        _selected = index;
        _dirty = true;
      });
      _noteRepeaterRowKept(channel);
      return;
    }
    _recordHistory();
    setState(() {
      _channelClipboard = [channel.copy()];
      channel.clear();
      _clearedLocations.add(channel.location);
      _selected = index;
      _dirty = true;
    });
  }

  Future<void> _pasteChannel(int index) async {
    if (_channelClipboard.isEmpty || index < 0 || index >= _channels.length) {
      return;
    }
    final target = _channels[index];
    if (!target.cleared) {
      final confirmed = await _confirmOverwriteChannel(target);
      if (!confirmed || !mounted) return;
    }
    final pasted = _channelClipboard.first.copy()..location = target.location;
    _recordHistory();
    setState(() {
      _channels[index] = pasted;
      _selected = index;
      _dirty = true;
      _clearedLocations.remove(target.location);
    });
  }

  Future<bool> _confirmOverwriteChannel(RadioChannel channel) async {
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.warning_amber_rounded, color: Color(0xFFC46A15)),
        title: Text(
          'Overwrite channel ${channelNumberLabel(_model, channel.location)}?',
        ),
        content: Text(
          channel.name.isEmpty
              ? 'This channel contains data. Pasting will replace it.'
              : '“${channel.name}” contains data. Pasting will replace it.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Overwrite channel'),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  void _deleteChannel() {
    final channel = _current;
    if (channel == null) return;
    if (isMidlandRepeaterRow(_model, channel.location)) {
      _recordHistory();
      setState(() {
        _keepMidlandRepeater(channel);
        _dirty = true;
      });
      _noteRepeaterRowKept(channel);
      return;
    }
    final location = channel.location;
    final wasCleared = channel.cleared;
    _recordHistory();
    setState(() {
      _channels.removeAt(_selected);
      if (wasCleared) {
        _clearedLocations.remove(location);
      } else {
        _clearedLocations.add(location);
      }
      _selected = _channels.isEmpty
          ? -1
          : _selected.clamp(0, _channels.length - 1);
      _dirty = true;
    });
  }

  void _clearChannel(int index) {
    if (index < 0 || index >= _channels.length) return;
    if (_channels[index].cleared) return;
    final channel = _channels[index];
    if (isMidlandRepeaterRow(_model, channel.location)) {
      _recordHistory();
      setState(() {
        _keepMidlandRepeater(channel);
        _selected = index;
        _dirty = true;
      });
      _noteRepeaterRowKept(channel);
      return;
    }
    _recordHistory();
    final location = channel.location;
    setState(() {
      channel.clear();
      _clearedLocations.add(location);
      _selected = index;
      _dirty = true;
    });
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
          content: Text(
            '$label stays in the radio. The name is cleared and the '
            'plain repeater frequency is back.',
          ),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 3),
        ),
      );
  }

  Future<void> _downloadRadio() async {
    if (_port == null || _model == null) return;
    if (_libraryOpen && _channels.isNotEmpty) {
      final replace = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          icon: const Icon(
            Icons.warning_amber_rounded,
            color: Color(0xFFC46A15),
          ),
          title: const Text('Replace current channel list?'),
          content: const Text(
            'Reading channels from the radio will replace the current channel list. '
            'Save it as a CSV first if you want to keep it.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Read channels'),
            ),
          ],
        ),
      );
      if (replace != true || !mounted) return;
    }
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: false)) return;
    await _transferTask(
      'Reading radio channels - do not disconnect...',
      () async {
        final result = await _bridge.download(
          model: _model!,
          port: _port!,
          zone: _selectedZone,
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
          _capabilities = result.capabilities;
          _radioZones = result.zones;
          _selectedZone = result.zone;
          _libraryName = _model!.replaceAll('_', ' ');
          _libraryOpen = true;
          _dirty = false;
          _page = 0;
          _radioSettings = null;
          _settingsDirty = false;
          _settingsLoadedFromRadio = false;
          _settingsLoadedModel = null;
          _settingsLoadedImage = null;
        });
      },
    );
  }

  Future<bool> _confirmRadioInstructions(
    RadioInstructions instructions, {
    required bool writing,
  }) async {
    final readyLabel = writing ? 'Radio is ready to receive' : 'Radio is ready';
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
          'Before ${writing ? 'writing' : 'reading'} '
          '${_model!.replaceAll('_', ' ')}',
        ),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: SelectableText(messages.join('\n\n')),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
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
      _status = 'Loading radio instructions…';
    });
    try {
      return await _bridge.instructions(_model!);
    } catch (error) {
      if (mounted) {
        setState(() => _status = 'Action failed');
        await _showActionError(error);
      }
      return null;
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _uploadRadio() async {
    if (_port == null || _model == null || _radioImage == null) return;
    final issues = _activeChannels
        .expand(
          (channel) => _channelIssues(channel).map(
            (issue) =>
                '${channelNumberLabel(_model, channel.location)}: $issue',
          ),
        )
        .toList();
    if (issues.isNotEmpty) {
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Fix channel issues first'),
          content: Text(issues.take(8).join('\n')),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
      return;
    }
    final uppercasesNames =
        _capabilities?.uppercaseNames == true &&
        _activeChannels.any(
          (channel) => channel.name != channel.name.toUpperCase(),
        );
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(
          Icons.warning_amber_rounded,
          color: Color(0xFFC46A15),
          size: 32,
        ),
        title: const Text('Write these channels to the radio?'),
        content: Text(
          'This will program ${_activeChannels.length} channels on $_model '
          'through $_port. Keep the radio connected and powered on.'
          '${uppercasesNames ? '\n\nLowercase channel names will be converted to uppercase because this radio only supports uppercase names.' : ''}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Write to radio'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    final instructions = await _loadRadioInstructions();
    if (instructions == null || !mounted) return;
    if (!await _confirmRadioInstructions(instructions, writing: true)) return;
    var changes = <Map<String, dynamic>>[];
    await _transferTask('Writing radio — do not disconnect…', () async {
      changes = await _bridge.upload(
        model: _model!,
        port: _port!,
        imagePath: _radioImage!,
        channels: _activeChannels,
        cleared: _clearedLocations.toList(),
        zone: _selectedZone,
        onProgress: _reportTransferProgress,
      );
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
        _dirty = false;
      });
    });
    if (changes.isNotEmpty && mounted) {
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Some channel values were adjusted'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'The write finished, but NewChirp adjusted values the radio '
                  'does not support or could not write some channels.',
                ),
                const SizedBox(height: 12),
                for (final entry in changes)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(() {
                      final location = entry['location'];
                      final name = entry['name'];
                      final reason = entry['reason'];
                      if (reason != null) {
                        return 'Channel $location $name could not be '
                            'written: $reason';
                      }
                      final notes = <String>[];
                      final nameFrom = entry['nameFrom'];
                      final nameTo = entry['nameTo'];
                      if (nameFrom != null &&
                          nameTo != null &&
                          '$nameFrom' != '$nameTo') {
                        notes.add('name changed from "$nameFrom" to "$nameTo"');
                      }
                      final fields = (entry['fields'] as List? ?? const [])
                          .join(', ');
                      if (fields.isNotEmpty) {
                        notes.add(
                          'locked field(s): $fields; everything else was '
                          'written',
                        );
                      }
                      return 'Channel $location $name: ${notes.join('; ')}.';
                    }()),
                  ),
                const Text(
                  'Names are converted only when the selected radio requires '
                  'it. Custom frequencies may require a channel outside the '
                  'radio\'s locked memory range.',
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
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
      _transferFraction = null;
      _transferDetail = '';
      _status = label;
    });
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
          () => _status = _transferCancelling ? 'Cancelled' : 'Action failed',
        );
      }
    } finally {
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

  void _cancelTransfer() {
    if (!_transferActive || _transferCancelling) return;
    setState(() {
      _transferCancelling = true;
      _transferLabel = 'Cancelling safely…';
    });
    _bridge.cancelActive();
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      autofocus: true,
      child: CallbackShortcuts(
        bindings: {
          const SingleActivator(LogicalKeyboardKey.keyZ, meta: true): _undo,
          const SingleActivator(
            LogicalKeyboardKey.keyZ,
            meta: true,
            shift: true,
          ): _redo,
          const SingleActivator(LogicalKeyboardKey.keyY, meta: true): _redo,
          const SingleActivator(LogicalKeyboardKey.keyZ, control: true): _undo,
          const SingleActivator(
            LogicalKeyboardKey.keyZ,
            control: true,
            shift: true,
          ): _redo,
          const SingleActivator(LogicalKeyboardKey.keyY, control: true): _redo,
        },
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
                            checkingForUpdates: _checkingForUpdates,
                            onCheckForUpdates: () => _checkForUpdates(),
                            onLoadChirpModule: _loadChirpModule,
                            onUnloadChirpModule: _unloadChirpModule,
                            onNew: _newLibrary,
                            onGmrsStarter: _useGmrsStarter,
                            onRestoreStock: _restoreStockChannels,
                            onOpen: _openLibraryFile,
                            onSave: () => _saveCsv(),
                            onSaveAs: () => _saveCsv(saveAs: true),
                            canSave: _libraryOpen,
                            minimalMode: _page == 2 || _page == 3 || _page == 4,
                            minimalTitle: switch (_page) {
                              2 => 'About & licenses',
                              3 => 'GMRS & FRS Frequency Reference',
                              _ => 'Radio settings',
                            },
                            minimalSubtitle: switch (_page) {
                              2 =>
                                'Application information and open-source licenses',
                              3 => 'Part 95 FRS/GMRS channel plan',
                              _ =>
                                'Radio-wide options exposed by the selected driver',
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
                'What would you like to do?',
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Open an existing CHIRP file or read channels directly from your radio.',
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
                        title: 'Load configuration',
                        description:
                            'Open a CHIRP CSV or native image file and continue editing.',
                        buttonLabel: 'Open file',
                        onPressed: _openLibraryFile,
                        help:
                            'Open a CHIRP-compatible CSV or native radio image. Native images '
                            'retain the selected model and stored image needed for radio transfer.',
                      ),
                      _WelcomeAction(
                        width: cardWidth,
                        icon: Icons.settings_input_antenna,
                        title: 'Read channels from a radio',
                        description:
                            'Connect a programming cable and import the radio’s current channels.',
                        buttonLabel: 'Connect radio',
                        onPressed: _openRadioConnection,
                        help:
                            'Open the radio connection screen, choose your cable and exact model, '
                            'then choose Read channels from the radio. Settings are read separately '
                            'from the Radio settings page.',
                      ),
                      _WelcomeAction(
                        width: cardWidth,
                        icon: Icons.travel_explore,
                        title: 'Find nearby repeaters',
                        description:
                            'Search RepeaterBook and add amateur or GMRS channels.',
                        buttonLabel: 'Find repeaters',
                        onPressed: _findRepeaters,
                        help:
                            'Search RepeaterBook by state and optional location, '
                            'preview matching repeaters, and add selected channels '
                            'to the current library.',
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 22),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.lightbulb_outline, color: Color(0xFF1F7455)),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Writing to a radio requires reading a matching image from it first. '
                          'You can plan or edit a CSV anytime, but radio writes stay locked until a read completes.',
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
          title: const Text('Couldn\u2019t check for updates'),
          content: Text(
            '${error.message}\n\n'
            'You can also download the latest version from newchirp.net.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } finally {
      if (mounted) setState(() => _checkingForUpdates = false);
    }
  }

  Future<void> _showUpdateAvailable(UpdateCheckResult result) {
    final downloadUrl = trustedDownloadUrl(result.releaseUrl);
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Update available'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'NewChirp ${result.latestVersion} is available. '
              'You are running ${result.currentVersion}.',
            ),
            const SizedBox(height: 12),
            const Text('This opens:'),
            const SizedBox(height: 4),
            SelectableText(
              downloadUrl,
              style: const TextStyle(color: Colors.black54),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Later'),
          ),
          FilledButton.icon(
            onPressed: () {
              unawaited(openExternalUrl(downloadUrl));
              Navigator.pop(context);
            },
            icon: const Icon(Icons.download_outlined),
            label: const Text('Open download page'),
          ),
        ],
      ),
    );
  }

  Future<void> _showUpToDate(UpdateCheckResult result) => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('You\u2019re up to date'),
      content: Text('NewChirp ${result.currentVersion} is the latest version.'),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Close'),
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
                          'Desktop radio programmer · Version $_newChirpVersion',
                          style: const TextStyle(color: Colors.black54),
                        ),
                        const SizedBox(height: 3),
                        const Text(
                          'Rick Lopez · Lead Programmer',
                          style: TextStyle(
                            color: Color(0xFF1F7455),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SelectableText(
                          'rick@newchirp.net',
                          style: TextStyle(color: Colors.black54),
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
                                  ? 'Checking for updates...'
                                  : 'Check for updates',
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 28),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(22),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'CHIRP compatibility layer',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      SizedBox(height: 12),
                      Text(
                        'NewChirp uses the CHIRP driver tree for radio hardware compatibility. CHIRP copyright is held by its contributors, and CHIRP is free software licensed under the GNU General Public License, version 3 or (at your option) any later version.',
                      ),
                      SizedBox(height: 12),
                      Text(
                        'CHIRP is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.',
                      ),
                      SizedBox(height: 12),
                      SelectableText(
                        'CHIRP project and source: https://github.com/kk7ds/chirp',
                        style: TextStyle(color: Color(0xFF1F7455)),
                      ),
                      SizedBox(height: 6),
                      SelectableText(
                        'NewChirp project and source: https://github.com/ricktek954/newchirp',
                        style: TextStyle(color: Color(0xFF1F7455)),
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
                            const Text(
                              'Open-source licenses',
                              style: TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'The complete CHIRP GPL text, the pySerial BSD notice, and licenses for Flutter dependencies are included with this application.',
                            ),
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
                              label: const Text('View complete licenses'),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              const Text(
                'NewChirp is an independent interface and is not affiliated with or endorsed by the CHIRP project.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.black54, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showChannelEditor(int channelIndex) async {
    if (channelIndex < 0 || channelIndex >= _channels.length) return;
    if (_channels[channelIndex].cleared) return;
    final draft = _channels[channelIndex].copy();
    if (showsMidlandChannelNumbers(_model)) {
      draft.prepareMxt295Editor();
    }
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) {
          void changed(VoidCallback update) => setDialogState(() => update());

          void save() {
            final saved = draft.copy();
            _recordHistory();
            setState(() {
              _channels[channelIndex] = saved;
              _sortChannelsByLocation();
              _selected = _channels.indexOf(saved);
              _dirty = true;
            });
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
                onChanged: changed,
                onSave: save,
                onClose: () => Navigator.pop(dialogContext),
                onDelete: () async {
                  final confirmed = await _confirmDeleteChannel(
                    _channels[channelIndex],
                  );
                  if (confirmed && dialogContext.mounted) {
                    _deleteChannel();
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
        title: Text(kept ? 'Reset $label?' : 'Delete channel $label?'),
        content: Text(
          kept
              ? 'Repeater rows 15 through 22 stay in the radio. '
                    'The name is cleared and the plain GMRS repeater '
                    'frequency is put back.'
              : channel.name.isEmpty
              ? 'This channel will be removed from the current configuration.'
              : '“${channel.name}” will be removed from the current configuration.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: kept
                ? null
                : FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF9B3D34),
                  ),
            onPressed: () => Navigator.pop(context, true),
            child: Text(kept ? 'Reset repeater' : 'Delete channel'),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  Widget _buildLibrary() {
    final visible = _channels.asMap().entries.where((entry) {
      final q = _query.toLowerCase();
      return q.isEmpty ||
          !entry.value.cleared &&
              (entry.value.name.toLowerCase().contains(q) ||
                  entry.value.frequency.toString().contains(q) ||
                  entry.value.comment.toLowerCase().contains(q));
    }).toList();
    final invalid = _activeChannels
        .where((channel) => _channelIssues(channel).isNotEmpty)
        .length;
    final storedImageReady =
        _model != null &&
        _radioImage != null &&
        _radioImage == _imageStore.pathForModel(_model!);
    return Padding(
      padding: const EdgeInsets.all(22),
      child: Column(
        children: [
          Row(
            children: [
              _Metric(
                label: 'Channels',
                value: '${_activeChannels.length}',
                icon: Icons.radio,
              ),
              const SizedBox(width: 12),
              _Metric(
                label: 'Scan enabled',
                value: '${_activeChannels.where((c) => c.skip.isEmpty).length}',
                icon: Icons.radar,
              ),
              const SizedBox(width: 12),
              _Metric(
                label: 'Needs attention',
                value: '$invalid',
                icon: invalid == 0
                    ? Icons.check_circle_outline
                    : Icons.error_outline,
              ),
            ],
          ),
          if (_radioImage == null) ...[
            const SizedBox(height: 12),
            DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xFFFFF7EC),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFE7C9A5)),
              ),
              child: const Padding(
                padding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Row(
                  children: [
                    Icon(Icons.shield_outlined, color: Color(0xFF9B5B18)),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'No radio image loaded. Editing and CSV export work, but '
                        'writing stays locked until you read from this radio.',
                      ),
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
                            ? 'Stored image ready for ${_model!.replaceAll('_', ' ')}. '
                                  'You can write without reading again.'
                            : 'A radio image is loaded from this session. '
                                  'Review all changes before writing.',
                      ),
                    ),
                  ],
                ),
              ),
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
                    decoration: const InputDecoration(
                      labelText: 'Zone',
                      isDense: true,
                    ),
                    items: _radioZones
                        .map(
                          (zone) => DropdownMenuItem(
                            value: zone.index,
                            child: Text(
                              '${zone.name} (${zone.channelCount} channels)',
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
                const _HelpButton(
                  title: 'Radio zones',
                  details:
                      'This radio stores channels in separate zones. Choose a '
                      'zone to view and edit its channels. Writing preserves '
                      'the other zones in the saved radio image.',
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
                        final compact = constraints.maxWidth < 480;
                        return Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _searchController,
                                onChanged: (value) =>
                                    setState(() => _query = value),
                                decoration: InputDecoration(
                                  prefixIcon: const Icon(Icons.search),
                                  hintText: compact
                                      ? 'Search'
                                      : 'Search name, frequency, or note',
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            if (compact) ...[
                              IconButton(
                                onPressed: _duplicateChannel,
                                tooltip: 'Duplicate channel',
                                icon: const Icon(Icons.copy_outlined),
                              ),
                              IconButton.filled(
                                onPressed: _addChannel,
                                tooltip: 'Add channel',
                                icon: const Icon(Icons.add),
                              ),
                            ] else ...[
                              OutlinedButton.icon(
                                onPressed: _duplicateChannel,
                                icon: const Icon(Icons.copy_outlined),
                                label: const Text('Duplicate'),
                              ),
                              const SizedBox(width: 8),
                              FilledButton.icon(
                                onPressed: _addChannel,
                                icon: const Icon(Icons.add),
                                label: const Text('Add channel'),
                              ),
                            ],
                            const SizedBox(width: 2),
                            const _HelpButton(
                              title: 'Channel editing',
                              details:
                                  'Add creates a channel in the next available radio memory slot. '
                                  'Duplicate copies the selected row, and Delete removes it after '
                                  'confirmation. Double-click any row to edit all of its fields. '
                                  'Right-click a row to copy, cut, paste, duplicate, or clear it. '
                                  'Drag the handle at the left edge of a row to move it; intervening '
                                  'channels shift through the same memory slots. '
                                  'Clear removes it from the radio on the next write. Use '
                                  'Cmd/Ctrl+Z to undo and Cmd/Ctrl+Shift+Z to redo.',
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
                            selected: _selected,
                            radioModel: _model,
                            capabilities: _capabilities,
                            columnOrder: _columnOrder,
                            columnWidths: _columnWidths,
                            onColumnOrderChanged: _setColumnOrder,
                            onColumnWidthChanged: _setColumnWidth,
                            onSelect: (index) =>
                                setState(() => _selected = index),
                            clipboardNotEmpty: _channelClipboard.isNotEmpty,
                            onCopy: _copyChannel,
                            onCut: _cutChannel,
                            onPaste: _pasteChannel,
                            onDuplicate: _duplicateChannelAt,
                            onClear: _clearChannel,
                            onMove: _moveChannel,
                            reorderEnabled: _query.isEmpty,
                            onOpen: (index) {
                              setState(() => _selected = index);
                              _showChannelEditor(index);
                            },
                          ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _printFrequencyReference() async {
    final temp = File(
      '${Directory.systemTemp.path}/newchirp-gmrs-frs-reference.pdf',
    );
    var prepared = false;
    await _task('Preparing frequency reference…', () async {
      final data = await rootBundle.load('assets/GMRS_FRS_Frequency_Chart.pdf');
      await temp.writeAsBytes(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
      );
      prepared = true;
    });

    if (!mounted || !prepared) return;

    final printers = await _systemPrinters();
    if (printers.isEmpty) {
      try {
        final openResult = await Process.run('/usr/bin/open', [temp.path]);
        if (openResult.exitCode != 0) {
          throw Exception(
            'Opening the reference PDF failed:\n'
            '${openResult.stderr.toString().trim()}',
          );
        }
      } catch (error) {
        if (mounted) await _showActionError(error);
        return;
      }

      if (mounted) {
        await showDialog<void>(
          context: context,
          builder: (context) => AlertDialog(
            icon: const Icon(Icons.print_outlined, color: Color(0xFFC46A15)),
            title: const Text('No printers found'),
            content: const Text(
              'NewChirp could not find any system printers, so the reference '
              'PDF was opened in your default PDF viewer. Use the viewer’s '
              'Print command to print it.',
            ),
            actions: [
              FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Close'),
              ),
            ],
          ),
        );
      }
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
          title: const Text('Choose a printer'),
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
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: selectedPrinter == null
                  ? null
                  : () => Navigator.pop(dialogContext, selectedPrinter),
              child: const Text('Print'),
            ),
          ],
        ),
      ),
    );

    if (chosenPrinter == null || !mounted) return;

    var printSent = false;
    await _task('Printing frequency reference…', () async {
      final result = await Process.run('/usr/bin/lp', [
        '-d',
        chosenPrinter,
        temp.path,
      ]);
      if (result.exitCode != 0) {
        throw Exception(
          'Could not send the reference to $chosenPrinter:\n'
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
          title: const Text('Print job sent'),
          content: Text('The GMRS/FRS reference was sent to $chosenPrinter.'),
          actions: [
            FilledButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
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
        'Shared 462 MHz interstitial',
      ],
      [
        '2',
        '462.5875',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        'Shared 462 MHz interstitial',
      ],
      [
        '3',
        '462.6125',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        'Shared 462 MHz interstitial',
      ],
      [
        '4',
        '462.6375',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        'Shared 462 MHz interstitial',
      ],
      [
        '5',
        '462.6625',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        'Shared 462 MHz interstitial',
      ],
      [
        '6',
        '462.6875',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        'Shared 462 MHz interstitial',
      ],
      [
        '7',
        '462.7125',
        '2 W',
        '12.5 kHz',
        '5 W',
        '20 kHz',
        'Shared 462 MHz interstitial',
      ],
      [
        '8',
        '467.5625',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '9',
        '467.5875',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '10',
        '467.6125',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '11',
        '467.6375',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '12',
        '467.6625',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '13',
        '467.6875',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '14',
        '467.7125',
        '0.5 W',
        '12.5 kHz',
        '0.5 W',
        '12.5 kHz',
        'Handheld only',
      ],
      [
        '15',
        '462.5500',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '16',
        '462.5750',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '17',
        '462.6000',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '18',
        '462.6250',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '19',
        '462.6500',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '20',
        '462.6750',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '21',
        '462.7000',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
      ],
      [
        '22',
        '462.7250',
        '2 W',
        '12.5 kHz',
        '50 W',
        '20 kHz',
        'Main / repeater output',
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
                'GMRS & FRS Frequency Reference',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: green,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                'United States Part 95 channel plan - color-coded by frequency band and power class.',
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: muted),
              ),
              const SizedBox(height: 14),
              Wrap(
                children: [
                  legendItem(band1, 'Ch 1-7: 462 MHz interstitial'),
                  legendItem(band2, 'Ch 8-14: 467 MHz interstitial'),
                  legendItem(band3, 'Ch 15-22: 462 MHz main'),
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
                            'Frequency (MHz)',
                            align: TextAlign.center,
                          ),
                          headerCell('FRS Power', align: TextAlign.center),
                          headerCell('FRS BW', align: TextAlign.center),
                          headerCell('GMRS Power', align: TextAlign.center),
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
                'Repeater Pairs (GMRS Only)',
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
                            'Input - You Transmit',
                            align: TextAlign.center,
                          ),
                          headerCell(
                            'Output - You Listen',
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
                            cell('Input = output + 5 MHz'),
                          ],
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 18),
              const DecoratedBox(
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
                        'Key notes',
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'All frequencies are in MHz. GMRS requires an FCC license; FRS is license-by-rule.\n'
                        'GMRS mobile/base radios may not transmit on channels 8-14. Repeater inputs are GMRS-only.\n'
                        'Community convention: Channel 20 (462.675 MHz) with CTCSS 141.3 Hz is often used as a travel/assistance channel.\n'
                        'Reference only - verify against current FCC Part 95 rules and your radio manual.',
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
                  'Radio settings',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Adjust radio-wide options such as squelch, backlight, VOX, '
                  'and other controls exposed by the selected CHIRP driver.',
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
                                    ? 'No radio model selected. Open Radio connection first.'
                                    : '${model.replaceAll('_', ' ')}  |  '
                                          '${_port ?? 'No programming cable selected'}'
                                          '${_settingsLoadedFromRadio
                                              ? '  |  read from radio'
                                              : hasImage
                                              ? '  |  stored image available'
                                              : ''}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          alignment: WrapAlignment.end,
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            if (canReadRadio)
                              FilledButton.tonalIcon(
                                onPressed: _settingsLoading || _busy
                                    ? null
                                    : _readRadioSettings,
                                icon: const Icon(Icons.cable),
                                label: const Text('Read settings from radio'),
                              ),
                            if (hasImage)
                              OutlinedButton.icon(
                                onPressed: _settingsLoading || _busy
                                    ? null
                                    : () => _loadRadioSettings(force: true),
                                icon: const Icon(Icons.refresh),
                                label: const Text('Reload stored image'),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                if (_settingsLoading)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Row(
                        children: [
                          SizedBox(
                            width: 22,
                            height: 22,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          SizedBox(width: 14),
                          Text('Loading radio settings...'),
                        ],
                      ),
                    ),
                  )
                else if (!hasImage)
                  _settingsMessage(
                    icon: Icons.info_outline,
                    title: 'Read radio settings',
                    body: canReadRadio
                        ? 'Read the current settings directly from the connected '
                              'radio. This refreshes the stored image and settings '
                              'only; the current channel list is not changed.'
                        : 'Select the programming cable and exact model on Radio '
                              'connection, then read the radio to load its '
                              'settings.',
                    action: canReadRadio
                        ? FilledButton.icon(
                            onPressed: _settingsLoading || _busy
                                ? null
                                : _readRadioSettings,
                            icon: const Icon(Icons.cable),
                            label: const Text('Read settings from radio'),
                          )
                        : FilledButton.icon(
                            onPressed: _openRadioConnection,
                            icon: const Icon(Icons.settings_input_antenna),
                            label: const Text('Open radio connection'),
                          ),
                  )
                else if (_settingsError != null)
                  _settingsMessage(
                    icon: Icons.error_outline,
                    title: 'Could not load radio settings',
                    body: _settingsError!,
                    action: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        if (canReadRadio)
                          FilledButton.icon(
                            onPressed: _settingsLoading || _busy
                                ? null
                                : _readRadioSettings,
                            icon: const Icon(Icons.cable),
                            label: const Text('Read settings from radio'),
                          ),
                        TextButton.icon(
                          onPressed: _settingsLoading || _busy
                              ? null
                              : () => _loadRadioSettings(force: true),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Reload stored image'),
                        ),
                      ],
                    ),
                  )
                else if (settings == null)
                  _settingsMessage(
                    icon: Icons.tune,
                    title: 'Settings have not loaded yet',
                    body: canReadRadio
                        ? 'Choose Read settings from radio for the current values, or '
                              'reload the stored image for cached values.'
                        : 'Load the settings from the stored radio image.',
                    action: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        if (canReadRadio)
                          FilledButton.icon(
                            onPressed: _settingsLoading || _busy
                                ? null
                                : _readRadioSettings,
                            icon: const Icon(Icons.cable),
                            label: const Text('Read settings from radio'),
                          ),
                        TextButton.icon(
                          onPressed: _settingsLoading || _busy
                              ? null
                              : () => _loadRadioSettings(force: true),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Reload stored image'),
                        ),
                      ],
                    ),
                  )
                else if (!hasSettings)
                  _settingsMessage(
                    icon: Icons.tune,
                    title: 'This radio does not expose global settings',
                    body:
                        'The selected CHIRP driver does not provide radio-wide '
                        'settings. Per-channel settings are still available in '
                        'the channel editor.',
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
                                  ? 'Unsaved settings changes'
                                  : _settingsLoadedFromRadio
                                  ? 'Settings match the values last read from the radio.'
                                  : 'Settings match the stored radio image.',
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
                            child: const Text('Discard changes'),
                          ),
                          const SizedBox(width: 10),
                          if (_port == null)
                            OutlinedButton.icon(
                              onPressed: _openRadioConnection,
                              icon: const Icon(Icons.cable),
                              label: const Text('Connect radio to write'),
                            )
                          else
                            FilledButton.icon(
                              onPressed:
                                  _settingsDirty && !_settingsHaveInvalidValues
                                  ? _writeRadioSettings
                                  : null,
                              icon: const Icon(Icons.save_outlined),
                              label: const Text('Write settings to radio'),
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
          const Padding(
            padding: EdgeInsets.only(top: 10),
            child: Text(
              'No editable options in this group.',
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
                'Radio connection',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Read channels from the radio first, edit them in the library, then write the verified image back.',
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
                          'Experimental CHIRP module loaded: '
                          '$_chirpModuleName',
                          style: const TextStyle(
                            color: Color(0xFF73420F),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: _busy ? null : _unloadChirpModule,
                        child: const Text('Unload'),
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
                      const _StepTitle(
                        number: '1',
                        title: 'Choose a programming cable',
                        help:
                            'NewChirp finds USB serial and mass-storage programming interfaces '
                            'automatically. Choose the one that matches your radio connection. '
                            'If nothing appears, connect the radio and press refresh.',
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              initialValue:
                                  _ports.any((port) => port.port == _port)
                                  ? _port
                                  : null,
                              isExpanded: true,
                              decoration: const InputDecoration(
                                labelText: 'Programming interface',
                                prefixIcon: Icon(Icons.cable),
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
                            tooltip: 'Refresh interfaces',
                            icon: const Icon(Icons.refresh),
                          ),
                          const SizedBox(width: 2),
                          const _HelpButton(
                            title: 'Refresh interfaces',
                            details:
                                'Rescan the system for USB serial and mass-storage '
                                'programming interfaces. If your radio is not listed, '
                                'connect it and press refresh.',
                          ),
                        ],
                      ),
                      if (_ports.isEmpty)
                        const Padding(
                          padding: EdgeInsets.only(top: 10),
                          child: Text(
                            'No programming interface detected. Connect the radio and '
                            'choose refresh.',
                            style: TextStyle(color: Color(0xFF9B5B18)),
                          ),
                        ),
                      const Padding(
                        padding: EdgeInsets.symmetric(vertical: 22),
                        child: Divider(),
                      ),
                      const _StepTitle(
                        number: '2',
                        title: 'Choose the exact radio model',
                        help:
                            'Load the supported radio catalog and select the exact model. Using the '
                            'wrong model can corrupt a radio. If a stored image already exists for '
                            'this model, writing is unlocked without reading again.',
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
                                label: const Text(
                                  'Load supported radio catalog',
                                ),
                              ),
                            ),
                            const SizedBox(width: 2),
                            const _HelpButton(
                              title: 'Load supported radio catalog',
                              details:
                                  'Fetch the list of radio models supported by the bundled CHIRP '
                                  'driver tree. Select the exact model before reading or writing.',
                            ),
                          ],
                        )
                      else
                        RadioModelPicker(
                          models: _models,
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
                      const _StepTitle(
                        number: '3',
                        title: 'Transfer safely',
                        help:
                            'Read channels pulls the full memory image from the radio, replaces the '
                            'current channel list, and stores the image for this model. Radio '
                            'settings have a separate read action on the Radio settings page. Write '
                            'sends the current channel list back using the stored image. Keep the '
                            'radio connected and powered on during either transfer.',
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton.icon(
                              onPressed:
                                  _busy || _port == null || _model == null
                                  ? null
                                  : _downloadRadio,
                              icon: const Icon(Icons.south),
                              label: const Padding(
                                padding: EdgeInsets.symmetric(vertical: 12),
                                child: Text('Read channels from radio'),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: _busy || _radioImage == null
                                  ? null
                                  : _uploadRadio,
                              icon: const Icon(Icons.north),
                              label: const Padding(
                                padding: EdgeInsets.symmetric(vertical: 12),
                                child: Text('Write to radio'),
                              ),
                            ),
                          ),
                          const SizedBox(width: 2),
                          const _HelpButton(
                            title: 'Transfer safely',
                            details:
                                'Read channels pulls the full memory image from the radio, replaces '
                                'the current channel list, and stores the image for this model. '
                                'Radio settings have a separate read action on the Radio settings '
                                'page. Write sends the current channel list back using that image. '
                                'Keep the radio connected and powered on during either.',
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
                                      ? 'No image for this model yet. Read once to enable writing.'
                                      : storedImageReady
                                      ? 'Stored image for ${_model!.replaceAll('_', ' ')} is ready. '
                                            'You can write without reading again.'
                                      : 'A radio image was read this session. '
                                            'Review all changes before writing.',
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
              const SizedBox(height: 14),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(18),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.info_outline, color: Color(0xFF1F7455)),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'NewChirp uses the provided CHIRP driver tree as its hardware compatibility layer. Its serial package is bundled, so CHIRP GUI dependencies such as wxPython are not needed.',
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
            label: 'Channel library',
            icon: Icons.table_rows_outlined,
            selected: page == 0,
            onTap: () => onPage(0),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: 'Radio connection',
            icon: Icons.settings_input_antenna,
            selected: page == 1,
            onTap: () => onPage(1),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: 'Find repeaters',
            icon: Icons.travel_explore,
            selected: false,
            onTap: onFindRepeaters,
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: 'Radio settings',
            icon: Icons.tune,
            selected: page == 4,
            onTap: () => onPage(4),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: 'Frequency reference',
            icon: Icons.table_chart_outlined,
            selected: page == 3,
            onTap: () => onPage(3),
          ),
          const SizedBox(height: 6),
          _NavItem(
            label: 'About & licenses',
            icon: Icons.info_outline,
            selected: page == 2,
            onTap: () => onPage(2),
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(10),
            child: Text(
              'DESKTOP RADIO PROGRAMMER\nRick Lopez · Lead Programmer\nrick@newchirp.net\nVersion $_newChirpVersion',
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
                          ? 'Preparing transfer...'
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
                          ? 'Waiting for the radio to report progress'
                          : '$percent% complete  |  $_elapsedText elapsed',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.black54),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Keep the radio powered on and the cable connected.',
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
        error = 'Enter a whole number';
      } else if (node.min != null && parsed < node.min!) {
        error = 'Value must be at least ${node.min}';
      } else if (node.max != null && parsed > node.max!) {
        error = 'Value must be at most ${node.max}';
      } else {
        node.value = parsed;
      }
    } else if (node.kind == 'number') {
      final parsed = double.tryParse(text.trim());
      if (parsed == null) {
        error = 'Enter a number';
      } else if (node.min != null && parsed < node.min!) {
        error = 'Value must be at least ${node.min}';
      } else if (node.max != null && parsed > node.max!) {
        error = 'Value must be at most ${node.max}';
      } else {
        node.value = parsed;
      }
    } else {
      final length = text.length;
      if (node.minLength != null && length < node.minLength!) {
        error = 'Use at least ${node.minLength} characters';
      } else if (node.maxLength != null && length > node.maxLength!) {
        error = 'Use at most ${node.maxLength} characters';
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
        '${node.label}: this setting type is not supported yet.',
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

const _glossaryTerms = <(String, String)>[
  (
    'FRS',
    'Family Radio Service. A license-free UHF service in the United States.',
  ),
  (
    'GMRS',
    'General Mobile Radio Service. A licensed UHF service in the United States.',
  ),
  ('RX', 'Receive. The frequency or tone used when listening.'),
  ('TX', 'Transmit. The frequency or tone used when sending.'),
  (
    'CTCSS',
    'Continuous Tone-Coded Squelch System. A subaudible analog tone commonly called a PL tone.',
  ),
  (
    'TSQL',
    'Tone squelch. Requires a matching CTCSS tone for both receive and transmit.',
  ),
  (
    'DCS',
    'Digital-Coded Squelch System. A digital squelch code; NewChirp labels it DTCS.',
  ),
  (
    'DTCS',
    'Digital-Coded Squelch System. A digital code used like a CTCSS tone to open a receiver or repeater.',
  ),
  (
    'DTCS POL',
    'DTCS polarity. Normal or inverted code polarity must match between the radio and repeater.',
  ),
  ('FM', 'Frequency modulation. Standard analog voice mode.'),
  (
    'NFM',
    'Narrowband FM. Uses less bandwidth and is common on FRS, GMRS, and busy repeater systems.',
  ),
  (
    'AM',
    'Amplitude modulation. Used by some aircraft and amateur-radio channels.',
  ),
  (
    'DUPLEX',
    'Transmit/receive relationship. Simplex uses the same frequency; offsets and splits use different transmit frequencies.',
  ),
  ('OFFSET', 'The frequency difference between receive and transmit.'),
  (
    'SPLIT',
    'Independent receive and transmit frequencies rather than a fixed offset.',
  ),
  ('STEP', 'Tuning step size used when changing frequency.'),
  ('SCAN', 'Whether the channel is included in scanning or marked to skip.'),
  (
    'BCL',
    'Busy Channel Lockout. Prevents transmitting when the channel is already in use.',
  ),
  (
    'PTT ID',
    'Station identification sent at the beginning or end of a transmission, depending on the radio.',
  ),
  (
    'S-CODE',
    'Signaling code selector. Chooses which stored PTT-ID or signaling code the channel uses.',
  ),
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
    final terms = _glossaryTerms
        .where(
          (entry) =>
              query.isEmpty ||
              entry.$1.toLowerCase().contains(query) ||
              entry.$2.toLowerCase().contains(query),
        )
        .toList();
    return AlertDialog(
      title: const Text('Abbreviations & terms'),
      content: SizedBox(
        width: 640,
        height: 520,
        child: Column(
          children: [
            TextField(
              controller: _controller,
              autofocus: true,
              onChanged: (value) => setState(() => _query = value),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Search abbreviations or definitions',
              ),
            ),
            const SizedBox(height: 14),
            Expanded(
              child: terms.isEmpty
                  ? const Center(child: Text('No matching terms.'))
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
          child: const Text('Close'),
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
    required this.checkingForUpdates,
    required this.onCheckForUpdates,
    required this.onLoadChirpModule,
    required this.onUnloadChirpModule,
    required this.onNew,
    required this.onGmrsStarter,
    required this.onRestoreStock,
    required this.onOpen,
    required this.onSave,
    required this.onSaveAs,
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
  final bool checkingForUpdates;
  final VoidCallback onCheckForUpdates;
  final VoidCallback onLoadChirpModule;
  final VoidCallback onUnloadChirpModule;
  final VoidCallback onNew;
  final VoidCallback onGmrsStarter;
  final VoidCallback onRestoreStock;
  final VoidCallback onOpen;
  final VoidCallback onSave;
  final VoidCallback onSaveAs;
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
                label: const Text('Print'),
              ),
            const SizedBox(width: 8),
            _buildHelpMenu(context),
          ],
        ),
      );
    }

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
                      const Padding(
                        padding: EdgeInsets.only(left: 7),
                        child: Text(
                          '• Edited',
                          style: TextStyle(
                            color: Color(0xFFC46A15),
                            fontSize: 12,
                          ),
                        ),
                      ),
                  ],
                ),
                Text(
                  busy
                      ? status
                      : chirpModuleName == null
                      ? 'CHIRP-compatible channel library'
                      : 'Experimental CHIRP module: $chirpModuleName',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: busy
                        ? const Color(0xFF1F7455)
                        : chirpModuleName != null
                        ? const Color(0xFF9B5B18)
                        : Colors.black45,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          MenuAnchor(
            builder: (context, controller, child) => TextButton.icon(
              onPressed: busy
                  ? null
                  : () => controller.isOpen
                        ? controller.close()
                        : controller.open(),
              icon: const Icon(Icons.note_add_outlined),
              label: const Text('New'),
            ),
            menuChildren: [
              MenuItemButton(
                onPressed: onNew,
                leadingIcon: const Icon(Icons.note_add_outlined),
                child: const Text('Blank configuration'),
              ),
              MenuItemButton(
                onPressed: onGmrsStarter,
                leadingIcon: const Icon(Icons.view_list_outlined),
                child: const Text('GMRS starter template'),
              ),
              MenuItemButton(
                onPressed: onRestoreStock,
                leadingIcon: const Icon(Icons.restore),
                child: const Text('Restore stock channels'),
              ),
            ],
          ),
          TextButton.icon(
            onPressed: busy ? null : onOpen,
            icon: const Icon(Icons.folder_open_outlined),
            label: const Text('Open file'),
          ),
          MenuAnchor(
            builder: (context, controller, child) => FilledButton.icon(
              onPressed: busy || !canSave
                  ? null
                  : () => controller.isOpen
                        ? controller.close()
                        : controller.open(),
              icon: const Icon(Icons.save_outlined),
              label: const Text('Save'),
            ),
            menuChildren: [
              MenuItemButton(onPressed: onSave, child: const Text('Save')),
              MenuItemButton(
                onPressed: onSaveAs,
                child: const Text('Save as…'),
              ),
            ],
          ),
          const SizedBox(width: 8),
          _buildHelpMenu(context),
        ],
      ),
    );
  }

  Widget _buildHelpMenu(BuildContext context) {
    return MenuAnchor(
      builder: (context, controller, child) => TextButton.icon(
        onPressed: () =>
            controller.isOpen ? controller.close() : controller.open(),
        icon: const Icon(Icons.help_outline),
        label: const Text('Help'),
      ),
      menuChildren: [
        MenuItemButton(
          onPressed: () => _showAbbreviationGlossary(context),
          leadingIcon: const Icon(Icons.menu_book_outlined),
          child: const Text('Abbreviations & terms'),
        ),
        const Divider(height: 1),
        MenuItemButton(
          onPressed: busy ? null : onLoadChirpModule,
          leadingIcon: const Icon(Icons.extension_outlined),
          child: const Text('Load CHIRP driver module…'),
        ),
        if (chirpModuleName != null)
          MenuItemButton(
            onPressed: busy ? null : onUnloadChirpModule,
            leadingIcon: const Icon(Icons.extension_off_outlined),
            child: const Text('Unload CHIRP module'),
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
                ? 'Checking for updates...'
                : 'Check for updates',
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
  final int? selectedZone;
  final Set<int> clearedLocations;
}

class _ChannelApplyDialog extends StatefulWidget {
  const _ChannelApplyDialog({
    required this.label,
    required this.count,
    required this.initialStart,
  });

  final String label;
  final int count;
  final int initialStart;

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
      title: Text('Apply ${widget.label}'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Choose how to add these channels to the current list.'),
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
                  title: const Text('Replace the current channel list'),
                  subtitle: const Text(
                    'Unsaved edits to the current list will be lost.',
                  ),
                ),
                RadioListTile<bool>(
                  value: false,
                  title: const Text('Insert starting at channel number'),
                  subtitle: Text(
                    'Channels in the ${widget.count}-channel range will be '
                    'overwritten.',
                  ),
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
                labelText: 'Starting channel number',
                errorText: _startError,
              ),
            ),
          ],
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(onPressed: _apply, child: const Text('Apply')),
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
      setState(() => _startError = 'Enter a channel number of 1 or higher.');
      return;
    }
    Navigator.pop(
      context,
      _ChannelApplyMode(replaceAll: false, startAt: start),
    );
  }
}

const _repeaterStates = <String>[
  'Alabama',
  'Alaska',
  'Arizona',
  'Arkansas',
  'California',
  'Colorado',
  'Connecticut',
  'Delaware',
  'District of Columbia',
  'Florida',
  'Georgia',
  'Guam',
  'Hawaii',
  'Idaho',
  'Illinois',
  'Indiana',
  'Iowa',
  'Kansas',
  'Kentucky',
  'Louisiana',
  'Maine',
  'Maryland',
  'Massachusetts',
  'Michigan',
  'Minnesota',
  'Mississippi',
  'Missouri',
  'Montana',
  'Nebraska',
  'Nevada',
  'New Hampshire',
  'New Jersey',
  'New Mexico',
  'New York',
  'North Carolina',
  'North Dakota',
  'Ohio',
  'Oklahoma',
  'Oregon',
  'Pennsylvania',
  'Puerto Rico',
  'Rhode Island',
  'South Carolina',
  'South Dakota',
  'Tennessee',
  'Texas',
  'Utah',
  'Vermont',
  'Virgin Islands',
  'Virginia',
  'Washington',
  'West Virginia',
  'Wisconsin',
  'Wyoming',
];

class RepeaterBookDialog extends StatefulWidget {
  const RepeaterBookDialog({super.key, required this.bridge});

  final RadioBridge bridge;

  @override
  State<RepeaterBookDialog> createState() => _RepeaterBookDialogState();
}

class _RepeaterBookDialogState extends State<RepeaterBookDialog> {
  final _filterController = TextEditingController();
  final _latitudeController = TextEditingController();
  final _longitudeController = TextEditingController();
  final _distanceController = TextEditingController();
  final _resultFilterController = TextEditingController();
  String _state = 'New York';
  String _service = 'all';
  bool _fmOnly = true;
  bool _openOnly = true;
  bool _mapView = false;
  bool _loading = false;
  String _status = '';
  String? _error;
  RepeaterSearchResults? _results;
  final Set<RepeaterSearchResult> _selected = {};
  RepeaterSortOrder _sortOrder = RepeaterSortOrder.source;
  Size? _dialogSize;
  final MapController _mapController = MapController();

  @override
  void dispose() {
    _filterController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    _distanceController.dispose();
    _resultFilterController.dispose();
    _mapController.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final latitude = double.tryParse(_latitudeController.text.trim());
    final longitude = double.tryParse(_longitudeController.text.trim());
    final distance = double.tryParse(_distanceController.text.trim());
    if ((latitude == null) != (longitude == null)) {
      setState(() => _error = 'Enter both latitude and longitude, or neither.');
      return;
    }
    if (latitude != null && (latitude < -90 || latitude > 90)) {
      setState(() => _error = 'Latitude must be between -90 and 90.');
      return;
    }
    if (longitude != null && (longitude < -180 || longitude > 180)) {
      setState(() => _error = 'Longitude must be between -180 and 180.');
      return;
    }
    if (distance != null && latitude == null) {
      setState(
        () =>
            _error = 'Latitude and longitude are required for a radius search.',
      );
      return;
    }
    if (distance != null && distance <= 0) {
      setState(() => _error = 'Radius must be greater than zero.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
      _results = null;
      _selected.clear();
      _status = 'Searching RepeaterBook…';
    });
    try {
      final results = await widget.bridge.searchRepeaters(
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
          _error = _service == 'gmrs'
              ? 'No matching GMRS repeaters were found. RepeaterBook may '
                    'not have a GMRS listing for this area yet.'
              : 'No matching repeaters were found.';
        }
      });
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<RadioChannel> get _selectedChannels {
    return [for (final result in _selected) result.channel.copy()];
  }

  void _searchAmateurInstead() {
    setState(() => _service = 'amateur');
    _search();
  }

  String _channelDetail(RepeaterSearchResult result) {
    final channel = result.channel;
    final frequency = '${channel.frequency.toStringAsFixed(4)} MHz';
    final tone = channel.tone.isEmpty ? 'no tone' : channel.tone;
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
          const Positioned.fill(
            child: ColoredBox(
              color: Color(0xCCFFFFFF),
              child: Center(
                child: Text('No coordinates are available for these results.'),
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
                  '${points.length} mapped • tap a pin to select',
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
                  const Text(
                    'Find repeaters',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 14),
                  Expanded(
                    child: SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Search RepeaterBook and add selected repeater channels to '
                            'your current library. Verify repeater status and access '
                            'before transmitting.',
                            style: TextStyle(color: Colors.black54),
                          ),
                          const SizedBox(height: 14),
                          Row(
                            children: [
                              Expanded(
                                child: DropdownButtonFormField<String>(
                                  isExpanded: true,
                                  initialValue: _state,
                                  decoration: const InputDecoration(
                                    labelText: 'State or territory',
                                  ),
                                  items: _repeaterStates
                                      .map(
                                        (state) => DropdownMenuItem(
                                          value: state,
                                          child: Text(state),
                                        ),
                                      )
                                      .toList(),
                                  onChanged: _loading
                                      ? null
                                      : (value) {
                                          if (value != null) {
                                            setState(() => _state = value);
                                          }
                                        },
                                ),
                              ),
                              const SizedBox(width: 12),
                              SizedBox(
                                width: 190,
                                child: DropdownButtonFormField<String>(
                                  isExpanded: true,
                                  initialValue: _service,
                                  decoration: const InputDecoration(
                                    labelText: 'Service',
                                  ),
                                  items: const [
                                    DropdownMenuItem(
                                      value: 'all',
                                      child: Text('Amateur + GMRS'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'amateur',
                                      child: Text('Amateur (ham)'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'gmrs',
                                      child: Text('GMRS'),
                                    ),
                                  ],
                                  onChanged: _loading
                                      ? null
                                      : (value) {
                                          if (value != null) {
                                            setState(() => _service = value);
                                          }
                                        },
                                ),
                              ),
                              const SizedBox(width: 12),
                              SizedBox(
                                width: 165,
                                child:
                                    DropdownButtonFormField<RepeaterSortOrder>(
                                      isExpanded: true,
                                      initialValue: _sortOrder,
                                      decoration: const InputDecoration(
                                        labelText: 'Sort results',
                                      ),
                                      items: const [
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.source,
                                          child: Text('Source order'),
                                        ),
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.city,
                                          child: Text('City'),
                                        ),
                                        DropdownMenuItem(
                                          value: RepeaterSortOrder.county,
                                          child: Text('County'),
                                        ),
                                      ],
                                      onChanged: (value) {
                                        if (value != null) {
                                          setState(() => _sortOrder = value);
                                        }
                                      },
                                    ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _filterController,
                            enabled: !_loading,
                            onSubmitted: (_) => _search(),
                            decoration: const InputDecoration(
                              labelText:
                                  'City, county, callsign, landmark, or notes',
                              prefixIcon: Icon(Icons.search),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: _latitudeController,
                                  enabled: !_loading,
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                        signed: true,
                                      ),
                                  decoration: const InputDecoration(
                                    labelText: 'Latitude (optional)',
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: _longitudeController,
                                  enabled: !_loading,
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                        signed: true,
                                      ),
                                  decoration: const InputDecoration(
                                    labelText: 'Longitude (optional)',
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: TextField(
                                  controller: _distanceController,
                                  enabled: !_loading,
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  decoration: const InputDecoration(
                                    labelText: 'Radius km',
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
                                title: const Text('Open repeaters only'),
                                value: _openOnly,
                                onChanged: _loading
                                    ? null
                                    : (value) => setState(
                                        () => _openOnly = value ?? false,
                                      ),
                              ),
                              CheckboxListTile(
                                contentPadding: EdgeInsets.zero,
                                dense: true,
                                controlAffinity:
                                    ListTileControlAffinity.leading,
                                title: const Text('FM-capable only'),
                                value: _fmOnly,
                                onChanged: _loading
                                    ? null
                                    : (value) => setState(
                                        () => _fmOnly = value ?? false,
                                      ),
                              ),
                            ],
                          ),
                          if (_loading) ...[
                            const LinearProgressIndicator(),
                            const SizedBox(height: 6),
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
                                label: const Text(
                                  'Search Amateur repeaters instead',
                                ),
                              ),
                          ],
                          if (results != null) ...[
                            const SizedBox(height: 8),
                            TextField(
                              controller: _resultFilterController,
                              onChanged: (_) => setState(() {}),
                              decoration: InputDecoration(
                                isDense: true,
                                labelText: 'Filter loaded results',
                                hintText:
                                    'City, county, callsign, mode, service, or frequency',
                                prefixIcon: const Icon(
                                  Icons.filter_alt_outlined,
                                ),
                                suffixIcon: _resultFilterController.text.isEmpty
                                    ? null
                                    : IconButton(
                                        tooltip: 'Clear result filter',
                                        onPressed: () => setState(
                                          _resultFilterController.clear,
                                        ),
                                        icon: const Icon(Icons.close),
                                      ),
                              ),
                            ),
                          ],
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  results == null
                                      ? 'Search to preview repeater channels.'
                                      : '${visibleResults.length} shown'
                                            ' of ${results.results.length} loaded'
                                            ' • Data from RepeaterBook.com',
                                  style: const TextStyle(
                                    color: Colors.black54,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                              if (results != null &&
                                  visibleResults.isNotEmpty) ...[
                                SegmentedButton<bool>(
                                  segments: const [
                                    ButtonSegment(
                                      value: false,
                                      icon: Icon(Icons.view_list_outlined),
                                      label: Text('List'),
                                    ),
                                    ButtonSegment(
                                      value: true,
                                      icon: Icon(Icons.map_outlined),
                                      label: Text('Map'),
                                    ),
                                  ],
                                  selected: {_mapView},
                                  showSelectedIcon: false,
                                  style: const ButtonStyle(
                                    visualDensity: VisualDensity.compact,
                                  ),
                                  onSelectionChanged: (selection) {
                                    setState(() => _mapView = selection.first);
                                  },
                                ),
                                const SizedBox(width: 8),
                                TextButton(
                                  onPressed: () => setState(
                                    () => _selected.addAll(visibleResults),
                                  ),
                                  child: const Text('Select all'),
                                ),
                                TextButton(
                                  onPressed: () => setState(_selected.clear),
                                  child: const Text('Clear'),
                                ),
                              ],
                            ],
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
                                : ListView.separated(
                                    itemCount: visibleResults.length,
                                    separatorBuilder: (_, _) =>
                                        const Divider(height: 1),
                                    itemBuilder: (context, index) {
                                      final result = visibleResults[index];
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
                        child: const Text('Close'),
                      ),
                      const SizedBox(width: 8),
                      FilledButton.tonalIcon(
                        onPressed: _loading ? null : _search,
                        icon: const Icon(Icons.search),
                        label: const Text('Search'),
                      ),
                      const SizedBox(width: 8),
                      FilledButton.icon(
                        onPressed: _selected.isEmpty || _loading
                            ? null
                            : () => Navigator.pop(context, _selectedChannels),
                        icon: const Icon(Icons.add),
                        label: Text(
                          _selected.isEmpty
                              ? 'Add selected'
                              : 'Add ${_selected.length} selected',
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
                  message: 'Drag to resize',
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
                child: const Text('Close'),
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

class _ChannelColumn {
  _ChannelColumn(this.label, this.width, this.value, {String? id, this.help})
    : id = id ?? label;
  final String id;
  final String label;
  double width;
  final String Function(RadioChannel) value;
  final String? help;
}

class _ChannelTable extends StatefulWidget {
  const _ChannelTable({
    super.key,
    required this.entries,
    required this.selected,
    required this.radioModel,
    required this.capabilities,
    required this.columnOrder,
    required this.columnWidths,
    required this.onColumnOrderChanged,
    required this.onColumnWidthChanged,
    required this.onSelect,
    required this.clipboardNotEmpty,
    required this.onCopy,
    required this.onCut,
    required this.onPaste,
    required this.onDuplicate,
    required this.onClear,
    required this.onMove,
    required this.reorderEnabled,
    required this.onOpen,
  });

  final List<MapEntry<int, RadioChannel>> entries;
  final int selected;
  final String? radioModel;
  final RadioCapabilities? capabilities;
  final List<String> columnOrder;
  final Map<String, double> columnWidths;
  final ValueChanged<List<String>> onColumnOrderChanged;
  final void Function(String id, double width) onColumnWidthChanged;
  final ValueChanged<int> onSelect;
  final bool clipboardNotEmpty;
  final ValueChanged<int> onCopy;
  final ValueChanged<int> onCut;
  final Future<void> Function(int) onPaste;
  final ValueChanged<int> onDuplicate;
  final ValueChanged<int> onClear;
  final void Function(int fromIndex, int toIndex) onMove;
  final bool reorderEnabled;
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
    super.dispose();
  }

  void _showRowMenu(BuildContext context, int index, Offset position) {
    final isCleared = widget.entries.any(
      (entry) => entry.key == index && entry.value.cleared,
    );
    showMenu<int>(
      context: context,
      position: RelativeRect.fromLTRB(
        position.dx,
        position.dy,
        position.dx,
        position.dy,
      ),
      items: [
        PopupMenuItem(value: 0, enabled: !isCleared, child: const Text('Copy')),
        PopupMenuItem(value: 1, enabled: !isCleared, child: const Text('Cut')),
        PopupMenuItem(
          value: 2,
          enabled: widget.clipboardNotEmpty,
          child: const Text('Paste'),
        ),
        PopupMenuItem(
          value: 3,
          enabled: !isCleared,
          child: const Text('Duplicate'),
        ),
        PopupMenuItem(
          value: 4,
          enabled: !isCleared,
          child: const Text('Clear channel'),
        ),
      ],
    ).then((value) {
      switch (value) {
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
      _ChannelColumn(
        'NAME',
        160,
        (channel) => channel.name.isEmpty ? '—' : channel.name,
        help: 'Channel name stored in the radio memory.',
      ),
      _ChannelColumn(
        'RX FREQUENCY',
        126,
        (channel) => channel.frequency <= 0
            ? ''
            : channel.frequency.toStringAsFixed(6),
        help: 'Receive frequency: the frequency the radio listens on.',
      ),
      _ChannelColumn(
        'TONE MODE',
        96,
        (channel) => channel.tone.isEmpty ? 'None' : channel.tone,
        help:
            'Receive/transmit squelch mode. Tone is CTCSS, TSQL is tone '
            'squelch, DTCS is a digital code, and Cross uses different tones.',
      ),
      _ChannelColumn(
        'TX TONE',
        82,
        (channel) => inactive(
          channel.tone == 'Tone' ||
              (channel.tone == 'Cross' && channel.crossMode.startsWith('Tone')),
          channel.txTone.toStringAsFixed(1),
        ),
        help: 'Transmit CTCSS tone in hertz. Set Tone Mode to Tone first.',
      ),
      _ChannelColumn(
        'RX TONE',
        82,
        (channel) => inactive(
          channel.tone == 'TSQL' ||
              (channel.tone == 'Cross' && channel.crossMode.endsWith('Tone')),
          channel.rxTone.toStringAsFixed(1),
        ),
        help:
            'Receive CTCSS tone in hertz. Set Tone Mode to TSQL or a matching '
            'Cross mode first.',
      ),
      _ChannelColumn(
        'DTCS',
        66,
        (channel) => inactive(
          channel.tone == 'DTCS' ||
              (channel.tone == 'Cross' && channel.crossMode.startsWith('DTCS')),
          channel.dtcs.toString().padLeft(3, '0'),
        ),
        help: 'Transmit DTCS digital squelch code.',
      ),
      _ChannelColumn(
        'RX DTCS',
        76,
        (channel) => inactive(
          channel.tone == 'Cross' && channel.crossMode.endsWith('DTCS'),
          channel.rxDtcs.toString().padLeft(3, '0'),
        ),
        help: 'Receive DTCS digital squelch code.',
      ),
      _ChannelColumn(
        'DTCS POL',
        76,
        (channel) => inactive(
          channel.tone == 'DTCS' ||
              (channel.tone == 'Cross' && channel.crossMode.contains('DTCS')),
          channel.dtcsPolarity,
        ),
        help: 'DTCS polarity: normal or inverted for transmit and receive.',
      ),
      _ChannelColumn(
        'DUPLEX',
        82,
        (channel) => channel.duplex.isEmpty ? 'Simplex' : channel.duplex,
        help:
            'Transmit/receive relationship. Simplex uses one frequency; '
            'offsets or split use different transmit frequencies.',
      ),
      _ChannelColumn(
        'OFFSET / TX FREQ',
        132,
        (channel) => inactive(
          channel.duplex.isNotEmpty && channel.duplex != 'off',
          channel.offset.toStringAsFixed(6),
        ),
        help:
            'Frequency offset, or the independent transmit frequency for split.',
      ),
      _ChannelColumn(
        'CROSS MODE',
        112,
        (channel) => inactive(channel.tone == 'Cross', channel.crossMode),
        help: 'Separate receive and transmit tone/code modes used with Cross.',
      ),
      _ChannelColumn(
        'MODE',
        68,
        (channel) => channel.mode,
        help:
            'Voice modulation: FM, narrowband FM, or AM depending on the radio.',
      ),
      if (showStep)
        _ChannelColumn(
          'STEP',
          68,
          (channel) => channel.step.toStringAsFixed(2),
          help: 'Tuning step size in kHz.',
        ),
      _ChannelColumn(
        'POWER',
        82,
        (channel) => channel.power.isEmpty ? '—' : channel.power,
        help: 'Selected transmit power level.',
      ),
      _ChannelColumn(
        'SCAN',
        72,
        (channel) => scanLabel(channel.skip),
        help: 'Whether the channel is included in scanning.',
      ),
      _ChannelColumn(
        'COMMENT',
        210,
        (channel) => channel.comment.isEmpty ? '—' : channel.comment,
        help: 'Free-form notes stored with the channel when supported.',
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
        column.label,
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
                message: column.help == null
                    ? 'Drag to reorder column'
                    : '${column.help}\n\nDrag to reorder column',
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
    double dragHandleWidth,
  ) {
    final isCleared = entry.value.cleared;
    final canDrag = widget.reorderEnabled && !isCleared;
    final dragLabel = entry.value.name.isEmpty
        ? 'Channel ${channelNumberLabel(widget.radioModel, entry.value.location)}'
        : entry.value.name;
    return DragTarget<int>(
      onWillAcceptWithDetails: (details) =>
          widget.reorderEnabled && details.data != entry.key,
      onAcceptWithDetails: (details) => widget.onMove(details.data, entry.key),
      builder: (context, candidates, rejected) {
        final isDropTarget = candidates.isNotEmpty;
        return Listener(
          behavior: HitTestBehavior.opaque,
          onPointerDown: (_) => widget.onSelect(entry.key),
          child: GestureDetector(
            onSecondaryTapDown: (details) =>
                _showRowMenu(context, entry.key, details.globalPosition),
            child: Tooltip(
              message: isCleared
                  ? 'Empty channel'
                  : 'Double-click to edit channel',
              child: InkWell(
                onDoubleTap: () => widget.onOpen(entry.key),
                child: Container(
                  height: 45,
                  color: isDropTarget
                      ? const Color(0xFFD7EAE1)
                      : entry.key == widget.selected
                      ? const Color(0xFFE8F3ED)
                      : isCleared
                      ? const Color(0xFFFAFAFA)
                      : Colors.white,
                  child: Row(
                    children: [
                      SizedBox(
                        width: dragHandleWidth,
                        child: Draggable<int>(
                          data: entry.key,
                          maxSimultaneousDrags: canDrag ? 1 : 0,
                          onDragStarted: () => widget.onSelect(entry.key),
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
                                'Move $dragLabel',
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
                                  ? 'Drag to rearrange channel'
                                  : 'Clear search to rearrange channels',
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
                                isCleared && column.label != '#'
                                    ? '—'
                                    : column.value(entry.value),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontWeight: column.label == 'NAME'
                                      ? FontWeight.w600
                                      : FontWeight.w400,
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
                        child: const Tooltip(
                          message: 'Drag rows to rearrange channels',
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
                Expanded(
                  child: Scrollbar(
                    controller: _verticalController,
                    child: ListView.builder(
                      controller: _verticalController,
                      itemExtent: 45,
                      itemCount: widget.entries.length,
                      itemBuilder: (context, index) {
                        final entry = widget.entries[index];
                        return _channelRow(
                          context,
                          entry,
                          columns,
                          dragHandleWidth,
                        );
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 10),
              ],
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
  });
  final RadioChannel channel;
  final String? radioModel;
  final RadioCapabilities? capabilities;
  final void Function(VoidCallback) onChanged;
  final VoidCallback onSave;
  final VoidCallback onDelete;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final issues = channel.validate(
      minimumLocation: capabilities?.memoryStart,
      maximumLocation: capabilities?.memoryEnd,
      radioModel: radioModel,
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
    final blocking = midlandGmrsIssues(radioModel, channel);
    Map<String, String> choices(
      List<String>? values,
      Map<String, String> fallback,
    ) {
      if (values == null || values.isEmpty) return fallback;
      return {
        for (final value in values) value: value.isEmpty ? 'None' : value,
      };
    }

    final toneModes = choices(capabilities?.toneModes, const {
      '': 'None',
      'Tone': 'Tone',
      'TSQL': 'Tone squelch',
      'DTCS': 'DTCS',
      'Cross': 'Cross',
    });
    final toneChoices = {
      for (final tone in capabilities?.tones ?? const <double>[])
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
    final usesTxTone =
        channel.tone == 'Tone' ||
        (channel.tone == 'Cross' && channel.crossMode.startsWith('Tone'));
    final usesRxTone =
        channel.tone == 'TSQL' ||
        (channel.tone == 'Cross' && channel.crossMode.endsWith('Tone'));
    final usesTxDtcs =
        channel.tone == 'DTCS' ||
        (channel.tone == 'Cross' && channel.crossMode.startsWith('DTCS'));
    final usesRxDtcs =
        channel.tone == 'DTCS' ||
        (channel.tone == 'Cross' && channel.crossMode.endsWith('DTCS'));
    final repeaterRow = isMidlandRepeaterRow(radioModel, channel.location);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 16, 10, 12),
            child: Row(
              children: [
                const Expanded(
                  child: Text(
                    'Channel details',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                ),
                IconButton(
                  onPressed: () => _showAbbreviationGlossary(context),
                  tooltip: 'Abbreviations & terms',
                  icon: const Icon(Icons.menu_book_outlined),
                ),
                IconButton(
                  onPressed: onDelete,
                  tooltip: repeaterRow ? 'Reset repeater' : 'Delete channel',
                  icon: Icon(
                    repeaterRow ? Icons.restart_alt : Icons.delete_outline,
                    color: repeaterRow ? null : const Color(0xFF9B3D34),
                  ),
                ),
                IconButton(
                  onPressed: onClose,
                  tooltip: 'Close editor',
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
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: showsMidlandChannelNumbers(radioModel)
                          ? _TextField(
                              label: 'Channel',
                              value: channelNumberLabel(
                                radioModel,
                                channel.location,
                              ),
                              readOnly: true,
                              onValue: (_) {},
                            )
                          : _NumberField(
                              label: 'Location',
                              value: channel.location.toDouble(),
                              decimals: 0,
                              onValue: (v) =>
                                  onChanged(() => channel.location = v.toInt()),
                            ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      flex: 2,
                      child: _TextField(
                        label: 'Name',
                        value: channel.name,
                        maxLength: capabilities?.nameLength,
                        onValue: (v) => onChanged(() => channel.name = v),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                if (midland)
                  _ChoiceField(
                    key: ValueKey(
                      'rx-${channel.location}-${channel.frequency}',
                    ),
                    label: 'Receive channel',
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
                  )
                else
                  _NumberField(
                    label: 'Receive frequency (MHz)',
                    value: channel.frequency,
                    decimals: 6,
                    onValue: (v) => onChanged(() => channel.frequency = v),
                  ),
                const SizedBox(height: 12),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: _ChoiceField(
                        key: ValueKey(
                          'dup-${channel.location}-${channel.duplex}-${channel.frequency}',
                        ),
                        label: 'Duplex',
                        value: channel.duplex,
                        enabled: !duplexLocked,
                        choices: midland
                            ? midlandDuplexChoices(
                                channel.location,
                                channel.duplex,
                                frequencyMhz: channel.frequency,
                              )
                            : choices(capabilities?.duplexes, const {
                                '': 'Simplex',
                                '+': '+ shift',
                                '-': '− shift',
                                'split': 'Split',
                                'off': 'TX off',
                              }),
                        onValue: (v) => onChanged(() {
                          channel.duplex = v;
                          if (midland) channel.offset = v == '+' ? 5 : 0;
                        }),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _NumberField(
                        label: channel.duplex == 'split'
                            ? 'TX frequency'
                            : 'Offset (MHz)',
                        value: channel.offset,
                        decimals: 6,
                        readOnly: midland,
                        onValue: (v) => onChanged(() => channel.offset = v),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                _ChoiceField(
                  label: 'Tone mode',
                  value: channel.tone,
                  choices: toneModes,
                  onValue: (v) => onChanged(() => channel.tone = v),
                ),
                if (channel.tone == 'Cross') ...[
                  const SizedBox(height: 12),
                  _ChoiceField(
                    label: 'Cross mode',
                    value: channel.crossMode,
                    choices: choices(capabilities?.crossModes, const {
                      'Tone->Tone': 'Tone → Tone',
                      'DTCS->': 'DTCS → None',
                      '->DTCS': 'None → DTCS',
                      'Tone->DTCS': 'Tone → DTCS',
                      'DTCS->Tone': 'DTCS → Tone',
                      '->Tone': 'None → Tone',
                      'DTCS->DTCS': 'DTCS → DTCS',
                    }),
                    onValue: (v) => onChanged(() => channel.crossMode = v),
                  ),
                ],
                if (usesTxTone || usesRxTone) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      if (usesTxTone)
                        Expanded(
                          child: _ChoiceField(
                            label: 'Transmit tone (Hz)',
                            value: channel.txTone.toStringAsFixed(1),
                            choices: toneChoices.isEmpty
                                ? {
                                    channel.txTone.toStringAsFixed(1): channel
                                        .txTone
                                        .toStringAsFixed(1),
                                  }
                                : toneChoices,
                            onValue: (v) => onChanged(
                              () => channel.txTone = double.parse(v),
                            ),
                          ),
                        ),
                      if (usesTxTone && usesRxTone) const SizedBox(width: 10),
                      if (usesRxTone)
                        Expanded(
                          child: _ChoiceField(
                            label: 'Receive tone (Hz)',
                            value: channel.rxTone.toStringAsFixed(1),
                            choices: toneChoices.isEmpty
                                ? {
                                    channel.rxTone.toStringAsFixed(1): channel
                                        .rxTone
                                        .toStringAsFixed(1),
                                  }
                                : toneChoices,
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
                            label: 'Transmit DTCS',
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
                            label: 'Receive DTCS',
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
                    label: 'DTCS polarity (TX / RX)',
                    value: channel.dtcsPolarity,
                    choices: const {
                      'NN': 'Normal / Normal',
                      'NR': 'Normal / Reverse',
                      'RN': 'Reverse / Normal',
                      'RR': 'Reverse / Reverse',
                    },
                    onValue: (v) => onChanged(() => channel.dtcsPolarity = v),
                  ),
                ],
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _ChoiceField(
                        label: 'Mode',
                        value: channel.mode,
                        choices: choices(capabilities?.modes, const {
                          'FM': 'FM',
                          'NFM': 'NFM',
                          'AM': 'AM',
                          'DV': 'Digital voice',
                        }),
                        onValue: (v) => onChanged(() => channel.mode = v),
                      ),
                    ),
                    if (capabilities?.hasTuningStep ?? true) ...[
                      const SizedBox(width: 10),
                      Expanded(
                        child: _ChoiceField(
                          label: 'Step (kHz)',
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
                  label: 'Scan',
                  value: channel.skip,
                  choices: scanChoices(capabilities?.skips),
                  onValue: (v) => onChanged(() => channel.skip = v),
                ),
                if ((capabilities?.powers ?? const []).isNotEmpty) ...[
                  const SizedBox(height: 12),
                  _ChoiceField(
                    label: 'Transmit power',
                    value: channel.power,
                    choices: choices(capabilities!.powers, const {}),
                    onValue: (v) => onChanged(() => channel.power = v),
                  ),
                ],
                const SizedBox(height: 12),
                _TextField(
                  label: 'Comment',
                  value: channel.comment,
                  maxLines: 3,
                  onValue: (v) => onChanged(() => channel.comment = v),
                ),
                if (channel.extras.isNotEmpty) ...[
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 18),
                    child: Divider(),
                  ),
                  const Text(
                    'Radio-specific channel settings',
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
                TextButton(onPressed: onClose, child: const Text('Cancel')),
                const Spacer(),
                FilledButton.icon(
                  onPressed: blocking.isEmpty ? onSave : null,
                  icon: const Icon(Icons.check, size: 18),
                  label: const Text('Save channel'),
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
  Widget build(BuildContext context) => const Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.inbox_outlined, size: 42, color: Colors.black26),
        SizedBox(height: 10),
        Text('No matching channels', style: TextStyle(color: Colors.black45)),
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
