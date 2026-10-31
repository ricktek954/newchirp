---
okf_version: "0.2"
type: Function
title: memory_with_extras
description: "Load a channel plus CHIRP's metadata-backed fields such as comments."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/memory_with_extras
language: python
---

# memory_with_extras

Load a channel plus CHIRP's metadata-backed fields such as comments.

## Signature

```python
def memory_with_extras(radio, number)
```

## Docstring

Load a channel plus CHIRP's metadata-backed fields such as comments.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `number` | `—` | `—` |

## Source
Lines 585–591 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [external_memory_owner](/chirp_bridge/external_memory_owner.md) |
| called_by | [main](/chirp_bridge/main.md) |
