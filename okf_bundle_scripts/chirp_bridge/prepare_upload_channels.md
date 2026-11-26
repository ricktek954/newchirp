---
okf_version: "0.2"
type: Function
title: prepare_upload_channels
description: Validate and apply imported channels without touching invalid slots.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-26T13:50:32Z"
concept_id: chirp_bridge/prepare_upload_channels
language: python
---

# prepare_upload_channels

Validate and apply imported channels without touching invalid slots.

## Signature

```python
def prepare_upload_channels(radio, items, progress_callback = None)
```

## Docstring

Validate and apply imported channels without touching invalid slots.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `items` | `—` | `—` |

| `progress_callback` | `—` | `None` |

## Source
Lines 1884–2016 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [normalize_upload_memory](/chirp_bridge/normalize_upload_memory.md) |
| calls | [apply_json](/chirp_bridge/apply_json.md) |
| calls | [memory_with_new_extras](/chirp_bridge/memory_with_new_extras.md) |
| calls | [set_memory_with_extras](/chirp_bridge/set_memory_with_extras.md) |
| calls | [channel_validation_message](/chirp_bridge/channel_validation_message.md) |
| called_by | [main](/chirp_bridge/main.md) |
