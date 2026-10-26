---
okf_version: "0.2"
type: Function
title: gm32DuplexChoices
description: Duplex menu for the current receive frequency.
resource: models/gm32_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:gm32_channel.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:18:51Z"
concept_id: models/gm32_channel/gm32DuplexChoices
language: dart
---

# gm32DuplexChoices

Duplex menu for the current receive frequency.

## Signature

```dart
Mapgm32DuplexChoicesgm32DuplexChoices
```

## Docstring

Duplex menu for the current receive frequency.

Channels 1-7 stay simplex. Channels 8-14 start simplex and may also
be receive-only. Channels 15-22 may be simplex, a +5 MHz repeater,
or receive-only. Anything else is receive-only.

## Source
Lines 87–87 in `models/gm32_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [gm32_channel](/models/gm32_channel.md) |
