---
okf_version: "0.2"
type: Function
title: repeaterbook_api_result_to_channel
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-24T19:23:42Z"
concept_id: chirp_bridge/repeaterbook_api_result_to_channel
language: python
---

# repeaterbook_api_result_to_channel

## Signature

```python
def repeaterbook_api_result_to_channel(result, number)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `result` | `—` | `—` |

| `number` | `—` | `—` |

## Source
Lines 2754–2811 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [memory_json](/chirp_bridge/memory_json.md) |
| calls | [repeaterbook_api_tone](/chirp_bridge/repeaterbook_api_tone.md) |
| called_by | [search_repeaterbook](/chirp_bridge/search_repeaterbook.md) |
