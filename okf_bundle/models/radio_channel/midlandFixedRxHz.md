---
okf_version: "0.2"
type: Function
title: midlandFixedRxHz
description: Official receive frequency in Hz for MXT295 channels 1 through 22.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: models/radio_channel/midlandFixedRxHz
language: dart
---

# midlandFixedRxHz

Official receive frequency in Hz for MXT295 channels 1 through 22.

## Signature

```dart
intmidlandFixedRxHzmidlandFixedRxHz
```

## Docstring

Official receive frequency in Hz for MXT295 channels 1 through 22.

Returns null for channels 23 through 99. Those rows pick one of the
same 22 GMRS channels from the list.

## Source
Lines 266–266 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
