# Wouxun KG-689E / KG-699E programming protocol

Recovered by static analysis of Wouxun's own programming software. No
physical radio, serial capture, or radio image has been examined yet.

## Evidence

| ID | Kind | Item | SHA-256 |
|---|---|---|---|
| E1 | OEM package | `689E_SOFT_CON.rar` (wouxun.com/resource) | `9a7b56650b30b9eac691f7b638cf0d87b84051d63c1d51add239ae4fb3876c4b` |
| E1 | Installer | `KG-689E-699E Setup.exe` (Setup Factory 6) | `a4432d443244a655bda49b7643e7adbfe3bc65288843d6d5ceece87b052dc597` |
| E1 | Programmer | `KG-699E 689E.exe` (MFC42, 184,320 bytes) | `21620918dc196e04631bc88e761fd7ff17add76156f3c57ca0bd2a55bd77f554` |
| E1 | UI strings | language CSV from the installer | `0bfb692fba9046a1aeb2ab1c693d50d2fbf9b074dc34462734851177bcdba863` |
| E2 | OEM package | `699E_SOFT_CON.rar` (66-88 MHz package) | `4d0a43c9c1371805c253752abad36bbb0c8dd0030b4a87f5ab0984ff06caddd2` |
| E3 | Replay tests | `test/wouxun_kg689e_driver_test.py` | — |

Both packages are archived in the maintainer's Downloads folder.

Unpacking: the installer overlay starts at file offset `0x11000`. After an
8-byte signature, the setup engine (`irsetup.exe`) is stored XOR `0x07` with
a 4-byte length. Then come four named entries (260-byte name, size, CRC-32)
compressed with PKWARE DCL implode, followed by six back-to-back DCL streams.
The sixth stream is the programmer. Every CRC-32 matched.

Addresses below are virtual addresses in `KG-699E 689E.exe` (image base
`0x400000`).

## Serial setup (`0x40b5ae`)

`CreateFileA`, then `GetCommState` and `SetCommState`:

- 9600 baud, 8 data bits, no parity, one stop bit, binary mode.
- DTR enabled (`fDtrControl = 1`); RTS left at the driver default.
- Timeouts: interval 388 ms; read 1000 ms per byte plus 1000 ms; write
  2000 ms per byte plus 2 ms.
- `SetupComm(4096, 1024)`.

## Session

| Step | Host sends | Radio answers | Code |
|---|---|---|---|
| Wake | (200 ms pause, `PurgeComm`) `HiWOUXUN 02` | `06` | `0x40b722`, retried up to 20 times |
| Identify | `02` | `06 'K' 'G' '6' '6' '9' 'V' F8` (exact) | `0x40b7c2` |
| Enter | `06` | `06` | `0x40b7c2` |
| Read | `52 hi lo 40` | `57 hi lo 40` + 64 bytes | `0x40b8e2` |
| Read ack | `06` | `06` | `0x40b8e2` |
| Write | `57 hi lo 10` + 16 bytes | `06` | `0x40b9b8` |

Reads have no checksum. There is no end-of-session command; the CPS closes
the port. The identity is the same `KG669V` as CHIRP's KG-UVD1P, but the
exchange differs: KG-UVD1P expects a 9-byte reply to the wake string.

## Block plan

The block table is built at runtime (`0x415e1f`). The address high byte is
sent first.

Read (thread `0x41df2d`), 67 blocks of 64 bytes:

1. `0x0010` to `0x07D0` in steps of `0x40`: the 128 channel records.
2. `0x1010` to `0x17D0` in steps of `0x40`: the 128 channel names.
3. `0x0810`, `0x0E20`, `0x1810`: settings.

Write (thread `0x41e1e2`):

1. Read block `0x0970` and send window message `0x47b` (handler `0x4100ee`
   → `0x416799`). A false result ends the write before anything is sent.
2. The channel and name pages, each as four 16-byte writes.
3. `0x0810` and `0x0820` only (32 bytes).
4. `0x0E20` to `0x0E50` (64 bytes).
5. `0x1810` and `0x1820` only (32 bytes).

`0x0830-0x084F`, `0x1830-0x184F`, `0x0970` and everything else are never
written.

## Frequency limits (`0x416799`)

Block `0x0970` holds the radio's own limits as big-endian BCD whole MHz,
converted with `atoi(itoa(value, 16))`:

| Offset | Meaning |
|---|---|
| `0x0974` | RX low |
| `0x0976` | RX high |
| `0x097C` | TX low |
| `0x097E` | TX high |

For each of the 128 channels whose RX low four BCD digits are valid
(`0x41d5a0`), the CPS requires `low <= RX <= high + 0.995 MHz`, and the same
for TX when TX is valid. One range per direction means each radio is single
band. This is what keeps a KG-699E (66-88 MHz) image off a KG-689E.

## Channel record (16 bytes at `0x0010 + 16 * (n - 1)`)

| Bytes | Field |
|---|---|
| 0-3 | RX frequency, little-endian BCD, 10 Hz units |
| 4-7 | TX frequency, same; invalid BCD means TX off |
| 8-9 | RX tone (decoder), little-endian |
| 10-11 | TX tone (encoder), little-endian |
| 12-13 | Flag word, little-endian |
| 14-15 | Unknown; never written by the CPS |

Tone word (`0x41d9de` decode, `0x41d71f` encode): `FFFF` off. A high byte
below `0x28` is CTCSS in 0.1 Hz. Otherwise it is DCS, with the code in the
low 9 bits (octal): `0x2800 | code` is normal and `0xA800 | code` inverted.

Flag word (grid `0x40370e`, column headers from the language table, encoder
`0x4043db` read-modify-write):

| Bit | Mask | Column | 0 / 1 |
|---|---|---|---|
| 1 | byte 12 `0x02` | Optional Signal | OFF / DTMF |
| 3 | byte 12 `0x08` | Busy Lock | OFF / Carrier wave |
| 5-6 | byte 12 `0x60` | Mute Mode | 0 QT, 1 QT+DTMF, 2 QT*DTMF |
| 12 | byte 13 `0x10` | Bandwidth | Narrow / Wide |
| 13 | byte 13 `0x20` | TX Power | Low / High |
| 14 | byte 13 `0x40` | Scan Add | OFF / ON |

The CPS never touches bits 0, 2, 4, 7-11 and 15.

## Channel name (6 bytes at `0x1010 + 16 * (n - 1)`)

Codes (`0x404a06`): `0-9` → 0-9, `A-Z`/`a-z` → 10-35, `?` → 36, `+` → 37,
`-` → 38. The first other character ends the name; it and the rest become
`FF`. An empty channel gets an all-`FF` name.

## NewChirp policy

- Desktop driver `drivers/newchirp_wouxun_kg689e.py` follows the read and
  write plans exactly. It also reads `0x0970` during a read so the channel
  editor can show the radio's real range. That command is one the CPS sends
  before every write.
- Writes repeat the CPS limit check against a fresh `0x0970` read and stop
  before any write when a channel is out of range or the radio reports no
  limits.
- Unknown bits and bytes are preserved. A newly used slot starts wide, high
  power, scan on, every option off, with bytes 14-15 left erased.
- Settings blocks are read and written back unchanged; they are not decoded.

## Not yet established

- Physical radio behaviour, timing, and a real image.
- The meaning of the settings blocks and of bytes 14-15.
- Whether the radio accepts a write without the `0x0970` read first (the CPS
  always reads it).
