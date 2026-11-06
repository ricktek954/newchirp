---
okf_version: "0.2"
type: Function
title: mapping_payload
description: "Describe CHIRP's bank/zone models for an image or channel owner."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-06T10:47:08Z"
concept_id: chirp_bridge/mapping_payload
language: python
---

# mapping_payload

Describe CHIRP's bank/zone models for an image or channel owner.

## Signature

```python
def mapping_payload(radio)
```

## Docstring

Describe CHIRP's bank/zone models for an image or channel owner.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

## Source
Lines 1527–1565 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_mapping_index_key](/chirp_bridge/mapping_index_key.md) |
| calls | [display_mapping_name](/chirp_bridge/display_mapping_name.md) |
| called_by | [apply_mapping_payload](/chirp_bridge/apply_mapping_payload.md) |
| called_by | [main](/chirp_bridge/main.md) |
