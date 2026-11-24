---
okf_version: "0.2"
type: Function
title: write
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/write
language: python
---

# write

## Signature

```python
def write(self, data)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `data` | `—` | `—` |

## Source
Lines 503–512 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [TracedSerial](/chirp_bridge/TracedSerial.md) |
| calls | [begin](/chirp_bridge/begin.md) |
| calls | [_note_serial_state](/chirp_bridge/note_serial_state.md) |
| calls | [_note_serial_activity](/chirp_bridge/note_serial_activity.md) |
| called_by | [emit_progress](/chirp_bridge/emit_progress.md) |
| called_by | [start_write_watchdog](/chirp_bridge/start_write_watchdog.md) |
