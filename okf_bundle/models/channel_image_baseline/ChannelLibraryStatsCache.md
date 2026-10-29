---
okf_version: "0.2"
type: Class
title: ChannelLibraryStatsCache
description: Remembers the last library snapshot so search and row selection can skip it.
resource: models/channel_image_baseline.dart
tags:
  - "lang:dart"
  - "type:Class"
  - "module:models"
  - "domain:channel_image_baseline.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T12:56:37Z"
concept_id: models/channel_image_baseline/ChannelLibraryStatsCache
language: dart
---

# ChannelLibraryStatsCache

Remembers the last library snapshot so search and row selection can skip it.

## Signature

```dart
class ChannelLibraryStatsCache
```

## Docstring

Remembers the last library snapshot so search and row selection can skip it.

Call [markDirty] after an in-place channel edit.
[read] also refreshes when the image, zone, baseline, radio, memory
limits, channel list, or cleared-slot count changes.

## Methods

- `markDirty`
- `read`

## Source
Lines 155–246 in `models/channel_image_baseline.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_image_baseline](/models/channel_image_baseline.md) |
