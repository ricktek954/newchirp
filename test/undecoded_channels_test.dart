import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  test('bridge undecoded channel entries parse', () {
    final parsed = undecodedChannelsFromJson([
      {'location': 37, 'error': 'list index out of range', 'raw': 'abc'},
      {'location': 52.0, 'error': null},
    ]);
    expect(parsed.map((c) => c.location), [37, 52]);
    expect(parsed.first.error, 'list index out of range');
    expect(parsed.first.raw, 'abc');
    expect(parsed.last.error, '');
    expect(undecodedChannelsFromJson(null), isEmpty);
  });
}
