---
okf_version: "0.2"
type: Function
title: channel_radio_for
description: Return the radio object that owns channel memories.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: chirp_bridge/channel_radio_for
language: python
---

# channel_radio_for

Return the radio object that owns channel memories.

## Signature

```python
def channel_radio_for(radio, zone = None)
```

## Docstring

Return the radio object that owns channel memories.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `zone` | `—` | `None` |

## Source
Lines 1210–1212 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [channel_context](/chirp_bridge/channel_context.md) |
