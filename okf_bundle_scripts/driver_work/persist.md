---
okf_version: "0.2"
type: Function
title: persist
description: "Write the cache back to the store, touching only changed files."
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-21T13:51:32Z"
concept_id: driver_work/persist
language: python
---

# persist

Write the cache back to the store, touching only changed files.

## Signature

```python
def persist(database, store, remove_missing = True)
```

## Docstring

Write the cache back to the store, touching only changed files.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `database` | `—` | `—` |

| `store` | `—` | `—` |

| `remove_missing` | `—` | `True` |

## Source
Lines 904–932 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [_store_records](/driver_work/store_records.md) |
| calls | [_dump](/driver_work/dump.md) |
| called_by | [main](/driver_work/main.md) |
| called_by | [migrate_from_sqlite](/driver_work/migrate_from_sqlite.md) |
