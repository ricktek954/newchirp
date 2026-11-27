---
okf_version: "0.2"
type: Function
title: _pdfText
description: "Escapes text for a PDF string: backslash and parentheses are escaped,"
resource: services/channel_list_pdf.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:channel_list_pdf.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: services/channel_list_pdf/pdfText
language: dart
---

# _pdfText

Escapes text for a PDF string: backslash and parentheses are escaped,

## Signature

```dart
String_pdfText(String value)
```

## Docstring

Escapes text for a PDF string: backslash and parentheses are escaped,
control characters become spaces, and characters outside Latin-1 become "?".

## Source
Lines 137–137 in `services/channel_list_pdf.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_list_pdf](/services/channel_list_pdf.md) |
