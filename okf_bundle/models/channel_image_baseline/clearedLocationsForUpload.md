---
okf_version: "0.2"
type: Function
title: clearedLocationsForUpload
description: All radio locations that must be blank for the current library to match.
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: models/channel_image_baseline/clearedLocationsForUpload
language: dart
---

# clearedLocationsForUpload

All radio locations that must be blank for the current library to match.

## Signature

```dart
SetclearedLocationsForUploadclearedLocationsForUpload
```

## Docstring

All radio locations that must be blank for the current library to match.

Clear tracking can become incomplete after replacing a library, importing
external data, or moving channels between views. For a full-image upload,
any in-range location not present as an active channel is empty.

## Source
Lines 78–83 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
