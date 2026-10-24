---
okf_version: "0.2"
type: Function
title: _parseManifest
description: Opens a newchirp.net download page in the default browser.
resource: services/update_checker.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_checker.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-24T18:03:09Z"
concept_id: services/update_checker/parseManifest
language: dart
---

# _parseManifest

Opens a newchirp.net download page in the default browser.

## Signature

```dart
_ReleaseManifest_parseManifest(String body)
```

## Docstring

Opens a newchirp.net download page in the default browser.

Returns false when [url] is not an allowed download page, or when no
usable launcher is available. The launched address is rebuilt as https on
newchirp.net, so a tricky string cannot change the site.

## Source
Lines 108–108 in `services/update_checker.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_checker](/services/update_checker.md) |
