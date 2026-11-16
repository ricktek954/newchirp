---
okf_version: "0.2"
type: Function
title: read_codeplug
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:fix/email-bug-batch"
  - "git:repo:newchirp"
timestamp: "2026-11-16T12:16:24Z"
concept_id: newchirp_mass_storage/read_codeplug
language: python
---

# read_codeplug

## Signature

```python
def read_codeplug(self, progress = None)
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `self` | `—` | `—` |

| `progress` | `—` | `None` |

## Source
Lines 511–579 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [CS750Profile](/newchirp_mass_storage/CS750Profile.md) |
| calls | [transfer](/newchirp_mass_storage/transfer.md) |
| calls | [receive](/newchirp_mass_storage/receive.md) |
| calls | [MassStorageError](/newchirp_mass_storage/MassStorageError.md) |
| calls | [rap_packet](/newchirp_mass_storage/rap_packet.md) |
