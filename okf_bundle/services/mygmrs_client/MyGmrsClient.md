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
timestamp: "2026-11-04T11:24:20Z"
concept_id: services/mygmrs_client/MyGmrsClient
language: dart
---

# MyGmrsClient

## Signature

```dart
MyGmrsClient({
    this.clientId = myGmrsClientId,
    Uri? redirectUri,
    Uri? apiBase,
    Future<void> Function(Uri uri)? openBrowser,
    Duration signInTimeout = const Duration(minutes: 5),
  })
```

## Source
Lines 50–56 in `services/mygmrs_client.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [mygmrs_client](/services/mygmrs_client.md) |
