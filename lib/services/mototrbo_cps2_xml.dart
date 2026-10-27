import 'package:xml/xml.dart';

import '../models/radio_channel.dart';

/// Read-only importer for conventional channels copied from MOTOTRBO CPS 2.0.
///
/// CPS2 exposes Zone XML through its copy operation. The XML contains one
/// `ConventionalPersonality` entry per channel and also carries DMR fields
/// such as color code, timeslot, contact, RX group list, and privacy key.
class MototrboCps2Xml {
  static List<RadioChannel> decode(String source) {
    if (source.trim().isEmpty) {
      throw const FormatException('The MOTOTRBO XML file is empty.');
    }

    late final XmlDocument document;
    try {
      document = XmlDocument.parse(source);
    } on XmlException catch (error) {
      throw FormatException('Could not read the MOTOTRBO XML: $error');
    }

    final channels = <RadioChannel>[];
    final zones = document.descendantElements.where(
      (element) =>
          element.name.local == 'set' && element.getAttribute('name') == 'Zone',
    );

    for (final zone in zones) {
      final zoneName = zone.getAttribute('alias')?.trim() ?? '';
      final collection = _child(zone, 'collection', name: 'ZoneItems');
      if (collection == null) continue;

      for (final personality in collection.childElements.where(
        (element) => element.name.local == 'set',
      )) {
        final fields = _fields(personality);
        if (!fields.containsKey('CP_PERSTYPE')) continue;

        final receiveMhz = _number(fields['CP_RXFREQ']);
        final transmitMhz = _number(fields['CP_TXFREQ']);
        if (receiveMhz <= 0 && transmitMhz <= 0) continue;

        final channel = _channel(
          personality,
          fields,
          location: channels.length + 1,
          zoneName: zoneName,
        );
        if (channel != null) channels.add(channel);
      }
    }

    if (channels.isEmpty) {
      throw const FormatException(
        'No conventional MOTOTRBO CPS 2.0 channels were found. In CPS2, '
        'select a Zone, copy it, and save or paste the XML into a file.',
      );
    }
    return channels;
  }

