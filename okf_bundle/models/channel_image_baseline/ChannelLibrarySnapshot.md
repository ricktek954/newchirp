---
okf_version: "0.2"
type: Function
title: channelLibrarySnapshot
description: Counts channels and compares with the radio image for one library refresh.
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: models/channel_image_baseline/channelLibrarySnapshot
language: dart
---

# channelLibrarySnapshot

Counts channels and compares with the radio image for one library refresh.

## Signature

```dart
ChannelLibrarySnapshotchannelLibrarySnapshot({
  required String? imagePath,
  required int? zone,
  required List<RadioChannel> channels,
  required Iterable<int> cleared,
  String mappingSignature = '',
  required ChannelImageBaseline? baseline,
  required int? memoryStart,
  required int? memoryEnd,
  int? maximumNameLength,
  required String? radioModel,
  List<double> validTuningSteps = const [],
  List<({double startMhz, double endMhz})> validBands = const [],
  List<String> validModes = const [],
  List<String> validToneModes = const [],
  List<String> validCrossModes = const [],
  bool hasTuningStep = true,
})
```

## Docstring

Counts channels and compares with the radio image for one library refresh.

## Source
Lines 191–208 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
