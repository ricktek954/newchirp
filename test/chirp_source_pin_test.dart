import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('release builds pin CHIRP to a commit and checksum', () {
    final pin = File('scripts/chirp-source.pin').readAsStringSync();
    expect(
      RegExp(r'^commit [0-9a-f]{40}$', multiLine: true).hasMatch(pin),
      isTrue,
    );
    expect(
      RegExp(r'^sha256 [0-9a-f]{64}$', multiLine: true).hasMatch(pin),
      isTrue,
    );

    const paths = [
      'scripts/update_chirp.sh',
      'scripts/bundle_macos_runtime.sh',
      'scripts/bundle_linux_runtime.sh',
      'scripts/bundle_windows_runtime.sh',
      '.github/workflows/release.yml',
    ];
    for (final path in paths) {
      final text = File(path).readAsStringSync();
      expect(text.contains('refs/heads/master'), isFalse, reason: path);
      expect(text.contains('chirp-master'), isFalse, reason: path);
    }
  });
}
