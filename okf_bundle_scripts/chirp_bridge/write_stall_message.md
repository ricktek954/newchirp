---
okf_version: "0.2"
type: Function
title: write_stall_message
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-25T09:30:41Z"
concept_id: chirp_bridge/write_stall_message
language: python
---

# write_stall_message

## Signature

```python
def write_stall_message(seconds, state)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `seconds` | `—` | `—` |

| `state` | `—` | `—` |

## Source
Lines 440–449 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [start_write_watchdog](/chirp_bridge/start_write_watchdog.md) |
