import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/models/channel_image_baseline.dart';
import 'package:newchirp/models/radio_channel.dart';
import 'package:newchirp/widgets/channel_library_image_bar.dart';

RadioChannel _channel(int location, String name) =>
    RadioChannel(location: location, name: name, frequency: 146.52);

void main() {
  test('channel signatures ignore row order and notice edits', () {
    final first = [_channel(2, 'B'), _channel(1, 'A')];
    final second = [_channel(1, 'A'), _channel(2, 'B')];
    expect(
      channelListSignature(first, const []),
      channelListSignature(second, const []),
    );

    final renamed = [_channel(1, 'A'), _channel(2, 'C')];
    expect(
      channelListSignature(renamed, const []),
      isNot(channelListSignature(second, const [])),
    );
    expect(
      channelListSignature(second, const [4]),
      isNot(channelListSignature(second, const [])),
    );
  });

  test('match follows the stored image baseline', () {
    final channels = [_channel(1, 'A')];
    final baseline = ChannelImageBaseline(
      imagePath: '/tmp/radio.img',
      zone: 0,
      signature: channelListSignature(channels, const []),
      loadedFromRadio: true,
    );

    expect(
      channelImageMatch(
        imagePath: null,
        zone: 0,
        channels: channels,
        cleared: const [],
        baseline: baseline,
      ),
      ChannelImageMatch.noImage,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/radio.img',
        zone: 0,
        channels: channels,
        cleared: const [],
        baseline: null,
      ),
      ChannelImageMatch.notLoaded,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/other.img',
        zone: 0,
        channels: channels,
        cleared: const [],
        baseline: baseline,
      ),
      ChannelImageMatch.notLoaded,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/radio.img',
        zone: 0,
        channels: channels,
        cleared: const [],
        baseline: baseline,
      ),
      ChannelImageMatch.matchesRadio,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/radio.img',
        zone: 0,
        channels: [_channel(1, 'Edited')],
        cleared: const [],
        baseline: baseline,
      ),
      ChannelImageMatch.differs,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/radio.img',
        zone: 0,
        channels: channels,
        cleared: const [],
        baseline: ChannelImageBaseline(
          imagePath: baseline.imagePath,
          zone: baseline.zone,
          signature: baseline.signature,
          loadedFromRadio: false,
        ),
      ),
      ChannelImageMatch.matchesImage,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/radio.img',
        zone: null,
        channels: [_channel(1, 'Edited')],
        cleared: const [],
        baseline: baseline,
      ),
      ChannelImageMatch.differs,
    );
    expect(
      channelImageMatch(
        imagePath: '/tmp/radio.img',
        zone: 1,
        channels: channels,
        cleared: const [],
        baseline: baseline,
      ),
      ChannelImageMatch.notLoaded,
    );
  });

  testWidgets('channel image bar enables actions only when channels differ', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ChannelLibraryImageBar(
            match: ChannelImageMatch.matchesImage,
            canDiscard: false,
            canWrite: false,
            showConnect: false,
            onDiscard: () {},
            onWrite: () {},
            onConnect: () {},
          ),
        ),
      ),
    );

    expect(find.text('Channels match the stored radio image.'), findsOneWidget);
    expect(
      tester
          .widget<TextButton>(find.byKey(const Key('channel-library-discard')))
          .onPressed,
      isNull,
    );
    expect(
      tester
          .widget<FilledButton>(find.byKey(const Key('channel-library-write')))
          .onPressed,
      isNull,
    );

    var discarded = false;
    var wrote = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ChannelLibraryImageBar(
            match: ChannelImageMatch.differs,
            canDiscard: true,
            canWrite: true,
            showConnect: false,
            onDiscard: () => discarded = true,
            onWrite: () => wrote = true,
            onConnect: () {},
          ),
        ),
      ),
    );
    expect(find.text('Unsaved channel changes'), findsOneWidget);
    await tester.tap(find.text('Discard changes'));
    await tester.tap(find.text('Write settings to radio'));
    expect(discarded, isTrue);
    expect(wrote, isTrue);
  });
}
