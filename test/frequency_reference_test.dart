import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/frequency_reference.dart';

void main() {
  test('marine, CB, and Australian UHF reference tables are complete', () {
    expect(marineVhfReferencePlan.groups.single.rows, hasLength(57));
    expect(
      marineVhfReferencePlan.groups.single.rows
          .firstWhere((row) => row.channel == '16')
          .frequency,
      '156.800',
    );

    expect(cb27ReferencePlan.groups, hasLength(2));
    expect(cb27ReferencePlan.groups[0].rows, hasLength(40));
    expect(
      cb27ReferencePlan.groups[0].rows[15].notes,
      'Australia: local calling (LSB)',
    );
    expect(
      cb27ReferencePlan.groups[0].rows[34].notes,
      'Australia: DX calling (LSB)',
    );
    expect(cb27ReferencePlan.groups[1].rows, hasLength(40));
    expect(cb27ReferencePlan.groups[1].rows.first.frequency, '27.60125');

    expect(australianUhfCbReferencePlan.groups.single.rows, hasLength(80));
    final australianRows = australianUhfCbReferencePlan.groups.single.rows;
    expect(australianRows[0].frequency, '476.4250');
    expect(australianRows[1].frequency, '476.4500');
    expect(australianRows[39].frequency, '477.4000');
    expect(australianRows[40].frequency, '476.4375');
    expect(australianRows[70].frequency, '477.1875');
    expect(australianRows.last.frequency, '477.4125');
    expect(australianRows[0].notes, 'Repeater output; input Ch 31');
    expect(australianRows[30].notes, 'Repeater input; output Ch 01');
    expect(australianRows[40].notes, 'Repeater output; input Ch 71');
    expect(australianRows[70].notes, 'Repeater input; output Ch 41');
    expect(australianRows[61].notes, 'Guard channel; receive-only');
    expect(australianRows[21].notes, 'Data/telemetry only; no voice');
    expect(australianRows[39].notes, 'Australia-wide road / truck');
  });

  test('PMR446 lists the 16 CEPT analogue channels', () {
    final rows = pmr446ReferencePlan.groups.single.rows;
    expect(rows, hasLength(16));
    expect(rows.first.frequency, '446.00625');
    expect(rows[7].frequency, '446.09375');
    expect(rows[8].frequency, '446.10625');
    expect(rows.last.frequency, '446.19375');
    expect(internationalFrequencyReferencePlans, contains(pmr446ReferencePlan));
  });

  test('each international reference has a printable PDF asset', () {
    for (final plan in internationalFrequencyReferencePlans) {
      expect(File(plan.pdfAsset).existsSync(), isTrue, reason: plan.pdfAsset);
    }
  });
}
