---
okf_version: "0.2"
type: Function
title: record
description: Adds an entry to memory and appends it to the log file.
resource: services/diagnostic_log.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:diagnostic_log.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: services/diagnostic_log/record
language: dart
---

# record

Adds an entry to memory and appends it to the log file.

## Signature

```dart
voidrecord(
    String category,
    String message, {
    Map<String, Object?> context = const {},
  })
```

## Docstring

Adds an entry to memory and appends it to the log file.

## Source
Lines 72–76 in `services/diagnostic_log.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [diagnostic_log](/services/diagnostic_log.md) |
