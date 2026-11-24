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
timestamp: "2026-11-24T18:50:05Z"
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
Lines 1283–1289 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [repair_uninitialized_extras](/chirp_bridge/repair_uninitialized_extras.md) |
| calls | [external_memory_owner](/chirp_bridge/external_memory_owner.md) |
| called_by | [prepare_upload_channels](/chirp_bridge/prepare_upload_channels.md) |
