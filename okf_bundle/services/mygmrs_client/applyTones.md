---
okf_version: "0.2"
type: Function
title: _applyTones
description: "Sets tone mode: same tone both ways = TSQL, transmit only = Tone,"
resource: services/mygmrs_client.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:mygmrs_client.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: services/mygmrs_client/applyTones
language: dart
---

# _applyTones

Sets tone mode: same tone both ways = TSQL, transmit only = Tone,

## Signature

```dart
void_applyTones(RadioChannel channel, double? txTone, double? rxTone)
```

## Docstring

Sets tone mode: same tone both ways = TSQL, transmit only = Tone,
otherwise Cross (88.5 Hz fills a missing side, as CHIRP does).

## Source
Lines 458–458 in `services/mygmrs_client.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [mygmrs_client](/services/mygmrs_client.md) |
