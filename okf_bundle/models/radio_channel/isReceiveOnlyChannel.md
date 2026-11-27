---
okf_version: "0.2"
type: Function
title: isReceiveOnlyChannel
description: "True when the channel has no transmit frequency (duplex \"off\"). Radios"
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: models/radio_channel/isReceiveOnlyChannel
language: dart
---

# isReceiveOnlyChannel

True when the channel has no transmit frequency (duplex "off"). Radios

## Signature

```dart
boolisReceiveOnlyChannel(RadioChannel channel)
```

## Docstring

True when the channel has no transmit frequency (duplex "off"). Radios
store such channels without a TX frequency and refuse PTT on them, which
owners can mistake for a failed write (RT-950 Pro report, 2026-11-20:
marine template channels added receive-only beeped on PTT).

## Source
Lines 473–473 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
