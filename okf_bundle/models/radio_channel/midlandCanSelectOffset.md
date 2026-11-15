---
okf_version: "0.2"
type: Function
title: midlandCanSelectOffset
description: Offset can be chosen only for GMRS channels 15 through 22.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:fix/triage-2026-11-15"
  - "git:repo:newchirp"
timestamp: "2026-11-15T13:11:31Z"
concept_id: models/radio_channel/midlandCanSelectOffset
language: dart
---

# midlandCanSelectOffset

Offset can be chosen only for GMRS channels 15 through 22.

## Signature

```dart
boolmidlandCanSelectOffset(int location, double frequencyMhz)
```

## Docstring

Offset can be chosen only for GMRS channels 15 through 22.

Repeater rows stay on +5 MHz, so that choice is not open there.

## Source
Lines 458–458 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
