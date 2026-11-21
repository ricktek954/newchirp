---
okf_version: "0.2"
type: Function
title: command
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/command
language: python
---

# command

## Signature

```python
def command(self, command)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `command` | `—` | `—` |

## Source
Lines 372–375 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_download](/newchirp_usb_dfu/download.md) |
| calls | [_wait_idle](/newchirp_usb_dfu/wait_idle.md) |
| called_by | [erase](/newchirp_usb_dfu/erase.md) |
| called_by | [identity](/newchirp_usb_dfu/identity.md) |
| called_by | [program_mode](/newchirp_usb_dfu/program_mode.md) |
| called_by | [set_address](/newchirp_usb_dfu/set_address.md) |
