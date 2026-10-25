# newchirp_mass_storage

## Classs

- [_LinuxScsiPassthrough](LinuxScsiPassthrough.md) — Linux generic SCSI SG_IO backend.
- [_MacScsiPassthrough](MacScsiPassthrough.md) — Persistent macOS IOKit SCSITask helper process.
- [_WindowsScsiPassthrough](WindowsScsiPassthrough.md) — Windows SCSI_PASS_THROUGH_DIRECT backend.
- [CS750Profile](CS750Profile.md) — Read-only CS750 RAP profile and codeplug transfer.
- [MassStorageError](MassStorageError.md)
- [RapMassStorageRadio](RapMassStorageRadio.md) — Generic command-response session over a raw SCSI transport.
- [ScsiPassthrough](ScsiPassthrough.md) — Reusable factory for platform-specific raw SCSI transport.

## Functions

- [__init__](init.md)
- [_command](command.md)
- [_helper_path](helper_path.md)
- [_read_exact](read_exact.md)
- [close](close.md)
- [list_devices](list_devices.md)
- [parse_rap_packet](parse_rap_packet.md)
- [rap_packet](rap_packet.md)
- [read_codeplug](read_codeplug.md)
- [receive](receive.md)
- [send](send.md)
- [transfer](transfer.md)
