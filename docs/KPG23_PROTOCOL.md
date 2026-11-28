# Kenwood KPG-23D / KPG-32D protocol notes

Last updated: 2026-11-26 (channel layouts)

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
| Fill reply | (same request) | `5A 03 <high+0xAC> <low> 80` + **one** fill byte, no checksum; the whole block is that value (0x16468, `Z` at DS:0x32DF). Real TK-359s send it for blank blocks (owner reports 2026-11-26: `5a 03 ac 00 80`, then `ff`). |
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

## Write sessions — traced 2026-11-26

Same QEMU method as the reads, with "Program > Write to radio" against a
simulated radio that logs every byte. Each CPS wrote the loaded test file
(`sample.u1f`, `uhf359.fdt`) and ended with "Done Writing The PC Data.";
the simulated memory afterwards was byte-identical to the file.

### TK-350 (KPG-23D 1.01)

| Step | Host bytes | Radio response |
| --- | --- | --- |
| Identity | `02` | 6 bytes. **Checked on write** (not on read): it must equal the file's model/band record at 0x0D00 (`P3501 01`); `P350S 00` or a different band (`P3504 01`) gives "Model Type is wrong. Overwrite ?" (the user can override). |
| Acknowledge | `06` | `06` |
| Write block | `57 <address:u16be> 80` + 128 bytes, no checksum | `06`; anything else (e.g. `15`) aborts with "Check Connection", no per-block retry |

- 26 blocks, ascending: 0xF000-0xFB80 and 0xFD00-0xFD80. **0xFC00-0xFCFF is
  never written** (read, but never written: likely factory alignment).
- No host `06` after a block's `06`, no exit command; the next frame
  follows the radio's `06` within ~5 ms.

### TK-359 (KPG-32D 1.00)

| Step | Host bytes | Radio response |
| --- | --- | --- |
| Wake / identity / ack | `PROGRAM`, `02`, `06` | `06`, 8-byte identity (checked as on read), `06` |
| Uniform block | `5A 03 <hi+AC> <lo> 80 <fill>` (`Z`, 0x168a9) | `06` |
| Data block | `58 03 <hi+AC> <lo> 80` + 128 bytes + sum8 (`X`, 0x168ae) | `06`, then host sends `03` (DS:0x32DE, commit) and the radio answers `06` |
| Leave | `45` (`E`, DS:0x32D8) | `06` |

