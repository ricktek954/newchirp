# Wouxun KG-905G Plus protocol

This note records the evidence behind `drivers/newchirp_kg905g.py`.

## Evidence

- Official product page:
  `https://www.buytwowayradios.com/wouxun-kg-905g-plus.html`
- Official programming package:
  `kg-905g_plus_setup_v2.1.1_20250514_.zip`
- Download SHA-256:
  `3a18b2d66313caad25a06dd5ed77dfe1ea33f41bea92b3e22242697e638a617a`
- Installer:
  `KG-905G Plus setup V2.1.1(20250514).exe`, SHA-256
  `204534cdb8637ce19b0a326be3a6a1585a019e3fec35f8136b0c8e07f3b12b70`
- Extracted CPS:
  `KG-905G Plus Program.exe`, SHA-256
  `5139fc67b4ed0a1dedffa6113200fc7120508dc9f72f454631098c30d6e1a83d`

Static CIL analysis covered the serial send/receive methods, channel
serializers, `ReadFreqData_Init`, the read and write background workers, and
the model-info parser. Hardware validation with this implementation is still
pending.

## Serial session

- Cable: Wouxun K-plug.
- Format: 19200 baud, 8 data bits, no parity, one stop bit.
- DTR asserted and RTS asserted.
- No hardware or software flow control.

Frame:

```text
7C | cmd | dir | len | encrypt(payload || checksum)
```

`dir` is `0xFF` from the computer and `0x00` from the radio. `len` is the
plaintext payload size without the checksum. Commands used by the CPS are:

- `0x80`: read machine data
- `0x81`: end session
- `0x82`: addressed read
- `0x83`: addressed write

Encrypt with seed `0x54`: the first cipher byte is `seed XOR plain[0]`, and
every later cipher byte is the previous cipher byte XOR the next plaintext
byte. Decrypt reverses the chain.

The checksum is an 8-bit sum of the command, direction, length, and payload.
Add `+3`, `+1`, `-1`, or `-3` according to whether `payload[0] & 3` is 0, 1,
2, or 3. An empty payload uses `+3`.

Reads use 64-byte blocks; the final block in a region may be shorter. The
request payload is a big-endian address and one-byte length. A read reply uses
command `0x82`, direction `0x00`, and a payload containing the echoed
big-endian address followed by the data. A write payload contains the
address followed by data, and the radio acknowledges command `0x83` with the
same two-byte address.

## CPS memory map

The official CPS allocates these program-data arrays:

```text
0x0340..0x043F  256 bytes  model/firmware information, read-only
0x0440..0x04BF  128 bytes  system settings
0x0540..0x054F   16 bytes  VFO data
0x05E0..0x1EEF 6416 bytes  channel records
0x1F00..0x2B87 3208 bytes  channel names
0x3000..0x3190  401 bytes  channel-present flags
0x3360..0x33DD  126 bytes  call-code records
0x35C0..0x3667  168 bytes  call-code names
0x3700..0x3727   40 bytes  radio settings
```

The CPS does not write the `0x0340` model/firmware region. Every other region
above is written back unchanged unless a channel field is edited.

The CPS identifies its model as `B3-10` at `0x0376`. A field capture used a
`KG-905G+` marker at `0x0040`; the driver reads that block only as a fallback
identity check and still never writes it.

## Channel records

Channels use 1-based indexes 1 through 400:

```text
record offset = 0x05E0 + channel * 16
name offset   = 0x1F00 + channel * 8
valid offset  = 0x3000 + channel
```

Valid flags written by the CPS are `0x9E`; zero means empty.

Each 16-byte record is:

```text
u32 rx frequency, little-endian, in 10 Hz units
u32 tx frequency, little-endian, in 10 Hz units
u16 rx tone
u16 tx tone
u8  power bits 0-1, AM bits 2-3, "scream" bits 4-7
u8  wide bit 0, mute bits 1-2, compand bit 3,
    busy-lockout bit 4, scan-add bit 5, favorite bit 7
u8  call-code index
u8  unexposed
```

CTCSS uses `0x8000 + tenths of a hertz` in the low 12 bits. DCS normal uses
`0x4000 + octal code`; inverted uses `0x6000 + octal code`.

New channels use call-code index 1. Unknown record bits and the final byte are
preserved when a channel is edited.

## GMRS policy

The driver accepts the 22 GMRS simplex frequencies and the eight repeater
outputs with an exact +5 MHz offset. The seven 467 MHz interstitial channels
are forced to narrow bandwidth and low power. Other transmit frequencies are
rejected because the radio is FCC type accepted for GMRS.

## Validation status

- Static: complete CPS transport and memory-map evidence.
- Offline: encrypted frame vectors, read coverage, all 400 channel bounds,
  tones, modes, preserving unknown bits, write ranges, malformed-image
  rejection, and no-write safety tests.
- Physical: not yet validated with NewChirp. A complete read should be saved
  and compared with the official CPS before enabling or relying on writes.
