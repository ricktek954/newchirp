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
timestamp: "2026-11-22T14:14:29Z"
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
Lines 2756–2848 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [fetch_repeaterbook_search](/chirp_bridge/fetch_repeaterbook_search.md) |
| calls | [resolve_us_zip_code](/chirp_bridge/resolve_us_zip_code.md) |
| calls | [normalize_repeaterbook_query](/chirp_bridge/normalize_repeaterbook_query.md) |
| calls | [repeaterbook_api_result_to_channel](/chirp_bridge/repeaterbook_api_result_to_channel.md) |
| called_by | [main](/chirp_bridge/main.md) |
