---
okf_version: "0.2"
type: Function
title: RadioChannel
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:16:01Z"
concept_id: models/radio_channel/RadioChannel
language: dart
---

# RadioChannel

## Signature

```dart
RadioChannel({
    required this.location,
    required this.name,
    required this.frequency,
    this.cleared = false,
    this.duplex = '',
    this.offset = 0.6,
    this.tone = '',
    this.txTone = 88.5,
    this.rxTone = 88.5,
    this.dtcs = 23,
    this.dtcsPolarity = 'NN',
    this.rxDtcs = 23,
    this.crossMode = 'Tone->Tone',
    this.mode = 'FM',
    this.step = 5.0,
    this.skip = '',
    this.power = '',
    this.comment = '',
    List<ChannelExtraField>? extras,
  })
```

## Source
Lines 405–425 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
