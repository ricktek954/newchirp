---
okf_version: "0.2"
type: Function
title: program_mode
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/program_mode
language: python
---

# program_mode

## Signature

```python
def program_mode(self)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Source
Lines 377–382 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [_wait_idle](/newchirp_usb_dfu/wait_idle.md) |
| calls | [command](/newchirp_usb_dfu/command.md) |
| calls | [identity](/newchirp_usb_dfu/identity.md) |
| calls | [set_address](/newchirp_usb_dfu/set_address.md) |
