---
okf_version: "0.2"
type: Function
title: command_version
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-16T10:54:43Z"
concept_id: check_linux_release_abi/command_version
language: python
---

# command_version

## Signature

```python
def command_version(command: list[str], pattern: str) -> str
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `command` | `list[str]` | `—` |

| `pattern` | `str` | `—` |

## Returns
`str`

## Source
Lines 43–55 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| called_by | [require_release_host](/check_linux_release_abi/require_release_host.md) |
