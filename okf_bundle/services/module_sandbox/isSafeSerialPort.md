---
okf_version: "0.2"
type: Function
title: isSafeSerialPort
description: "True for a serial port name of the usual form (/dev/cu.* or /dev/tty.* on macOS,"
resource: services/module_sandbox.dart
tags:
  - "lang:dart"
  - "type:Function"
  - "module:services"
  - "domain:module_sandbox.dart"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-27T09:02:23Z"
concept_id: services/module_sandbox/isSafeSerialPort
language: dart
---

# isSafeSerialPort

True for a serial port name of the usual form (/dev/cu.* or /dev/tty.* on macOS,

## Signature

```dart
boolisSafeSerialPort(SandboxPlatform platform, String port)
```

## Docstring

True for a serial port name of the usual form (/dev/cu.* or /dev/tty.* on macOS,
/dev/ttyUSB0, ttyACM0 or ttyS0 on Linux), so nothing else is passed in as a
"port". Always false where modules can't be sandboxed (Windows).

## Source
Lines 182–182 in `services/module_sandbox.dart`

## Relationships

| Type | Target |
|------|--------|
| related | [module_sandbox](/services/module_sandbox.md) |
