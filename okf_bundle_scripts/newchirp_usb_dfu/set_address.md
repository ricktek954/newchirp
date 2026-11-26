---
okf_version: "0.2"
type: Function
title: set_address
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-26T06:35:35Z"
concept_id: newchirp_usb_dfu/set_address
language: python
---

# set_address

## Signature

```python
def set_address(self, address)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `address` | `—` | `—` |

## Source
Lines 392–396 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [command](/newchirp_usb_dfu/command.md) |
| called_by | [erase](/newchirp_usb_dfu/erase.md) |
| called_by | [program_mode](/newchirp_usb_dfu/program_mode.md) |
