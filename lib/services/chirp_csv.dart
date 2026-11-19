import 'dart:convert';

import '../models/radio_channel.dart';

class ChirpCsv {
  static const headers = [
    'Location',
    'Name',
    'Frequency',
    'Duplex',
    'Offset',
    'Tone',
    'rToneFreq',
    'cToneFreq',
    'DtcsCode',
    'DtcsPolarity',
    'RxDtcsCode',
    'CrossMode',
    'Mode',
    'TStep',
    'Skip',
    'Power',
    'Comment',
    'URCALL',
    'RPT1CALL',
    'RPT2CALL',
    'DVCODE',
  ];

  static String encode(List<RadioChannel> channels) {
    final rows = <List<Object?>>[
      headers,
      ...channels.map(
        (c) => [
          c.location,
          c.name,
          c.frequency.toStringAsFixed(6),
          c.duplex,
          c.offset.toStringAsFixed(6),
          c.tone,
          c.txTone.toStringAsFixed(1),
          c.rxTone.toStringAsFixed(1),
          c.dtcs.toString().padLeft(3, '0'),
          c.dtcsPolarity,
          c.rxDtcs.toString().padLeft(3, '0'),
          c.crossMode,
          c.mode,
          c.step,
          c.skip,
          c.power,
          c.comment,
          '',
          '',
          '',
          '',
        ],
      ),
    ];
    return rows.map((row) => row.map(_escape).join(',')).join('\r\n');
  }

  /// Decodes a CSV file's bytes, accepting the encodings spreadsheet and
  /// OEM programs write: UTF-8 (with or without BOM), UTF-16 LE/BE with BOM,
  /// and Windows-1252.
  static List<RadioChannel> decodeBytes(List<int> bytes) =>
      decode(decodeText(bytes));

  static String decodeText(List<int> bytes) {
    if (bytes.length >= 2 && bytes[0] == 0xFF && bytes[1] == 0xFE) {
      return _utf16(bytes.sublist(2), littleEndian: true);
    }
    if (bytes.length >= 2 && bytes[0] == 0xFE && bytes[1] == 0xFF) {
      return _utf16(bytes.sublist(2), littleEndian: false);
    }
    if (bytes.length >= 3 &&
        bytes[0] == 0xEF &&
        bytes[1] == 0xBB &&
        bytes[2] == 0xBF) {
      return utf8.decode(bytes.sublist(3), allowMalformed: true);
    }
    try {
      return utf8.decode(bytes);
    } on FormatException {
      return _windows1252(bytes);
    }
  }

  static String _utf16(List<int> bytes, {required bool littleEndian}) {
    final units = <int>[];
    for (var i = 0; i + 1 < bytes.length; i += 2) {
      units.add(
        littleEndian
            ? bytes[i] | (bytes[i + 1] << 8)
            : (bytes[i] << 8) | bytes[i + 1],
      );
    }
    return String.fromCharCodes(units);
  }

  // Windows-1252 differs from Latin-1 only in 0x80-0x9F.
  static const _cp1252High = [
    0x20AC, 0x81, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, //
    0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x8D, 0x017D, 0x8F, //
    0x90, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, //
    0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x9D, 0x017E, 0x0178, //
  ];

  static String _windows1252(List<int> bytes) => String.fromCharCodes(
    bytes.map((b) => b >= 0x80 && b <= 0x9F ? _cp1252High[b - 0x80] : b),
  );

  static List<RadioChannel> decode(String source) {
    if (source.startsWith('\uFEFF')) source = source.substring(1);
    final rows = _parse(source, _delimiter(source));
    if (rows.isEmpty) return [];
    final names = rows.first.map((e) => e.trim()).toList();
    if (!names.contains('Frequency')) {
      final found = names.where((n) => n.isNotEmpty).take(8).join(', ');
      throw FormatException(
        'This CSV is not in CHIRP format: it has no "Frequency" column'
        '${found.isEmpty ? '' : ' (columns found: $found)'}. Export the '
        'channels as a CHIRP or NewChirp CSV, or send the file with a bug '
        'report so its format can be supported.',
      );
    }
    int col(String name) => names.indexOf(name);
    String value(List<String> row, String name, [String fallback = '']) {
      final index = col(name);
      return index >= 0 && index < row.length ? row[index].trim() : fallback;
    }

    double number(List<String> row, String name, double fallback) =>
        double.tryParse(value(row, name)) ?? fallback;
    int integer(List<String> row, String name, int fallback) =>
        int.tryParse(value(row, name)) ?? fallback;
    String dtcsPolarity(List<String> row) {
      final polarity = value(row, 'DtcsPolarity', 'NN').toUpperCase();
      return polarity.isEmpty ? 'NN' : polarity;
    }

    return rows.skip(1).where((r) => r.any((v) => v.trim().isNotEmpty)).map((
      r,
    ) {
      return RadioChannel(
        location: integer(r, 'Location', 0),
        name: value(r, 'Name'),
        frequency: number(r, 'Frequency', 0),
        duplex: value(r, 'Duplex'),
        offset: number(r, 'Offset', 0),
        tone: value(r, 'Tone'),
        txTone: number(r, 'rToneFreq', 88.5),
        rxTone: number(r, 'cToneFreq', 88.5),
        dtcs: integer(r, 'DtcsCode', 23),
        dtcsPolarity: dtcsPolarity(r),
        rxDtcs: integer(r, 'RxDtcsCode', 23),
        crossMode: value(r, 'CrossMode', 'Tone->Tone'),
        mode: value(r, 'Mode', 'FM'),
        step: number(r, 'TStep', 5),
        skip: value(r, 'Skip'),
        power: value(r, 'Power'),
        comment: value(r, 'Comment'),
      );
    }).toList();
  }

  static String _escape(Object? value) {
    final text = value?.toString() ?? '';
    if (!text.contains(RegExp('[,"\r\n]'))) return text;
    return '"${text.replaceAll('"', '""')}"';
  }

  /// CHIRP writes commas; some spreadsheet locales save with semicolons
  /// or tabs. Pick the separator the header line uses.
  static String _delimiter(String source) {
    final end = source.indexOf(RegExp('[\r\n]'));
    final header = end < 0 ? source : source.substring(0, end);
    if (header.contains(',')) return ',';
    if (header.contains(';')) return ';';
    if (header.contains('\t')) return '\t';
    return ',';
  }

  static List<List<String>> _parse(String source, [String delimiter = ',']) {
    final rows = <List<String>>[];
    var row = <String>[];
    var field = StringBuffer();
    var quoted = false;
    for (var i = 0; i < source.length; i++) {
      final char = source[i];
      if (char == '"') {
        if (quoted && i + 1 < source.length && source[i + 1] == '"') {
          field.write('"');
          i++;
        } else {
          quoted = !quoted;
        }
      } else if (char == delimiter && !quoted) {
        row.add(field.toString());
        field = StringBuffer();
      } else if ((char == '\n' || char == '\r') && !quoted) {
        if (char == '\r' && i + 1 < source.length && source[i + 1] == '\n') i++;
        row.add(field.toString());
        rows.add(row);
        row = <String>[];
        field = StringBuffer();
      } else {
        field.write(char);
      }
    }
    if (field.isNotEmpty || row.isNotEmpty) {
      row.add(field.toString());
      rows.add(row);
    }
    return rows;
  }
}
