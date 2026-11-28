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
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:31:59Z"
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
