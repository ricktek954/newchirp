---
okf_version: "0.2"
type: Function
title: erase_memory_with_extras
description: Erase a channel and remove its metadata-backed fields.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T10:03:21Z"
concept_id: chirp_bridge/erase_memory_with_extras
language: python
---

# erase_memory_with_extras

Erase a channel and remove its metadata-backed fields.

## Signature

```python
def erase_memory_with_extras(radio, number)
```

## Docstring

Erase a channel and remove its metadata-backed fields.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `number` | `—` | `—` |

## Source
Lines 370–375 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [external_memory_owner](/chirp_bridge/external_memory_owner.md) |
| called_by | [main](/chirp_bridge/main.md) |
