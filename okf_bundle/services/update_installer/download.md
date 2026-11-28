---
okf_version: "0.2"
type: Function
title: download
description: "Downloads this platform's installer for [update] into a temp folder."
resource: services/update_installer.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_installer.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T08:59:31Z"
concept_id: services/update_installer/download
language: dart
---

# download

Downloads this platform's installer for [update] into a temp folder.

## Signature

```dart
Futuredownloaddownload
```

## Docstring

Downloads this platform's installer for [update] into a temp folder.
Only trusted newchirp.net URLs are used; the size is capped and the
SHA-256 is checked when the release publishes one.

## Source
Lines 59–62 in `services/update_installer.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_installer](/services/update_installer.md) |
