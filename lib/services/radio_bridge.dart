import 'dart:convert';
import 'dart:ffi' show Abi;
import 'dart:io';

import 'package:flutter/services.dart';

import '../models/radio_channel.dart';
import '../models/repeater_search.dart';

const _progressPrefix = '__NEWCHIRP_PROGRESS__ ';

const _windowsSerialPortDeviceScript = r'''
$ports = @(
  Get-CimInstance Win32_PnPEntity |
    Where-Object { $_.Name -match '\((COM\d+)\)$' } |
    ForEach-Object {
      $match = [regex]::Match($_.Name, '\((COM\d+)\)$')
      [pscustomobject]@{
        port = $match.Groups[1].Value
        deviceName = ($_.Name -replace '\s*\(COM\d+\)$', '')
      }
    }
  Get-CimInstance Win32_SerialPort |
    ForEach-Object {
      [pscustomobject]@{
        port = $_.DeviceID
        deviceName = $_.Description
      }
    }
)
ConvertTo-Json -InputObject $ports -Compress
''';

class RadioBridgeException implements Exception {
  RadioBridgeException(this.message);
  final String message;
  @override
  String toString() => message;
}

class RadioInstructions {
  const RadioInstructions({
    required this.info,
    required this.experimental,
    required this.preDownload,
    required this.preUpload,
  });

  final String? info;
  final String? experimental;
  final String? preDownload;
  final String? preUpload;

  Iterable<String> get readMessages => [?experimental, ?info, ?preDownload];
  Iterable<String> get writeMessages => [?experimental, ?info, ?preUpload];
}

class RadioCapabilities {
  const RadioCapabilities({
    required this.duplexes,
    required this.toneModes,
    required this.crossModes,
    required this.modes,
    required this.steps,
    required this.skips,
    required this.powers,
    required this.tones,
    required this.dtcsCodes,
    required this.memoryStart,
    required this.memoryEnd,
    required this.nameLength,
    required this.validCharacters,
    required this.hasTuningStep,
  });

  final List<String> duplexes;
  final List<String> toneModes;
  final List<String> crossModes;
  final List<String> modes;
  final List<double> steps;
  final List<String> skips;
  final List<String> powers;
  final List<double> tones;
  final List<int> dtcsCodes;
  final int? memoryStart;
  final int? memoryEnd;
  final int nameLength;
  final String validCharacters;
  final bool hasTuningStep;

  bool get uppercaseNames =>
      validCharacters.isNotEmpty &&
      validCharacters == validCharacters.toUpperCase();

  factory RadioCapabilities.fromJson(Map<String, dynamic> json) {
    List<String> strings(String key) => (json[key] as List? ?? const [])
        .map((item) => item.toString())
        .toList();
    return RadioCapabilities(
      duplexes: strings('duplexes'),
      toneModes: strings('toneModes'),
      crossModes: strings('crossModes'),
      modes: strings('modes'),
      steps: (json['steps'] as List? ?? const [])
          .map((item) => (item as num).toDouble())
          .toList(),
      skips: strings('skips'),
      powers: strings('powers'),
      tones: (json['tones'] as List? ?? const [])
          .map((item) => (item as num).toDouble())
          .toList(),
      dtcsCodes: (json['dtcsCodes'] as List? ?? const [])
          .map((item) => (item as num).toInt())
          .toList(),
      memoryStart: (json['memoryStart'] as num?)?.toInt(),
      memoryEnd: (json['memoryEnd'] as num?)?.toInt(),
      nameLength: (json['nameLength'] as num?)?.toInt() ?? 16,
      validCharacters: '${json['validCharacters'] ?? ''}',
      hasTuningStep: json['hasTuningStep'] as bool? ?? true,
    );
  }
}

class RadioZone {
  const RadioZone({
    required this.index,
    required this.name,
    required this.channelCount,
  });

  final int index;
  final String name;
  final int channelCount;

  factory RadioZone.fromJson(Map<String, dynamic> json) => RadioZone(
    index: (json['index'] as num).toInt(),
    name: '${json['name'] ?? 'Zone'}',
    channelCount: (json['channelCount'] as num?)?.toInt() ?? 0,
  );
}

class RadioProgress {
  const RadioProgress({required this.label, this.fraction});

