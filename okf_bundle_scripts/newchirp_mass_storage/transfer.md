---
okf_version: "0.2"
type: Function
title: transfer
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:fix/email-bug-batch"
  - "git:repo:newchirp"
timestamp: "2026-11-16T12:16:24Z"
concept_id: newchirp_mass_storage/transfer
language: python
---

# transfer

## Signature

```python
def transfer(self, cdb, size, write_data = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `cdb` | `—` | `—` |

| `size` | `—` | `—` |

| `write_data` | `—` | `None` |

## Source
Lines 409–410 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [ScsiPassthrough](/newchirp_mass_storage/ScsiPassthrough.md) |
| called_by | [_command](/newchirp_mass_storage/command.md) |
| called_by | [read_codeplug](/newchirp_mass_storage/read_codeplug.md) |
| called_by | [receive](/newchirp_mass_storage/receive.md) |
| called_by | [send](/newchirp_mass_storage/send.md) |
