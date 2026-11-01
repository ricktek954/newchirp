---
okf_version: "0.2"
type: Function
title: __init__
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/init
language: python
---

# __init__

## Signature

```python
def __init__(self, port)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `port` | `—` | `—` |

## Source
Lines 234–284 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_load_library](/newchirp_usb_dfu/load_library.md) |
| calls | [_bind_library](/newchirp_usb_dfu/bind_library.md) |
| calls | [_devices](/newchirp_usb_dfu/devices.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
| calls | [libusb_exit](/newchirp_usb_dfu/libusb_exit.md) |
| calls | [close](/newchirp_usb_dfu/close.md) |
| calls | [_error_text](/newchirp_usb_dfu/error_text.md) |
