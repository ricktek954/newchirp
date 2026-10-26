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
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-26T06:06:15Z"
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
Lines 817–825 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [search_repeaterbook](/chirp_bridge/search_repeaterbook.md) |
