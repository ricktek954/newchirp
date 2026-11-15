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
    expect(cb27ReferencePlan.groups[1].rows, hasLength(40));
    expect(cb27ReferencePlan.groups[1].rows.first.frequency, '27.60125');

    expect(australianUhfCbReferencePlan.groups.single.rows, hasLength(80));
    expect(
      australianUhfCbReferencePlan.groups.single.rows
          .firstWhere((row) => row.channel == '41')
          .frequency,
      '476.4375',
    );
    expect(
      australianUhfCbReferencePlan.groups.single.rows
          .firstWhere((row) => row.channel == '80')
          .frequency,
      '477.4125',
    );
  });

  test('each international reference has a printable PDF asset', () {
    for (final plan in internationalFrequencyReferencePlans) {
      expect(File(plan.pdfAsset).existsSync(), isTrue, reason: plan.pdfAsset);
    }
  });
}
