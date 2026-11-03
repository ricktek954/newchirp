---
okf_version: "0.2"
type: Function
title: channelLibraryWriteReady
description: Allow incompatible rows only when the caller provides a review/skip step.
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:fix/repeater-compatibility"
  - "git:repo:newchirp"
timestamp: "2026-11-03T20:22:07Z"
concept_id: models/channel_image_baseline/channelLibraryWriteReady
language: dart
---

# channelLibraryWriteReady

Allow incompatible rows only when the caller provides a review/skip step.

## Signature

```dart
boolchannelLibraryWriteReady({
  required ChannelImageMatch match,
  required bool busy,
  required int invalidCount,
  bool allowIncompatibleReview = false,
  required bool hasPort,
  required bool hasRadioModel,
  required bool hasRadioImage,
})
```

## Docstring

Allow incompatible rows only when the caller provides a review/skip step.
Connection and image requirements still apply to that workflow.

## Source
Lines 88–96 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
