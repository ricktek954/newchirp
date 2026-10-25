---
okf_version: "0.2"
type: Function
title: extra_field_doc
description: "Return CHIRP's documentation or a concise fallback for common terms."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T00:30:13Z"
concept_id: chirp_bridge/extra_field_doc
language: python
---

# extra_field_doc

Return CHIRP's documentation or a concise fallback for common terms.

## Signature

```python
def extra_field_doc(setting)
```

## Docstring

Return CHIRP's documentation or a concise fallback for common terms.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `setting` | `—` | `—` |

## Source
Lines 271–280 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [setting_doc](/chirp_bridge/setting_doc.md) |
| called_by | [extra_fields_json](/chirp_bridge/extra_fields_json.md) |
