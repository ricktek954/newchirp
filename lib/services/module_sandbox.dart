import 'dart:io';

/// OS container for one user-loaded CHIRP driver module.
///
/// Normal radio commands stay unsandboxed. Only the helper started while a
/// module is loaded goes through [ModuleSandbox.prepare].
const moduleSandboxBubblewrapMessage =
    'NewChirp cannot load a CHIRP module because bubblewrap (bwrap) is not '
    'installed. Install bubblewrap, then try again.';

const _windowsMessage =
    'NewChirp cannot load a CHIRP module on Windows because it cannot run '
    'that module in a sandbox yet.';

const _otherMessage =
    'NewChirp cannot load a CHIRP module on this system because it cannot '
    'run that module in a sandbox yet.';

const _unsafePathMessage =
    'NewChirp cannot load a CHIRP module because a file path is not safe to '
    'place in the sandbox.';

const _serialMessage =
    'NewChirp cannot load a CHIRP module because the selected port is not a '
    'single radio serial device.';

const _pythonMessage =
    'NewChirp cannot load a CHIRP module because Python could not be prepared '
    'for the sandbox.';

const _macosToolMessage =
    'NewChirp cannot load a CHIRP module because the macOS sandbox tool is '
    'not available.';

const _workFolderMessage =
    'NewChirp cannot load a CHIRP module because it could not create a '
    'private work folder.';

const _valueFlags = <String>{
  '--source',
  '--vendor',
  '--newchirp-driver-dir',
  '--module',
  '--model',
  '--image',
  '--zone',
  '--port',
  '--channels',
  '--cleared',
  '--settings',
};

enum SandboxPlatform { macos, linux, windows, other }

class ModuleSandboxException implements Exception {
  ModuleSandboxException(this.message);

  final String message;

  @override
  String toString() => message;
}

class SandboxLaunch {
  const SandboxLaunch({
    required this.executable,
    required this.arguments,
    required this.environment,
    required this.workingDirectory,
  });

  final String executable;
  final List<String> arguments;
  final Map<String, String> environment;
  final String workingDirectory;
}

class SandboxFiles {
  const SandboxFiles({this.image, this.channels, this.settings, this.port});

  final String? image;
  final String? channels;
  final String? settings;
  final String? port;
}

SandboxPlatform currentSandboxPlatform() {
  if (Platform.isMacOS) return SandboxPlatform.macos;
  if (Platform.isLinux) return SandboxPlatform.linux;
  if (Platform.isWindows) return SandboxPlatform.windows;
  return SandboxPlatform.other;
}

/// A message when this operating system cannot sandbox a module at all.
/// Linux bubblewrap is checked separately because the OS itself can do it.
String? moduleSandboxRefusal(SandboxPlatform platform) {
  switch (platform) {
    case SandboxPlatform.windows:
      return _windowsMessage;
    case SandboxPlatform.other:
      return _otherMessage;
    case SandboxPlatform.macos:
    case SandboxPlatform.linux:
      return null;
  }
}

Future<String?> moduleSandboxBlocker() async {
  final platform = currentSandboxPlatform();
  final refusal = moduleSandboxRefusal(platform);
  if (refusal != null) return refusal;
  if (platform == SandboxPlatform.linux && await _findBubblewrap() == null) {
    return moduleSandboxBubblewrapMessage;
  }
  if (platform == SandboxPlatform.macos &&
      !File('/usr/bin/sandbox-exec').existsSync()) {
    return _macosToolMessage;
  }
  return null;
}

bool isSafeSandboxPath(String path) {
  if (path.isEmpty || path == '/') return false;
  if (!path.startsWith('/')) return false;
  const blocked = ['"', '\\', '\n', '\r', '(', ')', '\u0000'];
  for (final token in blocked) {
    if (path.contains(token)) return false;
  }
  final parts = path.split('/');
  if (parts.any((part) => part == '..')) return false;
  return true;
}

/// A directory NewChirp may expose inside the sandbox.
///
/// The home folder, its parents, and whole disks are never allow-roots.
/// One file under home can still be allowed on its own.
bool isSafeAllowRoot(String path, {String? home}) {
  if (!isSafeSandboxPath(path)) return false;
  const blocked = {
    '/Users',
    '/Volumes',
    '/home',
    '/tmp',
    '/private',
    '/private/tmp',
    '/private/var',
    '/private/var/folders',
    '/var/folders',
    '/dev',
    '/etc',
  };
  if (blocked.contains(path)) return false;
  if (home != null &&
      home.isNotEmpty &&
      (path == home || home.startsWith('$path/'))) {
    return false;
  }
  final parts = path.split('/').where((part) => part.isNotEmpty).toList();
  if (parts.length <= 2 &&
      (parts.first == 'Users' ||
          parts.first == 'home' ||
          parts.first == 'Volumes')) {
    return false;
  }
  return true;
}

