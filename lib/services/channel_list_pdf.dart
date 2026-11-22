import 'dart:convert';
import 'dart:typed_data';

import '../models/radio_channel.dart';

/// One printed column: header text, relative width, and right alignment.
class ChannelListColumn {
  const ChannelListColumn(this.header, this.width, {this.alignRight = false});

  final String header;
  final double width;
  final bool alignRight;
}

const channelListColumns = [
  ChannelListColumn('#', 0.45, alignRight: true),
  ChannelListColumn('Name', 1.7),
  ChannelListColumn('RX MHz', 1.0, alignRight: true),
  ChannelListColumn('Duplex', 0.7),
  ChannelListColumn('Offset / TX', 1.0, alignRight: true),
  ChannelListColumn('Tone', 1.8),
  ChannelListColumn('Mode', 0.6),
  ChannelListColumn('Power', 1.1),
  ChannelListColumn('Scan', 0.7),
  ChannelListColumn('Comment', 1.95),
];

String _mhz(double value) {
  // Six decimals, trimmed to at least three: 146.520, 462.5625.
  var text = value.toStringAsFixed(6);
  while (text.endsWith('0') && text.indexOf('.') < text.length - 4) {
    text = text.substring(0, text.length - 1);
  }
  return text;
}

String _dcs(int code, String polarity) =>
    'D${code.toString().padLeft(3, '0')}$polarity';

/// Human-readable squelch summary for one channel.
String channelToneSummary(RadioChannel channel) {
  final tx = effectiveTransmitCtcssTone(channel);
  final rx = effectiveReceiveCtcssTone(channel);
  final polarity = channel.dtcsPolarity.isEmpty
      ? ''
      : channel.dtcsPolarity.substring(0, 1);
  final rxPolarity = channel.dtcsPolarity.length > 1
      ? channel.dtcsPolarity.substring(1, 2)
      : polarity;
  return switch (channel.tone) {
    '' => '',
    'Tone' => 'Tone ${tx?.toStringAsFixed(1) ?? ''}',
    'TSQL' => 'TSQL ${rx?.toStringAsFixed(1) ?? tx?.toStringAsFixed(1) ?? ''}',
    'TSQL-R' => 'TSQL-R ${rx?.toStringAsFixed(1) ?? ''}',
    'DTCS' => 'DCS ${_dcs(channel.dtcs, polarity)}',
    'DTCS-R' => 'DCS-R ${_dcs(channel.dtcs, polarity)}',
    'Cross' => _crossSummary(channel, tx, rx, polarity, rxPolarity),
    _ => channel.tone,
  };
}

String _crossSummary(
  RadioChannel channel,
  double? tx,
  double? rx,
  String polarity,
  String rxPolarity,
) {
  final parts = channel.crossMode.split('->');
  final txKind = parts.isNotEmpty ? parts.first : '';
  final rxKind = parts.length > 1 ? parts.last : '';
  String side(String kind, {required bool transmit}) => switch (kind) {
    'Tone' =>
      (transmit ? tx : rx)?.toStringAsFixed(1) ??
          (transmit ? channel.txTone : channel.rxTone).toStringAsFixed(1),
    'DTCS' =>
      transmit
          ? _dcs(channel.dtcs, polarity)
          : _dcs(channel.rxDtcs, rxPolarity),
    _ => 'none',
  };
  return 'TX ${side(txKind, transmit: true)} / '
      'RX ${side(rxKind, transmit: false)}';
}

/// The printed cells for each active channel, in location order.
List<List<String>> channelListRows(
  List<RadioChannel> channels, {
  String? radioModel,
}) {
  final active = channels.where((channel) => !channel.cleared).toList()
    ..sort((a, b) => a.location.compareTo(b.location));
  return [
    for (final channel in active)
      [
        channelNumberLabel(radioModel, channel.location),
        channel.name,
        _mhz(channel.frequency),
        switch (channel.duplex) {
          '' => 'Simplex',
          'split' => 'Split',
          'off' => 'TX off',
          final other => other,
        },
        // For "split" the offset field holds the TX frequency itself.
        channel.duplex == '' || channel.duplex == 'off'
            ? ''
            : _mhz(channel.offset),
        channelToneSummary(channel),
        channel.mode,
        channel.power,
        scanLabel(channel.skip),
        channel.comment,
      ],
  ];
}

