---
okf_version: "0.2"
type: Function
title: _devices
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/devices
language: python
---

# _devices

## Signature

```python
def _devices(lib, context)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `lib` | `—` | `—` |

| `context` | `—` | `—` |

## Source
Lines 179–200 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [newchirp_usb_dfu](/newchirp_usb_dfu.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
| calls | [_error_text](/newchirp_usb_dfu/error_text.md) |
| calls | [_DeviceDescriptor](/newchirp_usb_dfu/DeviceDescriptor.md) |
| called_by | [__init__](/newchirp_usb_dfu/init.md) |
| called_by | [list_devices](/newchirp_usb_dfu/list_devices.md) |
