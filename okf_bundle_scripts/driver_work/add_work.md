---
okf_version: "0.2"
type: Function
title: add_work
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-21T13:51:32Z"
concept_id: driver_work/add_work
language: python
---

# add_work

## Signature

```python
def add_work(database, manufacturer, model, kind, title)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `database` | `—` | `—` |

| `manufacturer` | `—` | `—` |

| `model` | `—` | `—` |

| `kind` | `—` | `—` |

| `title` | `—` | `—` |

## Source
Lines 219–297 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [sanitize_reporter](/driver_work/sanitize_reporter.md) |
| calls | [get_or_create_radio](/driver_work/get_or_create_radio.md) |
| calls | [add_event](/driver_work/add_event.md) |
| calls | [new_uid](/driver_work/new_uid.md) |
| called_by | [_execute](/driver_work/execute.md) |
| called_by | [sync_driver_status](/driver_work/sync_driver_status.md) |
