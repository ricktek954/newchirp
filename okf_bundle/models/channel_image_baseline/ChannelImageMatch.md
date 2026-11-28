---
okf_version: "0.2"
type: Function
title: channelImageMatch
description: "How the on-screen channel list relates to the stored radio image: no image,"
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: models/channel_image_baseline/channelImageMatch
language: dart
---

# channelImageMatch

How the on-screen channel list relates to the stored radio image: no image,

## Signature

```dart
ChannelImageMatchchannelImageMatch({
  required String? imagePath,
  required int? zone,
  required List<RadioChannel> channels,
  required Iterable<int> cleared,
  String mappingSignature = '',
  required ChannelImageBaseline? baseline,
})
```

## Docstring

How the on-screen channel list relates to the stored radio image: no image,
not loaded this session, identical to it, or edited since.

## Source
Lines 99–106 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
