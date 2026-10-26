import 'dart:async';
import 'dart:convert';
import 'dart:ffi' show Abi;
import 'dart:io';

import 'package:flutter/foundation.dart';

import 'radio_bridge.dart';

const _maxRequestLength = 65536;

/// Why a radio helper process exited, in the same words as a one-shot job.
String describeRadioHelperExit({
  required int exitCode,
  required String stderr,
  required String stdout,
}) {
  if ((exitCode & 0xFFFFFFFF) == 0xC0000005) {
    return 'NewChirp\u2019s radio helper crashed while communicating with the '
        'radio (Windows access violation, exit code 0xC0000005).\n\n'
        'Unplug and reconnect the programming cable, put the radio back in '
        'CLONE mode, and try again. If it keeps happening, restart NewChirp '
        'and the computer before retrying.';
  }
  final details = stderr.isNotEmpty ? stderr : stdout;
  return details.isEmpty
      ? 'Radio bridge failed with exit code $exitCode.'
      : details;
}

/// Turns the existing command-line shape into one session request.
///
/// Only known commands and options are accepted. The helper never opens a
/// port that another program could write to.
@visibleForTesting
Map<String, Object?> encodeRadioHelperCommand(List<String> args) {
  if (args.isEmpty) {
    throw RadioBridgeException('Missing radio helper command.');
  }
  const commands = {
    'list-models',
    'list-interfaces',
    'model-info',
    'repeaterbook-search',
    'read-image',
    'download',
    'upload',
    'read-settings',
    'write-settings',
  };
  const flags = {'fm-only', 'open-only', 'metadata-only'};
  const ints = {'zone', 'limit'};
  const doubles = {'latitude', 'longitude', 'distance'};
  const strings = {
    'model',
    'country',
    'state',
    'service',
    'filter',
    'image',
    'port',
    'channels',
    'cleared',
    'settings',
  };
  final command = args.first;
  if (!commands.contains(command)) {
    throw RadioBridgeException('Unknown radio helper command.');
  }
  final payload = <String, Object?>{'command': command};
  for (var i = 1; i < args.length; i++) {
    final token = args[i];
    if (!token.startsWith('--') || token.length < 3) {
      throw RadioBridgeException('Invalid radio helper argument.');
    }
    final name = token.substring(2);
    final key = name.replaceAll('-', '_');
    if (flags.contains(name)) {
      payload[key] = true;
      continue;
    }
    if (!strings.contains(name) &&
        !ints.contains(name) &&
        !doubles.contains(name)) {
      throw RadioBridgeException('Invalid radio helper argument.');
    }
    i += 1;
    if (i >= args.length) {
      throw RadioBridgeException('Missing a value for $token.');
    }
    final raw = args[i];
    if (ints.contains(name)) {
      final parsed = int.tryParse(raw);
      if (parsed == null) {
        throw RadioBridgeException('Invalid number for $token.');
      }
      payload[key] = parsed;
    } else if (doubles.contains(name)) {
      final parsed = double.tryParse(raw);
      if (parsed == null) {
        throw RadioBridgeException('Invalid number for $token.');
      }
      payload[key] = parsed;
    } else if (raw.contains('\u0000')) {
      throw RadioBridgeException('Invalid radio helper argument.');
    } else {
      payload[key] = raw;
    }
  }
  return payload;
}

typedef RadioHelperFiles = ({String script, String vendor, Directory runtime});

/// One Python process for the whole app session.
///
/// The first radio job loads the CHIRP driver catalog. Later jobs reuse that
/// process, so picking a model or searching RepeaterBook does not import it
/// again. Cancelling a transfer stops the process. The next job starts a new
/// one. A loaded CHIRP module does not use this process.
class RadioHelperSession {
  Process? _process;
  Directory? _runtime;
  StreamSubscription<String>? _stdoutSub;
  StreamSubscription<String>? _stderrSub;
  Completer<Map<String, dynamic>>? _pending;
  Completer<void>? _ready;
  var _nextId = 0;
  int? _expectedId;
  var _handledExitGeneration = -1;
  var _generation = 0;
  var _cancelGeneration = 0;
  var _queued = 0;
  var _running = false;
  var _commandActive = false;
  var _pythonProbeCount = 0;
  String? _pythonPath;
  Future<void> _queue = Future<void>.value();
  void Function(RadioProgress)? _onProgress;
  final List<String> _stderrLines = <String>[];

  static final Finalizer<Process> _finalizer = Finalizer<Process>(
    (process) => process.kill(ProcessSignal.sigterm),
  );

  int? get pid => _running ? _process?.pid : null;

  int get pythonProbeCount => _pythonProbeCount;

  bool killActive() {
    if (!_commandActive && _queued == 0) return true;
    // Jobs that have not written a command yet see this and do not start.
    // A warm helper stays loaded. A transfer already on the radio is stopped.
    _cancelGeneration += 1;
    if (!_commandActive) return true;
    final ready = _ready;
    final helperIsIdle =
        _pending == null && _running && ready != null && ready.isCompleted;
    if (helperIsIdle) return true;
    final process = _process;
    if (process == null) return true;
    return process.kill(ProcessSignal.sigterm);
  }

