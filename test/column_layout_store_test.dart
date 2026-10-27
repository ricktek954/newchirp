import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/column_layout_store.dart';

void main() {
  test('column order and widths persist across store instances', () async {
    final directory = await Directory.systemTemp.createTemp(
      'newchirp-column-layout-',
    );
    addTearDown(() => directory.delete(recursive: true));
    final path = '${directory.path}/column-layout.json';

    await ColumnLayoutStore(path: path).save(
      const ColumnLayout(
        order: ['NAME', 'RX FREQUENCY', '#'],
        widths: {'NAME': 238, 'RX FREQUENCY': 144},
        showEmptySlots: true,
      ),
    );
    final restored = await ColumnLayoutStore(path: path).load();

    expect(restored?.order, ['NAME', 'RX FREQUENCY', '#']);
    expect(restored?.widths['NAME'], 238);
    expect(restored?.widths['RX FREQUENCY'], 144);
    expect(restored?.showEmptySlots, isTrue);
  });
}
