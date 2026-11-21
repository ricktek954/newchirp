---
okf_version: "0.2"
type: Function
title: main
resource: check_linux_release_abi.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:check_linux_release_abi.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-15T13:13:45Z"
concept_id: check_linux_release_abi/main
language: python
---

# main

## Signature

```python
def main() -> int
```

## Returns
`int`

## Source
Lines 183–209 in `check_linux_release_abi.py`

## Relationships

| Type | Target |
|------|--------|
| related | [check_linux_release_abi](/check_linux_release_abi.md) |
| calls | [parse_args](/check_linux_release_abi/parse_args.md) |
| calls | [check_roots](/check_linux_release_abi/check_roots.md) |
| calls | [require_release_host](/check_linux_release_abi/require_release_host.md) |
