---
okf_version: "0.2"
type: Function
title: _frequencyFitsStep
description: "True when [frequencyHz] lies on the [stepKhz] grid. 8.33 kHz (airband) is"
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: models/radio_channel/frequencyFitsStep
language: dart
---

# _frequencyFitsStep

True when [frequencyHz] lies on the [stepKhz] grid. 8.33 kHz (airband) is

## Signature

```dart
bool_frequencyFitsStep(int frequencyHz, double stepKhz)
```

## Docstring

True when [frequencyHz] lies on the [stepKhz] grid. 8.33 kHz (airband) is
special: its channels repeat every 25 kHz at offsets 0, 8.33 and 16.67 kHz.

## Source
Lines 914–914 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
