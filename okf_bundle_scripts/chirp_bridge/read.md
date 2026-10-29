---
okf_version: "0.2"
type: Function
title: read
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T13:11:19Z"
concept_id: chirp_bridge/read
language: python
---

# read

## Signature

```python
def read(self, size = 1)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `size` | `—` | `1` |

## Source
Lines 183–186 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [TracedSerial](/chirp_bridge/TracedSerial.md) |
| calls | [received](/chirp_bridge/received.md) |
| called_by | [fetch_repeaterbook_data](/chirp_bridge/fetch_repeaterbook_data.md) |
