---
okf_version: "0.2"
type: Module
title: newchirp_mass_storage
description: Reusable raw SCSI transport and RAP framing for NewChirp radios.
resource: newchirp_mass_storage.py
tags:
  - "lang:python"
  - "type:Module"
  - "module:newchirp_mass_storage.py"
  - "git:branch:main"
  - "git:repo:newchirp"
timestamp: "2026-10-25T01:57:36Z"
concept_id: newchirp_mass_storage
language: python
---

# newchirp_mass_storage

Reusable raw SCSI transport and RAP framing for NewChirp radios.

## Docstring

Reusable raw SCSI transport and RAP framing for NewChirp radios.

The CS750 is the first radio profile to use this module. Radio drivers should
keep model-specific command and image knowledge outside the transport layer so
other CPS families using SCSI mass-storage passthrough can reuse it.

## Relationships

| Type | Target |
|------|--------|
| related | [MassStorageError](/newchirp_mass_storage/MassStorageError.md) |
| related | [_helper_path](/newchirp_mass_storage/helper_path.md) |
| related | [_MacScsiPassthrough](/newchirp_mass_storage/MacScsiPassthrough.md) |
| related | [_WindowsScsiPassthrough](/newchirp_mass_storage/WindowsScsiPassthrough.md) |
| related | [_LinuxScsiPassthrough](/newchirp_mass_storage/LinuxScsiPassthrough.md) |
| related | [ScsiPassthrough](/newchirp_mass_storage/ScsiPassthrough.md) |
| related | [rap_packet](/newchirp_mass_storage/rap_packet.md) |
| related | [parse_rap_packet](/newchirp_mass_storage/parse_rap_packet.md) |
| related | [RapMassStorageRadio](/newchirp_mass_storage/RapMassStorageRadio.md) |
| related | [CS750Profile](/newchirp_mass_storage/CS750Profile.md) |
| related | [list_devices](/newchirp_mass_storage/list_devices.md) |
