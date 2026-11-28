---
okf_version: "0.2"
type: Function
title: cancelActive
description: Asks the running bridge process to stop (SIGTERM). True when nothing is running
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:31:59Z"
concept_id: services/radio_bridge/cancelActive
language: dart
---

# cancelActive

Asks the running bridge process to stop (SIGTERM). True when nothing is running

## Signature

```dart
boolcancelActive()
```

## Docstring

Asks the running bridge process to stop (SIGTERM). True when nothing is running
or the signal was sent.

## Source
Lines 513–513 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
