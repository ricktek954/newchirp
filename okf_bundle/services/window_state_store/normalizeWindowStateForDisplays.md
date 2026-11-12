---
okf_version: "0.2"
type: Function
title: normalizeWindowStateForDisplays
description: Normalize saved bounds against the current display layout.
resource: services/window_state_store.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:window_state_store.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-12T14:52:36Z"
concept_id: services/window_state_store/normalizeWindowStateForDisplays
language: dart
---

# normalizeWindowStateForDisplays

Normalize saved bounds against the current display layout.

## Signature

```dart
WindowStatenormalizeWindowStateForDisplaysnormalizeWindowStateForDisplays
```

## Docstring

Normalize saved bounds against the current display layout.

Windows can save window rectangles under one monitor's DPI basis and then
restore them after the window has moved to another monitor with a different
scale. In that layout, center on the primary display rather than trying to
reinterpret a position whose coordinate space is ambiguous.

## Source
Lines 51–56 in `services/window_state_store.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [window_state_store](/services/window_state_store.md) |
