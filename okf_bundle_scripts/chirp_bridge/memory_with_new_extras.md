---
okf_version: "0.2"
type: Function
title: memory_with_new_extras
description: "Reload a slot after giving it the incoming channel's basic fields."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-28T14:18:15Z"
concept_id: chirp_bridge/memory_with_new_extras
language: python
---

# memory_with_new_extras

Reload a slot after giving it the incoming channel's basic fields.

## Signature

```python
def memory_with_new_extras(radio, location, item)
```

## Docstring

Reload a slot after giving it the incoming channel's basic fields.

A channel's extra fields describe the channel that was in the slot. When
inserting or moving shifts a channel into a slot that held a different
kind (an analog channel onto a DMR one, for example), some drivers offer
different choices for the same field, so the incoming value is rejected
("Allow TX is not valid for this setting", 2026-11-21 DM-32UV report,
mailbox INBOX:863). Writing the basic fields first lets the driver switch
the slot's kind; the reloaded memory then lists the matching choices.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `location` | `—` | `—` |

| `item` | `—` | `—` |

## Source
Lines 1904–1918 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [apply_json](/chirp_bridge/apply_json.md) |
| called_by | [prepare_upload_channels](/chirp_bridge/prepare_upload_channels.md) |
