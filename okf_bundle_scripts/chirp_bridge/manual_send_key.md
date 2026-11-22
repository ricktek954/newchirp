---
okf_version: "0.2"
type: Function
title: manual_send_key
description: "Return the key a clone prompt says to press after OK, if any."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-22T10:24:24Z"
concept_id: chirp_bridge/manual_send_key
language: python
---

# manual_send_key

Return the key a clone prompt says to press after OK, if any.

## Signature

```python
def manual_send_key(pre_download)
```

## Docstring

Return the key a clone prompt says to press after OK, if any.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `pre_download` | `—` | `—` |

## Source
Lines 2046–2050 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [emit_read_ready](/chirp_bridge/emit_read_ready.md) |
| called_by | [manual_send_key_for_model](/chirp_bridge/manual_send_key_for_model.md) |
