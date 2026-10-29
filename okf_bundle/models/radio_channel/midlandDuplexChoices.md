---
okf_version: "0.2"
type: Function
title: midlandDuplexChoices
description: Duplex choices for one MXT295 slot.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T10:57:43Z"
concept_id: models/radio_channel/midlandDuplexChoices
language: dart
---

# midlandDuplexChoices

Duplex choices for one MXT295 slot.

## Signature

```dart
MapmidlandDuplexChoicesmidlandDuplexChoices
```

## Docstring

Duplex choices for one MXT295 slot.

Channels 1 through 7 stay simplex. Channels 8 through 14 are receive
only. Repeater rows are +5 MHz. A receive channel of 1 through 14 on
any other row also stays simplex. The current value stays in the list
when it is not legal, so the editor shows what is stored.

## Source
Lines 296–300 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
