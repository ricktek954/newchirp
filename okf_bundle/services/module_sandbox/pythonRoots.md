---
okf_version: "0.2"
type: Function
title: _pythonRoots
description: "Folders the Python install lives in (sys.prefix and friends), resolved"
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:02:23Z"
concept_id: services/module_sandbox/pythonRoots
language: dart
---

# _pythonRoots

Folders the Python install lives in (sys.prefix and friends), resolved

## Signature

```dart
Future_pythonRoots_pythonRoots
```

## Docstring

Folders the Python install lives in (sys.prefix and friends), resolved
through symlinks, so the sandbox can expose them read-only.

## Source
Lines 652–652 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
