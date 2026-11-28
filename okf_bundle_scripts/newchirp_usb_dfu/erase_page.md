---
okf_version: "0.2"
type: Function
title: _erase_page
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T07:42:55Z"
concept_id: newchirp_usb_dfu/erase_page
language: python
---

# _erase_page

## Signature

```python
def _erase_page(self, address)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `address` | `—` | `—` |

## Source
Lines 430–456 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_transfer](/newchirp_usb_dfu/transfer.md) |
| calls | [_status](/newchirp_usb_dfu/status.md) |
| calls | [_wait_idle](/newchirp_usb_dfu/wait_idle.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
| called_by | [erase](/newchirp_usb_dfu/erase.md) |
