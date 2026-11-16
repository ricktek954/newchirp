# Wouxun KG-UV8D protocol notes

Last updated: 2026-11-16

## Scope

This document records NewChirp's OEM CPS evidence for the original KG-UV8D
and the narrow compatibility overlay in
`drivers/newchirp_kg_uv8d_compat.py`. The transport and channel image remain
the pinned CHIRP `kguv8d.py` implementation. This is not a claim that a new
serial stack or complete independent codeplug implementation has been
validated.

## Official artifacts

- Wouxun download page:
  `https://www.wouxun.com/download.aspx?flid=1086`
- Archive: `UV8D_SEN.rar`
- Archive SHA-256:
  `86a9fbe354682ba9cdc658dc9ea1e17835b6425ad979af01f910affb35302eb2`
- Extracted executable: `KG-UV8D.exe`
- CPS identity: KG-UV8D Commander B2.1.03 (140808)
- Executable SHA-256:
  `534e0e82248b4ce8391e215fe56679ce6c1a2f2a235fde4c1986d6c34c280d57`
- Packaging: Setup Factory 6.0. The installer was statically unpacked and was
  not executed during analysis.

## Serial setup

The Windows CPS constructs a DCB for COM communication with:

| Setting | OEM value | Effective setting |
| --- | --- | --- |
| Baud rate | `0x4B00` | 19,200 |
| Byte size | 8 | 8 data bits |
| Parity | 0 | No parity |
| Stop bits | 0 | Windows `ONESTOPBIT` |

The serial open/configuration path is at `0x0040A650`. `WriteFile` and
`ReadFile` are wrapped by functions at `0x0040A740` and `0x0040A770`.

## Record framing

The pinned CHIRP driver and the static CPS call path agree on this frame:

```text
7D <command> <direction> <payload-length> <payload...> <checksum>
```

- `0x7D`: record start
- `0x80`: identify
- `0x81`: finish/reboot
- `0x82`: read
- `0x83`: write
- `0xFF`: host-to-radio direction
- Checksum: sum of command, direction, length, and payload modulo 256

Read and write payloads begin with a 16-bit big-endian address. A read payload
adds one length byte; NewChirp's established block size is 64 bytes. A write
payload adds the block data.

The CPS identification helper is at `0x0040A7A0`; the block read and write
helpers are at `0x0040A910` and `0x0040AA50`; checksum and response validation
are at `0x0040AAF0` and `0x0040AB60`. The main clone maps are at `0x004243C0`
and `0x00424790`.

Evidence level for the transport is E1 for the CPS call path and E3 for the
reporter's completed NewChirp download. The physical image itself was not
attached to the report, so it cannot yet be compared at E4.

## Tone words and reserved DCS values

The pinned driver uses CHIRP's Kenwood tone model:

- DCS marker: `0x2800`
- DCS code bits: `0x07FF`
- Reverse-polarity bit: `0x8000`
- No tone: `0xFFFF`

The stock decoder formats the masked DCS bits as octal before assigning the
result to CHIRP's restricted DCS-code list. A word of `0x2FFF` therefore
becomes code `3777`, which is not a legal octal-style DCS code and raised an
exception that aborted decoding all 999 channel slots.

The OEM tone formatter at `0x00420060` emits `DI%o`, `DI0%o`, `DN%o`, or
`DN0%o` strings for DCS and does not use the invalid value as a channel
identifier. NewChirp treats any stock-decoded DCS code outside the valid
`000`-`777` set as no tone on that side, preserves the exact stored word, and
continues decoding the remaining channels.

The compatibility layer deliberately does not guess a replacement tone code.
The saved image remains safe to preserve for analysis, and write support stays
limited to the stock CHIRP channel/settings path.

## Validation

Offline tests insert `0x2FFF` into both tone fields of an active fixture
channel and verify:

- all channel slots decode;
- editing the channel name preserves both original tone words;
- valid DCS `023` still decodes and round-trips;
- `0xFFFF` remains no tone.

The reporter must complete a physical read and compare the affected channel
with the radio before the override is considered hardware-validated. No upload
has been requested or verified.
