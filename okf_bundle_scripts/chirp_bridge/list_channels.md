---
okf_version: "0.2"
type: Function
title: list_channels
description: "Decode every channel, one at a time."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T10:43:55Z"
concept_id: chirp_bridge/list_channels
language: python
---

# list_channels

Decode every channel, one at a time.

## Signature

```python
def list_channels(radio, progress = None)
```

## Docstring

Decode every channel, one at a time.

A driver that cannot decode one slot (a value outside its tables, a
record written by other software) used to stop the whole channel list
with "could not decode the channel map" (2026-11-26 IC-E90 report,
mailbox UID 1017). Each slot is now decoded on its own: failures are
returned separately with the raw record so the app can say which
channels were left untouched, and the bug report carries the details.
Upload already refuses a slot that cannot be loaded, so those channels
are protected from writes. If no slot decodes at all, the decoder
itself is wrong and the first error is raised as before.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `progress` | `—` | `None` |

## Source
Lines 1284–1327 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [memory_with_extras](/chirp_bridge/memory_with_extras.md) |
| calls | [memory_json](/chirp_bridge/memory_json.md) |
| called_by | [main](/chirp_bridge/main.md) |
