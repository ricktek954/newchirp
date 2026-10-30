import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  test('ignores CHIRP replacement warnings with common quote styles', () {
    expect(
      isBenignBridgeStderrLine(
        "Replacing existing driver id 'Kenwood_TS-2000'",
      ),
      isTrue,
    );
    expect(
      isBenignBridgeStderrLine(
        'Replacing existing driver id "Kenwood_TS-2000"',
      ),
      isTrue,
    );
    expect(
      isBenignBridgeStderrLine(
        'Replacing existing driver id `Kenwood_TS-2000`',
      ),
      isTrue,
    );
  });

  test('keeps duplicate driver errors visible', () {
    expect(
      isBenignBridgeStderrLine('Duplicate radio driver id `Kenwood_TH-D75`'),
      isFalse,
    );
  });
}