bool isSafeSerialPort(SandboxPlatform platform, String port) {
  switch (platform) {
    case SandboxPlatform.macos:
      return RegExp(r'^/dev/(cu|tty)\.[A-Za-z0-9._-]+$').hasMatch(port);
    case SandboxPlatform.linux:
      return RegExp(r'^/dev/tty(USB|ACM|S)[0-9]+$').hasMatch(port);
    case SandboxPlatform.windows:
    case SandboxPlatform.other:
      return false;
  }
}

Map<String, String> moduleSandboxEnvironment(String workDir) {
  return {
    'HOME': workDir,
    'TMPDIR': workDir,
    'TEMP': workDir,
    'TMP': workDir,
    'PYTHONNOUSERSITE': '1',
    'PYTHONDONTWRITEBYTECODE': '1',
    'PATH': '/usr/bin:/bin:/opt/homebrew/bin',
    'LANG': 'en_US.UTF-8',
  };
}

List<String> replaceModuleArgument(List<String> arguments, String modulePath) {
  final copy = [...arguments];
  var found = false;
  for (var index = 0; index < copy.length - 1; index++) {
    if (copy[index] != '--module') continue;
    copy[index + 1] = modulePath;
    found = true;
  }
  if (!found) copy.addAll(['--module', modulePath]);
  return copy;
}

SandboxFiles sandboxFilesIn(List<String> arguments) {
  String? image;
  String? channels;
  String? settings;
  String? port;
  for (var index = 0; index < arguments.length; index++) {
    final flag = arguments[index];
    if (!_valueFlags.contains(flag) || index + 1 >= arguments.length) continue;
    final value = arguments[index + 1];
    index++;
    switch (flag) {
      case '--image':
        image = value;
      case '--channels':
        channels = value;
      case '--settings':
        settings = value;
      case '--port':
        port = value;
    }
  }
  return SandboxFiles(
    image: image,
    channels: channels,
    settings: settings,
    port: port,
  );
}

