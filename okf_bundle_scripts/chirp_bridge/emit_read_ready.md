---
okf_version: "0.2"
type: Function
title: emit_read_ready
description: Tell the user when a manually triggered clone read can begin.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-26T13:50:32Z"
concept_id: chirp_bridge/emit_read_ready
language: python
---

# emit_read_ready

Tell the user when a manually triggered clone read can begin.

## Signature

```python
def emit_read_ready(radio)
```

## Docstring

Tell the user when a manually triggered clone read can begin.

The bridge opens the port only after the user confirms the prompt, so a
radio key pressed before this message sends the image to a closed port.
The radio then waits for an ACK that never comes (2026-11-21 FT-1D
report: ID block lost, then "No response from radio").

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

## Source
Lines 2410–2428 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [manual_send_key](/chirp_bridge/manual_send_key.md) |
| calls | [emit_progress](/chirp_bridge/emit_progress.md) |
| calls | [manual_send_ready_message](/chirp_bridge/manual_send_ready_message.md) |
| called_by | [main](/chirp_bridge/main.md) |
