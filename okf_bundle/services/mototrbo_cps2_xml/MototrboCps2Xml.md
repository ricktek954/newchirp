---
okf_version: "0.2"
type: Class
title: MototrboCps2Xml
description: Read-only importer for conventional channels copied from MOTOTRBO CPS 2.0.
resource: services/mototrbo_cps2_xml.dart
tags:
  - "lang:dart"
  - "type:Class"
  - "module:services"
  - "domain:mototrbo_cps2_xml.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-27T09:51:21Z"
concept_id: services/mototrbo_cps2_xml/MototrboCps2Xml
language: dart
---

# MototrboCps2Xml

Read-only importer for conventional channels copied from MOTOTRBO CPS 2.0.

## Signature

```dart
class MototrboCps2Xml
```

## Docstring

Read-only importer for conventional channels copied from MOTOTRBO CPS 2.0.

CPS2 exposes Zone XML through its copy operation. The XML contains one
`ConventionalPersonality` entry per channel and also carries DMR fields
such as color code, timeslot, contact, RX group list, and privacy key.

## Methods

- `decode`
- `_channel`
- `_applyAnalogTones`
- `_tone`
- `_child`
- `_fields`
- `_text`
- `_value`
- `_display`
- `_number`
- `_numberOrNull`
- `_boolean`
- `_addExtra`

## Source
Lines 10–352 in `services/mototrbo_cps2_xml.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [mototrbo_cps2_xml](/services/mototrbo_cps2_xml.md) |
