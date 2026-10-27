---
okf_version: "0.2"
type: Function
title: trustedUpdateArtifactUrl
description: "Validated installer URL for [platform], or null when it is not installable."
resource: services/update_checker.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:update_checker.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-27T13:42:17Z"
concept_id: services/update_checker/trustedUpdateArtifactUrl
language: dart
---

# trustedUpdateArtifactUrl

Validated installer URL for [platform], or null when it is not installable.

## Signature

```dart
StringtrustedUpdateArtifactUrltrustedUpdateArtifactUrl
```

## Docstring

Validated installer URL for [platform], or null when it is not installable.

The artifact must be HTTPS on newchirp.net and have the native desktop
package extension. Fragments are discarded before the URL is used.

## Source
Lines 296–296 in `services/update_checker.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [update_checker](/services/update_checker.md) |
