---
okf_version: "0.2"
type: Class
title: ChannelImageBaseline
description: "Fingerprint of the channel list last read from, imported from, or written"
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Class"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: models/channel_image_baseline/ChannelImageBaseline
language: dart
---

# ChannelImageBaseline

Fingerprint of the channel list last read from, imported from, or written

## Signature

```dart
class ChannelImageBaseline
```

## Docstring

Fingerprint of the channel list last read from, imported from, or written
to the stored radio image.

Screen edits are compared with this so Discard and Write follow the radio
image, not whether a CSV file was saved.

## Source
Lines 10–24 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
