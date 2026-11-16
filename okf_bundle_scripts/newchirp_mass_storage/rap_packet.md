---
okf_version: "0.2"
type: Function
title: rap_packet
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Function"
  - "module:newchirp_mass_storage.py"
  - "git:branch:fix/email-bug-batch"
  - "git:repo:newchirp"
timestamp: "2026-11-16T12:16:24Z"
concept_id: newchirp_mass_storage/rap_packet
language: python
---

# rap_packet

## Signature

```python
def rap_packet(command, payload = b'')
```

## Parameters

| Name | Type | Default |
|------|------|---------|
| `command` | `—` | `—` |

| `payload` | `—` | `b''` |

## Source
Lines 416–427 in `newchirp_mass_storage.py`

## Relationships

| Type | Target |
|------|--------|
| related | [newchirp_mass_storage](/newchirp_mass_storage.md) |
| called_by | [_command](/newchirp_mass_storage/command.md) |
| called_by | [read_codeplug](/newchirp_mass_storage/read_codeplug.md) |
| called_by | [send](/newchirp_mass_storage/send.md) |
