import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/radio_bridge.dart';

void main() {
  test(
    'caches bridge assets for later operations in the same session',
    () async {
      var loaderCalls = 0;
      final bridge = RadioBridge(
        assetLoader: (key) async {
          loaderCalls++;
          if (loaderCalls > 1) {
            throw StateError('asset bundle became unavailable');
          }
          return <int>[1, 2, 3, 4];
        },
      );

      final first = await bridge.loadBundledAsset('scripts/cache-test.py');
      final second = await bridge.loadBundledAsset('scripts/cache-test.py');

      expect(loaderCalls, 1);
      expect(first, <int>[1, 2, 3, 4]);
      expect(second, first);
    },
  );

  test('missing bridge assets produce an actionable error', () async {
    final bridge = RadioBridge(
      assetLoader: (key) async => throw StateError('missing'),
    );

    await expectLater(
      bridge.loadBundledAsset('scripts/definitely-missing.py'),
      throwsA(
        isA<RadioBridgeException>().having(
          (error) => error.message,
          'message',
          contains('Reinstall the current NewChirp build'),
        ),
      ),
    );
  });
}
