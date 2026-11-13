---
okf_version: "0.2"
type: Function
title: resolvePythonExecutable
description: "Resolves Python 3.10+ and rejects a missing packaged Windows runtime"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-13T13:13:49Z"
concept_id: services/radio_bridge/resolvePythonExecutable
language: dart
---

# resolvePythonExecutable

Resolves a Python 3.10+ interpreter for the radio bridge and probes each
candidate before returning it.

Packaged Windows builds permit only `NEWCHIRP_PYTHON` and the bundled
`python\python.exe`. If neither can start, the function throws a
`RadioBridgeException` naming the expected path and asking the user to reinstall
NewChirp, rather than falling through to the Microsoft Store `python` aliases.
Source runs may use system Python.

## Signature

```dart
Future<String> resolvePythonExecutable({
  required String operatingSystem,
  required String? resourcesDirectory,
  required String? configuredPath,
  required String? macRuntime,
  required bool allowSystemPython,
  required PythonVersionProbe probe,
})
```

## Source
Lines 97-166 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
