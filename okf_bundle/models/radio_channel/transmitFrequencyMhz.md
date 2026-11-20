---
okf_version: "0.2"
type: Function
title: transmitFrequencyMhz
description: Why this MXT295 channel is not legal. Empty for every other radio.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-20T19:21:25Z"
concept_id: models/radio_channel/transmitFrequencyMhz
language: dart
---

# transmitFrequencyMhz

Why this MXT295 channel is not legal. Empty for every other radio.

## Signature

```dart
doubletransmitFrequencyMhztransmitFrequencyMhz
```

## Docstring

Why this MXT295 channel is not legal. Empty for every other radio.

The driver enforces the same rules in drivers/newchirp_mxt295.py.
Transmit frequency in MHz, or null when the channel cannot transmit.

## Source
Lines 469–469 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