// --- Minimal PDF writer -----------------------------------------------------
//
// Uses only the standard Helvetica fonts (no embedding) with WinAnsi
// encoding. Characters outside Latin-1 print as "?".

const _pageWidth = 842.0; // A4 landscape; Letter is chosen below when asked.
const _pageHeight = 595.0;
const _letterWidth = 792.0;
const _letterHeight = 612.0;
const _margin = 36.0;
const _fontSize = 8.0;
const _rowHeight = 12.0;

String _pdfText(String value) {
  final buffer = StringBuffer();
  for (final rune in value.runes) {
    final char = rune <= 0xFF ? String.fromCharCode(rune) : '?';
    if (char == r'\' || char == '(' || char == ')') buffer.write(r'\');
    if (rune < 0x20) {
      buffer.write(' ');
    } else {
      buffer.write(char);
    }
  }
  return buffer.toString();
}

// Helvetica advance widths (per 1000 em) for printable ASCII 32..126; other
// Latin-1 characters use an average width.
const _helveticaWidths = [
  278,
  278,
  355,
  556,
  556,
  889,
  667,
  191,
  333,
  333,
  389,
  584,
  278,
  333,
  278,
  278,
  556,
  556,
  556,
  556,
  556,
  556,
  556,
  556,
  556,
  556,
  278,
  278,
  584,
  584,
  584,
  556,
  1015,
  667,
  667,
  722,
  722,
  667,
  611,
  778,
  722,
  278,
  500,
  667,
  556,
  833,
  722,
  778,
  667,
  778,
  722,
  667,
  611,
  722,
  667,
  944,
  667,
  667,
  611,
  278,
  278,
  278,
  469,
  556,
  333,
  556,
  556,
  500,
  556,
  556,
  278,
  556,
  556,
  222,
  222,
  500,
  222,
  833,
  556,
  556,
  556,
  556,
  333,
  500,
  278,
  556,
  500,
  722,
  500,
  500,
  500,
  334,
  260,
  334,
  584,
];

double _textWidth(String text, double size, {bool bold = false}) {
  var total = 0.0;
  for (final rune in text.runes) {
    final width = rune >= 32 && rune <= 126 ? _helveticaWidths[rune - 32] : 556;
    total += width * (bold ? 1.06 : 1.0);
  }
  return total * size / 1000;
}

String _fit(String text, double maxWidth, {bool bold = false}) {
  if (_textWidth(text, _fontSize, bold: bold) <= maxWidth) return text;
  // A plain "..." because the Unicode ellipsis is outside WinAnsi here.
  var cut = text;
  while (cut.isNotEmpty &&
      _textWidth('$cut...', _fontSize, bold: bold) > maxWidth) {
    cut = cut.substring(0, cut.length - 1);
  }
  return cut.isEmpty ? '' : '${cut.trimRight()}...';
}

/// Build a landscape PDF listing [rows] under [title] and [subtitle].
Uint8List buildChannelListPdf({
  required String title,
  required String subtitle,
  required List<List<String>> rows,
  List<ChannelListColumn> columns = channelListColumns,
  bool letter = false,
}) {
  final width = letter ? _letterWidth : _pageWidth;
  final height = letter ? _letterHeight : _pageHeight;
  final usable = width - 2 * _margin;
  final totalWeight = columns.fold<double>(0, (sum, c) => sum + c.width);
  final columnWidths = [
    for (final c in columns) usable * c.width / totalWeight,
  ];
  const headerTop = 30.0; // title + subtitle block
  final rowsPerPage =
      ((height - 2 * _margin - headerTop - 2 * _rowHeight) / _rowHeight)
          .floor();
  final pageCount = rows.isEmpty ? 1 : (rows.length / rowsPerPage).ceil();

  String cellOps(
    String text,
    double x,
    double y,
    double cellWidth, {
    bool bold = false,
    bool right = false,
  }) {
    final fitted = _fit(text, cellWidth - (right ? 12 : 4), bold: bold);
    if (fitted.isEmpty) return '';
    final textX = right
        ? x + cellWidth - 10 - _textWidth(fitted, _fontSize, bold: bold)
        : x + 2;
    return 'BT /${bold ? 'F2' : 'F1'} $_fontSize Tf '
        '${textX.toStringAsFixed(2)} ${y.toStringAsFixed(2)} Td '
        '(${_pdfText(fitted)}) Tj ET\n';
  }

  final contents = <String>[];
  for (var page = 0; page < pageCount; page++) {
    final ops = StringBuffer();
    var y = height - _margin - 12;
    ops.write(
      'BT /F2 13 Tf ${_margin.toStringAsFixed(2)} '
      '${y.toStringAsFixed(2)} Td (${_pdfText(title)}) Tj ET\n',
    );
    y -= 13;
    ops.write(
      'BT /F1 8 Tf ${_margin.toStringAsFixed(2)} '
      '${y.toStringAsFixed(2)} Td (${_pdfText(subtitle)}) Tj ET\n',
    );
    y = height - _margin - headerTop - _rowHeight;

    // Header row with a rule underneath.
    var x = _margin;
    for (var i = 0; i < columns.length; i++) {
      ops.write(
        cellOps(
          columns[i].header,
          x,
          y + 3,
          columnWidths[i],
          bold: true,
          right: columns[i].alignRight,
        ),
      );
      x += columnWidths[i];
    }
    ops.write(
      '0.5 w ${_margin.toStringAsFixed(2)} '
      '${(y - 1).toStringAsFixed(2)} m '
      '${(width - _margin).toStringAsFixed(2)} '
      '${(y - 1).toStringAsFixed(2)} l S\n',
    );

    final start = page * rowsPerPage;
    final end = (start + rowsPerPage).clamp(0, rows.length);
    for (var r = start; r < end; r++) {
      y -= _rowHeight;
      if ((r - start).isOdd) {
        ops.write(
          '0.94 g ${_margin.toStringAsFixed(2)} '
          '${(y - 1).toStringAsFixed(2)} ${usable.toStringAsFixed(2)} '
          '${_rowHeight.toStringAsFixed(2)} re f 0 g\n',
        );
      }
      x = _margin;
      for (var i = 0; i < columns.length; i++) {
        final text = i < rows[r].length ? rows[r][i] : '';
        ops.write(
          cellOps(
            text,
            x,
            y + 2,
            columnWidths[i],
            right: columns[i].alignRight,
          ),
        );
        x += columnWidths[i];
      }
    }

    final footer = 'Page ${page + 1} of $pageCount';
    ops.write(
      'BT /F1 7 Tf '
      '${(width - _margin - _textWidth(footer, 7)).toStringAsFixed(2)} '
      '${(_margin - 14).toStringAsFixed(2)} Td (${_pdfText(footer)}) Tj ET\n',
    );
    if (rows.isEmpty && page == 0) {
      ops.write(cellOps('No channels.', _margin, y - _rowHeight, usable));
    }
    contents.add(ops.toString());
  }

  // Objects: 1 catalog, 2 pages, 3 F1, 4 F2, then a page + content pair each.
  final objects = <String>[];
  final pageIds = [for (var p = 0; p < pageCount; p++) 5 + 2 * p];
  objects.add('<< /Type /Catalog /Pages 2 0 R >>');
  objects.add(
    '<< /Type /Pages /Kids [${pageIds.map((id) => '$id 0 R').join(' ')}] '
    '/Count $pageCount >>',
  );
  objects.add(
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica '
    '/Encoding /WinAnsiEncoding >>',
  );
  objects.add(
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold '
    '/Encoding /WinAnsiEncoding >>',
  );
  for (var p = 0; p < pageCount; p++) {
    final contentId = pageIds[p] + 1;
    objects.add(
      '<< /Type /Page /Parent 2 0 R '
      '/MediaBox [0 0 ${width.toStringAsFixed(0)} ${height.toStringAsFixed(0)}] '
      '/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> '
      '/Contents $contentId 0 R >>',
    );
    final stream = latin1.encode(contents[p]);
    objects.add(
      '<< /Length ${stream.length} >>\nstream\n'
      '${latin1.decode(stream)}endstream',
    );
  }

  final out = BytesBuilder();
  void write(String text) => out.add(latin1.encode(text));
  write('%PDF-1.4\n%\xE2\xE3\xCF\xD3\n');
  final offsets = <int>[];
  for (var i = 0; i < objects.length; i++) {
    offsets.add(out.length);
    write('${i + 1} 0 obj\n${objects[i]}\nendobj\n');
  }
  final xref = out.length;
  write('xref\n0 ${objects.length + 1}\n0000000000 65535 f \n');
  for (final offset in offsets) {
    write('${offset.toString().padLeft(10, '0')} 00000 n \n');
  }
  write(
    'trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\n'
    'startxref\n$xref\n%%EOF\n',
  );
  return out.toBytes();
}
