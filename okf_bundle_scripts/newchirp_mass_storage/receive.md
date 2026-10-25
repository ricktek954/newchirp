---
okf_version: "0.2"
type: Function
title: receive
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T01:57:36Z"
concept_id: newchirp_mass_storage/receive
language: python
---

# receive

## Signature

```python
def receive(self, expected_command, expected_size)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `expected_command` | `—` | `—` |

| `expected_size` | `—` | `—` |

## Source
Lines 448–456 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [RapMassStorageRadio](/newchirp_mass_storage/RapMassStorageRadio.md) |
| calls | [transfer](/newchirp_mass_storage/transfer.md) |
| calls | [parse_rap_packet](/newchirp_mass_storage/parse_rap_packet.md) |
| calls | [MassStorageError](/newchirp_mass_storage/MassStorageError.md) |
| called_by | [_command](/newchirp_mass_storage/command.md) |
| called_by | [read_codeplug](/newchirp_mass_storage/read_codeplug.md) |
