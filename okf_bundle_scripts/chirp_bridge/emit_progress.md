---
okf_version: "0.2"
type: Function
title: emit_progress
description: Send structured transfer progress without touching the JSON stdout.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: chirp_bridge/emit_progress
language: python
---

# emit_progress

Send structured transfer progress without touching the JSON stdout.

## Signature

```python
def emit_progress(label, fraction = None)
```

## Docstring

Send structured transfer progress without touching the JSON stdout.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `label` | `—` | `—` |

| `fraction` | `—` | `None` |

## Source
Lines 232–244 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [write](/chirp_bridge/write.md) |
| called_by | [emit_read_ready](/chirp_bridge/emit_read_ready.md) |
| called_by | [fetch_repeaterbook_data](/chirp_bridge/fetch_repeaterbook_data.md) |
| called_by | [main](/chirp_bridge/main.md) |
| called_by | [status_progress](/chirp_bridge/status_progress.md) |
