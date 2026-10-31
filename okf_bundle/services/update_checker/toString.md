---
okf_version: "0.2"
type: Function
title: toString
description: Starts the platform browser for an already validated address.
resource: services/update_checker.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_checker.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-31T14:31:44Z"
concept_id: services/update_checker/toString
language: dart
---

# toString

Starts the platform browser for an already validated address.

## Signature

```dart
StringtoString()
```

## Docstring

Starts the platform browser for an already validated address.

Windows hands the address to Explorer, the shell entry point a user reaches
by clicking a link. Earlier builds shelled out to
`rundll32 url.dll,FileProtocolHandler`, which endpoint protection software
blocks by policy and which reports no error at all when it does nothing.
Explorer exits with a non-zero code even when it opens the page, so only a
failure to start the process counts as a failed launch.

## Source
Lines 39–39 in `services/update_checker.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_checker](/services/update_checker.md) |
