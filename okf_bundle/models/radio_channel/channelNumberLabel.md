---
okf_version: "0.2"
type: Function
title: channelNumberLabel
description: Channel number shown in the list.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:16:01Z"
concept_id: models/radio_channel/channelNumberLabel
language: dart
---

# channelNumberLabel

Channel number shown in the list.

## Signature

```dart
StringchannelNumberLabel(String? model, int location)
```

## Docstring

Channel number shown in the list.

For the MXT295, [location] is still the radio's memory slot. The label
matches the Midland screen: channels 1-99, with RPTR 15-22 between them.
Other radios show the slot number unchanged.

## Source
Lines 136–136 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
