---
okf_version: "0.2"
type: Function
title: _store_records
description: "Yield (relative path, record) for every row in the cache."
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-19T12:39:24Z"
concept_id: driver_work/store_records
language: python
---

# _store_records

Yield (relative path, record) for every row in the cache.

## Signature

```python
def _store_records(database)
```

## Docstring

Yield (relative path, record) for every row in the cache.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `database` | `—` | `—` |

## Source
Lines 842–897 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [_slug](/driver_work/slug.md) |
| calls | [_item_file_key](/driver_work/item_file_key.md) |
| calls | [_digest](/driver_work/digest.md) |
| called_by | [persist](/driver_work/persist.md) |
