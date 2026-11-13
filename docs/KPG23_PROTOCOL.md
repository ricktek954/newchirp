# Kenwood KPG-23D / KPG-32D protocol notes

Last updated: 2026-11-13

## Status

Experimental read-only support exists for the Kenwood TK-350 and TK-359.
The transport and channel record layout were derived from the supplied
official DOS programmers and their sample data. No NewChirp read has yet been
performed on physical hardware.

This document distinguishes verified observations from the KPG-family replay
rule used for block data.

## Artifacts

- KPG-23D 1.01 for TK-250/TK-350.
- KPG-32D 1.00 for TK-259/TK-359.
- `kpg23d.zip`, SHA-256:
  `2407d17f2f8890db3b21bdfe69beb7154444c3ecd5d44dd743c4e9d45d0279af`.
- `kpg32d.zip`, SHA-256:
  `91b828a2d1e032b807ae3bed107426b844833483015a73c7b801f89446c8f37e`.
- KPG-23D `SAMPLE.V1B`, 3,584 bytes, SHA-256:
  `6b61db4739fc1e19d18f47171620bdbb3ced2decb63c4aca9aaa87abb970b981`.
- KPG-32D `SAMPLE.FDT`, 21,503 bytes, SHA-256:
  `0107e63b70d156acabb2873b6ab8ddcbb0e291e94b15b0cff95889ae00ba5189`.

The OEM executables were analyzed statically and run only inside an isolated
FreeDOS/QEMU VM.

## Serial session

KPG-23D was observed using COM1 at `9600,N,8,1`.

| Step | Host bytes | Radio response |
| --- | --- | --- |
| Identity | `02` | Eight-byte family identity |
| Acknowledge identity | `06` | Optional `06` |
| Read block | `52 <address:u16be> <length:u8>` | See below |
| Leave mode | `45` (`E`) | `06` |

The observed first request after selecting TK-350 and 450-470 MHz was:

```text
52 f0 00 80
```

This is `R`, address `0xF000`, and a 128-byte request. The identity accepted
by the recovered TK-350 configuration was `P350S 00 e2 00`.

## Block response

The read-only implementation follows the shared Kenwood family framing:

```text
57 <3 header bytes> <length data bytes>
```

- `0x57` (`W`) indicates a data response.
- `0x5A` (`Z`) indicates a uniform fill block and is expanded to `0xFF`.
- The three response header bytes are retained by the OEM but are not part
  of channel memory.
- The host sends `0x06` and expects `0x06` after each accepted block.
- A failed exchange is retried up to three times.

The exact three header bytes could not be made to complete a full simulated
block exchange before hardware became available. The driver therefore logs
and preserves the family framing but must be validated by a physical read.
Uploads remain disabled.

## Memory size and records

- TK-350 image: `0x0E00` bytes, 160 channel slots.
- TK-359 image: `0x53FF` bytes, 250 channel slots.
- Channel record size: 16 bytes.
- Names: four ASCII bytes at record offset `0x08`.

Each channel begins with a 16-bit RX word and 16-bit TX word:

```text
rx_word = u16le(record[0:2])
tx_word = u16le(record[2:4])
```

For the 450-470 MHz band, the words encode frequency in 6.25 kHz steps:

```text
RX steps = signed16(rx_word - 0x4D18)
TX steps = signed16(tx_word - 0x6940)
frequency = 450000000 + steps * 6250
```

The supplied UHF data demonstrates the mapping:

| Frequency | RX word | TX word |
| --- | --- | --- |
| 430.000 MHz | `4098` | `5CC0` |
| 450.000 MHz | `4D18` | `6940` |
| 460.000 MHz | `5358` | `6F80` |
| 470.000 MHz | `5998` | `75C0` |

The remaining record bytes contain signalling and channel options. They are
preserved but not exposed until their UI labels and bit meanings are traced.

## Driver policy

- Read and retain the complete image.
- Accept a matching eight-byte family identity.
- Decode RX/TX frequency and four-character name records.
- Preserve all option bytes.
- Hide records whose RX frequency is outside 450-470 MHz.
- Reject all uploads and channel mutations.

## Remaining work

1. Capture one complete KPG-23D read from a TK-350.
2. Capture one complete KPG-32D read from a TK-359.
3. Confirm the three response header bytes and final partial-block handling.
4. Compare all decoded channels with the OEM CPS.
5. Trace power, signalling, scan, and option fields.
6. Validate write ranges and response behavior before enabling any upload.
