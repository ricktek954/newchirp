---
okf_version: "0.2"
type: Function
title: display_mapping_name
description: Return a safe display name for a CHIRP bank or zone.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-06T20:09:01Z"
concept_id: chirp_bridge/display_mapping_name
language: python
---

# display_mapping_name

Return a safe display name for a CHIRP bank or zone.

## Signature

```python
def display_mapping_name(value)
```

## Docstring

Return a safe display name for a CHIRP bank or zone.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `value` | `—` | `—` |

## Source
Lines 1536–1541 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [apply_mapping_payload](/chirp_bridge/apply_mapping_payload.md) |
| called_by | [mapping_payload](/chirp_bridge/mapping_payload.md) |
