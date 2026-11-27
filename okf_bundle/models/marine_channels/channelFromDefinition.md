---
okf_version: "0.2"
type: Function
title: _channelFromDefinition
description: "One marine channel as a radio channel. Receive-only channels (or all, if transmit is off) get duplex \"off\"."
resource: models/marine_channels.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:marine_channels.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: models/marine_channels/channelFromDefinition
language: dart
---

# _channelFromDefinition

One marine channel as a radio channel. Receive-only channels (or all, if transmit is off) get duplex "off".

## Signature

```dart
RadioChannel_channelFromDefinition(
  int location,
  MarineChannelDefinition definition, {
  required bool programTransmit,
  required MarineChannelPlan plan,
})
```

## Docstring

One marine channel as a radio channel. Receive-only channels (or all, if transmit is off) get duplex "off".

## Source
Lines 74–79 in `models/marine_channels.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [marine_channels](/models/marine_channels.md) |
