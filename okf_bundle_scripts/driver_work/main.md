---
okf_version: "0.2"
type: Function
title: main
resource: driver_work.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:driver_work.py"
  - "git:branch:feature/driver-work-ledger"
  - "git:repo:newchirp"
timestamp: "2026-11-18T08:11:58Z"
concept_id: driver_work/main
language: python
---

# main

## Signature

```python
def main()
```

## Source
Lines 583–792 in `driver_work.py`

## Relationships

| Type | Target |
|------|--------|
| related | [driver_work](/driver_work.md) |
| calls | [parse_args](/check_linux_release_abi/parse_args.md) |
| calls | [connect](/driver_work/connect.md) |
| calls | [find_work_id](/driver_work/find_work_id.md) |
| calls | [sync_driver_status](/driver_work/sync_driver_status.md) |
| calls | [query_work](/driver_work/query_work.md) |
| calls | [show_work](/driver_work/show_work.md) |
| calls | [add_work](/driver_work/add_work.md) |
| calls | [export_markdown](/driver_work/export_markdown.md) |
| calls | [add_event](/driver_work/add_event.md) |
| calls | [print_work_rows](/driver_work/print_work_rows.md) |
| calls | [today](/driver_work/today.md) |
