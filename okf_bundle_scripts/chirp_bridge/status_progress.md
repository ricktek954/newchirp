---
okf_version: "0.2"
type: Function
title: status_progress
description: Translate a CHIRP Status message into a structured progress event.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/status_progress
language: python
---

# status_progress

Translate a CHIRP Status message into a structured progress event.

## Signature

```python
def status_progress(status, start = 0.0, end = 1.0)
```

## Docstring

Translate a CHIRP Status message into a structured progress event.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `status` | `—` | `—` |

| `start` | `—` | `0.0` |

| `end` | `—` | `1.0` |

## Source
Lines 424–441 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [emit_progress](/chirp_bridge/emit_progress.md) |
| called_by | [radio_for](/chirp_bridge/radio_for.md) |
