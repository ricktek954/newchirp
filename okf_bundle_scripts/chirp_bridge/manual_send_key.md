---
okf_version: "0.2"
type: Function
title: manual_send_key
description: "Return the control a clone prompt says to press after OK, if any."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T13:55:48Z"
concept_id: chirp_bridge/manual_send_key
language: python
---

# manual_send_key

Return the control a clone prompt says to press after OK, if any.

## Signature

```python
def manual_send_key(pre_download)
```

## Docstring

Return the control a clone prompt says to press after OK, if any.

Bracketed and quoted names are returned as written; a named key or knob
becomes e.g. "the DIAL knob". A step that says to press an unnamed key
gives "the send key".

## Parameters

| Name | Type | Default |
|------|------|---------|
| `pre_download` | `—` | `—` |

## Source
Lines 2207–2225 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [emit_read_ready](/chirp_bridge/emit_read_ready.md) |
| called_by | [manual_send_key_for_model](/chirp_bridge/manual_send_key_for_model.md) |
