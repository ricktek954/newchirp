import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/window_state_store.dart';

void main() {
  test('window size, position, and maximized state persist', () async {
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-window-state-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final path = '${directory.path}/window-state.json';

    await WindowStateStore(path: path).save(
      const WindowState(
        width: 1280,
        height: 800,
        x: 120,
        y: 60,
        maximized: true,
      ),
    );
    final restored = await WindowStateStore(path: path).load();

    expect(restored?.width, 1280);
    expect(restored?.height, 800);
    expect(restored?.x, 120);
    expect(restored?.y, 60);
    expect(restored?.maximized, isTrue);
  });

  test('malformed state falls back to null', () async {
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-window-state-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final path = '${directory.path}/window-state.json';
    await File(path).writeAsString('{not json');

    expect(await WindowStateStore(path: path).load(), isNull);
  });

  test('mixed-scale Windows displays center ambiguous saved bounds', () {
    const state = WindowState(width: 1200, height: 800, x: 3840, y: 100);
    const primary = WindowDisplayArea(
      left: 0,
      top: 0,
      width: 1920,
      height: 1040,
      scaleFactor: 2,
    );
    const secondary = WindowDisplayArea(
      left: 3840,
      top: 0,
      width: 1920,
      height: 1080,
      scaleFactor: 1,
    );

    final normalized = normalizeWindowStateForDisplays(
      state: state,
      displays: const [primary, secondary],
      primary: primary,
      centerOnMixedScale: true,
    );

    expect(normalized?.width, 1200);
    expect(normalized?.height, 800);
    expect(normalized?.x, 360);
    expect(normalized?.y, 120);
  });

  test('matching-scale displays retain an accessible saved position', () {
    const state = WindowState(width: 1200, height: 800, x: 2200, y: 100);
    const primary = WindowDisplayArea(
      left: 0,
      top: 0,
      width: 1920,
      height: 1080,
      scaleFactor: 1,
    );
    const secondary = WindowDisplayArea(
      left: 1920,
      top: 0,
      width: 1920,
      height: 1080,
      scaleFactor: 1,
    );

    final normalized = normalizeWindowStateForDisplays(
      state: state,
      displays: const [primary, secondary],
      primary: primary,
      centerOnMixedScale: true,
    );

    expect(normalized?.x, 2200);
    expect(normalized?.y, 100);
  });

  test('offscreen bounds are centered and clamped to the primary display', () {
    const state = WindowState(width: 2600, height: 1400, x: 9000, y: 9000);
    const primary = WindowDisplayArea(
      left: 0,
      top: 0,
      width: 1920,
      height: 1040,
      scaleFactor: 1,
    );

    final normalized = normalizeWindowStateForDisplays(
      state: state,
      displays: const [primary],
      primary: primary,
      centerOnMixedScale: true,
    );

    expect(normalized?.width, 1920);
    expect(normalized?.height, 1040);
    expect(normalized?.x, 0);
    expect(normalized?.y, 0);
  });
}
