---
okf_version: "0.2"
type: Function
title: read
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:fix/repeater-compatibility"
  - "git:repo:newchirp"
timestamp: "2026-11-03T20:22:07Z"
concept_id: models/channel_image_baseline/read
language: dart
---

# read

## Signature

```dart
ChannelLibrarySnapshotread({
    required String? imagePath,
    required int? zone,
    required List<RadioChannel> channels,
    required Iterable<int> cleared,
    String mappingSignature = '',
    required ChannelImageBaseline? baseline,
    required int? memoryStart,
    required int? memoryEnd,
    required String? radioModel,
    List<double> validTuningSteps = const [],
    List<({double startMhz, double endMhz})> validBands = const [],
    List<String> validModes = const [],
    List<String> validToneModes = const [],
    List<String> validCrossModes = const [],
    bool hasTuningStep = true,
    int maxNameLength = 16,
  })
```

## Source
Lines 220–237 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
