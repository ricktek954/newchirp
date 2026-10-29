---
okf_version: "0.2"
type: Function
title: received
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T13:11:19Z"
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
Lines 84–89 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) |
| calls | [_finish_pending](/chirp_bridge/finish_pending.md) |
| called_by | [read](/chirp_bridge/read.md) |
