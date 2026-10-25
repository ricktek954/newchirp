---
okf_version: "0.2"
type: Function
title: send
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T01:57:36Z"
concept_id: newchirp_mass_storage/send
language: python
---

# send

## Signature

```python
def send(self, command, payload = b'')
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `command` | `—` | `—` |

| `payload` | `—` | `b''` |

## Source
Lines 440–446 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RapMassStorageRadio](/newchirp_mass_storage/RapMassStorageRadio.md) |
| calls | [rap_packet](/newchirp_mass_storage/rap_packet.md) |
| calls | [transfer](/newchirp_mass_storage/transfer.md) |
