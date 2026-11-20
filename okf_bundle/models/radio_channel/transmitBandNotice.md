---
okf_version: "0.2"
type: Function
title: transmitBandNotice
description: Advisory note for a channel the radio stores and receives but will not
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-20T19:21:25Z"
concept_id: models/radio_channel/transmitBandNotice
language: dart
---

# transmitBandNotice

Advisory note for a channel the radio stores and receives but will not

## Signature

```dart
StringtransmitBandNoticetransmitBandNotice
```

## Docstring

Advisory note for a channel the radio stores and receives but will not
transmit on, because its firmware limits transmit to [txBands]. It never
blocks saving or writing (RT-950 Pro report, 2026-11-20: marine VHF
channels beeped on PTT after a successful write).

## Source
Lines 489–492 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
