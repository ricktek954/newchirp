# Radtel RT-860 CPS protocol notes

Last updated: 2026-11-06

These notes cover the official Radtel RT-860 CPS and the experimental
read-only NewChirp driver. The OEM application is not part of this
repository.

## Evidence inventory

- Official product page:
  <https://www.radtels.com/pages/software-download>
- CPS listing: **Radtel RT-860 CPS PC Programming software V1.06 250620**
- Archive: `RT-860_Radio_CPS_V1_06_250620.zip`
- Archive SHA-256:
  `4a5a4b00a79fa4f6aae8ab77ae40cbaa954033b0089a3250e0a02448ae478a26`
- Extracted application: `RT-860 Radio CPS_V1_06_250620.exe`
- Application SHA-256:
  `f9b3d9d3fadae96caa3a1a0480a0f8a8622957d2142a745e70c1b711393ada69`
- Runtime and format: 32-bit .NET Framework WinForms application
- PE product metadata: `R6000`; internal filename
  `UV88 Radio Program.exe`; version `1.0.0.0`
- Evidence level: E1 for the complete read path and E2 for its synthetic
  replay tests. No OEM serial capture or physical RT-860 read is recorded.

The archive was downloaded from Radtel's official CDN and verified before
extraction. The executable was inspected as metadata and CIL; it was not run.

## UI-to-serial read path

`ReadForm.btnRead_Click` opens the existing serial port, installs
`MainForm.Comm_DataReceived`, sets connection and read state, and sends the
entry command. `MainForm.RevDateOperation` runs the read state machine:

1. Wait for one-byte programming-mode ACK `06`.
2. Request physical page `0x0008`.
3. Validate the 1,028-byte response and copy its 1,024-byte payload into
   `bufCFG`.
4. Continue through the sparse page list in the table below.
5. Send the exit command after page `0x035B`.

The CIL evidence is in `ReadForm.btnRead_Click` at offsets `0x01B3-0x024D`
and `MainForm.RevDateOperation` at offsets `0x00CD-0x060B`. The entry and
exit byte arrays are initialized in `MainForm..ctor` from field RVA
`0x0002BE68` (`5` bytes, entry) and `0x0002BE70` (`5` bytes, exit).

## Serial configuration

`PortForm.btnEnsure_Click` and `MainForm.MainForm_Load` set:

- 115200 baud
- 8 data bits, no parity, one stop bit
- `DTR = true`
- no hardware RTS/CTS flow control
- no XON/XOFF flow control

The UI opens and closes the configured port once as a probe before the read.
The programming session itself opens the port, discards input and output, and
sets `ReceivedBytesThreshold` to one byte.

## Command contract

All block checksums are an unsigned 8-bit sum. Bytes wrap modulo 256.

| Action/state | Host bytes | Response | Completeness | Next state | Evidence |
| --- | --- | --- | --- | --- | --- |
| Enter programming mode | `34 52 05 10 9B` | `06` | Exactly one ACK byte | Request page `0x0008` | Static byte array at RVA `0x2BE49`; receive state `0xCD-0x16B` |
| Read physical page | `52 AH AL SUM` | `52 AH AL <1024 data> SUM` | Exactly 1,028 bytes | Validate checksum and remap page | `RevDateOperation` offsets `0x173-0x3A4` and `0x610-0x6A2` |
| Exit programming mode | `34 52 05 EE 79` | None consumed | 10 ms delay before close | Close serial port | Static byte array at RVA `0x2BE57`; offsets `0x582-0x5C0` |

For a read command:

```text
AH   = physical_page >> 8
AL   = physical_page & 0xFF
SUM  = (0x52 + AH + AL) & 0xFF
```

The response checksum covers every preceding byte, including the echoed
`52 AH AL` header and all 1,024 payload bytes:

```text
SUM8(response[0:1027]) == response[1027]
```

The OEM receive callback reads one byte at a time (`ReadByte`) and increments
`cntRecv`. A 1,028-byte frame can therefore arrive across many callbacks. The
state machine advances only when the first byte is `52` and `cntRecv == 1028`;
it does not accept a short frame as a complete block.

## Sparse physical-page plan

The CPS does not clone every physical page. It reads 184 pages and copies them
into a logical image with unused gaps:

| Data | Physical pages | Count | Logical image range | CIL copy offsets |
| --- | --- | ---: | --- | --- |
| Settings | `0x008-0x00B` | 4 | `0x00000-0x00FFF` | `0x3C3-0x3F7` |
| Channels | `0x010-0x03F` | 48 | `0x02000-0x0DFFF` | `0x416-0x44B` |
| Zones | `0x070-0x0EF` | 128 | `0x1A000-0x39FFF` | `0x46D-0x4A2` |
| Broadcast memories | `0x358-0x35B` | 4 | `0xD4000-0xD4FFF` | `0x4C1-0x4F9` |

