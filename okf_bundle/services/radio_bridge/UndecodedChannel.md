---
okf_version: "0.2"
type: Class
title: UndecodedChannel
description: A channel slot the driver could not decode. The bridge leaves it out of
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Class"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:03:04Z"
concept_id: services/radio_bridge/UndecodedChannel
language: dart
---

# UndecodedChannel

A channel slot the driver could not decode. The bridge leaves it out of

## Signature

```dart
class UndecodedChannel
```

## Docstring

A channel slot the driver could not decode. The bridge leaves it out of
the channel list, the radio's bytes stay untouched, and uploads refuse
to write that slot (2026-11-26 IC-E90 report, mailbox UID 1017).

## Source
Lines 204–221 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
