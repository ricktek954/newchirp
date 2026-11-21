---
okf_version: "0.2"
type: Function
title: migrate_from_sqlite
description: One-time import of a schema-1 database into the text store.
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-21T13:54:42Z"
concept_id: driver_work/migrate_from_sqlite
language: python
---

# migrate_from_sqlite

One-time import of a schema-1 database into the text store.

## Signature

```python
def migrate_from_sqlite(legacy_path, store)
```

## Docstring

One-time import of a schema-1 database into the text store.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `legacy_path` | `—` | `—` |

| `store` | `—` | `—` |

## Source
Lines 935–953 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [connect](/driver_work/connect.md) |
| calls | [persist](/driver_work/persist.md) |
| called_by | [main](/driver_work/main.md) |
