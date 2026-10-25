---
okf_version: "0.2"
type: Function
title: load_chirp
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T00:30:13Z"
concept_id: chirp_bridge/load_chirp
language: python
---

# load_chirp

## Signature

```python
def load_chirp(source, vendor, newchirp_driver_dir = None, module_path = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `source` | `—` | `—` |

| `vendor` | `—` | `—` |

| `newchirp_driver_dir` | `—` | `None` |

| `module_path` | `—` | `None` |

## Source
Lines 107–146 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_load_module](/chirp_bridge/load_module.md) |
| called_by | [main](/chirp_bridge/main.md) |
