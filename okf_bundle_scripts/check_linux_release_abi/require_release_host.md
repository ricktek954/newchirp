---
okf_version: "0.2"
type: Function
title: require_release_host
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-16T10:54:43Z"
concept_id: check_linux_release_abi/require_release_host
language: python
---

# require_release_host

## Signature

```python
def require_release_host() -> list[str]
```

## Returns
`list[str]`

## Source
Lines 58–102 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| calls | [read_os_release](/check_linux_release_abi/read_os_release.md) |
| calls | [command_version](/check_linux_release_abi/command_version.md) |
| calls | [version_tuple](/check_linux_release_abi/version_tuple.md) |
| called_by | [main](/check_linux_release_abi/main.md) |
