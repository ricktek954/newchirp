---
okf_version: "0.2"
type: Function
title: identity
resource: newchirp_usb_dfu.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_usb_dfu.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-01T11:36:21Z"
concept_id: newchirp_usb_dfu/identity
language: python
---

# identity

## Signature

```python
def identity(self)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Source
Lines 384–386 in `newchirp_usb_dfu.py`

## Relationships

| Type | Target |
|------|--------|
| related | [DfuTransport](/newchirp_usb_dfu/DfuTransport.md) |
| calls | [command](/newchirp_usb_dfu/command.md) |
| calls | [_upload](/newchirp_usb_dfu/upload.md) |
| called_by | [program_mode](/newchirp_usb_dfu/program_mode.md) |
