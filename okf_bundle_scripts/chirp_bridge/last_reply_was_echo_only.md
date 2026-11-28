---
okf_version: "0.2"
type: Function
title: last_reply_was_echo_only
description: "True when the last exchange returned only the command's echo."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T14:18:15Z"
concept_id: chirp_bridge/last_reply_was_echo_only
language: python
---

# last_reply_was_echo_only

True when the last exchange returned only the command's echo.

## Signature

```python
def last_reply_was_echo_only(self)
```

## Docstring

True when the last exchange returned only the command's echo.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

## Source
Lines 386–391 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) |
| calls | [_finish_pending](/chirp_bridge/finish_pending.md) |
| called_by | [bridge_error_message](/chirp_bridge/bridge_error_message.md) |
