---
okf_version: "0.2"
type: Function
title: read
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/read
language: python
---

# read

## Signature

```python
def read(self, address, length)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `address` | `—` | `—` |

| `length` | `—` | `—` |

## Source
Lines 403–410 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_upload](/newchirp_usb_dfu/upload.md) |
