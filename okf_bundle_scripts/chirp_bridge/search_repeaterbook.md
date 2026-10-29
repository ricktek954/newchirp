---
okf_version: "0.2"
type: Function
title: search_repeaterbook
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T10:03:21Z"
concept_id: chirp_bridge/search_repeaterbook
language: python
---

# search_repeaterbook

## Signature

```python
def search_repeaterbook(country, state, service = 'amateur', query = '', latitude = None, longitude = None, distance = None, fm_only = False, open_only = False, limit = 200)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `country` | `—` | `—` |

| `state` | `—` | `—` |

| `service` | `—` | `'amateur'` |

| `query` | `—` | `''` |

| `latitude` | `—` | `None` |

| `longitude` | `—` | `None` |

| `distance` | `—` | `None` |

| `fm_only` | `—` | `False` |

| `open_only` | `—` | `False` |

| `limit` | `—` | `200` |

## Source
Lines 1073–1181 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [normalize_repeaterbook_query](/chirp_bridge/normalize_repeaterbook_query.md) |
| calls | [fetch_repeaterbook_data](/chirp_bridge/fetch_repeaterbook_data.md) |
| calls | [repeaterbook_item_to_channel](/chirp_bridge/repeaterbook_item_to_channel.md) |
| called_by | [main](/chirp_bridge/main.md) |
