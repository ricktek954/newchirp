---
okf_version: "0.2"
type: Function
title: _read_source
resource: generate_repeater_counties.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_repeater_counties.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-31T09:36:16Z"
concept_id: generate_repeater_counties/read_source
language: python
---

# _read_source

## Signature

```python
def _read_source(path: Path | None) -> tuple[bytes, bytes]
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `path` | `Path | None` | `—` |

## Returns
`tuple[bytes, bytes]`

## Source
Lines 100–115 in `generate_repeater_counties.py`

## Relationships

| Type | Target |
|------|--------|
| related | [generate_repeater_counties](/generate_repeater_counties.md) |
| calls | [read](/chirp_bridge/read.md) |
| called_by | [main](/generate_repeater_counties/main.md) |
