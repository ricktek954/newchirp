---
okf_version: "0.2"
type: Function
title: begin
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T10:03:21Z"
concept_id: chirp_bridge/begin
language: python
---

# begin

## Signature

```python
def begin(self, data)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `data` | `—` | `—` |

## Source
Lines 76–82 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) |
| calls | [_finish_pending](/chirp_bridge/finish_pending.md) |
| calls | [_command_summary](/chirp_bridge/command_summary.md) |
| called_by | [write](/chirp_bridge/write.md) |
