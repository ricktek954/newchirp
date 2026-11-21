---
okf_version: "0.2"
type: Function
title: close
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/close
language: python
---

# close

## Signature

```python
def close(self, reboot = True)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `reboot` | `—` | `True` |

## Source
Lines 429–438 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [libusb_exit](/newchirp_usb_dfu/libusb_exit.md) |
| calls | [reboot](/newchirp_usb_dfu/reboot.md) |
| called_by | [__init__](/newchirp_usb_dfu/init.md) |
