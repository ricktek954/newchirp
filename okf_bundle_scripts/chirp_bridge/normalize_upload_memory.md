---
okf_version: "0.2"
type: Function
title: normalize_upload_memory
description: Apply safe coercions advertised by CHIRP validation warnings.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: chirp_bridge/normalize_upload_memory
language: python
---

# normalize_upload_memory

Apply safe coercions advertised by CHIRP validation warnings.

## Signature

```python
def normalize_upload_memory(radio, memory)
```

## Docstring

Apply safe coercions advertised by CHIRP validation warnings.

CHIRP distinguishes fatal errors from warnings that describe values the
driver will coerce. NewChirp used to abort on both, which made custom
receive-only GMRS and MURS channels impossible to upload.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `memory` | `—` | `—` |

## Source
Lines 928–967 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [main](/chirp_bridge/main.md) |
