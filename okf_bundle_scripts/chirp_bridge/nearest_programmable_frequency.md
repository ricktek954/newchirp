---
okf_version: "0.2"
type: Function
title: nearest_programmable_frequency
description: Return the closest frequency representable by one of the steps.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-06T10:47:08Z"
concept_id: chirp_bridge/nearest_programmable_frequency
language: python
---

# nearest_programmable_frequency

Return the closest frequency representable by one of the steps.

## Signature

```python
def nearest_programmable_frequency(frequency_hz, steps_khz)
```

## Docstring

Return the closest frequency representable by one of the steps.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `frequency_hz` | `—` | `—` |

| `steps_khz` | `—` | `—` |

## Source
Lines 1100–1115 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [channel_validation_message](/chirp_bridge/channel_validation_message.md) |
