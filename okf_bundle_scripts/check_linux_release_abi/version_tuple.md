---
okf_version: "0.2"
type: Function
title: version_tuple
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:release/1.0.55"
  - "git:repo:newchirp"
timestamp: "2026-11-15T12:28:35Z"
concept_id: check_linux_release_abi/version_tuple
language: python
---

# version_tuple

## Signature

```python
def version_tuple(value: str, width: int = 3) -> tuple[int, ...]
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `value` | `str` | `—` |

| `width` | `int` | `3` |

## Returns
`tuple[int, ...]`

## Source
Lines 27–29 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| called_by | [check_roots](/check_linux_release_abi/check_roots.md) |
| called_by | [require_release_host](/check_linux_release_abi/require_release_host.md) |