Block order (top-level routine 0x16542): 0x0000-0x03FF (all `FF` here, sent
as `Z`), skip 0x0400-0x04FF, 0x0500-0x06FF, then from 0x0700 the
signalling sections at 0x0700, 0x1200 and 0x2200 sized by their entry
counts (0x16634), then 0x3200-0x33FF, then only the channel blocks that
cover the used channel range (0x16782: four 32-byte channels per 0x80
block, range from two bytes of the CPS's channel table), then 0x5380, then
`E`. For `uhf359.fdt` that was 23 frames (10 `Z`, 13 `X` with 13 commits):
0x0000-0x0380, 0x0500-0x0700, 0x1200, 0x2200-0x2300, 0x3200-0x3380, 0x3400,
0x5380.

### Write policy for NewChirp (implemented 2026-11-26, still gated)

- TK-350: refuse unless the radio's identity equals the image's 0x0D00
  record; write the same 26 blocks in the same order; never 0xFC00-0xFCFF.
- TK-359: write only blocks inside the CPS's writable set that differ from
  the image just read from the radio, as `Z` when uniform and `X` + commit
  otherwise; never 0x0400-0x04FF.
- TK-359 reads now store the image as read (`newchirp_kpg32_baseline`) and
  the 128th byte of the last block (`newchirp_kpg32_tail`, which the
  0x53FF-byte image cannot hold) in the image metadata; a write without
  them is refused.
- Channel edits: existing channels only (no add/delete until the CPS
  channel tables are traced). TK-350: RX/TX in 6.25 kHz steps, TX off as
  word `FFFF` (KPG-23D's empty Transmit column), 4-character names.
  TK-359: RX/TX frequencies only; renames and TX off are refused until the
  name length and TX-off encoding are confirmed. Every encode must decode
  back to the same value.
- TK-350 writing is enabled (2026-11-26) after the owner's read matched his
  channel plan; it graduates after one controlled write/read-back. The
  write waits for the identity `06` (as KPG-23D does) so a late reply cannot
  shift the block acknowledgements. `NEWCHIRP_WRITE_DISABLED` stays set on
  the TK-359 until its TX field is confirmed.

## Memory size and records

Checked 2026-11-26 by saving files from the OEM programmers in QEMU with
known frequencies typed in (kept as evidence, SHA-256 below), and by loading
the CPS's own sample files.

| File | Made with | SHA-256 |
| --- | --- | --- |
| `sample.u1f` | KPG-23D, TK-350 160ch, 450-470 MHz, RX 460.0125 / 462.5625 | `6c0c8bcf21297cf84925580085251d8649a981f2082ad6bab4844310443001b4` |
| `sample.u4f` | KPG-23D, TK-350 160ch, 400-430 MHz, default test frequencies | `377e8389aa852648e273318d3826c29d3805dc4dbefd5bbac14c0168b964c04a` |
| `uhf359.fdt` | KPG-32D, TK-359, 450-470 MHz, 460.0125/465.000 and 455.500 | `5129af7f5b2bc8cdd7c804a04d4c0768182961a235b727764360bb67623a9dd4` |

### TK-350 (KPG-23D)

- Image: `0x0E00` bytes (radio 0xF000-0xFDFF = file offsets 0-0xDFF).
- 160 channel records of 16 bytes from offset 0; name: four ASCII bytes at
  record offset `0x08` (KPG-23D pads with spaces on both sides, e.g. `  1 `).
- Erased slot: RX/TX words `FFFF` (option byte 13 stays `E0`).
- Option byte 12 (KPG-23D 1.01, options toggled and saved in QEMU
  2026-11-27): `FF` default; Power Med clears bit 6; Busy lockout Yes
  clears bit 4; Shift Yes clears bit 5. Signal DTMF clears bit 15 of the
  decode QT word. Scan Del is a bitmap near `0x0D40` (ch1 = bit 0 of
  `0x0D40`), not in the record.
- Option byte 13, step size: bit 5 set = RX word counts 6.25 kHz steps,
  clear = 5 kHz; bit 6 the same for TX; bit 7 always set. Records loaded
  into KPG-23D show RX `535A` as 460.0125 (bit set) / 377.020 (clear) and
  TX `6940` as 450.000 / 360.000, so the 5 kHz anchors at 450 MHz are RX
  `8C5E` and TX `AF90`. An owner's TK-350 had channel 114 at `80`
  (428.310 / 435.910); NewChirp 1.0.76 wrote 6.25 kHz words into it and the
  radio received/transmitted on 353.020 / 344.010 instead of 430.0125.
- QT tones: little-endian words at record `+4` (Decode, receive) and `+6`
  (Encode, transmit). Bits 15-14 set = CTCSS, bits 13-0 = Hz x 10
  (`e8 c3` 100.0, `55 c4` 110.9, `07 c7` 179.9 in the KPG-23D samples);
  `FFFF` = none. DQT encoding not yet identified. The owner's 2026-11-26
  channel list (UK repeaters with 67.0-118.8 Hz access tones) is the check
  for the next read.
- Model/band record at `0x0D00`: `P350` + band digit — `1` 450-470, `2`
  470-490, `3` 490-520, `4` 400-430 MHz (TK-250 files carry `P250`).
- Test frequencies (Edit > Test frequency): six RX/TX word pairs at
  `0x0B00`, 16-byte stride.
- The `.V1B` samples shipped with KPG-23D (`SAMPLE`, `KPG23D`, `POLICPLU`,
  `VARFF`, `KGRUDAI`) are TK-250 VHF files: TX word × 5 kHz or × 6.25 kHz,
  RX = TX + 45.05 MHz. They do not use the UHF anchors below.

Each channel begins with a 16-bit RX word and 16-bit TX word:

```text
rx_word = u16le(record[0:2])
tx_word = u16le(record[2:4])
```

With byte 13 bits 5/6 set, the words encode frequency in 6.25 kHz steps, the same for every UHF band
(450-470 and 400-430 MHz files both decode with these anchors):

```text
RX steps = signed16(rx_word - 0x4D18)
TX steps = signed16(tx_word - 0x6940)
frequency = 450000000 + steps * 6250
```

With the bit clear (5 kHz): `steps = signed16(word - 0x8C5E)` (RX) or
`signed16(word - 0xAF90)` (TX), `frequency = 450000000 + steps * 5000`.

KPG-23D-saved values:

| Source | Frequency | Word |
| --- | --- | --- |
| u1f ch1 RX | 460.0125 MHz | `535A` |
| u1f ch2 RX | 462.5625 MHz | `54F2` |
| u1f test 2 | RX 450.1 / TX 450.0 | `4D28` / `6940` |
| u1f test 3 | RX 469.975 / TX 469.9875 | `5994` / `75BE` |
| u4f test 1 | RX 418.1 / TX 418.0 | `3928` / `5540` |
| u4f test 2 | RX 406.1 / TX 406.0 | `31A8` / `4DC0` |

### TK-359 (KPG-32D)

- Image: `0x53FF` bytes; radio offsets equal `.FDT` file offsets.
- Identity copy at `0x0500` (`00 81 31 39 35 33 30 50`; byte 2 is the band,
  `1` 450-470, `2` 406-430 MHz).
- 250 channel records of 32 bytes from `0x3400` (offset 0 is unused `FF`).
- Record: `+02` RX flag, `+03..04` RX step count (big-endian), `+08..09` TX
  step count (big-endian), `+0A` TX flag, `+11..14` name, 4 bytes stored
  last character first (a real radio holds "OPEN" as `NEPO`).
- Counts are 6.25 kHz steps. RX flag bit 0: step-count bit 16. Flag bit 7
  is not a step-size bit (corrected 2026-11-28): two owners' radios
  (mailbox UIDs 1054, 1093) store words with bit 7 clear that only decode in
  band at 6.25 kHz, including KPG test pairs RX 460.100 / TX 460.000,
  450.100 / 450.000 and 469.900 / 470.000; flags seen are RX `EF`, `FF`,
  `6F` and TX `80`, `40`, `00`. Their meaning is unknown, so writes keep
  them. The 5 kHz encoding (if any) is not traced; NewChirp refuses TK-359
  frequencies that are not 6.25 kHz multiples.
  For TX, NewChirp sets bit 16 when the count would decode below 300 MHz
  (true for every TK-359 frequency except 406-409.6 MHz at 6.25 kHz).
- Erased slot: `FF FF FF` at `+02`.
- Test frequencies: 3-byte flag + big-endian count entries at `0x3300`
  (`81 1F 90` = 460.100 MHz).

| Source | Bytes | Frequency |
| --- | --- | --- |
| uhf359 ch1 RX | `EF 1F 82` | 460.0125 MHz |
| uhf359 ch1 TX | `22 A0`, flag `80` | 465.000 MHz |
| uhf359 ch2 RX/TX | `EF 1C B0` / `1C B0 80` | 455.500 MHz |
| SAMPLE.FDT ch1 (TK-259) | `EC 5D C0` | 150.000 MHz |

The remaining record bytes contain signalling and channel options. They are
preserved but not exposed until their UI labels and bit meanings are traced.

## Driver policy

- Read and retain the complete image.
- Decode RX/TX frequency and name records as laid out above.
- Preserve all option bytes.
- Show every channel in any UHF band; treat only erased slots, or values
  decoding outside 300-600 MHz, as blank. (Before 2026-11-26 the TK-350
  hid everything outside 450-470 MHz, and the TK-359 read 16-byte records
  from offset 0, which is unused.)
- Reject all uploads and channel mutations.

## Remaining work

1. Capture one complete KPG-23D read from a TK-350.
2. Capture one complete KPG-32D read from a TK-359.
3. Confirm the three response header bytes and final partial-block handling.
4. Compare all decoded channels with the OEM CPS.
5. Trace power, signalling, scan, and option fields.
6. Validate write ranges and response behavior before enabling any upload.
