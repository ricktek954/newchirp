---
okf_version: "0.2"
type: Function
title: fetch_repeaterbook_search
description: "Query NewChirp's relay without exposing RepeaterBook credentials."
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-11-22T10:24:24Z"
concept_id: chirp_bridge/fetch_repeaterbook_search
language: python
---

# fetch_repeaterbook_search

Query NewChirp's relay without exposing RepeaterBook credentials.

## Signature

```python
def fetch_repeaterbook_search(country, state, service, query = '', latitude = None, longitude = None, distance = None, fm_only = False, open_only = False, limit = 200)
```

## Docstring

Query NewChirp's relay without exposing RepeaterBook credentials.

## Parameters

| Name | Type | Default |
|------|------|---------|
| `country` | `—` | `—` |

| `state` | `—` | `—` |

| `service` | `—` | `—` |

| `query` | `—` | `''` |

| `latitude` | `—` | `None` |

| `longitude` | `—` | `None` |

| `distance` | `—` | `None` |

| `fm_only` | `—` | `False` |

| `open_only` | `—` | `False` |

| `limit` | `—` | `200` |

## Source
Lines 2366–2434 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [read](/chirp_bridge/read.md) |
| called_by | [search_repeaterbook](/chirp_bridge/search_repeaterbook.md) |
