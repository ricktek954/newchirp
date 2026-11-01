import 'dart:io';

String? chirpSourceForTests() {
  final pinFile = File('scripts/chirp-source.pin');
  if (!pinFile.existsSync()) {
    throw StateError('CHIRP source pin is missing.');
  }
  final pin = pinFile.readAsStringSync();
  final match = RegExp(
    r'^commit ([0-9a-f]{40})$',
    multiLine: true,
  ).firstMatch(pin);
  if (match == null) {
    throw StateError('CHIRP source pin contains an invalid commit.');
  }

  final commit = match.group(1)!;
  final versionFile = File('build_support/chirp-version.txt');
  if (versionFile.existsSync()) {
    final current = versionFile.readAsStringSync().trim();
    if (current != commit) {
      throw StateError(
        'CHIRP build metadata is stale. '
        'Run scripts/update_chirp.sh before running tests.',
      );
    }
  }

  final source = 'build_support/chirp-$commit';
  if (!File('$source/chirp/chirp_common.py').existsSync()) {
    return null;
  }
  return source;
}

String requireChirpSourceForTests() {
  final source = chirpSourceForTests();
  if (source == null) {
    throw StateError(
      'Pinned CHIRP source is unavailable. '
      'Run scripts/update_chirp.sh before running tests.',
    );
  }
  return source;
}
