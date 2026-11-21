---
okf_version: "0.2"
type: Function
title: main
resource: build_macos_dmg.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:build_macos_dmg.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-23T10:57:07Z"
concept_id: build_macos_dmg/main
language: python
---

# main

## Signature

```python
def main() -> None
```

## Returns
`None`

## Source
Lines 80–147 in `build_macos_dmg.py`

## Relationships

| Type | Target |
|------|--------|
| related | [build_macos_dmg](/build_macos_dmg.md) |
| calls | [parse_args](/check_linux_release_abi/parse_args.md) |
| calls | [build_background](/build_macos_dmg/build_background.md) |
| calls | [project_version](/build_macos_dmg/project_version.md) |
