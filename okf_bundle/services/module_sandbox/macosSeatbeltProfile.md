---
okf_version: "0.2"
type: Function
title: macosSeatbeltProfile
description: "macOS Seatbelt (sandbox-exec) profile. It starts from \"allow default\" (\"deny"
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:02:23Z"
concept_id: services/module_sandbox/macosSeatbeltProfile
language: dart
---

# macosSeatbeltProfile

macOS Seatbelt (sandbox-exec) profile. It starts from "allow default" ("deny

## Signature

```dart
StringmacosSeatbeltProfile({
  required String workDir,
  required String python,
  required List<String> pythonRoots,
  required String chirpSource,
  required String? driverDir,
  required List<String> readOnlyFiles,
  required List<String> readWriteFiles,
  required String? serialPort,
  List<String> alsoWritableRoots = const [],
  String? home,
})
```

## Docstring

macOS Seatbelt (sandbox-exec) profile. It starts from "allow default" ("deny
default" crashes sandbox-exec), denies home folders, other drives, temp and the
network, then re-allows Python, CHIRP, the listed files, the work folder and the port.

## Source
Lines 255–266 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