  final String label;
  final double? fraction;
}

class SerialPortInfo {
  const SerialPortInfo({required this.port, this.deviceName});

  final String port;
  final String? deviceName;

  String get label {
    final name = deviceName?.trim() ?? '';
    return name.isEmpty ? port : '$port — $name';
  }
}

class RadioSettingNode {
  RadioSettingNode({
    required this.id,
    required this.name,
    required this.shortName,
    required this.kind,
    required this.documentation,
    required this.value,
    required this.options,
    required this.mutable,
    required this.min,
    required this.max,
    required this.step,
    required this.minLength,
    required this.maxLength,
    required this.children,
  });

  final List<int> id;
  final String name;
  final String shortName;
  final String? documentation;
  final String kind;
  final List<String> options;
  final bool mutable;
  final num? min;
  final num? max;
  final num? step;
  final int? minLength;
  final int? maxLength;
  final List<RadioSettingNode> children;
  Object? value;
  bool invalid = false;

  String get label => shortName.isEmpty ? name : shortName;
  bool get isGroup => kind == 'group';

  factory RadioSettingNode.fromJson(Map<String, dynamic> json) {
    return RadioSettingNode(
      id: (json['id'] as List? ?? const [])
          .map((item) => (item as num).toInt())
          .toList(),
      name: '${json['name'] ?? ''}',
      shortName: '${json['shortName'] ?? ''}',
      kind: '${json['kind'] ?? 'string'}',
      documentation: json['documentation'] as String?,
      value: json['value'],
      options: (json['options'] as List? ?? const [])
          .map((item) => '$item')
          .toList(),
      mutable: json['mutable'] as bool? ?? false,
      min: json['min'] as num?,
      max: json['max'] as num?,
      step: json['step'] as num?,
      minLength: (json['minLength'] as num?)?.toInt(),
      maxLength: (json['maxLength'] as num?)?.toInt(),
      children: (json['children'] as List? ?? const [])
          .map(
            (item) => RadioSettingNode.fromJson(
              (item as Map).cast<String, dynamic>(),
            ),
          )
          .toList(),
    );
  }

  Map<String, Object?> toChangeJson() => {'id': id, 'value': value};
}

class RadioSettings {
  const RadioSettings({
    required this.hasSettings,
    required this.items,
    this.imagePath,
  });

  final bool hasSettings;
  final List<RadioSettingNode> items;
  final String? imagePath;

  factory RadioSettings.fromJson(Map<String, dynamic> json) {
    return RadioSettings(
      hasSettings: json['hasSettings'] as bool? ?? false,
      imagePath: json['imagePath'] as String?,
      items: (json['settings'] as List? ?? const [])
          .map(
            (item) => RadioSettingNode.fromJson(
              (item as Map).cast<String, dynamic>(),
            ),
          )
          .toList(),
    );
  }
}

class RadioBridge {
  RadioBridge({this.sourcePath, this.newDriversPath});
  final String? sourcePath;
  final String? newDriversPath;
  String? _loadedModulePath;
  Process? _activeProcess;
  bool _cancelRequested = false;

  String get chirpSource => _findChirpSource();
  String? get loadedModulePath => _loadedModulePath;

  bool cancelActive() {
    _cancelRequested = true;
    final process = _activeProcess;
    return process == null || process.kill(ProcessSignal.sigterm);
  }

  Future<List<SerialPortInfo>> serialPortDetails() async {
    final interfaces = await _massStoragePortDetails();
    if (Platform.isWindows) {
      final serial = await _windowsSerialPortDetails();
      return _deduplicatePorts([...serial, ...interfaces]);
    }
    final dev = Directory('/dev');
    if (!dev.existsSync()) return interfaces;
    final patterns = Platform.isMacOS
        ? ['cu.usb', 'cu.SLAB', 'cu.wch', 'tty.usb']
        : ['ttyUSB', 'ttyACM'];
    final ports =
        dev
            .listSync()
            .whereType<FileSystemEntity>()
            .map((e) => e.path)
            .where((path) => patterns.any(path.contains))
            .toList()
          ..sort();
    return _deduplicatePorts([
      ...ports.map((port) => SerialPortInfo(port: port)),
      ...interfaces,
    ]);
  }

