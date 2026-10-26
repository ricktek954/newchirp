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
