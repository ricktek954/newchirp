---
okf_version: "0.2"
type: Function
title: _alinco_result
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/alinco_result
language: python
---

# _alinco_result

## Signature

```python
def _alinco_result(command_bytes, command, response)
```

## Decorators

- `staticmethod`

## Parameters

| Name | Type | Default |
|------|------|---------|
| `command_bytes` | `—` | `—` |

| `command` | `—` | `—` |

| `response` | `—` | `—` |

## Source
Lines 270–290 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RadioCommunicationTrace](/chirp_bridge/RadioCommunicationTrace.md) |
| called_by | [_finish_pending](/chirp_bridge/finish_pending.md) |
