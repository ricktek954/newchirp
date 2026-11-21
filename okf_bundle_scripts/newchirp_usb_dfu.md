---
okf_version: "0.2"
type: Module
title: newchirp_usb_dfu
description: Minimal libusb DFU transport used by experimental STM32 radios.
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Module"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu
language: python
---

# newchirp_usb_dfu

Minimal libusb DFU transport used by experimental STM32 radios.

## Docstring

Minimal libusb DFU transport used by experimental STM32 radios.

The desktop bridge normally hands CHIRP a pyserial object.  TYT MD-UV380
radios instead expose ST's DfuSe interface (0483:df11), so this module drives
that interface through the system libusb and exposes a small transport used
by the NewChirp driver.

## Relationships

| Type | Target |
|------|--------|
| related | [DfuError](/newchirp_usb_dfu/DfuError.md) |
| related | [_DeviceDescriptor](/newchirp_usb_dfu/DeviceDescriptor.md) |
| related | [_candidate_libraries](/newchirp_usb_dfu/candidate_libraries.md) |
| related | [_load_library](/newchirp_usb_dfu/load_library.md) |
| related | [_bind_library](/newchirp_usb_dfu/bind_library.md) |
| related | [_error_text](/newchirp_usb_dfu/error_text.md) |
| related | [_devices](/newchirp_usb_dfu/devices.md) |
| related | [list_devices](/newchirp_usb_dfu/list_devices.md) |
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