  static RadioChannel? _channel(
    XmlElement personality,
    Map<String, XmlElement> fields, {
    required int location,
    required String zoneName,
  }) {
    final receiveMhz = _number(fields['CP_RXFREQ']);
    final transmitMhz = _number(fields['CP_TXFREQ']);
    final type = fields['CP_PERSTYPE'];
    final typeValue = _text(type).toUpperCase();
    final typeName = type?.getAttribute('Name')?.toUpperCase() ?? '';
    final digital =
        typeValue.startsWith('DGTLCONV') ||
        typeName == 'DIGITAL' ||
        fields.containsKey('CP_COLORCODE');

    var name = personality.getAttribute('alias')?.trim() ?? '';
    if (name.isEmpty) {
      name = _text(fields['CP_CNVPERSALIAS']).trim();
    }
    if (name.isEmpty) name = 'Channel $location';

    String duplex;
    double offset;
    final receiveOnly = _boolean(fields['CP_RXONLYEN']);
    if (receiveOnly || transmitMhz <= 0) {
      duplex = 'off';
      offset = 0;
    } else {
      final difference = transmitMhz - receiveMhz;
      if (difference.abs() < 0.0000005) {
        duplex = '';
        offset = 0;
      } else if (difference.abs() <= 100) {
        duplex = difference > 0 ? '+' : '-';
        offset = difference.abs();
      } else {
        duplex = 'split';
        offset = transmitMhz;
      }
    }

    final bandwidth = _text(fields['CP_CHNLBWDTH']).toUpperCase();
    final mode = digital
        ? 'DMR'
        : bandwidth.contains('12PT5')
        ? 'NFM'
        : 'FM';
    final scanList = _value(fields['CP_SCNROAMLISTIT']).toUpperCase();
    final autoScan = _boolean(fields['CP_UTOSCANEN']);
    final powerValue = _value(fields['CP_TXPWR']).toUpperCase();
    final power = powerValue == 'HIGHPWR'
        ? 'High'
        : powerValue == 'LOWPWR'
        ? 'Low'
        : _display(fields['CP_TXPWR']);

    final commentParts = <String>[
      'MOTOTRBO CPS 2.0',
      if (zoneName.isNotEmpty) 'Zone: $zoneName',
      digital ? 'Digital' : 'Analog',
    ];
    final cpsComment = _text(fields['Comments']).trim();
    if (cpsComment.isNotEmpty) commentParts.add(cpsComment);

    final extras = <ChannelExtraField>[];
    if (digital) {
      _addExtra(
        extras,
        'cps2_color_code',
        'Color Code',
        _text(fields['CP_COLORCODE']).trim(),
        kind: 'integer',
        documentation: 'MOTOTRBO DMR color code from the CPS 2.0 channel.',
      );
      final timeslot = _value(fields['CP_SLTASSGMNT']).toUpperCase();
      _addExtra(
        extras,
        'cps2_timeslot',
        'Timeslot',
        timeslot == 'SLOT1'
            ? '1'
            : timeslot == 'SLOT2'
            ? '2'
            : _display(fields['CP_SLTASSGMNT']),
        documentation: 'MOTOTRBO DMR timeslot from the CPS 2.0 channel.',
      );
      _addExtra(
        extras,
        'cps2_contact',
        'Contact',
        _display(fields['CP_UKPPERS']),
        documentation: 'CPS 2.0 digital contact reference.',
      );
      _addExtra(
        extras,
        'cps2_rx_group',
        'RX Group List',
        _display(fields['CP_TGLISTIT']),
        documentation: 'CPS 2.0 digital RX group list reference.',
      );
      _addExtra(
        extras,
        'cps2_privacy_key',
        'Privacy Key',
        _display(fields['CP_ENHCPRVCYIT']),
        documentation: 'CPS 2.0 privacy key reference.',
      );
    }

    final channel = RadioChannel(
      location: location,
      name: name,
      frequency: receiveMhz,
      duplex: duplex,
      offset: offset,
      mode: mode,
      step: digital ? 12.5 : 5,
      skip: !autoScan || scanList.isEmpty || scanList == 'NONE' ? 'S' : '',
      power: power,
      comment: commentParts.join(' · '),
      extras: extras,
    );
    if (!digital) _applyAnalogTones(channel, fields);
    return channel;
  }

  static void _applyAnalogTones(
    RadioChannel channel,
    Map<String, XmlElement> fields,
  ) {
    final transmit = _tone(
      fields['CP_TXSQCHTY'],
      fields['CP_TXTTPLFREQ'],
      fields['CP_TXTDPLCD'],
      fields['CP_TXDPLINV'],
    );
    final receive = _tone(
      fields['CP_XSQCHTY'],
      fields['CP_RXTPLFREQ'],
      fields['CP_RXDPLCD'],
      fields['CP_RXDPLINV'],
    );

    channel.txTone = transmit.value ?? 88.5;
    channel.rxTone = receive.value ?? 88.5;
    if (transmit.code != null) channel.dtcs = transmit.code!;
    if (receive.code != null) channel.rxDtcs = receive.code!;
    channel.dtcsPolarity =
        '${transmit.inverted ? 'R' : 'N'}'
        '${receive.inverted ? 'R' : 'N'}';

    if (transmit.kind == _ToneKind.none && receive.kind == _ToneKind.none) {
      channel.tone = '';
      return;
    }
    if (transmit.kind == _ToneKind.tone && receive.kind == _ToneKind.none) {
      channel.tone = 'Tone';
      return;
    }
    if (transmit.kind == _ToneKind.none && receive.kind == _ToneKind.tone) {
      channel.tone = 'Cross';
      channel.crossMode = '->Tone';
      return;
    }
    if (transmit.kind == _ToneKind.tone &&
        receive.kind == _ToneKind.tone &&
        transmit.value == receive.value) {
      channel.tone = 'TSQL';
      return;
    }
    if (transmit.kind == _ToneKind.dtcs &&
        receive.kind == _ToneKind.dtcs &&
        transmit.code == receive.code &&
        transmit.inverted == receive.inverted) {
      channel.tone = 'DTCS';
      return;
    }
    if (transmit.kind == _ToneKind.dtcs && receive.kind == _ToneKind.none) {
      channel.tone = 'DTCS';
      return;
    }

    channel.tone = 'Cross';
    channel.crossMode = switch ((transmit.kind, receive.kind)) {
      (_ToneKind.tone, _ToneKind.tone) => 'Tone->Tone',
      (_ToneKind.dtcs, _ToneKind.none) => 'DTCS->',
      (_ToneKind.none, _ToneKind.dtcs) => '->DTCS',
      (_ToneKind.tone, _ToneKind.dtcs) => 'Tone->DTCS',
      (_ToneKind.dtcs, _ToneKind.tone) => 'DTCS->Tone',
      (_ToneKind.dtcs, _ToneKind.dtcs) => 'DTCS->DTCS',
      (_, _) => 'Tone->',
    };
  }

