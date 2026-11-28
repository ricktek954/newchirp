---
okf_version: "0.2"
type: Function
title: read
description: "The cached snapshot, recomputed only when an input changed or [markDirty] was called."
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: models/channel_image_baseline/read
language: dart
---

# read

The cached snapshot, recomputed only when an input changed or [markDirty] was called.

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

The cached snapshot, recomputed only when an input changed or [markDirty] was called.

## Source
Lines 280–297 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
