---
okf_version: "0.2"
type: Function
title: compareVersions
description: "Compares two dotted version strings, ignoring any `+build` metadata."
resource: services/update_checker.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_checker.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-31T00:09:10Z"
concept_id: services/update_checker/compareVersions
language: dart
---

# compareVersions

Compares two dotted version strings, ignoring any `+build` metadata.

## Signature

```dart
intcompareVersions(String a, String b)
```

## Docstring

Compares two dotted version strings, ignoring any `+build` metadata.

Returns a positive number when [a] is newer than [b], a negative number
when [a] is older, and zero when they are equivalent.

## Source
Lines 229–229 in `services/update_checker.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_checker](/services/update_checker.md) |
