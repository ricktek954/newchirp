---
okf_version: "0.2"
type: Function
title: _installMacUpdate
description: Finds the running .app bundle and starts a detached helper script that
resource: services/update_installer.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_installer.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: services/update_installer/installMacUpdate
language: dart
---

# _installMacUpdate

Finds the running .app bundle and starts a detached helper script that

## Signature

```dart
Future_installMacUpdate_installMacUpdate
```

## Docstring

Finds the running .app bundle and starts a detached helper script that
waits for this process ([pid]) to quit, then installs the app from [dmg].

## Source
Lines 224–224 in `services/update_installer.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_installer](/services/update_installer.md) |
