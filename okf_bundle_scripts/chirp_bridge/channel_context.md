---
okf_version: "0.2"
type: Function
title: channel_context
description: Return the selected channel owner plus available radio zones.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T12:01:31Z"
concept_id: chirp_bridge/channel_context
language: python
---

# channel_context

Return the selected channel owner plus available radio zones.

## Signature

```python
def channel_context(radio, zone = None)
```

## Docstring

Return the selected channel owner plus available radio zones.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `zone` | `—` | `None` |

## Source
Lines 963–996 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [channel_radio_for](/chirp_bridge/channel_radio_for.md) |
| called_by | [main](/chirp_bridge/main.md) |
