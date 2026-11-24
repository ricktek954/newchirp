---
okf_version: "0.2"
type: Function
title: _note_serial_state
description: Record what the bridge is doing without counting it as activity.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/note_serial_state
language: python
---

# _note_serial_state

Record what the bridge is doing without counting it as activity.

## Signature

```python
def _note_serial_state(state)
```

## Docstring

Record what the bridge is doing without counting it as activity.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `state` | `—` | `—` |

## Source
Lines 435–437 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [read](/chirp_bridge/read.md) |
| called_by | [write](/chirp_bridge/write.md) |