  void stop() {
    _cancelGeneration += 1;
    _generation += 1;
    final process = _process;
    final runtime = _runtime;
    _process = null;
    _runtime = null;
    _running = false;
    _commandActive = false;
    _finalizer.detach(this);
    _failCurrent(RadioBridgeException('The radio helper stopped.'));
    unawaited(_stdoutSub?.cancel());
    unawaited(_stderrSub?.cancel());
    _stdoutSub = null;
    _stderrSub = null;
    process?.kill(ProcessSignal.sigterm);
    if (runtime != null) {
      unawaited(_deleteAfterExit(process, runtime));
    }
  }

  Future<String> resolvePython(Directory? resources) async {
    final cached = _pythonPath;
    if (cached != null) return cached;
    _pythonProbeCount += 1;
    final resolved = await _probePython(resources);
    _pythonPath = resolved;
    return resolved;
  }

  Future<Map<String, dynamic>> run({
    required List<String> args,
    required String source,
    required String? newDrivers,
    required String? scsiHelper,
    required String python,
    required Future<RadioHelperFiles> Function() materialize,
    void Function(RadioProgress)? onProgress,
  }) {
    final ticket = _cancelGeneration;
    return _enqueue(() {
      if (ticket != _cancelGeneration) {
        throw RadioBridgeException('The radio helper stopped.');
      }
      return _runLocked(
        ticket: ticket,
        args: args,
        source: source,
        newDrivers: newDrivers,
        scsiHelper: scsiHelper,
        python: python,
        materialize: materialize,
        onProgress: onProgress,
      );
    });
  }

  Future<T> _enqueue<T>(Future<T> Function() action) {
    final previous = _queue;
    final gate = Completer<void>();
    _queue = gate.future;
    _queued += 1;
    return previous
        .catchError((Object _) {})
        .then((_) => action())
        .whenComplete(() {
          _queued -= 1;
          if (!gate.isCompleted) gate.complete();
        });
  }

  Future<Map<String, dynamic>> _runLocked({
    required int ticket,
    required List<String> args,
    required String source,
    required String? newDrivers,
    required String? scsiHelper,
    required String python,
    required Future<RadioHelperFiles> Function() materialize,
    void Function(RadioProgress)? onProgress,
  }) async {
    _commandActive = true;
    _onProgress = onProgress;
    try {
      await _ensureStarted(
        ticket: ticket,
        source: source,
        newDrivers: newDrivers,
        scsiHelper: scsiHelper,
        python: python,
        materialize: materialize,
      );
      if (ticket != _cancelGeneration) {
        throw RadioBridgeException('The radio helper stopped.');
      }
      final process = _process;
      if (process == null || !_running) {
        throw RadioBridgeException('The radio helper stopped.');
      }
      final id = ++_nextId;
      final payload = encodeRadioHelperCommand(args);
      payload['id'] = id;
      final line = jsonEncode(payload);
      if (line.length > _maxRequestLength) {
        throw RadioBridgeException('The radio helper request is too large.');
      }
      final pending = Completer<Map<String, dynamic>>();
      _pending = pending;
      _expectedId = id;
      _stderrLines.clear();
      try {
        process.stdin.write('$line\n');
        await process.stdin.flush();
      } catch (_) {
        if (identical(_pending, pending) && !pending.isCompleted) {
          _pending = null;
          pending.completeError(
            RadioBridgeException('The radio helper stopped.'),
          );
        }
      }
      return await pending.future;
    } finally {
      _onProgress = null;
      _commandActive = false;
    }
  }

