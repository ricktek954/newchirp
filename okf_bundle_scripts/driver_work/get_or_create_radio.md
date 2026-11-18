---
okf_version: "0.2"
type: Function
title: get_or_create_radio
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:feature/driver-work-ledger"
  - "git:repo:newchirp"
timestamp: "2026-11-18T08:11:58Z"
concept_id: driver_work/get_or_create_radio
language: python
---

# get_or_create_radio

## Signature

```python
def get_or_create_radio(database, manufacturer, model)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `database` | `—` | `—` |

| `manufacturer` | `—` | `—` |

| `model` | `—` | `—` |

## Source
Lines 101–151 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| called_by | [add_work](/driver_work/add_work.md) |
| called_by | [sync_driver_status](/driver_work/sync_driver_status.md) |