`MainForm.RevDateOperation` jumps between those ranges after physical pages
`0x00B`, `0x03F`, `0x0EF`, and `0x35B`. The driver constructs a
`0xD5000`-byte image and leaves the intervening gaps as `0xFF`.

## Channel layout

`MainForm.SetChInfo` establishes a 48-byte channel record:

| Offset | Size | Meaning | Evidence |
| ---: | ---: | --- | --- |
| `0x00` | 1 | Demodulation: `0` FM, `1` AM, `2` SSB | `SetChInfo` `0x005A-0x007E`; CPS combo values |
| `0x01` | 1 | RX/TX limit flags | Shared iRadio record layout; not exposed |
| `0x02` | 1 | Active marker; CPS treats `1` as present | `SetChInfo` `0x0016-0x002A` |
| `0x03` | 1 | Narrow bandwidth flag | `SetChInfo` `0x02B2-0x02D3` |
| `0x04-0x05` | 2 | RX CTCSS/DCS | `SetChInfo` `0x01BA-0x0202` |
| `0x06-0x09` | 4 | RX frequency, little-endian, units of 10 Hz | `SetChInfo` `0x007F-0x011A` |
| `0x0A-0x0D` | 4 | TX frequency, little-endian, units of 10 Hz | `SetChInfo` `0x011B-0x01B9` |
| `0x0E-0x0F` | 2 | TX CTCSS/DCS | `SetChInfo` `0x0203-0x024D` |
| `0x10` | 1 | Power: `0` Low, `1` High | CPS combo values; `SetChInfo` `0x024E-0x0294` |
| `0x11` | 1 | TX priority | `SetChInfo` `0x0324-0x0369` |
| `0x12` | 1 | Low five bits TOT; high three bits CTC/DCS selection | `SetChInfo` `0x03FD-0x048A` |
| `0x13` | 1 | Scan bit 7, tail-tone bits 4-6, scrambler bits 0-3 | `SetChInfo` `0x02D9-0x03FC` |
| `0x14-0x17` | 4 | Mute code, big-endian display order | `SetChInfo` `0x0490-0x0514` |
| `0x18-0x1F` | 8 | Preserved/unknown channel bytes | Layout comparison with RT-880G |
| `0x20-0x2F` | 16 | Channel name, GBK, NUL/`FF` padded | `SetChInfo` `0x0515-0x0583` |

The channel array starts at logical image offset `0x02000`. The CPS exposes
1,024 channels.

The CPS calls mode value `2` **SSB**. CHIRP names this analog SSB memory mode
**USB**; the precise rule that selects LSB versus USB, and any CW path, has not
been established from a physical radio.

## Zone layout

`MainForm.DataToPanel` establishes 512-byte zone records at logical image
offset `0x1A000`, with 256 zones:

| Offset | Size | Meaning |
| ---: | ---: | --- |
| `0x000` | 1 | Membership count |
| `0x001` | 1 | Duplicate membership count |
| `0x004-0x013` | 16 | Zone name |
| `0x014-0x1A3` | 400 | 200 little-endian, zero-based channel numbers |

The remainder is preserved. Empty membership entries are `0xFFFF`.

## Retry and failure behavior

- The CPS retries the entry exchange up to three times with 200 ms settling
  delays.
- It aborts on an unexpected first byte, a wrong echoed page, a short
  response, or an incorrect checksum.
- Its progress timer aborts after 1,000 default-interval timer ticks. The
  NewChirp driver uses a one-second block timeout, which is stricter and
  sufficient at 115200 baud.
- The read-only driver always attempts the OEM exit command after a session
  was entered, including on malformed-response failures.

## Write-path boundary

The CIL contains a separate write state machine. It first reads physical page
zero and then emits 1,028-byte `0x90-0x93` region blocks, plus an optional
`0x9A` startup-image block. Those commands are not implemented or enabled by
NewChirp because the CPS password/authentication branch and complete
post-write acknowledgement sequence have not been replay-tested or validated
on hardware.

## Offline validation

`test/rt860_driver_test.py` covers:

- catalog registration and DTR/serial policy
- the exact 184-page sparse read order
- entry and exit magic
- fixed 1,028-byte framing and additive checksums
- fragmented receipt with a 113-byte maximum read
- wrong page echo, malformed checksum, and truncated responses
- channel frequency/name/power decoding
- zone membership decoding
- disabled uploads

## Remaining work

1. Capture the official CPS reading a physical RT-860.
2. Complete an unedited NewChirp read and compare every decoded channel and
   zone with a CPS export.
3. Resolve LSB/USB/CW behavior and the unknown channel bits.
4. Replay-test the OEM upload state machine before enabling any write.
5. Perform one controlled channel write and read-back, then restore the
   original image.
