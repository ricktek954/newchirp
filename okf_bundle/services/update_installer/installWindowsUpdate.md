---
okf_version: "0.2"
type: Function
title: _installWindowsUpdate
description: "Refuses an installer whose Authenticode signature isn't valid (PowerShell"
resource: services/update_installer.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_installer.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: services/update_installer/installWindowsUpdate
language: dart
---

# _installWindowsUpdate

Refuses an installer whose Authenticode signature isn't valid (PowerShell

## Signature

```dart
Future_installWindowsUpdate_installWindowsUpdate
```

## Docstring

Refuses an installer whose Authenticode signature isn't valid (PowerShell
exit code 7), then starts it detached.

## Source
Lines 256–256 in `services/update_installer.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_installer](/services/update_installer.md) |
