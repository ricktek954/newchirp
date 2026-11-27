---
okf_version: "0.2"
type: Function
title: convertRepeaterResponse
description: "Converts the website's JSON into channels: repeater outputs get +5 MHz duplex,"
resource: services/mygmrs_client.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:mygmrs_client.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: services/mygmrs_client/convertRepeaterResponse
language: dart
---

# convertRepeaterResponse

Converts the website's JSON into channels: repeater outputs get +5 MHz duplex,

## Signature

```dart
RepeaterSearchResultsconvertRepeaterResponse(
    Map<String, dynamic> payload, {
    bool openOnly = false,
  })
```

## Docstring

Converts the website's JSON into channels: repeater outputs get +5 MHz duplex,
tones are applied, and closed repeaters are dropped when [openOnly] is set.

## Source
Lines 221–224 in `services/mygmrs_client.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [mygmrs_client](/services/mygmrs_client.md) |
