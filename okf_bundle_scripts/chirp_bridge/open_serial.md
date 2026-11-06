---
okf_version: "0.2"
type: Function
title: open_serial
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:HEAD"
  - "git:repo:newchirp"
timestamp: "2026-11-06T10:47:08Z"
concept_id: chirp_bridge/open_serial
language: python
---

# open_serial

## Signature

```python
def open_serial(radio_class, port)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio_class` | `—` | `—` |

| `port` | `—` | `—` |

## Source
Lines 1182–1213 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [serial_read_timeout](/chirp_bridge/serial_read_timeout.md) |
| called_by | [radio_for](/chirp_bridge/radio_for.md) |
