---
okf_version: "0.2"
type: Function
title: verify_live_write
description: Read back live memories so a rejected write cannot report success.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/verify_live_write
language: python
---

# verify_live_write

Read back live memories so a rejected write cannot report success.

## Signature

```python
def verify_live_write(live_radio, memories, cleared)
```

## Docstring

Read back live memories so a rejected write cannot report success.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `live_radio` | `—` | `—` |

| `memories` | `—` | `—` |

| `cleared` | `—` | `—` |

## Source
Lines 1186–1203 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [live_memory_matches](/chirp_bridge/live_memory_matches.md) |
| called_by | [headless_live_adapter](/chirp_bridge/headless_live_adapter.md) |
