---
okf_version: "0.2"
type: Function
title: live_memory_matches
description: Compare fields that every live radio must retain after a write.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/live_memory_matches
language: python
---

# live_memory_matches

Compare fields that every live radio must retain after a write.

## Signature

```python
def live_memory_matches(expected, actual)
```

## Docstring

Compare fields that every live radio must retain after a write.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `expected` | `—` | `—` |

| `actual` | `—` | `—` |

## Source
Lines 1151–1183 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [verify_live_write](/chirp_bridge/verify_live_write.md) |
