---
okf_version: "0.2"
type: Function
title: elf_files
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-15T13:13:45Z"
concept_id: check_linux_release_abi/elf_files
language: python
---

# elf_files

## Signature

```python
def elf_files(roots: Iterable[Path]) -> Iterable[Path]
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `roots` | `Iterable[Path]` | `—` |

## Returns
`Iterable[Path]`

## Source
Lines 105–119 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| called_by | [check_roots](/check_linux_release_abi/check_roots.md) |
