---
okf_version: "0.2"
type: Function
title: midlandReceiveChannelIsLocked
description: "Channels 1 through 22 already have a receive channel, so the list"
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: models/radio_channel/midlandReceiveChannelIsLocked
language: dart
---

# midlandReceiveChannelIsLocked

Channels 1 through 22 already have a receive channel, so the list

## Signature

```dart
boolmidlandReceiveChannelIsLocked(int location)
```

## Docstring

Channels 1 through 22 already have a receive channel, so the list
cannot move them.

## Source
Lines 323–323 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