  Future<List<SerialPortInfo>> _massStoragePortDetails() async {
    try {
      final data = await _run(['list-interfaces']);
      final entries = data['interfaces'] as List? ?? const [];
      return entries
          .whereType<Map>()
          .map(
            (entry) => SerialPortInfo(
              port: '${entry['port'] ?? ''}',
              deviceName: '${entry['deviceName'] ?? ''}',
            ),
          )
          .where((entry) => entry.port.isNotEmpty)
          .toList();
    } catch (_) {
      // A missing platform helper must not hide serial clone-mode radios.
      return const [];
    }
  }

  List<SerialPortInfo> _deduplicatePorts(List<SerialPortInfo> ports) {
    final seen = <String>{};
    return ports.where((entry) => seen.add(entry.port)).toList();
  }

  Future<List<String>> serialPorts() async {
    final ports = await serialPortDetails();
    return ports.map((port) => port.port).toList();
  }

  /// Windows: read the live COM ports from the SERIALCOMM registry key, then
  /// fall back to .NET's SerialPort.GetPortNames() so only real ports show up.
  Future<List<String>> _windowsSerialPortNames() async {
    try {
      final result = await Process.run('reg', [
        'query',
        r'HKEY_LOCAL_MACHINE\HARDWARE\DEVICEMAP\SERIALCOMM',
      ]);
      if (result.exitCode == 0) {
        final ports = _parseComPorts('${result.stdout}');
        if (ports.isNotEmpty) return ports;
      }
    } on ProcessException {
      // reg.exe unavailable; fall through to the .NET lookup below.
    }
    try {
      final result = await Process.run('powershell', [
        '-NoProfile',
        '-Command',
        '[System.IO.Ports.SerialPort]::GetPortNames()',
      ]);
      if (result.exitCode == 0) return _parseComPorts('${result.stdout}');
    } on ProcessException {
      // Fall through; no ports available.
    }
    return const [];
  }

  Future<List<SerialPortInfo>> _windowsSerialPortDetails() async {
    final ports = await _windowsSerialPortNames();
    if (ports.isEmpty) return const [];
    String deviceOutput = '';
    try {
      final result = await Process.run('powershell', [
        '-NoProfile',
        '-Command',
        _windowsSerialPortDeviceScript,
      ]);
      if (result.exitCode == 0) deviceOutput = '${result.stdout}';
    } on ProcessException {
      // Device names are optional; the COM port list remains usable.
    }
    return parseWindowsSerialPortDetails(deviceOutput, ports);
  }

  static List<SerialPortInfo> parseWindowsSerialPortDetails(
    String output,
    Iterable<String> livePorts,
  ) {
    final deviceNames = <String, String>{};
    try {
      final decoded = jsonDecode(output.trim());
      final entries = decoded is List ? decoded : [decoded];
      for (final entry in entries) {
        if (entry is! Map) continue;
        final port = '${entry['port'] ?? ''}'.trim().toUpperCase();
        final deviceName = '${entry['deviceName'] ?? ''}'.trim();
        if (RegExp(r'^COM\d+$').hasMatch(port) && deviceName.isNotEmpty) {
          deviceNames.putIfAbsent(port, () => deviceName);
        }
      }
    } on FormatException {
      // Missing or malformed device metadata should not hide the ports.
    }
    final ports =
        livePorts
            .map((port) => port.trim().toUpperCase())
            .where((port) => RegExp(r'^COM\d+$').hasMatch(port))
            .toSet()
            .toList()
          ..sort((a, b) {
            return int.parse(
              a.substring(3),
            ).compareTo(int.parse(b.substring(3)));
          });
    return ports
        .map(
          (port) => SerialPortInfo(port: port, deviceName: deviceNames[port]),
        )
        .toList();
  }

  List<String> _parseComPorts(String output) {
    final ports = <String>{};
    for (final line in output.split('\n')) {
      final parts = line.trim().split(RegExp(r'\s+'));
      if (parts.isEmpty) continue;
      final last = parts.last;
      if (RegExp(r'^COM\d+$', caseSensitive: false).hasMatch(last)) {
        ports.add(last.toUpperCase());
      }
    }
    final list = ports.toList();
    list.sort((a, b) {
      return int.parse(a.substring(3)).compareTo(int.parse(b.substring(3)));
    });
    return list;
  }

