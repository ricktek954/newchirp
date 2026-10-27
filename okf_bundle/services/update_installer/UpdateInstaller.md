---
okf_version: "0.2"
type: Class
title: UpdateInstaller
description: Downloads a direct NewChirp installer and starts the native update helper.
resource: services/update_installer.dart
tags:
  - "lang:dart"
  - "type:Class"
  - "module:services"
  - "domain:update_installer.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-27T13:46:10Z"
concept_id: services/update_installer/UpdateInstaller
language: dart
---

# UpdateInstaller

Downloads a direct NewChirp installer and starts the native update helper.

## Signature

```dart
class UpdateInstaller
```

## Docstring

Downloads a direct NewChirp installer and starts the native update helper.

The app exits after [install] returns. Each helper waits for that exit,
replaces the application, and relaunches NewChirp.

## Methods

- `download`
- `install`
- `_installMacUpdate`
- `_installWindowsUpdate`
- `_installLinuxUpdate`

## Source
Lines 51–297 in `services/update_installer.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_installer](/services/update_installer.md) |
