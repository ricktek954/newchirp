---
okf_version: "0.2"
type: Function
title: _waitForSendKeyCue
description: "For radios that start a clone read from their own key (\"After clicking"
resource: main.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:main.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-22T10:07:40Z"
concept_id: main/waitForSendKeyCue
language: dart
---

# _waitForSendKeyCue

For radios that start a clone read from their own key ("After clicking

## Signature

```dart
String_waitForSendKeyCue(String message, String buttonLabel)
```

## Docstring

For radios that start a clone read from their own key ("After clicking
OK, press the [BAND] key"), tell the user to wait for the bridge's ready
cue. NewChirp opens the port only after the dialog closes, so an early
press sends the image to nobody and the radio then waits (2026-11-21
FT-1D report). The quoted text matches `manual_send_ready_message` in
`scripts/chirp_bridge.py`.

## Source
Lines 109–109 in `main.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [lib](/main.md) |