  Future<List<String>> models() async {
    final data = await _run(['list-models']);
    return (data['models'] as List).cast<String>();
  }

  Future<List<String>> loadModule(String path) async {
    final extension = path.toLowerCase();
    if (!extension.endsWith('.py') && !extension.endsWith('.mod')) {
      throw RadioBridgeException(
        'CHIRP modules must be Python .py files or .mod files.',
      );
    }
    if (!File(path).existsSync()) {
      throw RadioBridgeException('The selected CHIRP module was not found.');
    }
    final previous = _loadedModulePath;
    _loadedModulePath = path;
    try {
      return await models();
    } catch (_) {
      _loadedModulePath = previous;
      rethrow;
    }
  }

  void unloadModule() {
    _loadedModulePath = null;
  }

  Future<RadioInstructions> instructions(String model) async {
    final data = await _run(['model-info', '--model', model]);
    return RadioInstructions(
      info: data['info'] as String?,
      experimental: data['experimental'] as String?,
      preDownload: data['preDownload'] as String?,
      preUpload: data['preUpload'] as String?,
    );
  }

  Future<
    ({
      List<RadioChannel> channels,
      String model,
      String imagePath,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
      int? zone,
    })
  >
  readImage(String imagePath, {int? zone}) async {
    final data = await _run([
      'read-image',
      '--image',
      imagePath,
      if (zone != null) ...['--zone', '$zone'],
    ]);
    return (
      channels: (data['channels'] as List)
          .map(
            (entry) =>
                RadioChannel.fromJson((entry as Map).cast<String, dynamic>()),
          )
          .toList(),
      model: '${data['model']}',
      imagePath: '${data['imagePath']}',
      capabilities: RadioCapabilities.fromJson(
        (data['features'] as Map).cast<String, dynamic>(),
      ),
      zones: (data['zones'] as List? ?? const [])
          .map(
            (entry) =>
                RadioZone.fromJson((entry as Map).cast<String, dynamic>()),
          )
          .toList(),
      zone: (data['zone'] as num?)?.toInt(),
    );
  }

  Future<({RadioCapabilities capabilities, List<RadioZone> zones, int? zone})>
  imageInfo(String imagePath) async {
    final data = await _run([
      'read-image',
      '--image',
      imagePath,
      '--metadata-only',
    ]);
    return (
      capabilities: RadioCapabilities.fromJson(
        (data['features'] as Map).cast<String, dynamic>(),
      ),
      zones: (data['zones'] as List? ?? const [])
          .map(
            (entry) =>
                RadioZone.fromJson((entry as Map).cast<String, dynamic>()),
          )
          .toList(),
      zone: (data['zone'] as num?)?.toInt(),
    );
  }

  Future<RadioCapabilities> imageCapabilities(String imagePath) async =>
      (await imageInfo(imagePath)).capabilities;

  Future<
    ({
      List<RadioChannel> channels,
      String imagePath,
      RadioCapabilities capabilities,
      List<RadioZone> zones,
      int? zone,
    })
  >
  download({
    required String model,
    required String port,
    int? zone,
    void Function(RadioProgress)? onProgress,
  }) async {
    final data = await _run([
      'download',
      '--model',
      model,
      '--port',
      port,
      if (zone != null) ...['--zone', '$zone'],
    ], onProgress: onProgress);
    return (
      channels: (data['channels'] as List)
          .map((e) => RadioChannel.fromJson((e as Map).cast<String, dynamic>()))
          .toList(),
      imagePath: data['imagePath'] as String,
      capabilities: RadioCapabilities.fromJson(
        (data['features'] as Map).cast<String, dynamic>(),
      ),
      zones: (data['zones'] as List? ?? const [])
          .map(
            (entry) =>
                RadioZone.fromJson((entry as Map).cast<String, dynamic>()),
          )
          .toList(),
      zone: (data['zone'] as num?)?.toInt(),
    );
  }

