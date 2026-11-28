---
okf_version: "0.2"
type: Function
title: erase
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T07:42:55Z"
concept_id: newchirp_usb_dfu/erase
language: python
---

# erase

## Signature

```python
def erase(self, start, size)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `start` | `—` | `—` |

| `size` | `—` | `—` |

## Source
Lines 407–428 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_status](/newchirp_usb_dfu/status.md) |
| calls | [_wait_idle](/newchirp_usb_dfu/wait_idle.md) |
| calls | [command](/newchirp_usb_dfu/command.md) |
| calls | [_erase_page](/newchirp_usb_dfu/erase_page.md) |
| calls | [set_address](/newchirp_usb_dfu/set_address.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
