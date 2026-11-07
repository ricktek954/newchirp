---
okf_version: "0.2"
type: Function
title: coerce_setting_value
description: Match JSON values to labels or native option values.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-07T14:59:39Z"
concept_id: chirp_bridge/coerce_setting_value
language: python
---

# coerce_setting_value

Match JSON values to labels or native option values.

## Signature

```python
def coerce_setting_value(element, value)
```

## Docstring

Match JSON values to labels or native option values.

Some drivers expose numeric RadioSettingValueList options such as
0-8. JSON serializes those as strings, but CHIRP expects the original
integer when applying the value.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `element` | `—` | `—` |

| `value` | `—` | `—` |

## Source
Lines 1056–1070 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| called_by | [apply_json](/chirp_bridge/apply_json.md) |
| called_by | [apply_setting_changes](/chirp_bridge/apply_setting_changes.md) |
