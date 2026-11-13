import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  test('packaged Windows build never probes Microsoft Store aliases', () async {
    final probed = <String>[];

    await expectLater(
      resolvePythonExecutable(
        operatingSystem: 'windows',
        resourcesDirectory: r'C:\Program Files\NewChirp',
        configuredPath: null,
        macRuntime: null,
        allowSystemPython: false,
        probe: (executable, arguments) async {
          probed.add(executable);
          throw ProcessException(executable, arguments, 'not found');
        },
      ),
      throwsA(
        isA<RadioBridgeException>().having(
          (error) => error.message,
          'message',
          allOf(
            contains('bundled Python runtime'),
            contains(r'C:\Program Files\NewChirp\python\python.exe'),
            contains('Reinstall NewChirp'),
            contains('Microsoft Store'),
          ),
        ),
      ),
    );

    expect(probed, [r'C:\Program Files\NewChirp\python\python.exe']);
  });

  test('packaged Windows build resolves its bundled runtime', () async {
    final python = await resolvePythonExecutable(
      operatingSystem: 'windows',
      resourcesDirectory: r'C:\Program Files\NewChirp',
      configuredPath: null,
      macRuntime: null,
      allowSystemPython: false,
      probe: (executable, arguments) async => ProcessResult(0, 0, '3.13\n', ''),
    );

    expect(python, r'C:\Program Files\NewChirp\python\python.exe');
  });

  test('source runs retain the system Python fallback', () async {
    final probed = <String>[];
    final python = await resolvePythonExecutable(
      operatingSystem: 'windows',
      resourcesDirectory: r'C:\Program Files\NewChirp',
      configuredPath: null,
      macRuntime: null,
      allowSystemPython: true,
      probe: (executable, arguments) async {
        probed.add(executable);
        if (executable == 'python3') {
          return ProcessResult(0, 0, '3.13\n', '');
        }
        throw ProcessException(executable, arguments, 'not found');
      },
    );

    expect(python, 'python3');
    expect(probed, [
      r'C:\Program Files\NewChirp\python\python.exe',
      'python',
      'python3',
    ]);
  });
}
