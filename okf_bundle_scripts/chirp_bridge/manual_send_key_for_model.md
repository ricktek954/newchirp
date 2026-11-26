---
okf_version: "0.2"
type: Function
title: manual_send_key_for_model
description: "The send key from a registered driver's read prompt, if loaded."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-26T13:50:32Z"
concept_id: chirp_bridge/manual_send_key_for_model
language: python
---

# manual_send_key_for_model

The send key from a registered driver's read prompt, if loaded.

## Signature

```python
def manual_send_key_for_model(model)
```

## Docstring

The send key from a registered driver's read prompt, if loaded.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `model` | `—` | `—` |

## Source
Lines 1014–1025 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [manual_send_key](/chirp_bridge/manual_send_key.md) |
| called_by | [bridge_error_message](/chirp_bridge/bridge_error_message.md) |
