---
okf_version: "0.2"
type: Function
title: live_channel_context
description: Choose a live-radio subdevice without probing every memory slot.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/live_channel_context
language: python
---

# live_channel_context

Choose a live-radio subdevice without probing every memory slot.

## Signature

```python
def live_channel_context(radio, zone = None)
```

## Docstring

Choose a live-radio subdevice without probing every memory slot.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `zone` | `—` | `None` |

## Source
Lines 1206–1229 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [radio_for](/chirp_bridge/radio_for.md) |
