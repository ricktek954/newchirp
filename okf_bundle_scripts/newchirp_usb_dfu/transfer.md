---
okf_version: "0.2"
type: Function
title: _transfer
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/transfer
language: python
---

# _transfer

## Signature

```python
def _transfer(self, request_type, request, value, data_or_length, timeout = 2000)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `request_type` | `—` | `—` |

| `request` | `—` | `—` |

| `value` | `—` | `—` |

| `data_or_length` | `—` | `—` |

| `timeout` | `—` | `2000` |

## Source
Lines 291–320 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
| calls | [_error_text](/newchirp_usb_dfu/error_text.md) |
| called_by | [_download](/newchirp_usb_dfu/download.md) |
| called_by | [_status](/newchirp_usb_dfu/status.md) |
| called_by | [_upload](/newchirp_usb_dfu/upload.md) |
| called_by | [_wait_idle](/newchirp_usb_dfu/wait_idle.md) |
