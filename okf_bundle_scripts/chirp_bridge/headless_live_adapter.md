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
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
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
Lines 1003–1065 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [__init__](/chirp_bridge/init.md) |
| called_by | [radio_for](/chirp_bridge/radio_for.md) |
