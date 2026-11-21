---
okf_version: "0.2"
type: Function
title: build_background
resource: build_macos_dmg.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:build_macos_dmg.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-23T10:57:07Z"
concept_id: build_macos_dmg/build_background
language: python
---

# build_background

## Signature

```python
def build_background(destination: Path) -> None
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `destination` | `Path` | `—` |

## Returns
`None`

## Source
Lines 24–77 in `build_macos_dmg.py`

## Relationships

| Type | Target |
|------|--------|
| related | [build_macos_dmg](/build_macos_dmg.md) |
| calls | [line](/generate_gmrs_frs_pdf/line.md) |
| calls | [text](/generate_gmrs_frs_pdf/text.md) |
| called_by | [main](/build_macos_dmg/main.md) |
