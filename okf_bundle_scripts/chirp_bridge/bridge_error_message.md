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
timestamp: "2026-10-25T01:54:14Z"
concept_id: chirp_bridge/bridge_error_message
language: python
---

# bridge_error_message

Add safe, command-specific recovery guidance to bridge failures.

## Signature

```python
def bridge_error_message(exc, command = None, model = None)
```

## Docstring

Add safe, command-specific recovery guidance to bridge failures.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `exc` | `—` | `—` |

| `command` | `—` | `None` |

| `model` | `—` | `None` |

## Source
Lines 44–57 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [main](/chirp_bridge/main.md) |
