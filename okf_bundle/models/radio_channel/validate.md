---
okf_version: "0.2"
type: Function
title: validate
description: Problems that would stop this channel being written to the selected radio
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: models/radio_channel/validate
language: dart
---

# validate

Problems that would stop this channel being written to the selected radio

## Signature

```dart
Listvalidatevalidate
```

## Docstring

Problems that would stop this channel being written to the selected radio
(location range, name length, band, mode, step, tones...). Empty = OK.

## Source
Lines 790–801 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
