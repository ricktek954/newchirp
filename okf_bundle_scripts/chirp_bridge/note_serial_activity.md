---
okf_version: "0.2"
type: Function
title: _note_serial_activity
description: Bytes moved (or progress was made); record what happens next.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-23T09:51:32Z"
concept_id: chirp_bridge/note_serial_activity
language: python
---

# _note_serial_activity

Bytes moved (or progress was made); record what happens next.

## Signature

```python
def _note_serial_activity(state)
```

## Docstring

Bytes moved (or progress was made); record what happens next.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `state` | `—` | `—` |

## Source
Lines 429–432 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [read](/chirp_bridge/read.md) |
| called_by | [start_write_watchdog](/chirp_bridge/start_write_watchdog.md) |
| called_by | [write](/chirp_bridge/write.md) |
