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

  test('library stats stay cached until the channels change', () {
    final channels = [
      _channel(1, 'A'),
      RadioChannel(location: 2, name: 'B', frequency: 146.52, skip: 'S'),
    ];
    final cleared = <int>{};
    final baseline = ChannelImageBaseline(
      imagePath: '/tmp/radio.img',
      zone: 0,
      signature: channelListSignature(channels, cleared),
      loadedFromRadio: true,
    );
    final cache = ChannelLibraryStatsCache();

    ChannelLibrarySnapshot read({
      List<RadioChannel>? nextChannels,
      int? zone = 0,
      int? memoryEnd,
    }) {
      return cache.read(
        imagePath: '/tmp/radio.img',
        zone: zone,
        channels: nextChannels ?? channels,
        cleared: cleared,
        baseline: baseline,
        memoryStart: 1,
        memoryEnd: memoryEnd,
        radioModel: null,
      );
    }

    final first = read();
    expect(first.match, ChannelImageMatch.matchesRadio);
    expect(first.activeCount, 2);
    expect(first.scanEnabledCount, 1);
    expect(first.needsAttention, 0);
    expect(identical(first, read()), isTrue);

    channels[0].name = 'Edited';
    expect(identical(first, read()), isTrue);

    cache.markDirty();
    final edited = read();
    expect(identical(first, edited), isFalse);
    expect(edited.match, ChannelImageMatch.differs);
    expect(edited.needsAttention, 0);

    channels[0].frequency = 0;
    final invalid = read();
    expect(identical(edited, invalid), isTrue);
    cache.markDirty();
    expect(read().needsAttention, 1);

    final replaced = [_channel(1, 'A')];
    final afterReplace = read(nextChannels: replaced);
    expect(afterReplace.activeCount, 1);
    expect(afterReplace.match, ChannelImageMatch.differs);

    final otherZone = read(zone: 1);
    expect(otherZone.match, ChannelImageMatch.notLoaded);
    expect(identical(otherZone, read(zone: 1)), isTrue);

    final bounded = read(memoryEnd: 0);
    expect(bounded.needsAttention, 2);
    expect(identical(bounded, read(memoryEnd: 0)), isTrue);
  });

  test('library stats refresh when tuning-step capabilities change', () {
    final channels = [_channel(1, 'A')..frequency = 462.1245];
    final cache = ChannelLibraryStatsCache();

    ChannelLibrarySnapshot read(List<double> steps) => cache.read(
      imagePath: null,
      zone: null,
      channels: channels,
      cleared: const <int>[],
      baseline: null,
      memoryStart: 1,
      memoryEnd: 128,
      radioModel: 'Baofeng_UV-5R',
      validTuningSteps: steps,
    );

    final unknownSteps = read(const []);
    expect(unknownSteps.needsAttention, 0);

    final uv5rSteps = read(const [2.5, 5.0, 6.25, 10.0, 12.5, 25.0]);
    expect(uv5rSteps.needsAttention, 1);
    expect(identical(unknownSteps, uv5rSteps), isFalse);
  });

  test('library stats refresh when supported bands change', () {
    final channels = [_channel(4, '900')..frequency = 927.525];
    final cache = ChannelLibraryStatsCache();

    ChannelLibrarySnapshot read(
      List<({double startMhz, double endMhz})> bands,
    ) => cache.read(
      imagePath: null,
      zone: null,
      channels: channels,
      cleared: const <int>[],
      baseline: null,
      memoryStart: 1,
      memoryEnd: 199,
      radioModel: 'Baofeng_5RM',
      validBands: bands,
    );

    final unknownBands = read(const []);
    expect(unknownBands.needsAttention, 0);

    final fiveRmBands = read(const [
      (startMhz: 108.0, endMhz: 136.0),
      (startMhz: 400.0, endMhz: 520.0),
    ]);
    expect(fiveRmBands.needsAttention, 1);
    expect(identical(unknownBands, fiveRmBands), isFalse);
  });

  test('library stats refresh when supported modes change', () {
    final channels = [_channel(1, 'FUSION')..mode = 'DN'];
    final cache = ChannelLibraryStatsCache();

    ChannelLibrarySnapshot read(List<String> modes) => cache.read(
      imagePath: null,
      zone: null,
      channels: channels,
      cleared: const <int>[],
      baseline: null,
      memoryStart: 1,
      memoryEnd: 199,
      radioModel: 'Baofeng_UV-5R_Mini',
      validModes: modes,
    );

    final unknownModes = read(const []);
    expect(unknownModes.needsAttention, 0);

    final analogOnly = read(const ['FM', 'NFM']);
    expect(analogOnly.needsAttention, 1);
    expect(identical(unknownModes, analogOnly), isFalse);
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
