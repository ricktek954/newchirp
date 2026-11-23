---
okf_version: "0.2"
type: Function
title: repair_uninitialized_extras
description: Give extras that failed to load a valid default before writing.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-23T09:51:32Z"
concept_id: chirp_bridge/repair_uninitialized_extras
language: python
---

# repair_uninitialized_extras

Give extras that failed to load a valid default before writing.

## Signature

```python
def repair_uninitialized_extras(memory)
```

## Docstring

Give extras that failed to load a valid default before writing.

A slot written by other software can hold a byte outside a driver's
option table (for example Baofeng 5RM PTT-ID 0xFF). CHIRP then logs
"Failed to load ... out of range", leaves the value unset, and the
driver's set_memory fails with "x not in list", blocking the whole
upload. The stored byte was invalid, so the first valid option is the
safe replacement. Returns the names of repaired settings.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `memory` | `—` | `—` |

## Source
Lines 1181–1231 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [set_memory_with_extras](/chirp_bridge/set_memory_with_extras.md) |
