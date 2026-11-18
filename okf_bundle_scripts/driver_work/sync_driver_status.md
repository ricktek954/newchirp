---
okf_version: "0.2"
type: Function
title: sync_driver_status
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:feature/driver-work-ledger"
  - "git:repo:newchirp"
timestamp: "2026-11-18T08:11:58Z"
concept_id: driver_work/sync_driver_status
language: python
---

# sync_driver_status

## Signature

```python
def sync_driver_status(database, status_file)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `database` | `—` | `—` |

| `status_file` | `—` | `—` |

## Source
Lines 276–360 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [get_or_create_radio](/driver_work/get_or_create_radio.md) |
| calls | [status_from_ledger](/driver_work/status_from_ledger.md) |
| calls | [manufacturer_and_model](/driver_work/manufacturer_and_model.md) |
| calls | [add_work](/driver_work/add_work.md) |
| calls | [add_event](/driver_work/add_event.md) |
| calls | [display_path](/driver_work/display_path.md) |
| called_by | [main](/driver_work/main.md) |
