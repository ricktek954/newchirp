import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

String chirpSourceForTest() {
  const candidates = [
    'build_support/chirp-20261023',
    'build_support/chirp-20261016',
    '../chirp-20260626',
  ];
  for (final candidate in candidates) {
    if (File('$candidate/chirp/chirp_common.py').existsSync()) {
      return candidate;
    }
  }
  throw StateError('CHIRP source for tests was not found.');
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('loads .py and .mod modules for the current bridge session', () async {
    final source = chirpSourceForTest();
    for (final extension in ['py', 'mod']) {
      final suffix = extension == 'py' ? 'Py' : 'Mod';
      final module = File(
        '${Directory.systemTemp.path}/newchirp-module-$pid.$extension',
      );
      await module.writeAsString('''
from chirp import chirp_common, directory


@directory.register
class NewChirpLoadedModule${suffix}Radio(chirp_common.CloneModeRadio):
    VENDOR = "NewChirpTest"
    MODEL = "LoadedModule$suffix"
    VARIANT = ""
''', flush: true);
      addTearDown(() async {
        if (await module.exists()) await module.delete();
      });

      final bridge = RadioBridge(sourcePath: source);
      final models = await bridge.loadModule(module.path);

      expect(bridge.loadedModulePath, module.path);
      expect(models, contains('NewChirpTest_LoadedModule$suffix'));

      bridge.unloadModule();
      final baseModels = await bridge.models();

      expect(bridge.loadedModulePath, isNull);
      expect(baseModels, isNot(contains('NewChirpTest_LoadedModule$suffix')));
    }
  });

  test('rejects non-CHIRP module extensions', () async {
    final source = chirpSourceForTest();
    final module = File(
      '${Directory.systemTemp.path}/newchirp-module-$pid.txt',
    );
    await module.writeAsString('not a module', flush: true);
    addTearDown(() async {
      if (await module.exists()) await module.delete();
    });

    final bridge = RadioBridge(sourcePath: source);

    await expectLater(
      () => bridge.loadModule(module.path),
      throwsA(
        isA<RadioBridgeException>().having(
          (error) => error.message,
          'message',
          contains('.py'),
        ),
      ),
    );
    expect(bridge.loadedModulePath, isNull);
  });

  test('a loaded module can override a built-in CHIRP driver', () async {
    final source = chirpSourceForTest();
    final module = File(
      '${Directory.systemTemp.path}/newchirp-override-module-$pid.py',
    );
    await module.writeAsString('''
from chirp import chirp_common, directory


@directory.register
class NewChirpOverrideRadio(chirp_common.CloneModeRadio):
    VENDOR = "Yaesu"
    MODEL = "FT-857/897"
    VARIANT = ""

    @classmethod
    def get_prompts(cls):
        prompts = chirp_common.RadioPrompts()
        prompts.pre_download = "Loaded module override"
        return prompts
''', flush: true);
    addTearDown(() async {
      if (await module.exists()) await module.delete();
    });

    final bridge = RadioBridge(sourcePath: source);
    await bridge.loadModule(module.path);
    final instructions = await bridge.instructions('Yaesu_FT-857_897');

    expect(instructions.preDownload, 'Loaded module override');
  });

  test('rolls back a module that fails to load', () async {
    final source = chirpSourceForTest();
    final module = File(
      '${Directory.systemTemp.path}/newchirp-broken-module-$pid.py',
    );
    await module.writeAsString('this is not valid Python:', flush: true);
    addTearDown(() async {
      if (await module.exists()) await module.delete();
    });

    final bridge = RadioBridge(sourcePath: source);

    await expectLater(
      () => bridge.loadModule(module.path),
      throwsA(
        isA<RadioBridgeException>().having(
          (error) => error.message,
          'message',
          contains('Could not load CHIRP module'),
        ),
      ),
    );
    expect(bridge.loadedModulePath, isNull);
  });

  test('a loaded module cannot read the home folder', () async {
    final source = chirpSourceForTest();
    final secret = File('pubspec.yaml').absolute.path;
    final module = File(
      '${Directory.systemTemp.path}/newchirp-sandbox-probe-$pid.py',
    );
    final secretLiteral = jsonEncode(secret);
    await module.writeAsString('''
from chirp import chirp_common, directory
held = True
try:
    open($secretLiteral, encoding="utf-8").read()
    held = False
except Exception:
    held = True

@directory.register
class NewChirpSandboxProbe(chirp_common.CloneModeRadio):
    VENDOR = "NewChirpTest"
    MODEL = "SandboxHeld" if held else "SandboxLeak"
    VARIANT = ""
''', flush: true);
    addTearDown(() async {
      if (await module.exists()) await module.delete();
    });

    final bridge = RadioBridge(sourcePath: source);
    addTearDown(bridge.unloadModule);
    final models = await bridge.loadModule(module.path);

    expect(models, contains('NewChirpTest_SandboxHeld'));
    expect(models, isNot(contains('NewChirpTest_SandboxLeak')));
  });
}
