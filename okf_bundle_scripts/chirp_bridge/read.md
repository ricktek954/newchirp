---
okf_version: "0.2"
type: Function
title: read
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T20:05:59Z"
concept_id: chirp_bridge/read
language: python
---

# read

## Signature

```python
def read(self, size = 1)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `size` | `—` | `1` |

## Source
Lines 514–522 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [TracedSerial](/chirp_bridge/TracedSerial.md) |
| calls | [_note_serial_state](/chirp_bridge/note_serial_state.md) |
| calls | [received](/chirp_bridge/received.md) |
| calls | [_note_serial_activity](/chirp_bridge/note_serial_activity.md) |
| called_by | [fetch_repeaterbook_search](/chirp_bridge/fetch_repeaterbook_search.md) |
| called_by | [_load_module](/chirp_bridge/load_module.md) |
