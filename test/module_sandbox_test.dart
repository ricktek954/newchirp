import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/module_sandbox.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('windows and other systems refuse a module sandbox', () {
    expect(
      moduleSandboxRefusal(SandboxPlatform.windows),
      'NewChirp cannot load a CHIRP module on Windows because it cannot run '
      'that module in a sandbox yet.',
    );
    expect(
      moduleSandboxRefusal(SandboxPlatform.other),
      contains('cannot run that module in a sandbox'),
    );
    expect(moduleSandboxRefusal(SandboxPlatform.macos), isNull);
    expect(moduleSandboxRefusal(SandboxPlatform.linux), isNull);
    expect(moduleSandboxBubblewrapMessage, contains('bubblewrap'));
  });

  test('rejects sandbox paths that could escape the profile', () {
    expect(isSafeSandboxPath('/tmp/newchirp-ok'), isTrue);
    expect(isSafeSandboxPath('/tmp/has"quote'), isFalse);
    expect(isSafeSandboxPath('/tmp/../etc'), isFalse);
    expect(isSafeSandboxPath('/'), isFalse);
    expect(isSafeSandboxPath('relative/path'), isFalse);
    expect(isSafeSandboxPath('/tmp/foo (1)'), isFalse);
    expect(isSafeSandboxPath('/tmp/foo\\bar'), isFalse);
  });

  test('does not treat the home folder as an allow root', () {
    expect(isSafeAllowRoot('/Users/randy', home: '/Users/randy'), isFalse);
    expect(isSafeAllowRoot('/Users', home: '/Users/randy'), isFalse);
    expect(isSafeAllowRoot('/home/randy', home: '/home/randy'), isFalse);
    expect(isSafeAllowRoot('/Volumes/Radio', home: '/Users/randy'), isFalse);
    expect(
      isSafeAllowRoot('/Users/randy/project/chirp', home: '/Users/randy'),
      isTrue,
    );
  });

  test('serial allows one radio device', () {
    expect(
      isSafeSerialPort(SandboxPlatform.macos, '/dev/cu.usbserial-110'),
      isTrue,
    );
    expect(
      isSafeSerialPort(SandboxPlatform.macos, '/dev/tty.usbserial-10'),
      isTrue,
    );
    expect(isSafeSerialPort(SandboxPlatform.macos, '/dev/disk0'), isFalse);
    expect(isSafeSerialPort(SandboxPlatform.linux, '/dev/ttyUSB0'), isTrue);
    expect(isSafeSerialPort(SandboxPlatform.linux, '/dev/ttyACM1'), isTrue);
    expect(isSafeSerialPort(SandboxPlatform.linux, '/dev/sda'), isFalse);
    expect(isSafeSerialPort(SandboxPlatform.windows, r'COM3'), isFalse);
  });

  test('macOS profile blocks home and the network', () {
    final profile = macosSeatbeltProfile(
      workDir: '/var/folders/zz/T/newchirp-module-test',
      python: '/opt/homebrew/opt/python@3.15/bin/python3.15',
      pythonRoots: [
        '/opt/homebrew/Cellar/python@3.15/3.15.0/Frameworks/Python.framework/Versions/3.15',
      ],
      chirpSource: '/Users/randy/AI Projects/newchirp/build_support/chirp',
      driverDir: null,
      readOnlyFiles: [
        '/var/folders/zz/T/bridge.py',
        '/var/folders/zz/T/wheel.whl',
      ],
      readWriteFiles: [
        '/Users/randy/Library/Application Support/NewChirp/images/FT.img',
      ],
      serialPort: '/dev/cu.usbserial-110',
      home: '/Users/randy',
    );

    expect(profile, contains('(deny network*)'));
    expect(profile, contains('(subpath "/Users")'));
    expect(profile, contains('(subpath "/Volumes")'));
    expect(
      profile,
      contains('(subpath "/var/folders/zz/T/newchirp-module-test")'),
    );
    expect(profile, contains('(literal "/dev/cu.usbserial-110")'));
    expect(profile, contains('(literal "/dev/null")'));
    expect(profile, isNot(contains('(subpath "/Users/randy")')));
    expect(
      profile.indexOf('(deny file-read*'),
      lessThan(
        profile.indexOf(
          '(subpath "/Users/randy/AI Projects/newchirp/build_support/chirp")',
        ),
      ),
    );
    expect(
      profile.indexOf('(deny network*)'),
      greaterThan(
        profile.indexOf('(subpath "/var/folders/zz/T/newchirp-module-test")'),
      ),
    );
  });

  test('macOS profile refuses the home folder and a broken path', () {
    expect(
      () => macosSeatbeltProfile(
        workDir: '/var/folders/zz/T/newchirp-module-test',
        python: '/usr/bin/python3',
        pythonRoots: ['/usr'],
        chirpSource: '/Users/randy',
        driverDir: null,
        readOnlyFiles: const [],
        readWriteFiles: const [],
        serialPort: null,
        home: '/Users/randy',
      ),
      throwsA(isA<ModuleSandboxException>()),
    );
    expect(
      () => macosSeatbeltProfile(
        workDir: '/var/folders/zz/T/newchirp-module-test',
        python: '/usr/bin/python3',
        pythonRoots: ['/usr'],
        chirpSource: '/Users/randy/project/chirp',
        driverDir: null,
        readOnlyFiles: const ['/tmp/evil" (allow network*)'],
        readWriteFiles: const [],
        serialPort: null,
        home: '/Users/randy',
      ),
      throwsA(isA<ModuleSandboxException>()),
    );
  });

  test('linux bubblewrap drops the network and does not bind home', () {
    final args = linuxBubblewrapArguments(
      workDir: '/tmp/newchirp-module-test',
      python: '/usr/bin/python3',
      pythonRoots: ['/usr'],
      chirpSource: '/home/randy/src/chirp',
      driverDir: null,
      readOnlyFiles: ['/tmp/bridge.py'],
      readWriteFiles: ['/home/randy/.config/newchirp/images/FT.img'],
      serialPort: '/dev/ttyUSB0',
      pythonArguments: [
        '/tmp/bridge.py',
        '--module',
        '/tmp/newchirp-module-test/module.py',
      ],
      hasLib64: true,
      hasBin: true,
      home: '/home/randy',
    );

    expect(args, contains('--unshare-net'));
    expect(args, contains('--die-with-parent'));
    expect(args, contains('--clearenv'));
    expect(args.contains('--dev'), isFalse);
    expect(args, contains('/dev/ttyUSB0'));
    expect(args, contains('--dev-bind'));
    for (var index = 0; index < args.length - 1; index++) {
      if (args[index] != '--ro-bind' && args[index] != '--bind') continue;
      expect(args[index + 1], isNot('/home/randy'));
      expect(args[index + 1], isNot('/home'));
      expect(args[index + 1], isNot('/Users'));
    }
  });

  test('linux bubblewrap refuses a port that is not a radio device', () {
    expect(
      () => linuxBubblewrapArguments(
        workDir: '/tmp/newchirp-module-test',
        python: '/usr/bin/python3',
        pythonRoots: ['/usr'],
        chirpSource: '/home/randy/src/chirp',
        driverDir: null,
        readOnlyFiles: const [],
        readWriteFiles: const [],
        serialPort: '/dev/sda',
        pythonArguments: const ['/tmp/bridge.py'],
        hasLib64: false,
        hasBin: true,
        home: '/home/randy',
      ),
      throwsA(isA<ModuleSandboxException>()),
    );
  });

  test(
    'macOS launch plan uses sandbox-exec and a private environment',
    () async {
      if (!Platform.isMacOS) return;
      final source = Directory('build_support/chirp-20261016');
      expect(source.existsSync(), isTrue, reason: 'pinned local CHIRP tree');
      final sandbox = ModuleSandbox();
      addTearDown(sandbox.dispose);
      final module = File('${Directory.systemTemp.path}/newchirp-plan-$pid.py');
      await module.writeAsString('print("hi")\n');
      addTearDown(() async {
        if (await module.exists()) await module.delete();
      });

      final launch = await sandbox.prepare(
        python: 'python3',
        chirpSource: source.absolute.path,
        driverDir: null,
        wheel: module.absolute.path,
        bridge: module.absolute.path,
        modulePath: module.path,
        arguments: [module.absolute.path, '--module', module.path],
      );

      expect(launch.executable, '/usr/bin/sandbox-exec');
      expect(launch.environment['HOME'], launch.workingDirectory);
      expect(launch.environment.containsKey('SSH_AUTH_SOCK'), isFalse);
      expect(
        launch.environment.keys,
        unorderedEquals([
          'HOME',
          'TMPDIR',
          'TEMP',
          'TMP',
          'PYTHONNOUSERSITE',
          'PYTHONDONTWRITEBYTECODE',
          'PATH',
          'LANG',
        ]),
      );
      final profile = File(
        '${launch.workingDirectory}/profile.sb',
      ).readAsStringSync();
      expect(profile, contains('(deny network*)'));
      final moduleFlag = launch.arguments.indexOf('--module');
      expect(moduleFlag, greaterThanOrEqualTo(0));
      expect(launch.arguments[moduleFlag + 1], endsWith('/module.py'));
      expect(launch.arguments[moduleFlag + 1], isNot(module.absolute.path));
    },
  );
}
