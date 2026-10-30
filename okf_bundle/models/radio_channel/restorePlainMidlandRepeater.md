---
okf_version: "0.2"
type: Function
title: restorePlainMidlandRepeater
description: Puts the standard GMRS repeater back in this row and clears the name.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: models/radio_channel/restorePlainMidlandRepeater
language: dart
---

# restorePlainMidlandRepeater

Puts the standard GMRS repeater back in this row and clears the name.

## Signature

```dart
voidrestorePlainMidlandRepeater()
```

## Docstring

Puts the standard GMRS repeater back in this row and clears the name.

Does nothing when [location] is not one of the eight repeater slots.

## Source
Lines 582–582 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
