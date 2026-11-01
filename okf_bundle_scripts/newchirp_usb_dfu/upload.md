---
okf_version: "0.2"
type: Function
title: _upload
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/upload
language: python
---

# _upload

## Signature

```python
def _upload(self, block, length)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `block` | `—` | `—` |

| `length` | `—` | `—` |

## Source
Lines 365–370 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_transfer](/newchirp_usb_dfu/transfer.md) |
| calls | [_status](/newchirp_usb_dfu/status.md) |
| called_by | [identity](/newchirp_usb_dfu/identity.md) |
| called_by | [read](/newchirp_usb_dfu/read.md) |
