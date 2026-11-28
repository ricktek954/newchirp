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
timestamp: "2026-11-28T11:25:20Z"
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
Lines 1151–1234 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_finish_loading](/chirp_bridge/finish_loading.md) |
| calls | [_prefer_newchirp_drivers](/chirp_bridge/prefer_newchirp_drivers.md) |
| calls | [_allow_driver_specific_modes](/chirp_bridge/allow_driver_specific_modes.md) |
| calls | [_upstream_driver_modules](/chirp_bridge/upstream_driver_modules.md) |
| called_by | [main](/check_bundle_drivers/main.md) |
