---
okf_version: "0.2"
type: Function
title: isSafeAllowRoot
description: A directory NewChirp may expose inside the sandbox.
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:15:08Z"
concept_id: services/module_sandbox/isSafeAllowRoot
language: dart
---

# isSafeAllowRoot

A directory NewChirp may expose inside the sandbox.

## Signature

```dart
boolisSafeAllowRoot(String path, {String? home})
```

## Docstring

A directory NewChirp may expose inside the sandbox.

The home folder, its parents, and whole disks are never allow-roots.
One file under home can still be allowed on its own.

## Source
Lines 138–138 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
