---
okf_version: "0.2"
type: Function
title: apply_json
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-26T06:38:24Z"
concept_id: chirp_bridge/apply_json
language: python
---

# apply_json

## Signature

```python
def apply_json(radio, mem, item)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `mem` | `—` | `—` |

| `item` | `—` | `—` |

## Source
Lines 1693–1745 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [coerce_setting_value](/chirp_bridge/coerce_setting_value.md) |
| called_by | [memory_with_new_extras](/chirp_bridge/memory_with_new_extras.md) |
| called_by | [prepare_upload_channels](/chirp_bridge/prepare_upload_channels.md) |
