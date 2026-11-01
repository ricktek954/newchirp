---
okf_version: "0.2"
type: Function
title: list_devices
description: Return DfuSe radio interfaces as bridge pseudo-port records.
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/list_devices
language: python
---

# list_devices

Return DfuSe radio interfaces as bridge pseudo-port records.

## Signature

```python
def list_devices()
```

## Docstring

Return DfuSe radio interfaces as bridge pseudo-port records.

## Source
Lines 203–228 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [newchirp_usb_dfu](/newchirp_usb_dfu.md) |
| calls | [_load_library](/newchirp_usb_dfu/load_library.md) |
| calls | [_bind_library](/newchirp_usb_dfu/bind_library.md) |
| calls | [_devices](/newchirp_usb_dfu/devices.md) |
| calls | [libusb_exit](/newchirp_usb_dfu/libusb_exit.md) |
