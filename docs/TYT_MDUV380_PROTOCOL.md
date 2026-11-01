# TYT MD-UV380 protocol notes

Last updated: 2026-11-01

## Status

Experimental read/write support for conventional channels and zones is
implemented in `drivers/newchirp_tyt_mduv380.py`.

No physical MD-UV380 has yet been used to validate the complete read,
controlled edit, upload, and read-back sequence.

## Evidence

- Official CPS package:
  `CPS MD-UV380 Setup v2.42.zip`
- Package SHA-256:
  `92104a20b8c2d896ee67975ebdf0cbf7785d48e2abecde2a957484c236deba33`
- Extracted main CPS executable SHA-256:
  `62aa2101f75368ba61082fe3ceb999aa20573897f7b86a1ab616e47b390612bc`
- REA 6.5.0 with Ghidra 12.1.4 recovered the `PROGRAM_READDATA`,
  `PROGRAM_WRITEDATA`, `STDFU_*`, channel-list, and BCD frequency routines.
- editcp commit `64fc5857ef0f33c1363a6e5d138964c9c21f663c` supplied the
  MD-UV380 codeplug layout.
- QDMR commit `fb9c96af53f646c0706fa360209b2e0e6cd79a08` supplied the
  maintained DfuSe transport and UV390 field implementation.

## USB transport

The radio exposes ST DfuSe with USB VID:PID `0483:DF11`.

The NewChirp bridge lists the interface as a USB DFU pseudo-port and uses
`scripts/newchirp_usb_dfu.py`, a small libusb control-transfer transport.

Core operations:

- DFU upload request for reading a 1024-byte block
- DFU download request for writing a 1024-byte block
- DfuSe command `0x21` to set the base address
- DfuSe command `0x41` to erase a 64 KiB page
- TYT command `0x91 0x01` to enter programming mode
- TYT command `0xA2 0x01` followed by a 64-byte upload for identification
- TYT command `0x91 0x05` to reboot after the transfer

Accepted identity text is `MD-UV380`.

## Codeplug segments

| Segment | Radio address | Size |
| --- | ---: | ---: |
| Settings, zones, scan lists | `0x002000` | `0x03E000` |
| Channels and contacts | `0x110000` | `0x090000` |

Conventional channel records start at `0x110000`, are 64 bytes each, and
provide 3000 slots.

Zone records start at `0x0149E0`. Each zone has a 64-byte base record and a
224-byte extension. Zone names and the first 16 channel indexes are stored in
the base record; the remaining A-list channels and all B-list channels are
stored in the extension.

## Implemented fields

- RX and TX frequencies stored as eight-digit little-endian BCD
- FM/NFM/DMR mode and bandwidth
- Low/medium/high power
- 16-character UTF-16LE channel name
- CTCSS and DCS encode/decode fields
- DMR color code and time slot
- TX contact index and RX group-list index
- Receive-only and talkaround flags
- 250 named zones and ordered membership

Contacts, RX-group members, scan lists, optional signalling, APRS, encryption,
buttons, and radio-wide settings are preserved but not edited.

## Remaining validation

1. Read a physical MD-UV380 and verify the detected identity.
2. Compare channel and zone names/frequencies with CPS 2.42.
3. Make one controlled channel and zone edit, upload, read back, and verify the
   result on the radio before declaring hardware-tested support.
4. Validate the bundled libusb runtime on macOS, Windows, and Linux release
   builds.
