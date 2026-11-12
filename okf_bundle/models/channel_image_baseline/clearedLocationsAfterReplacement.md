---
okf_version: "0.2"
type: Function
title: clearedLocationsAfterReplacement
description: Cleared slots to retain when replacing the current channel library.
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-12T13:46:33Z"
concept_id: models/channel_image_baseline/clearedLocationsAfterReplacement
language: dart
---

# clearedLocationsAfterReplacement

Cleared slots to retain when replacing the current channel library.

## Signature

```dart
SetclearedLocationsAfterReplacementclearedLocationsAfterReplacement
```

## Docstring

Cleared slots to retain when replacing the current channel library.

Active locations present before the replacement but absent from the new
list must be erased from the radio on upload. Explicit clears remain unless
the replacement puts a channel in that slot.

## Source
Lines 52–56 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
