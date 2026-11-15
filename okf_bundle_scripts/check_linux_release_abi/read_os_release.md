---
okf_version: "0.2"
type: Function
title: read_os_release
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:release/1.0.55"
  - "git:repo:newchirp"
timestamp: "2026-11-15T12:28:35Z"
concept_id: check_linux_release_abi/read_os_release
language: python
---

# read_os_release

## Signature

```python
def read_os_release(path: Path = Path('/etc/os-release')) -> dict[str, str]
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `path` | `Path` | `Path('/etc/os-release')` |

## Returns
`dict[str, str]`

## Source
Lines 32–40 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| called_by | [require_release_host](/check_linux_release_abi/require_release_host.md) |
