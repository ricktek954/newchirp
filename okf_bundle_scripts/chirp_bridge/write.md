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
timestamp: "2026-11-21T10:48:44Z"
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
Lines 377–379 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [TracedSerial](/chirp_bridge/TracedSerial.md) |
| calls | [begin](/chirp_bridge/begin.md) |
| called_by | [emit_progress](/chirp_bridge/emit_progress.md) |
