# Radioddity X1 Pro Programming Protocol

Last updated: 2026-11-07

This document records the evidence and wire contract used by
`drivers/newchirp_x1pro.py`. The implementation was recovered from the
Radioddity firmware/CPS package dated 2026-07-15. It has synthetic replay
evidence only; no physical X1 Pro read or write has been completed.

## Evidence inventory

| Artifact | SHA-256 |
| --- | --- |
| `2026-07-15_Radioddity_X1_PRO_Firmware_Update_with_CPS.zip` | `88715c06694994d58b4791deeaa6641d7b4303fb15c317f062591eff56bb9519` |
| `X1PRO.exe` | `64f90289b838adae6d01691649b08812e5783751a6bbcae157b39d5e2af87339` |
| `model.xml` | `51b0e546fe644a865fe46c021f1fccf655723d953fc326a0cdd9276f7dde0005` |
| `language.xml` | `45cdb021e2ff644a7d2bcc7fe910b0579b6d9d28aa54067efb707d1fff7ee3b3` |
| `CodeUP_1.11.exe` | `2c974ed006a382576580de42faa4e9912bb2be45d91a0d193bc78b60403776d2` |
| CSC image `2026-07-15 X1PRO.nanfone` | `4ce7487a95bf2efa30dae9a87efeeac1f21a71141e653d1c3f291b458b0b242c` |
| `model.dat` | `d410ca506d3c55c2a98d191e57ec30379df35eb50efe12c93bf239bfc36261c2` |
| Recovered CIL listing | `c841dcab4446085810733d7c2ca3a1f9071d5deb78610f72a9e595b68f25d905` |
| User manual PDF | `e7ef2859130234944f1a702e6142b259adf973e42818fdbb11c59accf69a1307` |

The official archive is retained at:

```text
/Users/rlopez/Downloads/2026-07-15_Radioddity_X1_PRO_Firmware_Update_with_CPS.zip
```

`X1PRO.exe` was identified as a PE32 .NET assembly. The relevant managed
types are `wfintegrationFramework.MainForm`,
`wfintegrationFramework.Class.PortCommunication`,
`wfintegrationFramework.Class.Model`, and
`wfintegrationFramework.Class.ConvertHelp`. The CIL was disassembled with
isolated `dnfile`/`dncil` tooling.

`model.xml` supplies the serial configuration, framing constants, channel
columns, tone table, default 30-channel layout, and settings fields. The
application code supplies the state-machine order and receive behavior.

## Transport contract

The model declares `raudrate=115200` and dual-wire communication. The CPS
opens the port at 115200 baud, 8 data bits, no parity, one stop bit, and no
flow control. It does not assert DTR or RTS for this protocol.

| Action/state | Host bytes | Response and length rule | Next state | Evidence |
| --- | --- | --- | --- | --- |
| Open port | None | CPS waits 100 ms after opening the serial port | First handshake | `openPort`, CIL `0x11B18`; `model.xml` |
| Identify request | `02 50 52 4F 47 52 41 4D` (`02PROGRAM`) | Exactly one byte, `06` | Send second marker | `handShakeAsync`, CIL `0xC370`; first-stage fields |
| Identity request | `02` | Exactly eight bytes, `53 4D 50 35 35 38 FF FF` (`SMP558..`) | Confirm identity | `handShakeAsync`, CIL `0xC370`; second-stage fields |
| Identity confirm | `06` | Exactly one byte, `06` | Settings read | `handShakeAsync`, CIL `0xC370`; third-stage fields |
| Read settings | `52 E0 00 10` | Exactly 20 bytes: the four-byte request echoed, then 16 data bytes | Read channel 1 | `readParamAsync`, CIL `0xEE74`; `param startadr`, CIL `0x19AD` |
| Read channel N | `52 HH LL 10` | Exactly 20 bytes: request echoed, then 16 data bytes | Next address, or exit | `readChannelAsync`, CIL `0xDAFC` |
| Write settings | `57 E0 00 10` plus 16 data bytes | Exactly one byte, `06` | Write channel 1 | `writeParamAsync`, CIL `0x11190` |
| Write channel N | `57 HH LL 10` plus 16 data bytes | Exactly one byte, `06`; CPS sleeps 20 ms after the ACK | Next address, or exit | `writeChannelAsync`, CIL `0xF78C`; `Thread.Sleep(20)`, CIL `0xBFB` |
| Exit | `62` | No response is expected | Close port | `readAsync`/`writeAsync` exit states; `model.xml` |

`HH LL` is the 16-bit block address in network byte order. The length byte is
always decimal 16 / hexadecimal `10`. Reads return the complete four-byte
request as an echo followed by exactly 16 payload bytes. There is no checksum,
terminator, or returned-length field.

The CPS receive loop polls until the expected fixed number of bytes has been
received or the 2000 ms cancellation timer expires. A valid response may be
fragmented across serial reads. The NewChirp driver therefore accumulates
exact lengths until its deadline and then rejects short responses. It also
checks the four-byte read echo before accepting payload data.

