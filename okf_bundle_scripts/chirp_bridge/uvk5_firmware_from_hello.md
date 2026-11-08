---
okf_version: "0.2"
type: Function
title: uvk5_firmware_from_hello
description: Decode the UV-K5 hello reply without trusting non-printable bytes.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-08T13:12:45Z"
concept_id: chirp_bridge/uvk5_firmware_from_hello
language: python
---

# uvk5_firmware_from_hello

Decode the UV-K5 hello reply without trusting non-printable bytes.

## Signature

```python
def uvk5_firmware_from_hello(reply)
```

## Docstring

Decode the UV-K5 hello reply without trusting non-printable bytes.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `reply` | `—` | `—` |

## Source
Lines 38–62 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [_finish_pending](/chirp_bridge/finish_pending.md) |
