---
okf_version: "0.2"
type: Function
title: channel_validation_message
description: "Add a frequency suggestion to CHIRP's unsupported-step error."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T10:57:35Z"
concept_id: chirp_bridge/channel_validation_message
language: python
---

# channel_validation_message

Add a frequency suggestion to CHIRP's unsupported-step error.

## Signature

```python
def channel_validation_message(memory, errors, steps_khz)
```

## Docstring

Add a frequency suggestion to CHIRP's unsupported-step error.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `memory` | `—` | `—` |

| `errors` | `—` | `—` |

| `steps_khz` | `—` | `—` |

## Source
Lines 719–729 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [nearest_programmable_frequency](/chirp_bridge/nearest_programmable_frequency.md) |
| called_by | [main](/chirp_bridge/main.md) |
