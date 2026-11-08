import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/services/chirp_csv.dart';

void main() {
  test('CHIRP CSV round trips values and quoted comments', () {
    final source = RadioChannel(
      location: 12,
      name: 'LOCAL',
      frequency: 146.52,
      duplex: '-',
      offset: 0.6,
      tone: 'Tone',
      txTone: 100,
      comment: 'Club, primary "calling" channel',
    );

    final decoded = ChirpCsv.decode(ChirpCsv.encode([source]));

    expect(decoded, hasLength(1));
    expect(decoded.single.location, 12);
    expect(decoded.single.frequency, 146.52);
    expect(decoded.single.duplex, '-');
    expect(decoded.single.comment, source.comment);
  });

  test('blank DTCS polarity from OpenGD77 imports as NN', () {
    const source = '''
Location,Name,Frequency,Duplex,Offset,Tone,rToneFreq,cToneFreq,DtcsCode,DtcsPolarity,RxDtcsCode,CrossMode,Mode,TStep,Skip,Power,Comment,URCALL,RPT1CALL,RPT2CALL,DVCODE
1,RX ONLY,146.520000,,,,88.5,88.5,023,,023,Tone->Tone,FM,5.0,,,Imported,,,,
''';

    final decoded = ChirpCsv.decode(source);

    expect(decoded, hasLength(1));
    expect(decoded.single.dtcsPolarity, 'NN');
  });

  test('GMRS starter library contains all 22 channels', () {
    final channels = gmrsStarterChannels();
    expect(channels, hasLength(22));
    expect(channels.first.frequency, 462.5625);
    expect(channels.last.duplex, '+');
    expect(channels.last.offset, 5.0);
  });
}
