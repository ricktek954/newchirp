---
okf_version: "0.2"
type: Function
title: add_event
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:feature/driver-work-ledger"
  - "git:repo:newchirp"
timestamp: "2026-11-18T08:11:58Z"
concept_id: driver_work/add_event
language: python
---

# add_event

## Signature

```python
def add_event(database, work_id, event_type, summary)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `database` | `—` | `—` |

| `work_id` | `—` | `—` |

| `event_type` | `—` | `—` |

| `summary` | `—` | `—` |

## Source
Lines 154–181 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [today](/driver_work/today.md) |
| called_by | [add_work](/driver_work/add_work.md) |
| called_by | [main](/driver_work/main.md) |
| called_by | [sync_driver_status](/driver_work/sync_driver_status.md) |
