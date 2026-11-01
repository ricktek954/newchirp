---
okf_version: "0.2"
type: Function
title: write
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/write
language: python
---

# write

## Signature

```python
def write(self, address, data)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `address` | `—` | `—` |

| `data` | `—` | `—` |

## Source
Lines 412–420 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_download](/newchirp_usb_dfu/download.md) |
| calls | [_wait_idle](/newchirp_usb_dfu/wait_idle.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
