---
okf_version: "0.2"
type: Function
title: generate
resource: generate_repeater_counties.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:generate_repeater_counties.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-31T09:36:16Z"
concept_id: generate_repeater_counties/generate
language: python
---

# generate

## Signature

```python
def generate(census_csv: bytes, source_sha256: str) -> str
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `census_csv` | `bytes` | `—` |

| `source_sha256` | `str` | `—` |

## Returns
`str`

## Source
Lines 118–154 in `generate_repeater_counties.py`

## Relationships

| Type | Target |
|------|--------|
| related | [generate_repeater_counties](/generate_repeater_counties.md) |
| calls | [_display_name](/generate_repeater_counties/display_name.md) |
| calls | [_dart_string](/generate_repeater_counties/dart_string.md) |
| called_by | [main](/generate_repeater_counties/main.md) |
