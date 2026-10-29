---
okf_version: "0.2"
type: Function
title: external_memory_owner
description: Return the object that owns metadata for a radio or channel subdevice.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T11:04:49Z"
concept_id: chirp_bridge/external_memory_owner
language: python
---

# external_memory_owner

Return the object that owns metadata for a radio or channel subdevice.

## Signature

```python
def external_memory_owner(radio)
```

## Docstring

Return the object that owns metadata for a radio or channel subdevice.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

## Source
Lines 347–361 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [erase_memory_with_extras](/chirp_bridge/erase_memory_with_extras.md) |
| called_by | [memory_with_extras](/chirp_bridge/memory_with_extras.md) |
| called_by | [set_memory_with_extras](/chirp_bridge/set_memory_with_extras.md) |
