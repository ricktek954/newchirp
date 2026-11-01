---
okf_version: "0.2"
type: Function
title: _status
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/status
language: python
---

# _status

## Signature

```python
def _status(self)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Source
Lines 322–330 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_transfer](/newchirp_usb_dfu/transfer.md) |
| called_by | [_download](/newchirp_usb_dfu/download.md) |
| called_by | [_upload](/newchirp_usb_dfu/upload.md) |