  static _CpsTone _tone(
    XmlElement? typeElement,
    XmlElement? toneElement,
    XmlElement? codeElement,
    XmlElement? invertedElement,
  ) {
    final type = _value(typeElement).toUpperCase();
    if (type == 'TPL') {
      return _CpsTone(_ToneKind.tone, value: _numberOrNull(toneElement));
    }
    if (type == 'DPL') {
      final codeText = _text(codeElement).replaceFirst(RegExp(r'^0+'), '');
      return _CpsTone(
        _ToneKind.dtcs,
        code: int.tryParse(codeText),
        inverted: _boolean(invertedElement),
      );
    }
    return const _CpsTone(_ToneKind.none);
  }

  static XmlElement? _child(
    XmlElement parent,
    String localName, {
    String? name,
  }) {
    for (final child in parent.childElements) {
      if (child.name.local != localName) continue;
      if (name == null || child.getAttribute('name') == name) return child;
    }
    return null;
  }

  static Map<String, XmlElement> _fields(XmlElement personality) {
    final fields = <String, XmlElement>{};
    for (final child in personality.childElements) {
      if (child.name.local != 'field') continue;
      final name = child.getAttribute('name');
      if (name != null && name.isNotEmpty) fields[name] = child;
    }
    return fields;
  }

  static String _text(XmlElement? element) => element?.innerText ?? '';

  static String _value(XmlElement? element) => _text(element).trim();

  static String _display(XmlElement? element) {
    if (element == null) return '';
    final display = element.getAttribute('Name')?.trim();
    if (display != null &&
        display.isNotEmpty &&
        display.toUpperCase() != 'NONE') {
      return display;
    }
    final value = _value(element);
    return value.toUpperCase() == 'NONE' ? '' : value;
  }

  static double _number(XmlElement? element, {double? fallback = 0}) {
    return double.tryParse(_value(element)) ?? fallback ?? 0;
  }

  static double? _numberOrNull(XmlElement? element) =>
      double.tryParse(_value(element));

  static bool _boolean(XmlElement? element) {
    return const {
      'TRUE',
      'ON',
      '1',
      'YES',
    }.contains(_value(element).toUpperCase());
  }

  static void _addExtra(
    List<ChannelExtraField> extras,
    String name,
    String label,
    String value, {
    String kind = 'string',
    String? documentation,
  }) {
    if (value.isEmpty) return;
    extras.add(
      ChannelExtraField(
        name: name,
        label: label,
        kind: kind,
        value: kind == 'integer' ? int.tryParse(value) ?? value : value,
        documentation: documentation,
      ),
    );
  }
}

enum _ToneKind { none, tone, dtcs }

class _CpsTone {
  const _CpsTone(this.kind, {this.value, this.code, this.inverted = false});

  final _ToneKind kind;
  final double? value;
  final int? code;
  final bool inverted;
}
