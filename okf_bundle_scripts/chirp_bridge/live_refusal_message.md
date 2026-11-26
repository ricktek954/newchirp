---
okf_version: "0.2"
type: Function
title: live_refusal_message
description: Say which channel a live radio refused and how far the write got.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-26T13:50:32Z"
concept_id: chirp_bridge/live_refusal_message
language: python
---

# live_refusal_message

Say which channel a live radio refused and how far the write got.

## Signature

```python
def live_refusal_message(exc, memory, start, end)
```

## Docstring

Say which channel a live radio refused and how far the write got.

2026-11-24 TH-D7G report: "Radio refused 191" after a CSV from another
model; the slot's values and the stopping point were not shown.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `exc` | `—` | `—` |

| `memory` | `—` | `—` |

| `start` | `—` | `—` |

| `end` | `—` | `—` |

## Source
Lines 2068–2107 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [headless_live_adapter](/chirp_bridge/headless_live_adapter.md) |
