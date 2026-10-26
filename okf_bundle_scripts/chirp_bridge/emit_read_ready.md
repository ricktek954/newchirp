---
okf_version: "0.2"
type: Function
title: emit_read_ready
description: Tell the user when a manual PTT-triggered clone read can begin.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-26T06:06:15Z"
concept_id: chirp_bridge/emit_read_ready
language: python
---

# emit_read_ready

Tell the user when a manual PTT-triggered clone read can begin.

## Signature

```python
def emit_read_ready(radio)
```

## Docstring

Tell the user when a manual PTT-triggered clone read can begin.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

## Source
Lines 644–650 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [emit_progress](/chirp_bridge/emit_progress.md) |
| called_by | [main](/chirp_bridge/main.md) |
