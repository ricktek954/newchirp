import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/widgets/channel_grid_layout.dart';

void main() {
  test('selection remembers the previous row and skips a repeat', () {
    final selection = ChannelSelection(-1);
    final seen = <int>[];
    selection.addListener(() => seen.add(selection.value));

    selection.choose(4);
    expect(selection.previous, -1);
    expect(selection.value, 4);
    expect(seen, [4]);

    selection.choose(4);
    expect(seen, [4]);

    selection.choose(1);
    expect(selection.previous, 4);
    expect(selection.value, 1);
    expect(seen, [4, 1]);
  });

  testWidgets('a column width change does not rebuild the cell', (
    tester,
  ) async {
    final width = ValueNotifier<double>(80);
    var builds = 0;
    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: Align(
          alignment: Alignment.topLeft,
          child: ColumnWidthBox(
            width: width,
            child: Builder(
              builder: (context) {
                builds += 1;
                return const Text('CELL');
              },
            ),
          ),
        ),
      ),
    );

    width.value = 140;
    await tester.pump();

    expect(builds, 1);
    expect(tester.getSize(find.byType(ColumnWidthBox)).width, 140);
  });

  testWidgets('selection repaints the old and new rows only', (tester) async {
    final selection = ChannelSelection(0);
    final builds = [0, 0, 0];

    Widget row(int index) {
      return ChannelRowFrame(
        selection: selection,
        index: index,
        dropTarget: false,
        cleared: false,
        child: Builder(
          builder: (context) {
            builds[index] += 1;
            return Text('row $index');
          },
        ),
      );
    }

    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: Column(children: [row(0), row(1), row(2)]),
      ),
    );
    expect(builds, [1, 1, 1]);

    selection.choose(1);
    await tester.pump();

    expect(builds, [1, 1, 1]);
    expect(_rowColor(tester, 'row 0'), Colors.white);
    expect(_rowColor(tester, 'row 1'), const Color(0xFFE8F3ED));
    expect(_rowColor(tester, 'row 2'), Colors.white);
  });
}

Color _rowColor(WidgetTester tester, String text) {
  final container = tester.widget<Container>(
    find.ancestor(of: find.text(text), matching: find.byType(Container)),
  );
  return container.color!;
}
