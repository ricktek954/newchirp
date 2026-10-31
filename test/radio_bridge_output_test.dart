import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  test('bridge output tolerates non-UTF-8 diagnostic bytes', () {
    final output = bridgeProcessDecoder.convert(<int>[
      0x50, // P
      0x79, // y
      0x20, // space
      0xb5, // legacy-encoded micro sign
      0x20, // space
      0x72, // r
    ]);

    expect(output, 'Py \ufffd r');
  });
}
