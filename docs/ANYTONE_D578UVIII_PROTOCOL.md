# AnyTone AT-D578UVIII Plus protocol notes

Last updated: 2026-11-01

## Status

Experimental read/write support for conventional channels and zones is
implemented in `drivers/newchirp_anytone_d578uviii.py`.

No physical AT-D578UVIII Plus has yet been used to validate the complete read,
controlled edit, upload, and read-back sequence.

## Evidence

- Official AnyTone package:
  `AT-D578UV_PLUS_PC_SOFTWARE.zip`
- Package SHA-256:
  `c0785deeee48de742b1832b7c97263bfc96f0e996de8aef7eaac759124d338a4`
- Extracted CPS 1.21 executable:
  `D578UV V1.21 CPS/D578UV_Setup_1.21.exe`
- Extracted application SHA-256:
  `47737a24a496efdfe4924419ad81ab91317abcf30618801b7a4b631801b6146b`
- REA 6.5.0 with Ghidra 12.1.4 recovered the VB6 native application inventory,
  the `D578UV2` model string, and the CPS read/write command paths.
- QDMR commit `fb9c96af53f646c0706fa360209b2e0e6cd79a08` supplied the
  maintained D578UV I/II channel, zone, and transport field layouts.
- Public `NI5I/Anytone-AT-D578UVIII-Plus-Codeplug` commit
  `65ec2c0700fdaae027536aeaa90f92bf116386ee` supplied a CPS 1.20 D578UVIII
  Plus codeplug and matching channel/zone CSV exports for field comparison.

## Serial transport

The programming interface is USB serial at 115200 baud.

Session setup:

```text
PC  -> PROGRAM
Radio -> QX 06
PC  -> 02
Radio -> I model[7] bands version[6] 06
```

Accepted model identifiers are `D578UV`, `D578UV2`, `D578UV3`, and
`D578UVIII`.

Read request:

```text
52 ADDR[4 big endian] 10
```

Read response:

```text
57 ADDR[4] 10 DATA[16] CHECKSUM 06
```

The checksum is the low eight bits of the sum of the address, length, and data
bytes.

Write request:

```text
57 ADDR[4 big endian] 10 DATA[16] CHECKSUM 06
```

The radio answers each write with one `06` byte.

Session teardown:

```text
PC -> END
```

## Codeplug locations

| Region | Radio address |
| --- | ---: |
| Channel bitmap | `0x024C1500` |
| Channel records | `0x00800000`, four 0x40000 banks |
| Zone bitmap | `0x024C1300` |
| Zone channel lists | `0x01000000`, 0x200 per zone |
| Zone names | `0x02540000`, 0x20 per zone |

Channel records are 64 bytes. Zone channel lists are arrays of 16-bit
little-endian channel indexes terminated by `0xFFFF`.

## Implemented fields

- RX frequency and TX offset, BCD encoded in big-endian byte order
- FM/NFM/DMR mode and bandwidth
- Low/mid/high/turbo power
- 16-character channel name
- CTCSS and DCS encode/decode fields
- DMR color code and time slot
- TX contact index and RX group-list index
- Receive-only and talkaround flags
- 250 named zones with ordered channel membership

Radio-wide settings, contacts, RX-group members, scan lists, optional
signalling, APRS, encryption, and call lists are not edited. The upload writes
only the conventional channel and zone regions.

## Remaining validation

1. Read a physical D578UVIII Plus and compare the channel/zone display with the
   official CPS.
2. Confirm that the radio reports `D578UV2`, `D578UV3`, or another accepted
   model identifier.
3. Make one controlled channel and zone edit, upload, read back, and verify the
   result on the radio before declaring hardware-tested support.
