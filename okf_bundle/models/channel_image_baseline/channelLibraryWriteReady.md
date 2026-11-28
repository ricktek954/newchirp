---
okf_version: "0.2"
type: Function
title: channelLibraryWriteReady
description: "True when Write may be enabled: not busy, no invalid channels, a port,"
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: models/channel_image_baseline/channelLibraryWriteReady
language: dart
---

# channelLibraryWriteReady

True when Write may be enabled: not busy, no invalid channels, a port,

## Signature

```dart
boolchannelLibraryWriteReady({
  required ChannelImageMatch match,
  required bool busy,
  required int invalidCount,
  required bool hasPort,
  required bool hasRadioModel,
  required bool hasRadioImage,
})
```

## Docstring

True when Write may be enabled: not busy, no invalid channels, a port,
a radio model and an image that was loaded this session.

## Source
Lines 146–153 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
