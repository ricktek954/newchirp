---
okf_version: "0.2"
type: Function
title: readImage
description: "Channels, capabilities and zones/banks from a saved radio image (optionally"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:31:59Z"
concept_id: services/radio_bridge/readImage
language: dart
---

# readImage

Channels, capabilities and zones/banks from a saved radio image (optionally

## Signature

```dart
FuturereadImagereadImage
```

## Docstring

Channels, capabilities and zones/banks from a saved radio image (optionally
one [zone]). Slots that can't be decoded go to [lastUndecodedChannels].

## Source
Lines 738–750 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
