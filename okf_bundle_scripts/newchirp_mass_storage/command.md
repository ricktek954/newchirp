---
okf_version: "0.2"
type: Function
title: _command
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T01:57:36Z"
concept_id: newchirp_mass_storage/command
language: python
---

# _command

## Signature

```python
def _command(self, command, payload = b'', response_command = None, response_size = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `command` | `—` | `—` |

| `payload` | `—` | `b''` |

| `response_command` | `—` | `None` |

| `response_size` | `—` | `None` |

## Source
Lines 471–487 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [CS750Profile](/newchirp_mass_storage/CS750Profile.md) |
| calls | [transfer](/newchirp_mass_storage/transfer.md) |
| calls | [receive](/newchirp_mass_storage/receive.md) |
| calls | [rap_packet](/newchirp_mass_storage/rap_packet.md) |
