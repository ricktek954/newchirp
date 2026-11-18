# Kenwood TM-V71A/E Clone Protocol (from MCP-2A 3.22)

Last updated: 2026-11-18

Driver: `drivers/newchirp_tmv71.py` (`KenwoodTMV71CloneRadio`,
model `Kenwood_TM-V71_CloneMode`). Status: experimental, **read-only**.

## Artifact inventory

| Item | Value |
| --- | --- |
| Application | Kenwood MCP-2A (Memory Control Program), setup version 3.22.0.0, JVC KENWOOD Corporation |
| Archive | `M2A322.zip`, SHA-256 `901596b9b52d398131408d257c54dfb0548e79f269dfe830792a6e9ebce0e678` |
| `setup.exe` (InstallShield 24 bootstrapper) | `7408d9bb0a473687c8484f1669dd6765521c919ada4d10e96b7b62c95b28b0b2` |
| `MCP-2A.exe` (.NET, x86, Dotfuscator control-flow obfuscation) | `e7a71f0e58b32ec02f41f6da5f1b6b927177c0ba5a3b7a497c19cff23421bf48` |
| `Localize.dll` | `fc3e2f169a10bbc16373c20be32873d46e276081d8c27eb0345fc1762defe82f` |

Extraction: the PE overlay at `0xE5A00` holds a count followed by UTF-16
name/path/version/size records (`data1.cab`, `data1.hdr`, `data2.cab`, ...).
`unshield` extracts `Program_Files/MCP-2A.exe`, and `ilspycmd` decompiles it.
Class names survive obfuscation. Method bodies are flattened state machines
and were traced by following the case labels.

Models in `SystemEnum.EnumModelName`: `MN_TMV71`, `MN_TMD71` (TM-D710),
`MN_TMR71` (RC-D710 head), `MN_TMD71P` (`TM-D710P`, which MCP-2A refuses
with error -6).

## Serial lifecycle (`Communication..ctor`, `Communication.a(bool)`)

- 8 data bits, no parity, 1 stop bit. `DtrEnable = RtsEnable = true`.
  `Handshake = RequestToSend` (RTS/CTS).
- `ReadTimeout = 100 ms` per byte and `WriteTimeout = 500 ms`. The port is
  reopened with `ReadTimeout = 1000 ms` before `TY`.
- Baud comes from the registry or auto-detection. On a `TC` timeout the
  auto-baud cycle is 9600 → 57600 → 38400 → 19200 → 9600, up to three
  rounds. Handshake and RTS are dropped while the baud changes.
- No baud change occurs after `0M PROGRAM`.

NewChirp uses the pinned CHIRP Kenwood live `ID` probe (4800–115200), which
is proven on the TM-V71 live driver, then sets a 1 s timeout for clone
traffic.

## Protocol contract

| Action/state | Host bytes | Response encoding / layout | Length & completeness | Retry / next | Evidence |
| --- | --- | --- | --- | --- | --- |
| Terminal-control probe (`Seq_TC_Command`) | `TC 1\r` | ASCII. `?` + CR, or `T` + 4 bytes + CR | Fixed. Each byte read with the 100 ms timeout | On timeout: baud cycle, retry TC | E1. **Not sent by NewChirp** |
| Identity (`Seq_ID_Command`) | `ID\r` | ASCII `ID ` + model (≤ 8 bytes) + CR | Terminated by CR, max 8 model bytes | Retried once on timeout. Prefix-matched against `TM-V71`, `TM-D710P`, `TM-D710`, `RC-D710` | E1. NewChirp requires the `TM-V71` prefix |
| Market type (`Seq_TY_Command`) | `TY\r` | ASCII `TY ` + 9 chars `a,b,c,d,e` (commas at 1, 3, 5, 7) + CR | Fixed | Fills `MakeTYInfo` (market/region) | E1. **Not sent by NewChirp** |
| Firmware (`Seq_FV_Command`) | `FV 0\r` (V71) | ASCII `FV 0,` + version (13 bytes) + CR | Fixed | Informational | E1. Not sent |
| Enter clone (`Seq_0M_Command`) | `0M PROGRAM\r` | ASCII `0M\r`. `N` = refused | Fixed 3 bytes | Failure aborts | E1, E2 |
| Read block (`Communication.b(int,int)`) | `52 hi lo len` (`len` = count & 0xFF, so 256 → `00`) | Binary `57 hi lo len` echo, then `len` payload bytes | Fixed. The echo is byte-checked against the request. Payload is read byte-by-byte to the requested count; a shorter reply is a timeout failure | Then host sends `06` and must receive `06`. Any mismatch → -3 (abort) | E1, E2 |
| Write block (`Communication.a(int,int)`) | `57 hi lo len` + payload | Binary single byte `06` | Fixed 1 byte | Any other byte → abort | E1. **Disabled in NewChirp** |
| Exit (`Seq_E_Command`) | `E` | `06` | 1 byte | — | E1, E2 |
| Quit (`Seq_Q_Command`) | `Q` | `06` | 1 byte | Write path only | E1 |

