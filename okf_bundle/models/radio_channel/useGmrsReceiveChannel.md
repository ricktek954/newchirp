---
okf_version: "0.2"
type: Function
title: useGmrsReceiveChannel
description: Sets this row to one of the 22 GMRS receive channels.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:16:01Z"
concept_id: models/radio_channel/useGmrsReceiveChannel
language: dart
---

# useGmrsReceiveChannel

Sets this row to one of the 22 GMRS receive channels.

## Signature

```dart
voiduseGmrsReceiveChannel(int channelNumber)
```

## Docstring

Sets this row to one of the 22 GMRS receive channels.

The row starts simplex with no offset. Choosing duplex + later
sets the offset to 5 MHz. Fixed rows 1 through 22 do not move.

## Source
Lines 482–482 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
