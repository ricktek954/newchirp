---
okf_version: "0.2"
type: Function
title: settings_tree_json
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:fix/email-triage-20261030"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:31:36Z"
concept_id: chirp_bridge/settings_tree_json
language: python
---

# settings_tree_json

## Signature

```python
def settings_tree_json(elements, prefix = ())
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `elements` | `—` | `—` |

| `prefix` | `—` | `()` |

## Source
Lines 775–817 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [setting_doc](/chirp_bridge/setting_doc.md) |
| calls | [setting_value_json](/chirp_bridge/setting_value_json.md) |
| called_by | [settings_payload](/chirp_bridge/settings_payload.md) |
