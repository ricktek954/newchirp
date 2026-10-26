---
okf_version: "0.2"
type: Function
title: moduleSandboxRefusal
description: A message when this operating system cannot sandbox a module at all.
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:codex/handle-open-prs"
  - "git:repo:newchirp"
timestamp: "2026-10-26T12:15:08Z"
concept_id: services/module_sandbox/moduleSandboxRefusal
language: dart
---

# moduleSandboxRefusal

A message when this operating system cannot sandbox a module at all.

## Signature

```dart
StringmoduleSandboxRefusalmoduleSandboxRefusal
```

## Docstring

A message when this operating system cannot sandbox a module at all.
Linux bubblewrap is checked separately because the OS itself can do it.

## Source
Lines 96–96 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
