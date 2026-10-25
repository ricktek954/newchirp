---
okf_version: "0.2"
type: Function
title: repeaterbook_item_to_channel
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T00:30:13Z"
concept_id: chirp_bridge/repeaterbook_item_to_channel
language: python
---

# repeaterbook_item_to_channel

## Signature

```python
def repeaterbook_item_to_channel(item, number)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `item` | `—` | `—` |

| `number` | `—` | `—` |

## Source
Lines 752–802 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [memory_json](/chirp_bridge/memory_json.md) |
| calls | [repeaterbook_tone](/chirp_bridge/repeaterbook_tone.md) |
| called_by | [search_repeaterbook](/chirp_bridge/search_repeaterbook.md) |
