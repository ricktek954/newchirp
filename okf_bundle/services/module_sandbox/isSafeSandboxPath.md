---
okf_version: "0.2"
type: Function
title: isSafeSandboxPath
description: "True for an absolute path that is safe to put in a sandbox profile: no quotes,"
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:02:23Z"
concept_id: services/module_sandbox/isSafeSandboxPath
language: dart
---

# isSafeSandboxPath

True for an absolute path that is safe to put in a sandbox profile: no quotes,

## Signature

```dart
boolisSafeSandboxPath(String path)
```

## Docstring

True for an absolute path that is safe to put in a sandbox profile: no quotes,
backslashes, parentheses, line breaks, NUL or ".." parts, and not "/".

## Source
Lines 132–132 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
