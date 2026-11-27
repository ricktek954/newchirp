---
okf_version: "0.2"
type: Function
title: radioBridgeFailureMessage
description: "User-facing message for a bridge process that exited with [exitCode];"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:03:04Z"
concept_id: services/radio_bridge/radioBridgeFailureMessage
language: dart
---

# radioBridgeFailureMessage

User-facing message for a bridge process that exited with [exitCode];

## Signature

```dart
StringradioBridgeFailureMessage({
  required int exitCode,
  required String details,
  required bool moduleSandboxed,
})
```

## Docstring

User-facing message for a bridge process that exited with [exitCode];
recognizes a few known failures and otherwise shows [details].

## Source
Lines 66–70 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
