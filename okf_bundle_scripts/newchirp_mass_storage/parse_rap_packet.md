---
okf_version: "0.2"
type: Function
title: parse_rap_packet
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T01:57:36Z"
concept_id: newchirp_mass_storage/parse_rap_packet
language: python
---

# parse_rap_packet

## Signature

```python
def parse_rap_packet(data, expected_size = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `data` | `—` | `—` |

| `expected_size` | `—` | `None` |

## Source
Lines 408–431 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [newchirp_mass_storage](/newchirp_mass_storage.md) |
| calls | [MassStorageError](/newchirp_mass_storage/MassStorageError.md) |
| called_by | [receive](/newchirp_mass_storage/receive.md) |
