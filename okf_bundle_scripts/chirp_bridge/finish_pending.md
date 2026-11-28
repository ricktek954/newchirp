---
okf_version: "0.2"
type: Function
title: _finish_pending
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T14:18:15Z"
concept_id: chirp_bridge/finish_pending
language: python
---

# _finish_pending

## Signature

```python
def _finish_pending(self)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Source
Lines 292–384 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) |
| calls | [_alinco_result](/chirp_bridge/alinco_result.md) |
| calls | [uvk5_firmware_from_hello](/chirp_bridge/uvk5_firmware_from_hello.md) |
| called_by | [begin](/chirp_bridge/begin.md) |
| called_by | [format](/chirp_bridge/format.md) |
| called_by | [last_reply_was_echo_only](/chirp_bridge/last_reply_was_echo_only.md) |
| called_by | [received](/chirp_bridge/received.md) |
