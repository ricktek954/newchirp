---
okf_version: "0.2"
type: Function
title: _prefer_newchirp_drivers
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T11:25:20Z"
concept_id: chirp_bridge/prefer_newchirp_drivers
language: python
---

# _prefer_newchirp_drivers

## Signature

```python
def _prefer_newchirp_drivers(directory)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `directory` | `—` | `—` |

## Source
Lines 1122–1128 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_is_newchirp_driver](/chirp_bridge/is_newchirp_driver.md) |
| called_by | [_finish_loading](/chirp_bridge/finish_loading.md) |
| called_by | [load_chirp](/chirp_bridge/load_chirp.md) |
