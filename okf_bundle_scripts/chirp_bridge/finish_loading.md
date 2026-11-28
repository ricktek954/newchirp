---
okf_version: "0.2"
type: Function
title: _finish_loading
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T14:18:15Z"
concept_id: chirp_bridge/finish_loading
language: python
---

# _finish_loading

## Signature

```python
def _finish_loading(directory, module_path)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `directory` | `—` | `—` |

| `module_path` | `—` | `—` |

## Source
Lines 1144–1148 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_prefer_newchirp_drivers](/chirp_bridge/prefer_newchirp_drivers.md) |
| calls | [_load_module](/chirp_bridge/load_module.md) |
| called_by | [load_chirp](/chirp_bridge/load_chirp.md) |
