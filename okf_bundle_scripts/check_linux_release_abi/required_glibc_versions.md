---
okf_version: "0.2"
type: Function
title: required_glibc_versions
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-16T10:54:43Z"
concept_id: check_linux_release_abi/required_glibc_versions
language: python
---

# required_glibc_versions

## Signature

```python
def required_glibc_versions(path: Path) -> tuple[set[str], bool]
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `path` | `Path` | `—` |

## Returns
`tuple[set[str], bool]`

## Source
Lines 122–133 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| called_by | [check_roots](/check_linux_release_abi/check_roots.md) |
