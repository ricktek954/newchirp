---
okf_version: "0.2"
type: Function
title: MyGmrsClient
resource: services/mygmrs_client.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:mygmrs_client.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-06T15:24:31Z"
concept_id: services/mygmrs_client/MyGmrsClient
language: dart
---

# MyGmrsClient

## Signature

```dart
MyGmrsClient({
    Uri? brokerBase,
    Future<void> Function(Uri uri)? openBrowser,
    Duration signInTimeout = const Duration(seconds: 90),
    Duration signInPollInterval = const Duration(milliseconds: 1200),
  })
```

## Source
Lines 42–47 in `services/mygmrs_client.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [mygmrs_client](/services/mygmrs_client.md) |
