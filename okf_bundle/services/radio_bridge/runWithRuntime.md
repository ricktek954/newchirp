---
okf_version: "0.2"
type: Function
title: _runWithRuntime
description: "Starts the Python bridge with CHIRP and NewChirp's drivers, streams progress"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:03:04Z"
concept_id: services/radio_bridge/runWithRuntime
language: dart
---

# _runWithRuntime

Starts the Python bridge with CHIRP and NewChirp's drivers, streams progress

## Signature

```dart
Future_runWithRuntime_runWithRuntime
```

## Docstring

Starts the Python bridge with CHIRP and NewChirp's drivers, streams progress
lines from stderr to [onProgress], and returns the JSON from stdout. A non-zero
exit becomes a RadioBridgeException with a readable message.

## Source
Lines 1040–1044 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
