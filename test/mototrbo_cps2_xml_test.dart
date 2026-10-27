import 'dart:io';

import 'package:file_selector_platform_interface/file_selector_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/main.dart';
import 'package:newchirp/services/column_layout_store.dart';
import 'package:newchirp/services/file_save_warning_store.dart';
import 'package:newchirp/services/mototrbo_cps2_xml.dart';

void main() {
  test('imports analog and DMR channels from CPS2 Zone XML', () {
    final channels = MototrboCps2Xml.decode(_sampleXml);

    expect(channels, hasLength(3));

    final analog = channels[0];
    expect(analog.location, 1);
    expect(analog.name, 'FIRE DISP');
    expect(analog.frequency, 462.55);
    expect(analog.duplex, '+');
    expect(analog.offset, 5);
    expect(analog.tone, 'TSQL');
    expect(analog.txTone, 100);
    expect(analog.rxTone, 100);
    expect(analog.mode, 'NFM');
    expect(analog.power, 'High');
    expect(analog.skip, '');
    expect(analog.comment, contains('Zone: Operations'));
    expect(analog.comment, contains('Dispatch'));

    final digital = channels[1];
    expect(digital.location, 2);
    expect(digital.name, 'TG 9');
    expect(digital.frequency, 462.6125);
    expect(digital.duplex, '');
    expect(digital.mode, 'DMR');
    expect(digital.skip, 'S');
    final extras = {
      for (final extra in digital.extras) extra.name: extra.value,
    };
    expect(extras['cps2_color_code'], 7);
    expect(extras['cps2_timeslot'], '2');
    expect(extras['cps2_contact'], 'Dispatch Talkgroup');
    expect(extras['cps2_rx_group'], 'Dispatch RX');
    expect(extras['cps2_privacy_key'], isNull);

    final receiveOnly = channels[2];
    expect(receiveOnly.name, 'WEATHER');
    expect(receiveOnly.duplex, 'off');
    expect(receiveOnly.mode, 'FM');
    expect(receiveOnly.comment, contains('Zone: Weather'));
  });

  test('rejects XML without CPS2 conventional personalities', () {
    expect(
      () => MototrboCps2Xml.decode(
        '<config><category name="Contacts" /></config>',
      ),
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          contains('No conventional MOTOTRBO'),
        ),
      ),
    );
  });

  test('rejects malformed XML with a useful error', () {
    expect(
      () => MototrboCps2Xml.decode('<config>'),
      throwsA(
        isA<FormatException>().having(
          (error) => error.message,
          'message',
          contains('Could not read the MOTOTRBO XML'),
        ),
      ),
    );
  });

  testWidgets('opens CPS2 XML and preserves DMR fields in the editor', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final temp = Directory.systemTemp.createTempSync('newchirp-cps2-test-');
    addTearDown(() => temp.deleteSync(recursive: true));
    final source = File('${temp.path}/R7-zone.xml')
      ..writeAsStringSync(_sampleXml);
    final selector = _XmlOpenSelector(source.path);
    final previousSelector = FileSelectorPlatform.instance;
    FileSelectorPlatform.instance = selector;
    addTearDown(() => FileSelectorPlatform.instance = previousSelector);

    await tester.pumpWidget(
      NewChirpApp(
        columnLayoutStore: ColumnLayoutStore(path: '${temp.path}/layout.json'),
        fileSaveWarningStore: FileSaveWarningStore(
          path: '${temp.path}/file-save.json',
        ),
        checkForUpdatesOnStartup: false,
      ),
    );
    await tester.pumpAndSettle();

    await tester.runAsync(() async {
      await tester.tap(find.text('Open file').first);
      await Future<void>.delayed(const Duration(milliseconds: 100));
    });
    await tester.pumpAndSettle();

    expect(selector.calls, 1);
    expect(find.text('FIRE DISP'), findsOneWidget);
    expect(find.text('TG 9'), findsOneWidget);

    await tester.tap(find.text('TG 9'));
    await tester.pump(const Duration(milliseconds: 50));
    await tester.tap(find.text('TG 9'));
    await tester.pumpAndSettle();

    expect(find.text('Channel details'), findsOneWidget);
    expect(find.text('DMR (MOTOTRBO)'), findsOneWidget);
    expect(find.text('Color Code'), findsOneWidget);
  });
}

