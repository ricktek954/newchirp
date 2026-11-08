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

  static List<RadioChannel> decode(String source) {
    final rows = _parse(source);
    if (rows.isEmpty) return [];
    final names = rows.first.map((e) => e.trim()).toList();
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

  static List<List<String>> _parse(String source) {
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
      } else if (char == ',' && !quoted) {
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
