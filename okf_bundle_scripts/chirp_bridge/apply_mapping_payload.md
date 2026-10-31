---
okf_version: "0.2"
type: Function
title: apply_mapping_payload
description: Apply bank/zone names and memberships to an already loaded image.
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-30T23:58:44Z"
concept_id: chirp_bridge/apply_mapping_payload
language: python
---

# apply_mapping_payload

Apply bank/zone names and memberships to an already loaded image.

## Signature

```python
def apply_mapping_payload(radio, requested_models, active_locations)
```

## Docstring

Apply bank/zone names and memberships to an already loaded image.

The client sends the complete state for each model. Unchanged models are
left alone so writing channels cannot accidentally reorder unrelated
banks. Removing memberships happens before additions, which also supports
one-bank-per-channel models when a channel moves between banks.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `radio` | `—` | `—` |

| `requested_models` | `—` | `—` |

| `active_locations` | `—` | `—` |

## Source
Lines 1412–1552 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [_mapping_models_by_index](/chirp_bridge/mapping_models_by_index.md) |
| calls | [mapping_payload](/chirp_bridge/mapping_payload.md) |
| calls | [_mapping_entries_by_index](/chirp_bridge/mapping_entries_by_index.md) |
| calls | [_mapping_index_key](/chirp_bridge/mapping_index_key.md) |
| called_by | [main](/chirp_bridge/main.md) |
