---
okf_version: "0.2"
type: Function
title: _applyChannels
description: "Puts [incoming] channels into the list, replacing everything or adding them"
resource: main.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:main.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:34:01Z"
concept_id: main/applyChannels
language: dart
---

# _applyChannels

Puts [incoming] channels into the list, replacing everything or adding them

## Signature

```dart
void_applyChannels(
    List<RadioChannel> incoming,
    _ChannelApplyMode mode, {
    required String libraryName,
    String? libraryPath,
    bool clearRemovedLocations = true,
  })
```

## Docstring

Puts [incoming] channels into the list, replacing everything or adding them
to free slots, and records the change for undo.

## Source
Lines 2178–2184 in `main.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [lib](/main.md) |
