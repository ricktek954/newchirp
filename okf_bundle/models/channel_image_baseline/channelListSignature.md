---
okf_version: "0.2"
type: Function
title: channelListSignature
description: "Fingerprint (JSON text) of a channel list plus its cleared slots, sorted by"
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: models/channel_image_baseline/channelListSignature
language: dart
---

# channelListSignature

Fingerprint (JSON text) of a channel list plus its cleared slots, sorted by

## Signature

```dart
StringchannelListSignature(
  List<RadioChannel> channels,
  Iterable<int> cleared,
)
```

## Docstring

Fingerprint (JSON text) of a channel list plus its cleared slots, sorted by
location so the same channels always give the same string.

## Source
Lines 36–39 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
