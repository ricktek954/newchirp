---
okf_version: "0.2"
type: Function
title: check_roots
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-16T10:54:43Z"
concept_id: check_linux_release_abi/check_roots
language: python
---

# check_roots

## Signature

```python
def check_roots(roots: list[Path]) -> tuple[list[str], tuple[int, ...] | None]
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `roots` | `list[Path]` | `—` |

## Returns
`tuple[list[str], tuple[int, ...] | None]`

## Source
Lines 136–159 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| calls | [elf_files](/check_linux_release_abi/elf_files.md) |
| calls | [required_glibc_versions](/check_linux_release_abi/required_glibc_versions.md) |
| calls | [version_tuple](/check_linux_release_abi/version_tuple.md) |
| called_by | [main](/check_linux_release_abi/main.md) |
