import 'dart:convert';

import 'radio_channel.dart';

/// Fingerprint of the channel list last read from, imported from, or written
/// to the stored radio image.
///
/// Screen edits are compared with this so Discard and Write follow the radio
/// image, not whether a CSV file was saved.
class ChannelImageBaseline {
  const ChannelImageBaseline({
    required this.imagePath,
    required this.zone,
    required this.signature,
    required this.loadedFromRadio,
  });

  final String imagePath;
  final int? zone;
  final String signature;
  final bool loadedFromRadio;
}

enum ChannelImageMatch {
  noImage,
  notLoaded,
  matchesRadio,
  matchesImage,
  differs,
}

String channelListSignature(
  List<RadioChannel> channels,
  Iterable<int> cleared,
) {
  final encoded = [...channels]
    ..sort((left, right) => left.location.compareTo(right.location));
  final clearedLocations = cleared.toList()..sort();
  return jsonEncode({
    'channels': encoded.map((channel) => channel.toJson()).toList(),
    'cleared': clearedLocations,
  });
}

ChannelImageMatch channelImageMatch({
  required String? imagePath,
  required int? zone,
  required List<RadioChannel> channels,
  required Iterable<int> cleared,
  required ChannelImageBaseline? baseline,
}) {
  if (imagePath == null) return ChannelImageMatch.noImage;
  if (baseline == null || baseline.imagePath != imagePath) {
    return ChannelImageMatch.notLoaded;
  }
  // Replacing the library clears the selected zone. Keep comparing against
  // the zone that was loaded until the user chooses a different one.
  if (zone != null && zone != baseline.zone) {
    return ChannelImageMatch.notLoaded;
  }
  final current = channelListSignature(channels, cleared);
  if (current != baseline.signature) return ChannelImageMatch.differs;
  return baseline.loadedFromRadio
      ? ChannelImageMatch.matchesRadio
      : ChannelImageMatch.matchesImage;
}

String channelImageStatusText(ChannelImageMatch match) => switch (match) {
  ChannelImageMatch.noImage =>
    'No stored radio image. Read the radio before writing channels.',
  ChannelImageMatch.notLoaded =>
    'Channel list has not been loaded from the stored radio image.',
  ChannelImageMatch.matchesRadio =>
    'Channels match the values last read from the radio.',
  ChannelImageMatch.matchesImage => 'Channels match the stored radio image.',
  ChannelImageMatch.differs => 'Unsaved channel changes',
};

/// Channel counts and the radio-image match for one library refresh.
class ChannelLibrarySnapshot {
  const ChannelLibrarySnapshot({
    required this.match,
    required this.needsAttention,
    required this.activeCount,
    required this.scanEnabledCount,
  });

  static const empty = ChannelLibrarySnapshot(
    match: ChannelImageMatch.noImage,
    needsAttention: 0,
    activeCount: 0,
    scanEnabledCount: 0,
  );

  final ChannelImageMatch match;
  final int needsAttention;
  final int activeCount;
  final int scanEnabledCount;
}

ChannelLibrarySnapshot channelLibrarySnapshot({
  required String? imagePath,
  required int? zone,
  required List<RadioChannel> channels,
  required Iterable<int> cleared,
  required ChannelImageBaseline? baseline,
  required int? memoryStart,
  required int? memoryEnd,
  required String? radioModel,
}) {
  var activeCount = 0;
  var scanEnabledCount = 0;
  var needsAttention = 0;
  for (final channel in channels) {
    if (channel.cleared) continue;
    activeCount++;
    if (channel.skip.isEmpty) scanEnabledCount++;
    if (channel
        .validate(
          minimumLocation: memoryStart,
          maximumLocation: memoryEnd,
          radioModel: radioModel,
        )
        .isNotEmpty) {
      needsAttention++;
    }
  }
  return ChannelLibrarySnapshot(
    match: channelImageMatch(
      imagePath: imagePath,
      zone: zone,
      channels: channels,
      cleared: cleared,
      baseline: baseline,
    ),
    needsAttention: needsAttention,
    activeCount: activeCount,
    scanEnabledCount: scanEnabledCount,
  );
}

/// Remembers the last library snapshot so search and row selection can skip it.
///
/// Call [markDirty] after an in-place channel edit.
/// [read] also refreshes when the image, zone, baseline, radio, memory
/// limits, channel list, or cleared-slot count changes.
class ChannelLibraryStatsCache {
  var _dirty = true;
  ChannelLibrarySnapshot _snapshot = ChannelLibrarySnapshot.empty;
  List<RadioChannel>? _channels;
  int _channelCount = -1;
  Iterable<int>? _cleared;
  int _clearedCount = -1;
  String? _imagePath;
  int? _zone;
  ChannelImageBaseline? _baseline;
  int? _memoryStart;
  int? _memoryEnd;
  String? _radioModel;

  void markDirty() {
    _dirty = true;
  }

  ChannelLibrarySnapshot read({
    required String? imagePath,
    required int? zone,
    required List<RadioChannel> channels,
    required Iterable<int> cleared,
    required ChannelImageBaseline? baseline,
    required int? memoryStart,
    required int? memoryEnd,
    required String? radioModel,
  }) {
    final sameInputs =
        !_dirty &&
        identical(channels, _channels) &&
        channels.length == _channelCount &&
        identical(cleared, _cleared) &&
        cleared.length == _clearedCount &&
        imagePath == _imagePath &&
        zone == _zone &&
        identical(baseline, _baseline) &&
        memoryStart == _memoryStart &&
        memoryEnd == _memoryEnd &&
        radioModel == _radioModel;
    if (sameInputs) return _snapshot;

    final snapshot = channelLibrarySnapshot(
      imagePath: imagePath,
      zone: zone,
      channels: channels,
      cleared: cleared,
      baseline: baseline,
      memoryStart: memoryStart,
      memoryEnd: memoryEnd,
      radioModel: radioModel,
    );
    _dirty = false;
    _channels = channels;
    _channelCount = channels.length;
    _cleared = cleared;
    _clearedCount = cleared.length;
    _imagePath = imagePath;
    _zone = zone;
    _baseline = baseline;
    _memoryStart = memoryStart;
    _memoryEnd = memoryEnd;
    _radioModel = radioModel;
    _snapshot = snapshot;
    return snapshot;
  }
}
