---
okf_version: "0.2"
type: Function
title: prepareMxt295Editor
description: Snaps locked MXT295 fields to the legal GMRS values.
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:16:01Z"
concept_id: models/radio_channel/prepareMxt295Editor
language: dart
---

# prepareMxt295Editor

Snaps locked MXT295 fields to the legal GMRS values.

## Signature

```dart
voidprepareMxt295Editor()
```

## Docstring

Snaps locked MXT295 fields to the legal GMRS values.

Channels 23 through 99 keep their frequency. An illegal duplex on
those rows is left in place so the editor can explain it.

## Source
Lines 495–495 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
