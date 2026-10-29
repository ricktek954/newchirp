---
okf_version: "0.2"
type: Function
title: set_memory_with_extras
description: Write a channel and persist fields CHIRP stores outside radio memory.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T12:56:26Z"
concept_id: chirp_bridge/set_memory_with_extras
language: python
---

# set_memory_with_extras

Write a channel and persist fields CHIRP stores outside radio memory.

## Signature

```python
def set_memory_with_extras(radio, memory)
```

## Docstring

Write a channel and persist fields CHIRP stores outside radio memory.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `memory` | `—` | `—` |

## Source
Lines 392–397 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [external_memory_owner](/chirp_bridge/external_memory_owner.md) |
| called_by | [main](/chirp_bridge/main.md) |