No checksums exist at the block level. Responses are binary, not hex text.

## Address ranges (`Sequense_MemRead`, `Sequense_MemWrite`)

Blocks are 256-byte aligned. Each length is `256 - addr % 256`, clipped to
the range end.

| Model | Read | Write |
| --- | --- | --- |
| TM-V71 | `0x0000–0x7EFF` | `0x0004–0x7EFF` (bytes 0–3 untouched) |
| TM-D710 | body + `0x8000–0x9BFF` + `0xFEF0–0xFF8F` | body from 4 + `0x8003…` + FE/FF |
| RC-D710 | `0x8000–0x9BFF` + `0xFEF0–0xFF8F` | head ranges only |

`0x7F00` (`MemAdr_Adjust_START`) starts the factory adjustment area and is
never accessed. Before writing, `Sequense_PreMemWrite` handles password
protection (byte `0x23`, password at `0x2A`) and clears bytes `0x10/0x11`
(repeater / external remote). Port these rules before any write is enabled.

## Memory map (body)

MCP-2A uses a single shared map (`MemMapAddress`). Its body offsets match
pinned CHIRP `tmd710.KenwoodTMD710Radio.MEM_FORMAT` exactly, so the driver
reuses that layout below `#seekto 0x08660`:

| Offset | Content |
| --- | --- |
| `0x0000` | type, ROM type, power, packet/EchoLink modes, global settings |
| `0x0030` / `0x00D0` | DTMF memories / names |
| `0x0170` | repeater ID |
| `0x0200–0x0DFF` | PM groups 0–5 (512 bytes each) |
| `0x0E00` | channel flags (`MemChFlag`): 1000 memories + program-scan, WX, call |
| `0x1700` | channel data, 16 bytes × 1030 (`MemChData`) |
| `0x5760` | call channels |
| `0x5800` | channel names, 8 bytes each (`MemNameData`) |
| `0x7D00` | MCP group / PM names, comment |

Names are 8 characters: `Collection.GetMemoryNameLength` returns 8 for
`ReleaseVer >= 2`, and `SystemConfig.ReleaseVer` is the constant 3. The
driver restricts names to uppercase to match the pinned CHIRP TM-V71 live
driver. Sky Command (`0x8660`) is head-only and removed from settings.

The image stores radio bytes as read. Stock CHIRP's TM-D710 driver copies
byte 1 into byte 0, mirroring MCP-2A's file convention of storing the `TY`
market letter at offset 0. This driver does not.

## Evidence levels

- Transport and ranges: E1 (static trace) and E2 (`test/kenwood_tmv71_driver_test.py`
  replays full, fragmented, wrong-echo, short-block, NAK, refused-0M, and
  wrong-model sessions).
- Memory decode: E1 against MCP-2A and the CHIRP TM-D710 layout. No TM-V71
  image has been compared.
- E3–E5: none.

## Open items

1. Physical TM-V71A/E read (E3/E4), compared with MCP-2A's view of the same
   radio.
2. Confirm whether firmware before 2.0 limits names to 6 characters.
3. Decide whether to send `TC 1`/`TY` like MCP-2A. Prefer this if a radio
   refuses `0M` without them.
4. TM-V71 body fitted with the RC-D710 head (`ComModelCheckCode` 3/5).
5. Writes: port the `PreMemWrite` password and repeater rules, write from
   `0x0004`, then do a controlled edit and read-back (E5).
