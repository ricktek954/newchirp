# Icom IC-41S protocol and image notes

Evidence source: Icom **CS-41S Cloning Software Rev. 1.3**. The package help
identifies the supported transceiver as the **Icom IC-41S UHF C.R.S.
TRANSCEIVER**. No IC-41W model string or other transceiver model was found in
the extracted CPS files.

## Artifact identity

- CPS ZIP SHA-256:
  `9d93ade74ca671a1a037bb39fc5f040cbe1e24ab1447d19747e0230aef23502f`
- Main executable `EX2928E.exe` SHA-256:
  `1b47aae5605044dfb45b937ee4326f0ec108306bf106575ac17ea7e29528d0d5`
- Initial image `EX2928EA.ics` SHA-256:
  `a876e5097d265326dba5ca6ca38023dd91e4ecbac9cf2158cd31cd65553a18f3`
- Supplied sample `IC-41S_80ch_18032011_2_M.icf` SHA-256:
  `eb3dd05b5e4add4bcfeeddb6de8e86f1e2c6cdb2785469b71750891d608ddb9a`

The proprietary CPS executable and sample image are evidence only and are not
committed to this repository.

## Clone transport

REA/Ghidra recovered the following legacy Icom clone frames from the CPS
executable:

```text
FEFE EE EF E0 %04X %04X FD
FEFE EE EF E2 %04X %04X FD
FEFE EE EF E3 %04X %04X FD
FEFE EE EF E4
FEFE EE EF E5 49 63 6F 6D 20 49 6E 63 2E
```

`E4` data uses `%04X%02X` address and length fields, hexadecimal byte text,
and an 8-bit checksum. This is the legacy `IcomCloneModeRadio._raw_frames =
False` path already implemented by CHIRP's `icf` module.

The CPS serial settings are 9600 8N1 for normal cloning and 38400 8N1 for high
speed. NewChirp initially uses normal speed only. The initial image reports
model header `29280000`, map revision `1`, 16-byte ICF records, and a decoded
image size of `0x7D80` bytes.

## Image layout

- Serialized variable data starts at `0x0178`.
- When channel data is present, a 200-byte zone section precedes the channel
  table, so channels begin at `0x0240`.
- An empty CPS image omits the zone section and stores its placeholder channel
  at `0x0178`.
- The global settings block follows the channel records. Its stable marker is
  `50 0F 01 02 46 45 43 10`.
- Each channel record is 22 bytes:

| Offset | Size | Meaning |
| --- | --- | --- |
| `0x00` | 4 | RX frequency in big-endian Hz |
| `0x04` | 4 | TX frequency in big-endian Hz |
| `0x08` | 2 | RX CTCSS/DCS value, unknown encoding |
| `0x0A` | 2 | TX CTCSS/DCS value, unknown encoding |
| `0x0C` | 8 | Channel label, space padded |
| `0x14` | 2 | Packed channel flags |

The sample proves flag `0x40` marks an active channel and flag `0x20` requests
the stored TX frequency (split/duplex). Other flag bits, the tone encoding,
radio settings, scan-list membership, and zone-record fields remain
provisional and are preserved without modification.

The supplied sample contains 93 channel records. The CPS help specifies 450
to 520 MHz private-channel operation, 2.5 and 3.125 kHz steps, eight zones,
and eight-character private-channel names.

## Validation limits

No physical IC-41S image or transfer capture was available. The driver is
therefore experimental and read/write enabled with backup-first warnings.
Hardware validation must compare a full unedited download with CS-41S, then
change one simplex and one split channel and verify both with a readback.
