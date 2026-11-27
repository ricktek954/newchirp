---
okf_version: "0.2"
type: Function
title: _crossSummary
description: "Tone text for a Cross-mode channel, e.g. \"TX 100.0 / RX D023N\"."
resource: services/channel_list_pdf.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:channel_list_pdf.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: services/channel_list_pdf/crossSummary
language: dart
---

# _crossSummary

Tone text for a Cross-mode channel, e.g. "TX 100.0 / RX D023N".

## Signature

```dart
String_crossSummary(
  RadioChannel channel,
  double? tx,
  double? rx,
  String polarity,
  String rxPolarity,
)
```

## Docstring

Tone text for a Cross-mode channel, e.g. "TX 100.0 / RX D023N".

## Source
Lines 65–71 in `services/channel_list_pdf.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_list_pdf](/services/channel_list_pdf.md) |
