# Radtel RT-950 Pro protocol notes

Last updated: 2026-11-09

The RT-950 Pro is a separate NewChirp model. It shares the RT-950/BT-9000
handshake and 32-byte channel encoding, but its CPS layout contains larger
settings segments and an additional `0x54/0x55` block.

## Evidence

### OEM CPS

- Package: `RT-950_EnCPS_Setup_v1.3.0.rar`
- Executable: `BT-9000_CPS.exe`
- Executable SHA-256:
  `605054c46ec17520b0f79b78585c3be431a6dcb95164dc638985455e813d7a1e`
- Resource assembly SHA-256:
  `3c17d6cf42ffda4fa32dfdcf845e8a328dff627987ab88d25e3a12b0b68298a7`

The OEM CPS establishes the shared handshake, randomized `SEND`
authentication, rotating symbol substitution, block framing, channel field
layout, tone encoding, and frequency encoding documented in
`RT950_PROTOCOL.md`.

### RT-950 Pro reference driver

- File: `radtel_rt950pro.py`
- SHA-256:
  `359e673eeafa8ccee20d222276cc4d57194f2a826a443a4cb4b710a81297f2e5`
- Origin: community CHIRP development driver by Nathan G. Barguss, MIT
  licensed
- Evidence level: static reference, not OEM ground truth

This driver supplied the larger Pro read map and confirms that the radio uses
the same transport family as the base RT-950. NewChirp's implementation does
not import or bundle the reference file.

## Transport

- 115200 baud, 8N1
- RTS and DTR asserted
- Hardware and XON/XOFF flow control disabled
- Initial `PROGRAMBT9000U` ACK window: 3.0 seconds
- `F` response: 16 bytes
- `M` response: 12-byte model code
- `SEND`: 25-byte randomized authentication request followed by ACK `0x06`
- Read request: `<command> <address:u16be> 0x80`
- Read response: echoed address plus 128 encrypted payload bytes
- End command: ASCII `E`

The first ACK timeout was increased from the base driver's 1.5 seconds because
the physical Pro reaches Program mode but returned no bytes within the shorter
window.

## Pro read map

| Command | Radio address | Length | Image address | Content |
| --- | ---: | ---: | ---: | --- |
| `0x52` | `0x0000` | `0x7800` | `0x0000` | 960 channel records |
| `0x52` | `0x8000` | `0x0100` | `0x8000` | VFO settings |
| `0x52` | `0x9000` | `0x0100` | `0x9000` | Function settings |
| `0x52` | `0xA000` | `0x0200` | `0xA000` | DTMF data |
| `0x52` | `0xB000` | `0x0200` | `0xB000` | Modulation parameters |
| `0x52` | `0xD000` | `0x0300` | `0xD000` | Modulation names |
| `0x54` | `0x0000` | `0x0080` | `0xC000` | APRS data |

The complete read is 259 blocks. The saved CHIRP image is `0xD300` bytes with
unread gaps preserved as `0xFF`.

## Channel records

The Pro retains the RT-950's 960 fixed 32-byte records:

- RX and TX frequencies: four little-endian base-100 fields in 10 Hz units
- RX and TX tones: two-byte CTCSS/DCS words
- Signalling group, PTT ID, power, scrambler, encryption, busy lock, scan,
  transmit enable, modulation, bandwidth, FHSS, and a 12-byte GB2312 name

## Read/write policy

The Pro driver is read-only. A complete physical Pro read has not yet been
validated. The community reference includes a write path, but its warning and
lack of a NewChirp physical read-back require treating writes as unproven.

Next milestone: Christophe performs a successful NewChirp read and confirms
the reported model code, all 960 channel records, and the Pro settings blocks.
Only then should a controlled one-channel write/read-back path be considered.
