# Kenwood KPG-23D / KPG-32D protocol notes

Last updated: 2026-11-26

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

## Serial session (TK-350, KPG-23D 1.01) — traced 2026-11-26

Source: `KPG23D.EXE` 1.01 (12/02/1994), SHA-256
`32973eacc6db151f3cfb2fa10591d59653da028d78651776813c529415ba8248`, run in
FreeDOS 1.4 under QEMU 11.1.3 with the `serial_write`, `serial_read` and
`serial_update_parameters` trace events, first with no radio and then with a
simulated radio on the serial socket. Model `TK-350 (160ch)`, band
`UHF 450-470 MHz`, no voice scrambler. The same settings were seen with the
program's default TK-250 file loaded.

UART set-up for every read (COM1, base 0x3F8):

| Register | Value | Meaning |
| --- | --- | --- |
| LCR | `0x87`, then `0x07` | DLAB on; then 8 data bits, no parity, **2 stop bits** |
| DLL/DLM | `0x18`, `0x00` | divisor 24 = **4,800 baud** |
| IER | `0x00` | polled, no interrupts |
| MCR | never written by KPG-23D | see below |

Bytes are sent and received through PC BIOS INT 14h (`int86(0x14)` with
AH=00 init, AH=01 send, AH=02 receive; also AH=81). An IBM-compatible BIOS
writes MCR=03 (DTR+RTS) to send a byte and MCR=01 (DTR only) to receive, so
on a real PC **DTR stays raised and RTS is raised only while sending**.
QEMU's SeaBIOS does not drive MCR in INT 14h, which is why the trace shows no
MCR writes; do not read that as "lines off". The Setup menu only chooses
COM1 or COM2; the speed is fixed.

| Step | Host bytes | Radio response |
| --- | --- | --- |
| Identity | `02` | 6 bytes (simulated `P350S 00`); content is not checked before reading (`P250S 00` read the same way) |
| Acknowledge identity | `06` | `06` |
| Read block | `52 <address:u16be> 80` | `57 <address:u16be> 80` + 128 data bytes, no checksum |
| Acknowledge block | `06` | `06` |

- 28 blocks, `0xF000` to `0xFD80` (0x0E00 bytes), strictly sequential.
- No exit command: the session ends after the last block's `06`/`06`.
- A `5A` (`Z`) reply, with or without data, makes KPG-23D show
  "Check Connection. Retry or Cancel?". It is not part of this protocol.
- Without a radio, one `02` is sent and the error appears after about six
  seconds; Retry repeats the whole set-up and sends `02` again.

Earlier notes (2026-11-13) recorded `9600,N,8,1`, an 8-byte identity, an `E`
exit and a `Z` fill reply. The trace shows those were wrong for KPG-23D: the
9600/8N1 lines are the PC BIOS initialising COM1 at boot, before KPG-23D runs.
NewChirp used 9600 8N1 with DTR/RTS on, so a TK-350 never heard the request.
This matches the 2026-11 reports (ledger 71), where no TK-350 ever answered.

The KPG-32D manual specifies a KPG-8 or KPG-22 cable. It also warns that
automatic entry into PC mode is not reliable: for a failed connection, switch
the radio off, hold `[LMP]` and `[CALL]` while switching it on, and wait for
`-PC-` on the display before starting the read.

## Serial session (TK-359, KPG-32D 1.00) — traced 2026-11-26

Source: `KPG32D.EXE` 1.00 (07/09/1996), SHA-256
`5c1014f201b0dbb8887a4789cd6380878482c7bca109db9695f4fe570283e7fa`, same
QEMU method, model `TK-359`, band `UHF 450-470 MHz`, run to "Done Reading
The Radio Data" against a simulated radio. Protocol constants sit at
DS:0x32CA: `PROGRAM`, `02`, `S`, `X`, `15`, `06`, `80`, `E`, then the
INT 14h init byte `E7` (9600 baud, no parity, 2 stop bits, 8 bits).

- UART: 9600 baud, **8N2** (LCR `0x07`, divisor 12).
- Lines: INT 14h send/receive as above (DTR raised, RTS only while
  sending). KPG-32D also writes MCR itself: `(MCR & ~DTR) | RTS` on COM1 and
  COM2 once before the session, and MCR=`01` (DTR only) after every byte.

| Step | Host bytes | Radio response |
| --- | --- | --- |
| Wake | `PROGRAM` | `06` |
| Identity | `02` | 8 bytes, checked back to front (0x15F1F): byte 7 `P`, 6 `0`, 5 `2`/`3` (TK-259/TK-359), 4 `5`, 3 `9`, 2 `1`/`2` (band), 1 `81`, byte 0 not checked. A mismatch is answered `15` and "Check Radio Type". |
| Acknowledge identity | `06` | `06` |
| Read block | `53 03 <high+0xAC> <low> 80` (24-bit address 0x03AC00 + offset, no carry into the top byte) | `58 03 <high+0xAC> <low> 80` + 128 data bytes + sum8 of the data |
| Acknowledge block | `06` (bad checksum: `15`, radio `06`, retry up to 3) | `06` |
| Leave | `45` (`E`) | `06` |

The block list is data-driven: KPG-32D always reads 0x0000-0x03FF and
0x0500-0x06FF, then 3 bytes at 0x3232, then the channel areas those bytes
select, 0x3200-0x33FF, 0x3400 and 0x5380. It never reads 0x0400-0x04FF.
With all-`FF` data it requested every block up to and past 0x5400.
NewChirp reads every 0x80 block from 0x0000 to 0x53FF except 0x0400-0x04FF,
a superset of the CPS reads; radio offsets equal `.FDT` file offsets (the
served `SAMPLE.FDT` decoded to the same channels in KPG-32D).

`SAMPLE.FDT` is a **TK-259 (VHF 150-174 MHz)** codeplug: KPG-32D shows
channels 1-3 at 150.000, 151.000 and 152.000 MHz. The TK-359 (UHF) channel
decoding in NewChirp was derived from it and is not yet validated against a
UHF image.

Earlier notes (2026-11-13) had the TK-359 on the TK-350 protocol (9600 8N1,
bare `02`, `R`/`W` blocks from 0xF000). That was wrong; a TK-359 would not
have answered.

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
