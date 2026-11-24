---
okf_version: "0.2"
type: Function
title: reported_model_choice
description: "Return (vendor, model) when a driver's ID check names a sibling model."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/reported_model_choice
language: python
---

# reported_model_choice

Return (vendor, model) when a driver's ID check names a sibling model.

## Signature

```python
def reported_model_choice(message, model)
```

## Docstring

Return (vendor, model) when a driver's ID check names a sibling model.

CHIRP drivers raise "Radio reports X (not Y)" when the radio answers with
another model's ID. Only suggest X when it is a registered driver from the
same vendor, so an unrecognized or garbled ID keeps the original error.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `message` | `—` | `—` |

| `model` | `—` | `—` |

## Source
Lines 560–578 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [bridge_error_message](/chirp_bridge/bridge_error_message.md) |
