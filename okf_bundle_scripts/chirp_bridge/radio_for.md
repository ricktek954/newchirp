---
okf_version: "0.2"
type: Function
title: radio_for
resource: chirp_bridge.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:chirp_bridge.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-29T13:11:19Z"
concept_id: chirp_bridge/radio_for
language: python
---

# radio_for

## Signature

```python
def radio_for(directory, model, port, progress_range = (0.0, 1.0), image = None, detect_serial = True, channel_zone = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `directory` | `—` | `—` |

| `model` | `—` | `—` |

| `port` | `—` | `—` |

| `progress_range` | `—` | `(0.0, 1.0)` |

| `image` | `—` | `None` |

| `detect_serial` | `—` | `True` |

| `channel_zone` | `—` | `None` |

## Source
Lines 893–951 in `chirp_bridge.py`

## Relationships

| Type | Target |
|------|--------|
| related | [chirp_bridge](/chirp_bridge.md) |
| calls | [ScsiPassthrough](/newchirp_mass_storage/ScsiPassthrough.md) |
| calls | [TracedSerial](/chirp_bridge/TracedSerial.md) |
| calls | [open_serial](/chirp_bridge/open_serial.md) |
| calls | [status_progress](/chirp_bridge/status_progress.md) |
| calls | [close](/chirp_bridge/close.md) |
| calls | [headless_live_adapter](/chirp_bridge/headless_live_adapter.md) |
| calls | [live_channel_context](/chirp_bridge/live_channel_context.md) |
| called_by | [main](/chirp_bridge/main.md) |
