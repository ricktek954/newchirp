---
okf_version: "0.2"
type: Function
title: received
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-06T10:47:08Z"
concept_id: chirp_bridge/received
language: python
---

# received

## Signature

```python
def received(self, data)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `data` | `—` | `—` |

## Source
Lines 117–122 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) |
| calls | [_finish_pending](/chirp_bridge/finish_pending.md) |
| called_by | [read](/chirp_bridge/read.md) |
| called_by | [readline](/chirp_bridge/readline.md) |
| called_by | [readlines](/chirp_bridge/readlines.md) |
