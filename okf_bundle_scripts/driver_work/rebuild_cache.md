---
okf_version: "0.2"
type: Function
title: rebuild_cache
description: Build a fresh SQLite cache from the text store (atomic replace).
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-21T13:54:42Z"
concept_id: driver_work/rebuild_cache
language: python
---

# rebuild_cache

Build a fresh SQLite cache from the text store (atomic replace).

## Signature

```python
def rebuild_cache(store, cache_path)
```

## Docstring

Build a fresh SQLite cache from the text store (atomic replace).

## Parameters

| Name | Type | Default |
|------|------|---------|
| `store` | `—` | `—` |

| `cache_path` | `—` | `—` |

## Source
Lines 709–843 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [_read_store](/driver_work/read_store.md) |
| calls | [connect](/driver_work/connect.md) |
| calls | [StoreError](/driver_work/StoreError.md) |
| calls | [display_path](/driver_work/display_path.md) |
| called_by | [connect](/driver_work/connect.md) |
| called_by | [main](/driver_work/main.md) |
