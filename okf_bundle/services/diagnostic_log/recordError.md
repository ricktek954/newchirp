---
okf_version: "0.2"
type: Function
title: recordError
description: Records an error with its stack trace.
resource: services/diagnostic_log.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:diagnostic_log.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: services/diagnostic_log/recordError
language: dart
---

# recordError

Records an error with its stack trace.

## Signature

```dart
voidrecordError(
    String category,
    Object error,
    StackTrace stackTrace, {
    Map<String, Object?> context = const {},
  })
```

## Docstring

Records an error with its stack trace.

## Source
Lines 109–114 in `services/diagnostic_log.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [diagnostic_log](/services/diagnostic_log.md) |
