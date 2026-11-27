---
okf_version: "0.2"
type: Function
title: mount
description: "Bind-mounts [source] at the same path ([mode] = --bind or --ro-bind),"
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:02:23Z"
concept_id: services/module_sandbox/mount
language: dart
---

# mount

Bind-mounts [source] at the same path ([mode] = --bind or --ro-bind),

## Signature

```dart
voidmount(String source, String mode)
```

## Docstring

Bind-mounts [source] at the same path ([mode] = --bind or --ro-bind),
creating parent folders first; skipped if a parent is already mounted.

## Source
Lines 454–454 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
