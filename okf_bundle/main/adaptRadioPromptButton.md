---
okf_version: "0.2"
type: Function
title: adaptRadioPromptButton
description: "Rewrites a CHIRP driver prompt for NewChirp's dialog: strips HTML, turns"
resource: main.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:main.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:34:25Z"
concept_id: main/adaptRadioPromptButton
language: dart
---

# adaptRadioPromptButton

Rewrites a CHIRP driver prompt for NewChirp's dialog: strips HTML, turns

## Signature

```dart
StringadaptRadioPromptButton(String message, String buttonLabel)
```

## Docstring

Rewrites a CHIRP driver prompt for NewChirp's dialog: strips HTML, turns
"Click OK" into "Click "[buttonLabel]"", and for radios sent with [PTT] (or
their own key) tells the user to wait for the transfer window's ready message.

## Source
Lines 82–82 in `main.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [lib](/main.md) |
