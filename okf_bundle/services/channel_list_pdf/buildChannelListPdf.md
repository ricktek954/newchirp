---
okf_version: "0.2"
type: Function
title: buildChannelListPdf
description: "Build a landscape PDF listing [rows] under [title] and [subtitle]."
resource: services/channel_list_pdf.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:channel_list_pdf.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:00:11Z"
concept_id: services/channel_list_pdf/buildChannelListPdf
language: dart
---

# buildChannelListPdf

Build a landscape PDF listing [rows] under [title] and [subtitle].

## Signature

```dart
Uint8ListbuildChannelListPdf({
  required String title,
  required String subtitle,
  required List<List<String>> rows,
  List<ChannelListColumn> columns = channelListColumns,
  bool letter = false,
})
```

## Docstring

Build a landscape PDF listing [rows] under [title] and [subtitle].

## Source
Lines 275–281 in `services/channel_list_pdf.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [channel_list_pdf](/services/channel_list_pdf.md) |
