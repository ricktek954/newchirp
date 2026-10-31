---
okf_version: "0.2"
type: Function
title: _windowsSerialPortNames
description: "Windows: read the live COM ports from the SERIALCOMM registry key, then"
resource: services/radio_bridge.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:radio_bridge.dart"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: services/radio_bridge/windowsSerialPortNames
language: dart
---

# _windowsSerialPortNames

Windows: read the live COM ports from the SERIALCOMM registry key, then

## Signature

```dart
Future_windowsSerialPortNames_windowsSerialPortNames
```

## Docstring

Windows: read the live COM ports from the SERIALCOMM registry key, then
fall back to .NET's SerialPort.GetPortNames() so only real ports show up.

## Source
Lines 353–353 in `services/radio_bridge.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [radio_bridge](/services/radio_bridge.md) |
