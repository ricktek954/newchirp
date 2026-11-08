# Yaesu FT-991A Live CAT Protocol

Last updated: 2026-11-08

## Scope

This document covers the Yaesu FT-991A live CAT channel driver in
`drivers/newchirp_yaesu_ft991a.py`. It is based on Yaesu's public CAT command
reference and public FT-991A reverse-engineering work.

RT Systems ADMS-991A is a paid, serial-gated download and was not obtained.
The driver does not copy or redistribute RT Systems code.

## Evidence inventory

- Yaesu, `FT-991A CAT Operation Reference Book`, document
  `FT-991A_CAT_OM_ENG_1711-D.pdf`
  - SHA-256:
    `52164f737e37a3ffc8276eccedf8ecb524607198c38d386ae4ff7b2fc1d60c95`
  - Documents CAT identity `0670`, serial commands, channel fields, modes,
    the 50-entry CTCSS table, and the 104-entry DCS table.
- Gil Kloepfer KI5BPK, FT-991A internal NVRAM memory map revision 0.7f
  - SHA-256:
    `dc72359ca2c5b983b5821a727c0b5f62a5d9b7b87461259765bcf4d450e26e5c`
  - Documents the visible/filled bitmaps, 117 channel records, and the
    96-byte channel record layout.
- Gil Kloepfer, SPR/SPW pseudocode
  - SHA-256:
    `ae87abeac11960fcd65a18ae0d1bb00e39cfd1649b0e6e651844d9610a8c5bee`
  - Documents two-byte reads, read/modify/write requirements, command
    checksums, and response validation.
- CHIRP issue 2531, public FT-991 exchange capture
  - Workbook SHA-256:
    `8ca3fe60db1ad2294c963ecc2db495d647fc32cda2ae6b801d1214935b9949c0`
  - Contains actual `ID`, `SPR`, and `SPW` traffic from a programmer writing
    FT-991 configuration memory.
- CHIRP issue 2531, C-style channel map
  - SHA-256:
    `41456ff1708903e03455b8cc0a4063bd5826c4e71f8b555c56c9f12a370017c3`
- Public interoperability notes:
  `j0ju/ft991a-interoperability-tools` commit
  `2f96ee50af56d83993c08dfbb078175b36b9d494`

## Transport

- CAT serial, 8N1.
- The driver probes 38,400, 19,200, 9,600, and 4,800 baud.
- Identity query: ASCII `ID;`.
- Accepted response: `ID0670;`.
- The driver sends `AI0;` to disable automatic information reports.

## SPR read

The request is:

```text
SPR <address-high> <address-low> <checksum> ;
```

`checksum` is the low byte of the sum of the first five bytes. The radio
returns nine bytes:

```text
SPR <address-high> <address-low> <data-1> <data-2> <checksum> ;
```

The response checksum is the low byte of the request checksum plus both data
bytes. Every SPR operation affects the addressed byte and the following byte.

## SPW write

The request is:

```text
SPW <address-high> <address-low> <data-1> <data-2> <checksum> ;
```

The checksum is the low byte of the sum of the first seven bytes. A successful
write returns exactly `A;`.

NewChirp performs a read/modify/write for every changed pair so bytes outside
the validated channel fields are preserved.

## Channel map

| NVRAM address | Contents |
| --- | --- |
| `0x3229-0x3238` | Visible channel bitmap, channels 1-117 |
| `0x3239-0x3248` | Filled/used channel bitmap |
| `0x3249-0x6368` | 131 channel-format records |
| `0x3249 + (channel - 1) * 96` | Selected channel record |

The driver exposes channels 1-117. Bit zero of the first bitmap byte is channel
1; the next byte starts channel 9.

### Channel record fields

The driver reads and writes these documented offsets:

| Offset | Contents |
| ---: | --- |
| 0 | Memory mode |
| 1 bit 0 | Scan skip |
| 2 bits 1 and 4-5 | Duplex/simplex and shift direction |
| 3 bits 2-4 | Tone/DCS mode |
| 4 bit 4 | FM narrow |
| 70 | CTCSS tone-table index |
| 71 | DCS code-table index |
| 76-79 | Receive frequency, 32-bit big-endian Hz |
| 80-83 | Repeater offset, 32-bit big-endian Hz |
| 84-95 | Twelve-character ASCII memory tag |

Unknown bytes and undocumented channel fields are never deliberately changed.
Erasing a channel clears only its visible bitmap bit, matching the radio's
stored-record/unerase model.

## Safety policy

- The model requires CAT identity `0670`; FT-991 non-A identity `0570` is
  rejected.
- Malformed SPR responses, incorrect addresses, bad checksums, and missing
  terminators fail closed.
- The driver refuses nonstandard split frequencies because the public evidence
  does not establish a reliable split-marker encoding.
- Per-channel RF power is not exposed because the radio stores power by band
  and mode rather than in the channel record.
- DCS polarity is radio-wide and is not changed by channel edits.

## Validation status

- E1: official CAT command definitions and public NVRAM map.
- E2: replay tests cover identification, captured channel decoding,
  read/modify/write preservation, bitmap clearing, and checksum failure.
- E3: public RT Systems exchange capture demonstrates the same SPR/SPW
  transport and channel-record addresses.
- E4: no physical NewChirp hardware validation yet.
- E5: none.

The first hardware test must read channels and compare timestamps against the
radio and the user's existing programmer, then edit one inactive memory,
write it, and verify by reading it back and inspecting the radio display.