  Future<List<Map<String, dynamic>>> upload({
    required String model,
    required String port,
    required String imagePath,
    required List<RadioChannel> channels,
    required List<int> cleared,
    int? zone,
    void Function(RadioProgress)? onProgress,
  }) async {
    final temp = File(
      '${Directory.systemTemp.path}/newchirp-upload-$pid-'
      '${DateTime.now().microsecondsSinceEpoch}.json',
    );
    await temp.writeAsString(
      jsonEncode(channels.map((e) => e.toJson()).toList()),
    );
    final data = await _run([
      'upload',
      '--model',
      model,
      '--port',
      port,
      if (zone != null) ...['--zone', '$zone'],
      '--image',
      imagePath,
      '--channels',
      temp.path,
      '--cleared',
      cleared.join(','),
    ], onProgress: onProgress);
    final skipped = (data['skipped'] as List? ?? const [])
        .map((entry) => (entry as Map).cast<String, dynamic>())
        .toList();
    final adjusted = (data['adjusted'] as List? ?? const [])
        .map((entry) => (entry as Map).cast<String, dynamic>())
        .toList();
    return [...skipped, ...adjusted];
  }

  Future<RadioSettings> readSettings({
    required String model,
    String? imagePath,
    String? port,
    void Function(RadioProgress)? onProgress,
  }) async {
    if ((imagePath == null) == (port == null)) {
      throw ArgumentError(
        'Specify exactly one of imagePath or port for readSettings.',
      );
    }
    final data = await _run([
      'read-settings',
      '--model',
      model,
      if (port != null) ...['--port', port] else ...['--image', imagePath!],
    ], onProgress: onProgress);
    return RadioSettings.fromJson(data);
  }

  Future<void> writeSettings({
    required String model,
    required String port,
    required String imagePath,
    required List<Map<String, Object?>> changes,
    void Function(RadioProgress)? onProgress,
  }) async {
    final temp = File(
      '${Directory.systemTemp.path}/newchirp-settings-$pid-'
      '${DateTime.now().microsecondsSinceEpoch}.json',
    );
    try {
      await temp.writeAsString(jsonEncode({'changes': changes}));
      await _run([
        'write-settings',
        '--model',
        model,
        '--port',
        port,
        '--image',
        imagePath,
        '--settings',
        temp.path,
      ], onProgress: onProgress);
    } finally {
      if (await temp.exists()) await temp.delete();
    }
  }

  Future<Map<String, dynamic>> _run(
    List<String> args, {
    void Function(RadioProgress)? onProgress,
  }) async {
    final runtime = await Directory.systemTemp.createTemp('newchirp-run-');
    try {
      return await _runWithRuntime(args, runtime, onProgress: onProgress);
    } finally {
      if (await runtime.exists()) await runtime.delete(recursive: true);
    }
  }

  Future<RepeaterSearchResults> searchRepeaters({
    required String state,
    required String service,
    String filter = '',
    double? latitude,
    double? longitude,
    double? distance,
    bool fmOnly = true,
    bool openOnly = true,
    void Function(RadioProgress)? onProgress,
  }) async {
    final data = await _run([
      'repeaterbook-search',
      '--state',
      state,
      '--service',
      service,
      '--filter',
      filter,
      if (latitude != null) ...['--latitude', '$latitude'],
      if (longitude != null) ...['--longitude', '$longitude'],
      if (distance != null) ...['--distance', '$distance'],
      if (fmOnly) '--fm-only',
      if (openOnly) '--open-only',
      '--limit',
      '200',
    ], onProgress: onProgress);
    return RepeaterSearchResults.fromJson(data);
  }

