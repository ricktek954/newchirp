# Ferrite link protocol (RT-950 Pro)

Ferrite is open-source replacement firmware for the Radtel RT-950 Pro
(<https://github.com/FerriteFW/ferrite>, PolyForm Noncommercial). NewChirp's
driver (`drivers/newchirp_ferrite.py`) is written from Ferrite's published
specification, `FerriteFW/docs` `manual/G-link-protocol.md` (protocol 1) and
`manual/10-channels-zones.md`, read 2026-11-24 at docs commit `7dcbe19`.
Field order inside the channel record was confirmed against the Ferrite
Console (`core/src/channels.rs`) and firmware (`ferrite-app` `persist.rs`,
`slot.rs`) sources. No Ferrite code is used.

## Evidence classes

- Static: the specification and source reading above.
- Replay / OEM capture: none.
- Physical radio: none yet.

## Transport

- Cable: USB serial, 115200 8N1. Send `0x03` (ends a terminal session),
  wait 0.3 s, drop any text, then `0x00` (gives the cable to the link).
- Frame: COBS(type, seq, payload up to 240 bytes, CRC-16/CCITT-FALSE of
  type+seq+payload, little-endian), then `0x00`.
- Each request (type 0x01-0x7F) is answered with `type | 0x80`, the same
  seq, then a status byte. Type 0x51 frames are unasked events and are
  skipped. 2 s answer timeout per frame.
- Status: 0 ok, 1 bad frame, 2 unknown type, 3 bad argument, 4 refused,
  5 PIN lock, 7 busy (retry), 8 not found, 9 invalid + reason text,
  10 cancelled on the radio.

## Operations used

| Request | Payload | Answer after status | Use |
| --- | --- | --- | --- |
| `HELLO` 0x01 | 1, 8 zero bytes, `NewChirp` | protocol, largest payload, may go on, firmware (len, text), build, caps, stored layout, chip layout, lists hash | Refuse protocol ≠ 1, a PIN-locked radio, or chip layout ≠ 3 (an unfinished update) |
| `READ_MANY` 0x17 | what (2 channels, 3 zones), first u16, count u16 | next u16, then (index u16, length u8, record) | Read all held records; empty indexes are skipped; also used with count 1 to check or verify one channel |
| `BEGIN` 0x13 | count u16 | — | Radio shows its progress screen |
| `WRITE_MANY` 0x18 | what 2, then (index u16, length u8, record) | applied u8 (+ reason for 9) | Write changed channels; length 0 deletes; busy retried 20 times |
| `END` 0x14 | — | — | Close the progress screen (always sent after `BEGIN`) |

## Channel record (41 bytes on the link)

| Offset | Field |
| --- | --- |
| 0 | number u16 (0-based; shown as 1-4000) |
| 2 | zone u16 (0-511, 0xFFFF none) |
| 4 | RX u32, 10 Hz |
| 8 | name, 16 bytes, NUL-padded (A-Z a-z 0-9 space `- . / _ # + & ( ) ' !`) |
| 24 | mode: 0 FM, 1 NFM, 2 AM, 3 USB, 4 LSB, 5 CW, 6 WFM, 7 NAM |
| 25 | narrow (follows the mode) |
| 26 / 28 | RX / TX tone word u16: CTCSS in 0.1 Hz; bit 15 DCS, bit 14 inverted, code in octal; 0 none |
| 30 | offset i32, 10 Hz: signed shift, or the TX frequency when split |
| 34 | power 0 low, 1 mid, 2 high |
| 35 | step index (10 Hz ... 100 kHz; 10 = 12.5 kHz) |
| 36 | squelch 0-9, 10 Global |
| 37 | busy lockout |
| 38 | bit 0 reverse, bit 1 split |
| 39 | flags: 1 skip, 2 APRS, 4 RX only, 0x40 hidden, 0x80 priority |
| 40 | end tone (bits 0-2) and tail (bits 3-4), 0 Global |

Zone records (what 3) are read as 28 bytes: name[16], scan-all, shown,
by-distance, resume, dwell, reserved, priority 1 and 2 (u16), channel count.

## NewChirp image

`NEWCHIRP-FERRITE` header (64 bytes: version, protocol, layout, build,
firmware text at 24), then 4,000 channel slots and 512 zone slots
(1 held-flag byte + record), then a baseline copy of the 4,000 channel slots
as last read or written. Writes send only channels that differ from the
baseline, after checking that each is still on the radio as the baseline
says (or already as the image wants it), then read each back.

## Not implemented

Bluetooth (FFE0/FFE1), compression (`Z`), settings, APRS, positions,
contacts, presets, zone editing, `STREAM`, firmware update and stock
restore (Ferrite Console's job).
