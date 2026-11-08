# Radioddity GS-5B 1.XX Programming Protocol

Last updated: 2026-11-08

This document records the evidence and wire contract used by
`drivers/newchirp_gs5b.py`. The implementation was recovered from
Radioddity's official GS-5B Pro CPS v1.1.3, distributed as:

`Radioddity_GS-5B-Pro_CPS_Setup_v1.1.3.zip`

The package is retained at:

```text
/Users/rlopez/Downloads/Radioddity_GS-5B-Pro_CPS_Setup_v1.1.3.zip
```

## Evidence inventory

| Artifact | SHA-256 |
| --- | --- |
| Official CPS ZIP | `628ed2f64c644673a8a9a3c7aa6d45d1d42f2baaf32f860e3922c824e501396f` |
| CPS setup executable | `b3d37b7607a7fc5fba4eff3378b99b82454d863104ce002120c4f1b4532eb576` |
| Extracted `SHX-8800Pro_CPS.exe` | `7878a58b2e33a153e3e137ab803b90db43ac438a00851853641fe2bccba92d54` |
| English resource assembly | `027efb5f2cc9dc44f21d11fc681c0150e2bd3c4f31e484a9d2c122c3baf12d95` |

The older 2020 GS-5B package remains available for 0.XX hardware:

`Radioddity GS-5B Programming Software_20200907.zip`

SHA-256:
`c950b3c2a2581e42756c8b7fa991e3f8d2fcb2c1e10b845bcef382d5d0d39cc4`

That legacy package contains
`Radioddity GS-5B Computer Software V1.2.8.exe`, SHA-256
`2ddcb3887ca464df8d36142398bba035888358d5f85be60a8c2feb490becb617`.
Its channel transport is the upstream CHIRP `PROGROMSHXU` path. The
GS-5B 1.XX radio in the current bug report does not acknowledge that
handshake.

## Transport contract

The CPS opens the serial port at 115200 baud, 8 data bits, no parity, one
stop bit, with DTR and RTS asserted. It does not use hardware or software
flow control.

| Action/state | Host bytes | Response and length rule | Next state |
| --- | --- | --- | --- |
| Connect | `PROGRAMSHXPU` | Exactly one byte, `06` | Send ready marker |
| Ready | `46` (`F`) | Exactly 16 identity bytes | Read/write pages |
| Read page | `52 HH LL 40` | Exactly 68 bytes: the four-byte request echo followed by 64 data bytes | Next page |
| Write page | `57 HH LL 40` plus 64 data bytes | Exactly one byte, `06` | Next page |
| Exit/reset | `45` (`E`) | No response is expected | Close port |

The `HH LL` address is unsigned big-endian. The OEM state machine allows five
attempts for a page response with a one-second retry timer. NewChirp follows
the same bounded retry policy and fails closed after the final attempt.

## Memory map

The CPS reads and writes 64-byte pages in these ranges:

```text
0x0000-0x3FC0  channels 1-512, two 32-byte records per page
0x8000         VFO block
0x9000         radio settings block
0xA000-0xB03F  DTMF, zone names, FM and auxiliary data
```

The saved image is `0xB040` bytes. The undocumented gaps between the mapped
ranges are never written.

## Channel record

Each channel occupies 32 bytes:

| Bytes | Meaning | Encoding |
| --- | --- | --- |
| `0..3` | Receive frequency | Four packed-decimal pairs, least-significant pair first |
| `4..7` | Transmit frequency | Four packed-decimal pairs, least-significant pair first |
| `8..9` | Receive CTCSS/DCS | See tone encoding |
| `10..11` | Transmit CTCSS/DCS | See tone encoding |
| `12` | Signal group | CPS value modulo 20; preserved by NewChirp |
| `13` | PTT ID | CPS value modulo 4; preserved by NewChirp |
| `14` | Power | `0=High`, `1=Medium`, `2=Low` |
| `15` bit 2 | Scan add | `0=skip`, `1=scan` |
| `15` bit 3 | Busy lock | `off/on` |
| `15` bit 6 | Bandwidth | `0=wide`, `1=narrow` |
| `16..19` | Unmapped | Preserved |
| `20..31` | Name | Up to 12 GB2312 bytes, `FF` padded |

An empty record is `FF`-filled. The CPS treats a record as active only when
the receive-frequency bytes contain a valid packed-decimal value.

## Tone encoding

For numeric CTCSS, the radio stores the tone in tenths of a hertz as an
unsigned little-endian word. For example, 100.0 Hz is `E8 03`.

DCS is encoded as a one-based table index in the first byte with the second
byte zero. The CPS table contains 105 normal codes and the same 105 inverted
codes:

- index 0: `D023N`, written as `01 00`
- index 104: `D754N`, written as `6A 00`
- index 105: `D023I`, written as `6B 00`
- index 209: `D754I`, written as `D2 00`

The code order matches CHIRP's DTCS table plus code `645`.

## Current boundary

`GS-5B (1.XX)` is a separate experimental model entry. The original
`Radioddity_GS-5B` entry remains available for radios using the older 0.XX
CPS and `PROGROMSHXU` transport.

Current evidence is E1 plus synthetic replay E2: complete managed call paths,
handshake order, page framing, address ranges, record fields, tone table, and
transport tests. No physical read, controlled write, or read-back has been
completed for 1.XX hardware.

The next validation must read a physical GS-5B 1.XX, save the `0xB040` image,
compare all 512 records with the OEM CPS, and only then write one unused channel
and verify it with both CPS and NewChirp.