  Future<Map<String, dynamic>> _runWithRuntime(
    List<String> args,
    Directory runtime, {
    void Function(RadioProgress)? onProgress,
  }) async {
    _cancelRequested = false;
    final script = await _materializeBridge(runtime);
    final vendor = await _materializePythonDependencies(runtime);
    final source = _findChirpSource();
    final newDrivers = _findNewChirpDrivers();
    final python = await _resolvePython();
    final scsiHelper = _findScsiHelper();
    late final Process process;
    try {
      process = await Process.start(
        python,
        [
          script,
          '--source',
          source,
          '--vendor',
          vendor,
          if (newDrivers != null) ...['--newchirp-driver-dir', newDrivers],
          if (_loadedModulePath != null) ...['--module', _loadedModulePath!],
          ...args,
        ],
        environment: {'NEWCHIRP_SCSI_HELPER': ?scsiHelper},
        includeParentEnvironment: true,
      );
    } on ProcessException catch (error) {
      throw RadioBridgeException(
        'NewChirp could not start its CHIRP helper. Python 3 was not found '
        'or could not be launched (${error.message}).',
      );
    }
    _activeProcess = process;
    if (_cancelRequested) process.kill(ProcessSignal.sigterm);
    final stdoutFuture = process.stdout.transform(utf8.decoder).join();
    final stderrLines = <String>[];
    final stderrFuture = process.stderr
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .forEach((line) {
          if (!line.startsWith(_progressPrefix)) {
            stderrLines.add(line);
            return;
          }
          try {
            final data = jsonDecode(line.substring(_progressPrefix.length));
            if (data is! Map) return;
            final rawFraction = data['fraction'];
            final fraction = rawFraction is num
                ? rawFraction.toDouble().clamp(0.0, 1.0).toDouble()
                : null;
            onProgress?.call(
              RadioProgress(
                label: '${data['label'] ?? 'Working...'}',
                fraction: fraction,
              ),
            );
          } on FormatException {
            stderrLines.add(line);
          }
        });
    late final int exitCode;
    late final String stdout;
    late final String stderr;
    try {
      exitCode = await process.exitCode;
      stdout = (await stdoutFuture).trim();
      await stderrFuture;
      stderr = stderrLines.join('\n').trim();
    } finally {
      if (identical(_activeProcess, process)) _activeProcess = null;
    }
    if (exitCode != 0) {
      final details = stderr.isNotEmpty ? stderr : stdout;
      if ((exitCode & 0xFFFFFFFF) == 0xC0000005) {
        throw RadioBridgeException(
          'NewChirp\u2019s radio helper crashed while communicating with the '
          'radio (Windows access violation, exit code 0xC0000005).\n\n'
          'Unplug and reconnect the programming cable, put the radio back in '
          'CLONE mode, and try again. If it keeps happening, restart NewChirp '
          'and the computer before retrying.',
        );
      }
      throw RadioBridgeException(
        details.isEmpty
            ? 'Radio bridge failed with exit code $exitCode.'
            : details,
      );
    }
    final output = stdout;
    try {
      return (jsonDecode(output) as Map).cast<String, dynamic>();
    } on FormatException {
      throw RadioBridgeException(
        output.isEmpty
            ? 'The radio bridge completed without returning data.'
            : 'The radio bridge returned an invalid response: $output',
      );
    }
  }

  /// The bundled CHIRP tree uses Python 3.10+ syntax, so prefer an interpreter
  /// that is new enough even when an older system Python is first on PATH.
  Future<String> _resolvePython() async {
    final configured = Platform.environment['NEWCHIRP_PYTHON'];
    final resources = _bundledResourcesDirectory();
    final macRuntime = switch (Abi.current()) {
      Abi.macosArm64 => 'python-arm64',
      Abi.macosX64 => 'python-x64',
      _ => null,
    };
    final candidates = <String>[
      if (configured != null && configured.isNotEmpty) configured,
      if (resources != null && Platform.isWindows)
        '${resources.path}/python/python.exe',
      if (resources != null && Platform.isMacOS && macRuntime != null)
        '${resources.path}/$macRuntime/bin/python3',
      if (resources != null && !Platform.isWindows && !Platform.isMacOS)
        '${resources.path}/python/bin/python3',
      if (resources != null && Platform.isMacOS)
        '${resources.path}/python/bin/python3',
      if (Platform.isMacOS) '/opt/homebrew/bin/python3',
      if (Platform.isMacOS) '/usr/local/bin/python3',
      if (Platform.isWindows) 'python',
      'python3',
    ];
    for (final candidate in candidates) {
      try {
        final result = await Process.run(candidate, [
          '-c',
          'import sys; print("%d.%d" % sys.version_info[:2])',
        ]);
        if (result.exitCode != 0) continue;
        final parts = '${result.stdout}'.trim().split('.');
        final major = int.tryParse(parts.first);
        final minor = int.tryParse(parts.length > 1 ? parts[1] : '0');
        if (major != null &&
            minor != null &&
            (major > 3 || (major == 3 && minor >= 10))) {
          return candidate;
        }
      } on ProcessException {
        // Candidate is not available; try the next interpreter.
      }
    }
    return 'python3';
  }

