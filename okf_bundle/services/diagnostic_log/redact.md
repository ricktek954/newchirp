---
okf_version: "0.2"
type: Function
title: _redact
description: "Replaces the user's home folder with \"~\" so reports don't reveal the account name."
resource: services/diagnostic_log.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:diagnostic_log.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: services/diagnostic_log/redact
language: dart
---

# _redact

Replaces the user's home folder with "~" so reports don't reveal the account name.

## Signature

```dart
String_redact(String value)
```

## Docstring

Replaces the user's home folder with "~" so reports don't reveal the account name.

## Source
Lines 226–226 in `services/diagnostic_log.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [diagnostic_log](/services/diagnostic_log.md) |
