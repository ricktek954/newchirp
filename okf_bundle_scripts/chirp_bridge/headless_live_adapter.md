---
okf_version: "0.2"
type: Function
title: headless_live_adapter
description: Give a live radio the file-backed interfaces NewChirp requires.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/headless_live_adapter
language: python
---

# headless_live_adapter

Give a live radio the file-backed interfaces NewChirp requires.

## Signature

```python
def headless_live_adapter(live_radio)
```

## Docstring

Give a live radio the file-backed interfaces NewChirp requires.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `live_radio` | `—` | `—` |

## Source
Lines 1071–1148 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [__init__](/chirp_bridge/init.md) |
| calls | [verify_live_write](/chirp_bridge/verify_live_write.md) |
| called_by | [radio_for](/chirp_bridge/radio_for.md) |