String macosSeatbeltProfile({
  required String workDir,
  required String python,
  required List<String> pythonRoots,
  required String chirpSource,
  required String? driverDir,
  required List<String> readOnlyFiles,
  required List<String> readWriteFiles,
  required String? serialPort,
  List<String> alsoWritableRoots = const [],
  String? home,
}) {
  final reads = <String>[];
  final execRoots = <String>[];
  void addRoot(String path) {
    if (!isSafeAllowRoot(path, home: home)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
    if (!execRoots.contains(path)) execRoots.add(path);
  }

  addRoot(workDir);
  addRoot(chirpSource);
  if (driverDir != null && driverDir.isNotEmpty) addRoot(driverDir);
  final acceptedPythonRoots = _acceptedRoots(pythonRoots, home);
  for (final root in acceptedPythonRoots) {
    addRoot(root);
  }
  if (!isSafeSandboxPath(python)) {
    throw ModuleSandboxException(_unsafePathMessage);
  }
  for (final path in readOnlyFiles) {
    if (!isSafeSandboxPath(path)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
    if (!reads.contains(path)) reads.add(path);
  }
  final writes = <String>[];
  for (final path in readWriteFiles) {
    if (!isSafeSandboxPath(path)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
    if (!writes.contains(path)) writes.add(path);
  }
  if (serialPort != null &&
      !isSafeSerialPort(SandboxPlatform.macos, serialPort)) {
    throw ModuleSandboxException(_serialMessage);
  }

  // Seatbelt keeps the last matching rule. (deny default) crashes
  // sandbox-exec on current macOS, so this starts from allow default and
  // then takes back home, other drives, temp, devices, and the network.
  final buffer = StringBuffer()
    ..writeln('(version 1)')
    ..writeln('(allow default)')
    ..writeln('(deny file-read* (subpath "/Users") (subpath "/Volumes"))')
    ..writeln('(deny file-write*')
    ..writeln('  (subpath "/Users")')
    ..writeln('  (subpath "/Volumes")')
    ..writeln('  (subpath "/tmp")')
    ..writeln('  (subpath "/private/tmp")')
    ..writeln('  (subpath "/var/folders")')
    ..writeln('  (subpath "/private/var/folders")')
    ..writeln('  (subpath "/dev"))');
  for (final root in execRoots) {
    if (root == workDir || root == chirpSource || root == driverDir) continue;
    buffer.writeln(
      '(allow file-read* file-map-executable (subpath ${_quote(root)}))',
    );
  }
  buffer.writeln('(allow file-read* (subpath ${_quote(chirpSource)}))');
  if (driverDir != null && driverDir.isNotEmpty) {
    buffer.writeln('(allow file-read* (subpath ${_quote(driverDir)}))');
  }
  buffer.writeln(
    '(allow file-read* file-map-executable (literal ${_quote(python)}))',
  );
  for (final path in reads) {
    buffer.writeln('(allow file-read* (literal ${_quote(path)}))');
  }
  for (final root in [workDir, ...alsoWritableRoots]) {
    if (!isSafeAllowRoot(root, home: home)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
    buffer.writeln('(allow file-read* file-write* (subpath ${_quote(root)}))');
  }
  for (final path in writes) {
    buffer.writeln('(allow file-read* file-write* (literal ${_quote(path)}))');
  }
  buffer.writeln(
    '(allow file-read* file-write* file-ioctl (literal "/dev/null"))',
  );
  if (serialPort != null) {
    buffer.writeln(
      '(allow file-read* file-write* file-ioctl (literal ${_quote(serialPort)}))',
    );
  }
  buffer
    ..writeln('(deny network*)')
    ..writeln('(deny process-info* (target others))')
    ..writeln('(deny signal (target others))');
  return buffer.toString();
}

List<String> linuxBubblewrapArguments({
  required String workDir,
  required String python,
  required List<String> pythonRoots,
  required String chirpSource,
  required String? driverDir,
  required List<String> readOnlyFiles,
  required List<String> readWriteFiles,
  required String? serialPort,
  required List<String> pythonArguments,
  required bool hasLib64,
  required bool hasBin,
  String? home,
}) {
  void requireRoot(String path) {
    if (!isSafeAllowRoot(path, home: home)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
  }

  void requireFile(String path) {
    if (!isSafeSandboxPath(path)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
  }

  requireRoot(workDir);
  requireRoot(chirpSource);
  if (driverDir != null && driverDir.isNotEmpty) requireRoot(driverDir);
  final acceptedPythonRoots = _acceptedRoots(pythonRoots, home);
  for (final root in acceptedPythonRoots) {
    requireRoot(root);
  }
  requireFile(python);
  for (final path in [...readOnlyFiles, ...readWriteFiles]) {
    requireFile(path);
  }
  if (serialPort != null &&
      !isSafeSerialPort(SandboxPlatform.linux, serialPort)) {
    throw ModuleSandboxException(_serialMessage);
  }

  final covered = <String>['/usr', '/lib', '/proc'];
  if (hasLib64) covered.add('/lib64');
  if (hasBin) covered.add('/bin');
  final args = <String>[
    '--unshare-net',
    '--die-with-parent',
    '--clearenv',
    '--setenv',
    'HOME',
    workDir,
    '--setenv',
    'TMPDIR',
    workDir,
    '--setenv',
    'TEMP',
    workDir,
    '--setenv',
    'TMP',
    workDir,
    '--setenv',
    'PYTHONNOUSERSITE',
    '1',
    '--setenv',
    'PYTHONDONTWRITEBYTECODE',
    '1',
    '--setenv',
    'PATH',
    '/usr/bin:/bin',
    '--setenv',
    'LANG',
    'en_US.UTF-8',
    '--proc',
    '/proc',
    '--chdir',
    workDir,
    '--ro-bind',
    '/usr',
    '/usr',
    '--ro-bind',
    '/lib',
    '/lib',
    if (hasLib64) ...['--ro-bind', '/lib64', '/lib64'],
    if (hasBin) ...['--ro-bind', '/bin', '/bin'],
  ];
  final created = <String>{...covered};
  final bound = <String>{...covered};

  void mount(String source, String mode) {
    if (_isInside(source, bound)) return;
    _bubblewrapParents(args, created, covered, source);
    args.addAll([mode, source, source]);
    bound.add(source);
    created.add(source);
  }

  mount(workDir, '--bind');
  for (final root in acceptedPythonRoots) {
    mount(root, '--ro-bind');
  }
  mount(chirpSource, '--ro-bind');
  if (driverDir != null && driverDir.isNotEmpty) {
    mount(driverDir, '--ro-bind');
  }
  for (final path in readOnlyFiles) {
    mount(path, '--ro-bind');
  }
  for (final path in readWriteFiles) {
    mount(path, '--bind');
  }
  for (final device in [
    '/dev/null',
    '/dev/urandom',
    '/dev/zero',
    ?serialPort,
  ]) {
    _bubblewrapParents(args, created, covered, device);
    args.addAll(['--dev-bind', device, device]);
  }
  args.add('--');
  args.add(python);
  args.addAll(pythonArguments);
  return args;
}

class ModuleSandbox {
  Directory? _workDir;

  Future<SandboxLaunch> prepare({
    required String python,
    required String chirpSource,
    required String? driverDir,
    required String wheel,
    required String bridge,
    required String modulePath,
    required List<String> arguments,
  }) async {
    final platform = currentSandboxPlatform();
    final refusal = moduleSandboxRefusal(platform);
    if (refusal != null) throw ModuleSandboxException(refusal);
    if (platform == SandboxPlatform.linux && await _findBubblewrap() == null) {
      throw ModuleSandboxException(moduleSandboxBubblewrapMessage);
    }
    if (platform == SandboxPlatform.macos &&
        !File('/usr/bin/sandbox-exec').existsSync()) {
      throw ModuleSandboxException(_macosToolMessage);
    }

    final work = await _ensureWork();
    final moduleCopy = await _copyModule(work, modulePath);
    final pythonExe = await _resolvePython(python);
    final pythonRoots = await _pythonRoots(pythonExe);
    final rewritten = replaceModuleArgument(arguments, moduleCopy);
    final files = sandboxFilesIn(rewritten);
    final home = Platform.environment['HOME'];
    final serial = _serialPort(platform, files.port);
    final readOnly = <String>[wheel, bridge, moduleCopy];
    if (files.channels != null) readOnly.add(files.channels!);
    if (files.settings != null) readOnly.add(files.settings!);
    final readWrite = <String>[if (files.image != null) files.image!];

    if (platform == SandboxPlatform.macos) {
      final resolvedWork = work.resolveSymbolicLinksSync();
      final profile = macosSeatbeltProfile(
        workDir: work.path,
        python: pythonExe,
        pythonRoots: pythonRoots,
        chirpSource: chirpSource,
        driverDir: driverDir,
        readOnlyFiles: readOnly,
        readWriteFiles: readWrite,
        serialPort: serial,
        alsoWritableRoots: resolvedWork == work.path
            ? const []
            : [resolvedWork],
        home: home,
      );
      final profileFile = File('${work.path}/profile.sb');
      await profileFile.writeAsString(profile, flush: true);
      return SandboxLaunch(
        executable: '/usr/bin/sandbox-exec',
        arguments: ['-f', profileFile.path, '--', pythonExe, ...rewritten],
        environment: moduleSandboxEnvironment(work.path),
        workingDirectory: work.path,
      );
    }

    final bwrap = await _findBubblewrap();
    if (bwrap == null) {
      throw ModuleSandboxException(moduleSandboxBubblewrapMessage);
    }
    return SandboxLaunch(
      executable: bwrap,
      arguments: linuxBubblewrapArguments(
        workDir: work.path,
        python: pythonExe,
        pythonRoots: pythonRoots,
        chirpSource: chirpSource,
        driverDir: driverDir,
        readOnlyFiles: readOnly,
        readWriteFiles: readWrite,
        serialPort: serial,
        pythonArguments: rewritten,
        hasLib64: Directory('/lib64').existsSync(),
        hasBin: Directory('/bin').existsSync(),
        home: home,
      ),
      environment: moduleSandboxEnvironment(work.path),
      workingDirectory: work.path,
    );
  }

  Future<void> dispose() async {
    final directory = _workDir;
    _workDir = null;
    if (directory == null) return;
    try {
      if (await directory.exists()) {
        await directory.delete(recursive: true);
      }
    } on FileSystemException {
      // The next load creates a new folder. A leftover folder holds no secrets
      // beyond the module the user already chose.
    }
  }

  Future<Directory> _ensureWork() async {
    final existing = _workDir;
    if (existing != null && await existing.exists()) return existing;
    final directory = await Directory.systemTemp.createTemp('newchirp-module-');
    if (!Platform.isWindows) {
      final chmod = await Process.run('chmod', ['700', directory.path]);
      if (chmod.exitCode != 0) {
        await directory.delete(recursive: true);
        throw ModuleSandboxException(_workFolderMessage);
      }
    }
    final home = Platform.environment['HOME'];
    if (!isSafeAllowRoot(directory.path, home: home)) {
      await directory.delete(recursive: true);
      throw ModuleSandboxException(_unsafePathMessage);
    }
    _workDir = directory;
    return directory;
  }

  Future<String> _copyModule(Directory work, String modulePath) async {
    final lower = modulePath.toLowerCase();
    final extension = lower.endsWith('.mod') ? 'mod' : 'py';
    final destination = File('${work.path}/module.$extension');
    try {
      await File(modulePath).copy(destination.path);
    } on FileSystemException {
      throw ModuleSandboxException(
        'NewChirp cannot load a CHIRP module because the module file could '
        'not be copied into the sandbox.',
      );
    }
    return destination.path;
  }

  Future<String> _resolvePython(String python) async {
    var candidate = python.trim();
    if (candidate.isEmpty) throw ModuleSandboxException(_pythonMessage);
    if (!candidate.contains('/')) {
      final which = await Process.run('which', [candidate]);
      if (which.exitCode != 0) throw ModuleSandboxException(_pythonMessage);
      candidate = '${which.stdout}'.trim().split('\n').first.trim();
    }
    final file = File(candidate);
    if (!await file.exists()) throw ModuleSandboxException(_pythonMessage);
    final resolved = file.resolveSymbolicLinksSync();
    if (!isSafeSandboxPath(resolved)) {
      throw ModuleSandboxException(_unsafePathMessage);
    }
    return resolved;
  }

  Future<List<String>> _pythonRoots(String python) async {
    final result = await Process.run(python, [
      '-c',
      'import sys; print(sys.prefix)',
    ]);
    if (result.exitCode != 0) throw ModuleSandboxException(_pythonMessage);
    final prefix = '${result.stdout}'.trim();
    final roots = <String>[];
    void add(String path) {
      if (path.isEmpty || path == '/') return;
      final entity = Directory(path);
      final resolved = entity.existsSync()
          ? entity.resolveSymbolicLinksSync()
          : path;
      for (final candidate in [path, resolved]) {
        if (candidate.isEmpty ||
            candidate == '/' ||
            roots.contains(candidate)) {
          continue;
        }
        roots.add(candidate);
      }
    }

    add(prefix);
    add(File(python).parent.parent.path);
    if (roots.isEmpty) throw ModuleSandboxException(_pythonMessage);
    return roots;
  }

  String? _serialPort(SandboxPlatform platform, String? port) {
    if (port == null || port.isEmpty || !port.startsWith('/')) return null;
    if (!isSafeSerialPort(platform, port)) {
      throw ModuleSandboxException(_serialMessage);
    }
    return port;
  }
}

List<String> _acceptedRoots(List<String> paths, String? home) {
  final kept = <String>[];
  for (final path in paths) {
    if (!isSafeAllowRoot(path, home: home) || kept.contains(path)) continue;
    kept.add(path);
  }
  if (kept.isEmpty) throw ModuleSandboxException(_unsafePathMessage);
  return kept;
}

String _quote(String path) {
  if (!isSafeSandboxPath(path)) {
    throw ModuleSandboxException(_unsafePathMessage);
  }
  return '"$path"';
}

bool _isInside(String path, Set<String> roots) {
  for (final root in roots) {
    if (path == root || path.startsWith('$root/')) return true;
  }
  return false;
}

void _bubblewrapParents(
  List<String> args,
  Set<String> created,
  List<String> covered,
  String source,
) {
  final parts = source.split('/').where((part) => part.isNotEmpty).toList();
  var current = '';
  for (var index = 0; index < parts.length - 1; index++) {
    current = '$current/${parts[index]}';
    if (created.contains(current)) continue;
    if (_isInside(current, covered.toSet()) || covered.contains(current)) {
      created.add(current);
      continue;
    }
    args.addAll(['--dir', current]);
    created.add(current);
  }
}

Future<String?> _findBubblewrap() async {
  for (final candidate in ['/usr/bin/bwrap', '/bin/bwrap']) {
    if (File(candidate).existsSync()) return candidate;
  }
  final which = await Process.run('which', ['bwrap']);
  if (which.exitCode != 0) return null;
  final path = '${which.stdout}'.trim().split('\n').first.trim();
  if (path.isEmpty || !File(path).existsSync()) return null;
  return path;
}
