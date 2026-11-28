---
okf_version: "0.2"
type: Function
title: manual_send_ready_message
description: Ready cue for a radio that starts the clone from its own key.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T14:18:15Z"
concept_id: chirp_bridge/manual_send_ready_message
language: python
---

# manual_send_ready_message

Ready cue for a radio that starts the clone from its own key.

## Signature

```python
def manual_send_ready_message(key)
```

## Docstring

Ready cue for a radio that starts the clone from its own key.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `key` | `—` | `—` |

## Source
Lines 2442–2446 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [bridge_error_message](/chirp_bridge/bridge_error_message.md) |
| called_by | [emit_read_ready](/chirp_bridge/emit_read_ready.md) |
