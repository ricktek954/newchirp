---
okf_version: "0.2"
type: Function
title: normalize_repeaterbook_query
description: "Treat location words like \"Broward County\" as a county name."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-06T10:47:08Z"
concept_id: chirp_bridge/normalize_repeaterbook_query
language: python
---

# normalize_repeaterbook_query

Treat location words like "Broward County" as a county name.

## Signature

```python
def normalize_repeaterbook_query(query)
```

## Docstring

Treat location words like "Broward County" as a county name.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `query` | `—` | `—` |

## Source
Lines 1875–1883 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [search_repeaterbook](/chirp_bridge/search_repeaterbook.md) |
