---
okf_version: "0.2"
type: Function
title: fetch_repeaterbook_data
description: "Fetch RepeaterBook's CHIRP-compatible compressed database."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T00:30:13Z"
concept_id: chirp_bridge/fetch_repeaterbook_data
language: python
---

# fetch_repeaterbook_data

Fetch RepeaterBook's CHIRP-compatible compressed database.

## Signature

```python
def fetch_repeaterbook_data(service, country, state)
```

## Docstring

Fetch RepeaterBook's CHIRP-compatible compressed database.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `service` | `—` | `—` |

| `country` | `—` | `—` |

| `state` | `—` | `—` |

## Source
Lines 699–738 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [repeaterbook_resource_name](/chirp_bridge/repeaterbook_resource_name.md) |
| calls | [repeaterbook_cache_path](/chirp_bridge/repeaterbook_cache_path.md) |
| calls | [emit_progress](/chirp_bridge/emit_progress.md) |
| called_by | [search_repeaterbook](/chirp_bridge/search_repeaterbook.md) |
