---
okf_version: "0.2"
type: Function
title: _download
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/download
language: python
---

# _download

## Signature

```python
def _download(self, block, data)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `block` | `—` | `—` |

| `data` | `—` | `—` |

## Source
Lines 359–363 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_transfer](/newchirp_usb_dfu/transfer.md) |
| calls | [_status](/newchirp_usb_dfu/status.md) |
| called_by | [command](/newchirp_usb_dfu/command.md) |
| called_by | [reboot](/newchirp_usb_dfu/reboot.md) |
| called_by | [write](/newchirp_usb_dfu/write.md) |
