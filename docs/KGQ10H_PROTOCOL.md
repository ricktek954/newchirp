# Wouxun KG-Q10H protocol

This note records the evidence behind `drivers/newchirp_kgq10h.py`.

## Evidence

- Authorized dealer product page:
  `https://www.buytwowayradios.com/wouxun-kg-q10h.html`
- Official programming package:
  `kg-q10h_setup_v2_1_.02.02_20231115_.zip`
- Download SHA-256:
  `a83483f9393fc4ff794faa2c0a703017a0f3bec7f054f62767bb2548b60807e7`
- Installer:
  `KG-Q10H setup V2[1].02.02(20231115).exe`, SHA-256
  `7f2bdd283ef839d5ef61b6b6b20dd5ae2c13c754cdbeabb0a2f30654a8aa816b`
- Extracted CPS:
  `KG-Q10H.exe`, SHA-256
  `2314ca128659c470ab4a8ca592d0751cb4f8b1e9f48fc8418871cd055a194ed6`
- `lang.csv`, SHA-256
  `1fba38cc5fd2f5f0180c9832be4b9e8e9e3ddedf31336738ef9e26ce9d6f59b8`
- Static analysis: REA 6.5.0 managed metadata and CIL inspection, supplemented
  with a local IL reader.

The installer is a Setup Factory 6 package. It contains one .NET Framework
4.0 managed executable and the language table. The executable identifies
itself as `KG-Q332 Commander version 2.02.02(20231115)`.

## Serial session

- Cable: Wouxun K-plug or compatible two-pin USB serial cable.
- Format: 115200 baud, 8 data bits, no parity, one stop bit.
- DTR asserted and RTS asserted.
- The CPS does not configure parity, stop bits, or handshaking explicitly;
  these remain the .NET SerialPort defaults.
- The CPS sets a 1,000 ms write timeout. It has no explicit read timeout.

Frame from the host:

```text
7C | command | FF | payload_length | encrypt(payload || checksum)
```

The encryption seed is `0x57`:

```text
cipher[0] = seed XOR plain[0]
cipher[n] = cipher[n - 1] XOR plain[n]
```

The checksum is the low eight bits of:

```text
command + direction + payload_length + sum(payload)
```

There is no position-dependent checksum adjustment.

## Commands

| Item | Action/state | Host bytes | Response | Completeness and state |
| --- | --- | --- | --- | --- |
| Identity read | Opening the selected port | `82 FF 03 <address:2> 40` before encryption | `82 00 <length> ...`; address and requested bytes follow decryption | Four 64-byte blocks from `0x0340`; model is accepted when the internal model is `KG-Q332` |
| Read data | `BGK_ReadFreq_DoWork` | `82 FF 03 <address:2> <size>` before encryption | Command `0x82`, direction `0`, payload `address:2 + data` | `serialPort_DataReceived` accumulates until `UartReadBuf[3] + 5` bytes; the CPS copies `UartReadBuf[3] - 2` returned data bytes |
| Write data | `BGK_WriteFreq_DoWork` | `83 FF <size+2> <address:2> <data>` before encryption | Command `0x83`, direction `0`, payload `address:2` | Success requires the echoed address and a valid checksum |
| End session | `Comm_finish` | `81 FF 00 00` before encryption | None | Sent after read or write attempts |

The read worker requests 64 bytes and the write worker sends 32 bytes. The
last block is shortened when a CPS memory region does not end on a block
boundary.

## Retry and response handling

`SeriarPort_Switch` opens the user-selected port and sends the identity read.
`BGK_ReadFreq_DoWork` and `BGK_WriteFreq_DoWork` poll completion up to
`CommOutTimeDef = 500` times. A request is re-sent on poll zero and then every
20 polls; each poll sleeps 12 ms. This produces an approximately 240 ms
resend interval and a roughly six-second operation deadline.

The receive callback:

1. Synchronizes on `0x7C`.
2. Accumulates a second read when the serial event contains only a fragment.
3. Declares a response complete at `length_field + 5` bytes.
4. Decrypts bytes from the end back to the payload start.
5. XORs the first encrypted payload byte with seed `0x57`.
6. Sums the command, direction, length, address, and data and compares the
   result with the final checksum byte.
7. Verifies that the returned address equals the requested address.

The driver retries malformed, short, timed-out, and wrong-address replies
rather than accepting a partial image.

## CPS memory map

The CPS uploads these program regions in this order:

```text
0x0440..0x0507    200 bytes   system settings
0x0540..0x05BF    128 bytes   VFO A/B records
0x05E0..0x445F  16000 bytes   1,000 channel records
0x4460..0x733F  12000 bytes   1,000 channel names
0x7340..0x7727   1000 bytes   channel-present flags
0x7740..0x78A7    360 bytes   scan groups and VFO scan ranges
0x78B0..0x78D7     40 bytes   FM broadcast presets
0x78E0..0x7B37    600 bytes   call-code records
0x7B40..0x7FFF   1200 bytes   call-code names
```

The CPS reads the additional identity region `0x0340..0x043F`, but never
includes it in an upload. NewChirp follows that write boundary.

Identity fields in the 256-byte identity region:

```text
0x036C  12 bytes  display name, normally KG-Q10H
0x0382  16 bytes  internal model, KG-Q332
0x0392  16 bytes  software version, normally VC1.04
```

## Channel records

Channels are 1-based values from 1 through 999:

```text
record offset = 0x05E0 + channel * 16
name offset   = 0x4460 + channel * 12
valid offset  = 0x7340 + channel
```

The channel-present byte is `0x9E`. Each record is:

```text
u32 receive frequency, little-endian, in 10 Hz units
u32 transmit frequency, little-endian, in 10 Hz units
u16 receive CTCSS/DCS word, little-endian
u16 transmit CTCSS/DCS word, little-endian
u8  power bits 0-1, AM bits 2-3, scrambler bits 4-7
u8  wide/narrow bit 0, mute bits 1-2, compander bit 3,
    favorite bit 4, scan-add bit 5, location bit 6, unknown bit 7
u8  call-code index
u8  not exposed by the CPS channel editor
```

A transmit frequency of zero represents a receive-only channel.

CTCSS uses `0x8000 + tenths of a hertz` in the low 14 bits. DCS normal uses
`0x4000 + octal code value`; inverted DCS sets `0x2000`. For example, RX D023
normal is `0x4013` and inverted DCS 754 is `0x61EC`.

Names are encoded with GB2312 by the CPS and are zero-padded to 12 bytes.
NewChirp uses GB18030 when decoding and encoding because it is the compatible
superset available in Python.

## Read/write policy

- Channel records, names, and presence flags are editable.
- Frequencies, tones, FM/NFM/AM mode, four power levels, and skip state are
  implemented.
- Unknown channel bits and the final unexposed byte are preserved.
- Scan groups, call codes, system settings, VFO records, and FM presets are
  preserved byte-for-byte but are not exposed as NewChirp settings yet.
- The identity/calibration region is never sent to the radio.

## Validation status

- Static: complete CPS transport and channel-memory evidence.
- Offline: CPS frame vectors, fragmented receive frames, all nine upload
  boundaries, identity matching, returned-address checks, tones, power,
  modes, unknown-bit preservation, and no-write rejection tests.
- Physical: pending. NewChirp still needs a hardware read comparison and a
  controlled write/read-back validation.
