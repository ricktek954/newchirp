---
okf_version: "0.2"
type: Function
title: start_write_watchdog
description: Start a daemon thread that ends a stalled radio write.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/start_write_watchdog
language: python
---

# start_write_watchdog

Start a daemon thread that ends a stalled radio write.

## Signature

```python
def start_write_watchdog(seconds = None, exit_fn = None, stream = None)
```

## Docstring

Start a daemon thread that ends a stalled radio write.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `seconds` | `—` | `None` |

| `exit_fn` | `—` | `None` |

| `stream` | `—` | `None` |

## Source
Lines 452–484 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_note_serial_activity](/chirp_bridge/note_serial_activity.md) |
| calls | [write](/chirp_bridge/write.md) |
| calls | [format](/chirp_bridge/format.md) |
| calls | [write_stall_message](/chirp_bridge/write_stall_message.md) |
| called_by | [main](/chirp_bridge/main.md) |
