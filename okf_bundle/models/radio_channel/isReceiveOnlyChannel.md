---
okf_version: "0.2"
type: Function
title: isReceiveOnlyChannel
description: Why this MXT295 channel is not legal. Empty for every other radio.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-20T20:10:28Z"
concept_id: models/radio_channel/isReceiveOnlyChannel
language: dart
---

# isReceiveOnlyChannel

Why this MXT295 channel is not legal. Empty for every other radio.

## Signature

```dart
boolisReceiveOnlyChannel(RadioChannel channel)
```

## Docstring

Why this MXT295 channel is not legal. Empty for every other radio.

The driver enforces the same rules in drivers/newchirp_mxt295.py.
True when the channel has no transmit frequency (duplex "off"). Radios
store such channels without a TX frequency and refuse PTT on them, which
owners can mistake for a failed write (RT-950 Pro report, 2026-11-20:
marine template channels added receive-only beeped on PTT).

## Source
Lines 472–472 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
