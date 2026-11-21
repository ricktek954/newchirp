---
okf_version: "0.2"
type: Function
title: connect
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-21T13:51:32Z"
concept_id: driver_work/connect
language: python
---

# connect

## Signature

```python
def connect(path, create = True, store = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `path` | `—` | `—` |

| `create` | `—` | `True` |

| `store` | `—` | `None` |

## Source
Lines 109–123 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [rebuild_cache](/driver_work/rebuild_cache.md) |
| called_by | [main](/check_private_data/main.md) |
| called_by | [main](/driver_work/main.md) |
| called_by | [migrate_from_sqlite](/driver_work/migrate_from_sqlite.md) |
| called_by | [rebuild_cache](/driver_work/rebuild_cache.md) |
