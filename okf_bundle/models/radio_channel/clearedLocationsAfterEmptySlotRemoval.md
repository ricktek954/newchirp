---
okf_version: "0.2"
type: Function
title: clearedLocationsAfterEmptySlotRemoval
description: "Cleared-slot set after deleting the empty slot at [location]: later cleared"
resource: models/radio_channel.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:models"
  - "domain:radio_channel.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: models/radio_channel/clearedLocationsAfterEmptySlotRemoval
language: dart
---

# clearedLocationsAfterEmptySlotRemoval

Cleared-slot set after deleting the empty slot at [location]: later cleared

## Signature

```dart
SetclearedLocationsAfterEmptySlotRemovalclearedLocationsAfterEmptySlotRemoval
```

## Docstring

Cleared-slot set after deleting the empty slot at [location]: later cleared
slots move down by one, and the old highest slot (within [rangeEnd], if given)
becomes cleared because everything after it shifted up.

## Source
Lines 219–224 in `models/radio_channel.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_channel](/models/radio_channel.md) |
