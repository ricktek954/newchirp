---
okf_version: "0.2"
type: Function
title: _read_store
description: "Load every record, refusing files that are not clean JSON."
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-19T12:39:24Z"
concept_id: driver_work/read_store
language: python
---

# _read_store

Load every record, refusing files that are not clean JSON.

## Signature

```python
def _read_store(store)
```

## Docstring

Load every record, refusing files that are not clean JSON.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `store` | `—` | `—` |

## Source
Lines 683–702 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [StoreError](/driver_work/StoreError.md) |
| calls | [display_path](/driver_work/display_path.md) |
| called_by | [rebuild_cache](/driver_work/rebuild_cache.md) |
