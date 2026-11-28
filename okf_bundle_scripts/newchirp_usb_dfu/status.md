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
timestamp: "2026-11-28T07:42:55Z"
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
Lines 326–334 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_transfer](/newchirp_usb_dfu/transfer.md) |
| called_by | [_download](/newchirp_usb_dfu/download.md) |
| called_by | [erase](/newchirp_usb_dfu/erase.md) |
| called_by | [_erase_page](/newchirp_usb_dfu/erase_page.md) |
| called_by | [_upload](/newchirp_usb_dfu/upload.md) |
