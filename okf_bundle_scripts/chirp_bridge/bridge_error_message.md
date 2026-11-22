---
okf_version: "0.2"
type: Function
title: bridge_error_message
description: "Add safe, command-specific recovery guidance to bridge failures."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-22T10:24:24Z"
concept_id: chirp_bridge/bridge_error_message
language: python
---

# bridge_error_message

Add safe, command-specific recovery guidance to bridge failures.

## Signature

```python
def bridge_error_message(exc, command = None, model = None, port = None)
```

## Docstring

Add safe, command-specific recovery guidance to bridge failures.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `exc` | `—` | `—` |

| `command` | `—` | `None` |

| `model` | `—` | `None` |

| `port` | `—` | `None` |

## Source
Lines 475–799 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [last_reply_was_echo_only](/chirp_bridge/last_reply_was_echo_only.md) |
| calls | [format](/chirp_bridge/format.md) |
| calls | [manual_send_key_for_model](/chirp_bridge/manual_send_key_for_model.md) |
| calls | [manual_send_ready_message](/chirp_bridge/manual_send_ready_message.md) |
| called_by | [main](/chirp_bridge/main.md) |