  Directory? _bundledResourcesDirectory() {
    final executable = File(Platform.resolvedExecutable);
    if (Platform.isMacOS) {
      final macosDirectory = executable.parent;
      final contentsDirectory = macosDirectory.parent;
      if (!contentsDirectory.path.endsWith('/Contents')) return null;
      return Directory('${contentsDirectory.path}/Resources');
    }
    return executable.parent;
  }

  Future<String> _materializeBridge(Directory runtime) async {
    final file = File('${runtime.path}/chirp_bridge.py');
    final data = await _loadAssetBytes('scripts/chirp_bridge.py');
    await file.writeAsString(utf8.decode(data), flush: true);
    final massStorage = File('${runtime.path}/newchirp_mass_storage.py');
    final massStorageData = await _loadAssetBytes(
      'scripts/newchirp_mass_storage.py',
    );
    await massStorage.writeAsBytes(massStorageData, flush: true);
    return file.path;
  }

  Future<String> _materializePythonDependencies(Directory runtime) async {
    final file = File('${runtime.path}/pyserial-3.5-py2.py3-none-any.whl');
    final data = await _loadAssetBytes(
      'assets/python/pyserial-3.5-py2.py3-none-any.whl',
    );
    await file.writeAsBytes(data, flush: true);
    return file.path;
  }

  Future<List<int>> _loadAssetBytes(String key) async {
    try {
      final data = await rootBundle.load(key);
      return data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes);
    } catch (bundleError, bundleStack) {
      for (final candidate in _bundledAssetCandidates(key)) {
        if (await candidate.exists()) return candidate.readAsBytes();
      }
      Error.throwWithStackTrace(bundleError, bundleStack);
    }
  }

  Iterable<File> _bundledAssetCandidates(String key) sync* {
    if (!key.contains('..') && !key.startsWith('/')) {
      yield File(key);
    }
    final executable = File(Platform.resolvedExecutable);
    if (Platform.isMacOS) {
      final contents = executable.parent.parent;
      yield File(
        '${contents.path}/Frameworks/App.framework/Versions/A/Resources/'
        'flutter_assets/$key',
      );
      yield File('${contents.path}/Resources/flutter_assets/$key');
    } else {
      yield File('${executable.parent.path}/data/flutter_assets/$key');
    }
  }

  String _findChirpSource() {
    final configured = sourcePath ?? Platform.environment['CHIRP_SOURCE'];
    if (configured != null && Directory(configured).existsSync()) {
      return Directory(configured).absolute.path;
    }

    final resources = _bundledResourcesDirectory();
    if (resources != null &&
        Directory('${resources.path}/chirp').existsSync()) {
      return resources.absolute.path;
    }

    final candidates = <Directory>[Directory('../chirp-20260626')];
    var cursor = File(Platform.resolvedExecutable).parent;
    for (var i = 0; i < 10; i++) {
      candidates.add(Directory('${cursor.path}/chirp-20260626'));
      candidates.add(Directory('${cursor.path}/../chirp-20260626'));
      cursor = cursor.parent;
    }
    for (final candidate in candidates) {
      if (File('${candidate.path}/chirp/chirp_common.py').existsSync()) {
        return candidate.absolute.path;
      }
    }
    throw RadioBridgeException(
      'The CHIRP driver folder was not found. Keep chirp-20260626 beside '
      'NewChirp, or set the CHIRP_SOURCE environment variable.',
    );
  }

  String? _findNewChirpDrivers() {
    final configured =
        newDriversPath ?? Platform.environment['NEWCHIRP_DRIVERS'];
    if (configured == null || configured.isEmpty) return null;
    final directory = Directory(configured);
    if (!directory.existsSync()) return null;
    return directory.absolute.path;
  }

  String? _findScsiHelper() {
    final configured = Platform.environment['NEWCHIRP_SCSI_HELPER'];
    final resources = _bundledResourcesDirectory();
    final candidates = <String>[
      if (configured != null && configured.isNotEmpty) configured,
      if (resources != null) '${resources.path}/newchirp_scsi',
      'tools/newchirp_scsi_mac',
      'build/newchirp_scsi_mac',
    ];
    for (final candidate in candidates) {
      if (File(candidate).existsSync()) return File(candidate).absolute.path;
    }
    return null;
  }
}