The CPS does not retry a failed handshake, read, or write. It stops the
operation when the expected response is absent or mismatched. NewChirp follows
that fail-fast behavior and always attempts the `62` exit command in a
`finally` block.

## State-machine order

The OEM read path is:

```text
handshake
  -> read settings at E000
  -> read channels 0000 through 01D0 in 16-byte pages
  -> send 62
```

The OEM write path is:

```text
handshake
  -> write settings at E000
  -> write channels 0000 through 01D0 in 16-byte pages
  -> send 62 after the last ACK and 20 ms delay
```

NewChirp writes all 30 channel pages, including empty pages. It does not infer
that an unmodified page may be skipped.

## Channel map

The CPS defines 30 fixed 16-byte channel records starting at address `0x0000`.
NewChirp channel number 1 is record 0; channel number 30 is record 29.

| Record bytes | Width | Meaning | Encoding |
| --- | ---: | --- | --- |
| `0..3` | 4 | Receive frequency | Unsigned big-endian Hz |
| `4..7` | 4 | Transmit frequency | Unsigned big-endian Hz |
| `8..9` | 2 | Receive CTCSS/DCS | Little-endian raw tone word |
| `10..11` | 2 | Transmit CTCSS/DCS | Little-endian raw tone word |
| `12` bit 0-1 | 2 | Power | `0=Low 0.5 W`, `1=Medium 5 W`, `2=High 7 W` |
| `12` bit 2 | 1 | Bandwidth | `0=Narrow`, `1=Wide` |
| `12` bit 4 | 1 | Scan add | `0=skip`, `1=scan` |
| `12` bit 5 | 1 | Busy lock | `0=off`, `1=on` |
| `13..15` | 3 | Unmapped | Preserved |

The CPS has no channel-name column. NewChirp reports `has_name=False` rather
than synthesizing names from record numbers.

Tone words use these rules:

| Tone type | Raw word |
| --- | --- |
| Off | `FF FF` |
| CTCSS | Little-endian `round(frequency_hz * 10)` |
| DCS normal | Little-endian `0x2800 + int(str(code), 8)` |
| DCS inverted | Normal DCS word with bit 15 set |

For example, CTCSS 100.0 Hz is `E8 03`; DCS 023 normal is `13 28`; and
inverted DCS 023 is `13 A8`. The model XML table agrees with the decoded
values in `readChannelAsync`.

## Settings map

The only settings page is 16 bytes at address `0xE000`.

| Byte/bit | Width | Setting | Values |
| --- | ---: | --- | --- |
| `B0P1` | 4 | Squelch level | `0` through `9` |
| `B0P0` | 1 | Key tone | off/on |
| `B0P6` | 1 | Record | off/on |
| `B0P7` | 1 | Roger beep | off/on |
| `B1P5` | 1 | Power save | off/on |
| `B2P3` | 3 | Scan mode | `0=OS`, `1=TS` |
| `B6P0` | 8 | Noise reduction | `0=Off`, `1`, `2`, `3` |
| `B7P0` | 8 | VOX | `0=Off`, `1=On` |

All other bits in the settings block are preserved during a settings edit.
Out-of-range values are normalized for display without changing unrelated
fields.

## Product and model identity

The CPS model title is `X1 PRO`, and the fixed handshake identity is
`SMP558\xff\xff`. The package and product material identify the radio as the
Radioddity X1 Pro GMRS with 22 GMRS channels, eight repeater channels, three
power levels, 50 CTCSS tones, and 104 DCS codes.

The generic `model.xml` frequency bounds are 400-520 MHz, but the product and
default channel table describe GMRS operation from 462.550000 through
467.725000 MHz. NewChirp intentionally exposes the documented GMRS range.

## Evidence level and unresolved work

Current evidence is E1/E2:

- E1: complete managed call paths, model schema, and exact static constants.
- E2: synthetic transport replay covering handshake, settings, 30 channel
  reads, 30 channel writes, fragmentation, short replies, mismatched echoes,
  ACKs, exit, fields, and settings preservation.

The matching browser transport is
`/Volumes/RICKEXT/web/newchirpweb/lib/radioddity-x1pro-web.ts`. The browser
channel model exposes one shared TX/RX tone, so an unchanged split tone is
preserved, while changing the displayed tone writes the new value to both
sides. The desktop driver retains the full independent TX/RX tone model.

There is no OEM serial capture (E3), physical NewChirp read (E4), or
controlled physical write/read-back (E5). The driver therefore remains
experimental even though both read and write are enabled for testing.

Unknown or unvalidated items:

- Physical response timing and cable behavior for this exact model.
- Firmware versions other than the CSC image shipped in the 2026-07-15
  package.
- Semantics of channel bytes 13-15 and unmapped settings bits.
- Whether every radio accepts arbitrary values inside the broader CPS
  frequency bounds; NewChirp deliberately restricts itself to GMRS.

Next milestone: a physical read on an X1 Pro, compared channel-by-channel with
a saved OEM image. After that, edit one unused memory while retaining a
backup, upload, read back, and verify all 30 channels plus settings.
