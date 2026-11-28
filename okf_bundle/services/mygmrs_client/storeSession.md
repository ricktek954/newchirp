---
okf_version: "0.2"
type: Function
title: _storeSession
description: "Keeps the session token from the website. It expires after `expiresIn`"
resource: services/mygmrs_client.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:mygmrs_client.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:01:42Z"
concept_id: services/mygmrs_client/storeSession
language: dart
---

# _storeSession

Keeps the session token from the website. It expires after `expiresIn`

## Signature

```dart
void_storeSession(Map<String, dynamic> response)
```

## Docstring

Keeps the session token from the website. It expires after `expiresIn`
seconds (default 43200 = 12 hours).

## Source
Lines 128–128 in `services/mygmrs_client.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [mygmrs_client](/services/mygmrs_client.md) |
