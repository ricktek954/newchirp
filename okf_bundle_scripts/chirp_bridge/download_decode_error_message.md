---
okf_version: "0.2"
type: Function
title: download_decode_error_message
description: Explain a post-download map failure without losing the saved image.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-31T16:29:22Z"
concept_id: chirp_bridge/download_decode_error_message
language: python
---

# download_decode_error_message

Explain a post-download map failure without losing the saved image.

## Signature

```python
def download_decode_error_message(model, image, exc)
```

## Docstring

Explain a post-download map failure without losing the saved image.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `model` | `—` | `—` |

| `image` | `—` | `—` |

| `exc` | `—` | `—` |

## Source
Lines 1342–1352 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [main](/chirp_bridge/main.md) |
