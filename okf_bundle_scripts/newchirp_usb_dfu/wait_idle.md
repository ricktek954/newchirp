---
okf_version: "0.2"
type: Function
title: _wait_idle
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T07:42:55Z"
concept_id: newchirp_usb_dfu/wait_idle
language: python
---

# _wait_idle

## Signature

```python
def _wait_idle(self, timeout = 10)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `timeout` | `—` | `10` |

## Source
Lines 336–361 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [DfuError](/newchirp_usb_dfu/DfuError.md) |
| calls | [_transfer](/newchirp_usb_dfu/transfer.md) |
| called_by | [command](/newchirp_usb_dfu/command.md) |
| called_by | [erase](/newchirp_usb_dfu/erase.md) |
| called_by | [_erase_page](/newchirp_usb_dfu/erase_page.md) |
| called_by | [program_mode](/newchirp_usb_dfu/program_mode.md) |
| called_by | [write](/newchirp_usb_dfu/write.md) |
