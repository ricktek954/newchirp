---
okf_version: "0.2"
type: Function
title: receiveOnlyWriteNote
description: "Write-confirmation note naming the receive-only channels, or '' if none."
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: models/radio_channel/receiveOnlyWriteNote
language: dart
---

# receiveOnlyWriteNote

Write-confirmation note naming the receive-only channels, or '' if none.

## Signature

```dart
StringreceiveOnlyWriteNote(
  List<RadioChannel> channels,
  String Function(int location) label,
)
```

## Docstring

Write-confirmation note naming the receive-only channels, or '' if none.

## Source
Lines 477–480 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