class _XmlOpenSelector extends FileSelectorPlatform {
  _XmlOpenSelector(this.path);

  final String path;
  int calls = 0;

  @override
  Future<XFile?> openFile({
    List<XTypeGroup>? acceptedTypeGroups,
    String? initialDirectory,
    String? confirmButtonText,
  }) async {
    calls += 1;
    return XFile(path);
  }
}

const _sampleXml = '''
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<config>
  <category name="Zone">
    <set name="Zone" alias="Operations" key="NORMAL">
      <collection name="ZoneItems">
        <set name="ConventionalPersonality" alias="FIRE DISP" key="ANLGCONV">
          <field name="CP_PERSTYPE" Name="Analog">ANLGCONV</field>
          <field name="CP_RXFREQ">462.550000</field>
          <field name="CP_TXFREQ">467.550000</field>
          <field name="CP_UTOSCANEN">True</field>
          <field name="CP_RXONLYEN">False</field>
          <field name="CP_XSQCHTY">TPL</field>
          <field name="CP_RXTPLFREQ">100.0</field>
          <field name="CP_TXSQCHTY">TPL</field>
          <field name="CP_TXTTPLFREQ">100.0</field>
          <field name="CP_CHNLBWDTH" Name="12.5">STR_12PT5KHZ</field>
          <field name="CP_TXPWR" Name="High">HIGHPWR</field>
          <field name="CP_SCNROAMLISTIT" Name="Operations">ScanItems/Operations</field>
          <field name="Comments">Dispatch</field>
        </set>
        <set name="ConventionalPersonality" alias="TG 9" key="DGTLCONV6PT25">
          <field name="CP_PERSTYPE" Name="Digital">DGTLCONV6PT25</field>
          <field name="CP_RXFREQ">462.612500</field>
          <field name="CP_TXFREQ">462.612500</field>
          <field name="CP_UTOSCANEN">False</field>
          <field name="CP_RXONLYEN">False</field>
          <field name="CP_COLORCODE">7</field>
          <field name="CP_SLTASSGMNT" Name="2">SLOT2</field>
          <field name="CP_UKPPERS" Name="Dispatch Talkgroup">TG9</field>
          <field name="CP_TGLISTIT" Name="Dispatch RX">TGLIST/Dispatch</field>
          <field name="CP_ENHCPRVCYIT" Name="None">NONE</field>
          <field name="CP_TXPWR" Name="Low">LOWPWR</field>
          <field name="CP_SCNROAMLISTIT" Name="None">NONE</field>
          <field name="Comments" />
        </set>
      </collection>
    </set>
  </category>
  <category name="Zone">
    <set name="Zone" alias="Weather" key="NORMAL">
      <collection name="ZoneItems">
        <set name="ConventionalPersonality" alias="WEATHER" key="ANLGCONV">
          <field name="CP_PERSTYPE" Name="Analog">ANLGCONV</field>
          <field name="CP_RXFREQ">162.550000</field>
          <field name="CP_TXFREQ">162.550000</field>
          <field name="CP_UTOSCANEN">True</field>
          <field name="CP_RXONLYEN">True</field>
          <field name="CP_XSQCHTY">CSQ</field>
          <field name="CP_TXSQCHTY">CSQ</field>
          <field name="CP_CHNLBWDTH" Name="25">STR_25KHZ</field>
          <field name="CP_TXPWR" Name="High">HIGHPWR</field>
          <field name="CP_SCNROAMLISTIT" Name="Weather">ScanItems/Weather</field>
          <field name="Comments" />
        </set>
      </collection>
    </set>
  </category>
</config>
''';