  Future<void> _ensureStarted({
    required int ticket,
    required String source,
    required String? newDrivers,
    required String? scsiHelper,
    required String python,
    required Future<RadioHelperFiles> Function() materialize,
  }) async {
    if (_running && _process != null) return;
    final files = await materialize();
    if (ticket != _cancelGeneration) {
      await _deleteRuntime(files.runtime);
      throw RadioBridgeException('The radio helper stopped.');
    }
    final previousRuntime = _runtime;
    _runtime = files.runtime;
    if (previousRuntime != null && !identical(previousRuntime, files.runtime)) {
      unawaited(_deleteRuntime(previousRuntime));
    }
    _generation += 1;
    final generation = _generation;
    await _stdoutSub?.cancel();
    await _stderrSub?.cancel();
    _stdoutSub = null;
    _stderrSub = null;
    if (ticket != _cancelGeneration) {
      await _deleteRuntime(files.runtime);
      if (identical(_runtime, files.runtime)) _runtime = null;
      throw RadioBridgeException('The radio helper stopped.');
    }
    final arguments = <String>[
      '-u',
      files.script,
      '--source',
      source,
      '--vendor',
      files.vendor,
      if (newDrivers != null) ...['--newchirp-driver-dir', newDrivers],
      '--session',
    ];
    late final Process process;
    try {
      process = await Process.start(
        python,
        arguments,
        environment: {'NEWCHIRP_SCSI_HELPER': ?scsiHelper},
        includeParentEnvironment: true,
      );
    } on ProcessException catch (error) {
      await _deleteRuntime(files.runtime);
      if (identical(_runtime, files.runtime)) _runtime = null;
      throw RadioBridgeException(
        'NewChirp could not start its CHIRP helper. Python 3 was not found '
        'or could not be launched (${error.message}).',
      );
    }
    _process = process;
    _running = true;
    _stderrLines.clear();
    _finalizer.detach(this);
    _finalizer.attach(this, process, detach: this);
    final ready = Completer<void>();
    _ready = ready;
    _stdoutSub = process.stdout
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen(
          (line) => _onStdout(line, generation),
          onError: (Object _) => _onProcessGone(process, generation),
          onDone: () => _onProcessGone(process, generation),
        );
    _stderrSub = process.stderr
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen((line) {
          if (line.startsWith('__NEWCHIRP_PROGRESS__ ')) return;
          _stderrLines.add(line);
        });
    if (ticket != _cancelGeneration) {
      process.kill(ProcessSignal.sigterm);
    }
    try {
      await ready.future;
    } catch (error) {
      if (identical(_runtime, files.runtime)) {
        unawaited(_deleteAfterExit(process, files.runtime));
        _runtime = null;
      }
      rethrow;
    }
  }

  void _onStdout(String line, int generation) {
    if (generation != _generation || line.isEmpty) return;
    Object? decoded;
    try {
      decoded = jsonDecode(line);
    } on FormatException {
      _breakProtocol(generation);
      return;
    }
    if (decoded is! Map) {
      _breakProtocol(generation);
      return;
    }
    final ready = _ready;
    final type = decoded['type'];
    if (ready != null && !ready.isCompleted) {
      if (type == 'ready') {
        ready.complete();
        return;
      }
      _breakProtocol(generation);
      return;
    }
    if (type == 'progress') {
      final rawFraction = decoded['fraction'];
      final fraction = rawFraction is num
          ? rawFraction.toDouble().clamp(0.0, 1.0).toDouble()
          : null;
      _onProgress?.call(
        RadioProgress(
          label: '${decoded['label'] ?? 'Working...'}',
          fraction: fraction,
        ),
      );
      return;
    }
    if (type != 'result') {
      _breakProtocol(generation);
      return;
    }
    final pending = _pending;
    if (pending == null ||
        pending.isCompleted ||
        decoded['id'] != _expectedId) {
      _breakProtocol(generation);
      return;
    }
    _pending = null;
    if (decoded['ok'] == true) {
      final result = decoded['result'];
      if (result is! Map) {
        pending.completeError(
          RadioBridgeException(
            'The radio helper returned an invalid response.',
          ),
        );
        return;
      }
      pending.complete(result.cast<String, dynamic>());
      return;
    }
    final error = '${decoded['error'] ?? ''}'.trim();
    pending.completeError(
      RadioBridgeException(error.isEmpty ? 'The radio helper failed.' : error),
    );
  }

  void _breakProtocol(int generation) {
    if (generation != _generation) return;
    final process = _process;
    _running = false;
    _process = null;
    _failCurrent(
      RadioBridgeException('The radio helper returned an invalid response.'),
    );
    process?.kill(ProcessSignal.sigterm);
  }

  void _onProcessGone(Process process, int generation) {
    if (generation != _generation || _handledExitGeneration == generation) {
      return;
    }
    _handledExitGeneration = generation;
    _running = false;
    if (identical(_process, process)) _process = null;
    unawaited(() async {
      final code = await process.exitCode;
      if (generation != _generation) return;
      _generation += 1;
      _failCurrent(
        RadioBridgeException(
          describeRadioHelperExit(
            exitCode: code,
            stderr: _stderrLines.join('\n').trim(),
            stdout: '',
          ),
        ),
      );
    }());
  }

  void _failCurrent(RadioBridgeException error) {
    final ready = _ready;
    if (ready != null && !ready.isCompleted) ready.completeError(error);
    final pending = _pending;
    _pending = null;
    if (pending != null && !pending.isCompleted) pending.completeError(error);
  }

  Future<void> _deleteAfterExit(Process? process, Directory runtime) async {
    try {
      if (process != null) await process.exitCode;
      await _deleteRuntime(runtime);
    } catch (_) {
      // A leftover temp folder holds a copy of the helper, not a secret.
    }
  }

  Future<void> _deleteRuntime(Directory runtime) async {
    if (await runtime.exists()) await runtime.delete(recursive: true);
  }

  Future<String> _probePython(Directory? resources) async {
    final configured = Platform.environment['NEWCHIRP_PYTHON'];
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
}
