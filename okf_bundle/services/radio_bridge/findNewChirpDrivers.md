---
okf_version: "0.2"
type: Function
title: _findNewChirpDrivers
description: "NewChirp's own drivers folder: the settings or NEWCHIRP_DRIVERS, else"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:31:59Z"
concept_id: services/radio_bridge/findNewChirpDrivers
language: dart
---

# _findNewChirpDrivers

NewChirp's own drivers folder: the settings or NEWCHIRP_DRIVERS, else

## Signature

```dart
String_findNewChirpDrivers_findNewChirpDrivers
```

## Docstring

NewChirp's own drivers folder: the settings or NEWCHIRP_DRIVERS, else
the `newchirp_drivers` folder installed beside CHIRP's package. The
bridge loads it after CHIRP's drivers so a NewChirp driver always takes
precedence over an upstream driver with the same ID.

## Source
Lines 1305–1305 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
