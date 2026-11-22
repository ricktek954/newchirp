import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/services/channel_list_pdf.dart';

void main() {
  RadioChannel channel(
    int location,
    String name,
    double frequency, {
    String duplex = '',
    double offset = 0.6,
    String tone = '',
    double txTone = 88.5,
    double rxTone = 88.5,
    int dtcs = 23,
    String crossMode = 'Tone->Tone',
    bool cleared = false,
  }) => RadioChannel(
    location: location,
    name: name,
    frequency: frequency,
    duplex: duplex,
    offset: offset,
    tone: tone,
    txTone: txTone,
    rxTone: rxTone,
    dtcs: dtcs,
    crossMode: crossMode,
    cleared: cleared,
  );

  test('rows list active channels in location order with readable tones', () {
    final rows = channelListRows([
      channel(3, 'NOAA', 162.55, duplex: 'off'),
      channel(1, 'W1AW RPT', 146.94, duplex: '-', tone: 'Tone', txTone: 100),
      channel(2, 'GONE', 147.0, cleared: true),
      channel(4, 'DCS', 446.0, tone: 'DTCS', dtcs: 754),
      channel(
        5,
        'SPLIT',
        145.5,
        duplex: 'split',
        offset: 435.25,
        tone: 'Cross',
        crossMode: 'Tone->DTCS',
        txTone: 67.0,
        dtcs: 23,
      ),
    ]);

    expect(rows.map((row) => row[0]), ['1', '3', '4', '5']);
    expect(rows[0].sublist(1, 6), [
      'W1AW RPT',
      '146.940',
      '-',
      '0.600',
      'Tone 100.0',
    ]);
    expect(rows[1].sublist(3, 5), ['TX off', '']);
    expect(rows[2][5], 'DCS D754N');
    expect(rows[3].sublist(3, 6), ['Split', '435.250', 'TX 67.0 / RX D023N']);
  });

  test('pdf has a valid structure, escapes text and paginates', () {
    final rows = [
      for (var i = 1; i <= 120; i++)
        ['$i', r'NAME (A\B)', '146.520', 'Simplex', '', '', 'FM', '', '', ''],
    ];
    final bytes = buildChannelListPdf(
      title: 'NewChirp channel list: Test',
      subtitle: 'Library · 120 channels',
      rows: rows,
    );
    final text = latin1.decode(bytes);

    expect(text.startsWith('%PDF-1.4'), isTrue);
    expect(text.trimRight().endsWith('%%EOF'), isTrue);
    expect(text, contains(r'(NAME \(A\\B\)) Tj'));
    final pages = RegExp(r'/Type /Page ').allMatches(text).length;
    expect(pages, greaterThan(1));
    expect(text, contains('Page 1 of $pages'));

    // Every xref entry points at the start of its object.
    final startxref = int.parse(
      RegExp(r'startxref\n(\d+)').firstMatch(text)!.group(1)!,
    );
    expect(text.substring(startxref).startsWith('xref'), isTrue);
    final entries = RegExp(
      r'(\d{10}) 00000 n ',
    ).allMatches(text.substring(startxref)).toList();
    for (var i = 0; i < entries.length; i++) {
      final offset = int.parse(entries[i].group(1)!);
      expect(text.substring(offset).startsWith('${i + 1} 0 obj'), isTrue);
    }
  });

  test('long names are cut to fit their column', () {
    final bytes = buildChannelListPdf(
      title: 't',
      subtitle: 's',
      rows: [
        ['1', 'A VERY LONG CHANNEL NAME THAT CANNOT FIT', '146.520'],
      ],
    );
    expect(latin1.decode(bytes), contains('...) Tj'));
  });

  test('writes a sample for visual review when asked', () {
    final path = Platform.environment['NEWCHIRP_CHANNEL_PDF_SAMPLE'];
    if (path == null) return;
    File(path).writeAsBytesSync(
      buildChannelListPdf(
        title: 'NewChirp channel list: Baofeng UV-5R',
        subtitle: 'My library · 40 channels · printed 2026-11-22',
        rows: channelListRows([
          for (var i = 1; i <= 40; i++)
            channel(
              i,
              i.isEven ? 'RPT $i' : 'SIMPLEX $i',
              146.0 + i * 0.015,
              duplex: i.isEven ? '+' : '',
              tone: i % 3 == 0 ? 'TSQL' : (i.isEven ? 'Tone' : ''),
              txTone: 100.0,
              rxTone: 100.0,
            ),
        ]),
        letter: true,
      ),
    );
  });
}
