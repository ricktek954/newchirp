---
okf_version: "0.2"
type: Function
title: _execute
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-21T13:51:32Z"
concept_id: driver_work/execute
language: python
---

# _execute

## Signature

```python
def _execute(args, database)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `args` | `—` | `—` |

| `database` | `—` | `—` |

## Source
Lines 1070–1207 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [find_work_id](/driver_work/find_work_id.md) |
| calls | [sync_driver_status](/driver_work/sync_driver_status.md) |
| calls | [query_work](/driver_work/query_work.md) |
| calls | [show_work](/driver_work/show_work.md) |
| calls | [add_work](/driver_work/add_work.md) |
| calls | [export_markdown](/driver_work/export_markdown.md) |
| calls | [add_event](/driver_work/add_event.md) |
| calls | [sanitize_tester](/driver_work/sanitize_tester.md) |
| calls | [print_work_rows](/driver_work/print_work_rows.md) |
| calls | [work_ref](/driver_work/work_ref.md) |
| calls | [today](/driver_work/today.md) |
| called_by | [main](/driver_work/main.md) |
