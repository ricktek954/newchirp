---
okf_version: "0.2"
type: Function
title: isBenignBridgeStderrLine
description: "True for harmless stderr lines (CHIRP's \"Replacing existing driver id\" notice"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:03:04Z"
concept_id: services/radio_bridge/isBenignBridgeStderrLine
language: dart
---

# isBenignBridgeStderrLine

True for harmless stderr lines (CHIRP's "Replacing existing driver id" notice

## Signature

```dart
boolisBenignBridgeStderrLine(String line)
```

## Docstring

True for harmless stderr lines (CHIRP's "Replacing existing driver id" notice
when NewChirp's drivers override stock ones), which are not errors.

## Source
Lines 57–57 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
