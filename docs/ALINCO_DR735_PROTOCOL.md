# Alinco DR-735 programming protocol

Source: Alinco **DR-735 Memory Editor 0.06**, the official freeware clone
utility from Alinco's DR-735T/E download page. It was decompiled with
ilspycmd and is unobfuscated .NET (VB.NET).

| Artifact | SHA-256 |
| --- | --- |
| `DR-735_Memory_Editor_0.06.zip` (download) | `3931cfc1cab4b977d4f433582850995ed323cd7dc3c1f62e247281c0c7992924` |
| `DR-735 Memory Editor ver.0.06.exe.deploy` | `a7e5ce73a821bb2469b546edfe943c8c7cac6cea39314b4a2599c7aa71f80eaa` |

Key classes: `sio` (serial port), `Form1.btRead_Click` / `btWrite_Click`
(sequencing), `Form1.ExpandMem` (record decoder), `Memory.btnOK_Click`
(record encoder), and `Module1` (tables and band limits).

Evidence levels: **E1** is the static trace of the OEM code. **E2** is
replay against fakes in `test/alinco_dr735_driver_test.py`. The stock CHIRP
image `tests/images/Alinco_DR735T.img` (SHA-256
`0e16a6265403cca457b7fe64f1091d89dc35cebbc23f1716aa5d9f906835c5f9`)
gives real record bytes. There is no NewChirp physical-radio evidence yet.

## Cabling and modes

- The cable is the Alinco ERW-7 (FTDI USB serial, 3.5 mm plug), plugged into
  the **LEFT speaker jack on the rear panel**. The ERW-7 conversion plug is
  not used.
- The radio is powered on normally. Alinco's notes say to disregard the
  manual's Clone mode instructions and not enter Clone mode for this utility.
- The ERW-7 is a single wire, so the host sees each command echoed before
  the radio's reply. `sio.ECHO` is always `True` in the OEM editor.

## Serial settings

.NET `SerialPort` defaults: 38400 baud, 8N1, no handshake. DTR and RTS are
deasserted. Only `BaudRate` and `PortName` are set.

## Framing (`sio.SioSendData`)

- The host sends `command + "\r\n"`.
- It collects input until the buffer matches `\r\n.*\r\n` (echo line, then
  reply line) or the timeout expires.
- It strips the echo (`len(command) + 2` characters) and all CRLFs, and
  returns the rest.
- The timeout is 100 ms for `AL~`, `AL~WHO`, `AL~DR735J` and `AL~RESET`, and
  500 ms for every `AL~EEPEL` / `AL~EEPDL` block.

## Commands

| Command | Reply | Use |
| --- | --- | --- |
| `AL~` | `OK` | Wake / sync. Sent first by Read only. |
| `AL~WHO` | model ID | Identity, checked against the list below |
| `AL~EEPEL<aaaa>R` | 128 hex digits | Read a 64-byte common-channel record |
| `AL~EEPEL<aaaa>W<128 hex>` | `OK` | Write a common-channel record |
| `AL~EEPDL<aaaa>R` | 128 hex digits | Read a 64-byte record in the second space |
| `AL~EEPDL<aaaa>W<128 hex>` | `OK` | Write a record in the second space |
| `AL~DR735J` | `OK` | Enter write mode (before the first write) |
| `AL~RESET` | `OK` | End of write; the radio reboots |

`<aaaa>` is 4 uppercase hex digits. Common channel *n* (0–999) is at
`EEPEL n*64`, so 0x0000–0xF9C0. CHIRP feature #11857 found that `EEPEL`
addresses above 0xFFFF time out. The OEM never uses them: the extended
channels live in the `EEPDL` space.

### Model IDs (`btRead_Click`, `Module1.CheckFreq`)

| ID | Allowed ranges |
| --- | --- |
| `DR735EN` | 144–146, 430–440 MHz |
| `DR735RN` | 144–148, 430–440 MHz |
| `DR735J`, `DR735EE`, `DR735GN`, `DR735GE`, `DR735TN`, `DR735TE`, `DR735RE` | 108–136 (AIR), 136–174, 400–480 MHz |

Any other reply shows "MODEL NG". Stock CHIRP accepts only `DR735TN` and
`DR735TE`.

## Read sequence

1. `AL~` → `OK`
2. `AL~WHO` → model
3. Common channels 0–999: `EEPEL n*64`
4. Left L00–L99: `EEPDL 0xC000 + i*64`
5. Right R00–R99: `EEPDL 0xE000 + i*64`
6. Program scan P1A–P5A: `0x1000 + i*64`; P1B–P5B: `0x1200 + i*64`
7. Call channels: VHF `0x1400`, UHF `0x1480`
8. Auto program scan: APL `0x1180`, APH `0x1380`
9. Dual memories d00–d99, L/R pairs: `0x2000 + i*64` for 200 records
10. VFOs: L-VHF `0x0100`, L-UHF `0x0180`, L-AIR `0x1500`, R-UHF `0x0140`,
    R-VHF `0x01C0`, R-AIR `0x1540`
11. Colors `0x0080`; settings `0x0000` + `0x0040`; DTMF `0x1700`, `0x1740`,
    `0x1780`

A block that isn't exactly 128 characters shows "ERR".

## Write sequence

1. `AL~WHO` (no `AL~` wake)
2. `AL~DR735J` → `OK`
3. Each common channel: if `used == 0x55`, check the frequency against the
   model ranges; then `EEPEL W` → `OK`
4. L, R, P, call, APL/APH and dual records (`EEPDL W`), then VFOs
5. Colors (`0x0080`). Settings are **read again**, modified, and written back
   (`0x0000`, `0x0040`). Then DTMF.
6. `AL~RESET` → `OK`

## 64-byte channel record

Offsets are bytes. Multi-byte fields are little-endian.

| Off | Field | Values |
| --- | --- | --- |
| 0 | used | `0x55` in use; anything else is empty |
| 1 | skip | 0/1 |
| 2 | favorite | 0/1 |
| 3 | step | index into AUTO, 5, 6.25, 8.33, 10, 12.5, 15, 20, 25, 30, 50, 100. Forced to 0 on memory channels. |
| 4–7 | frequency (Hz) | u32 |
| 8–11 | shift (Hz) | u32 |
| 12 | shift direction | 0 simplex, 1 −, 2 + |
| 13 | subtone | 0 none, 1 TONE (encode), 3 TSQ (encode + decode), 0x0C DCS |
| 14 | encode tone | index into 39 tones (CHIRP `ALINCO_TONES`) |
| 15 | decode tone | same table |
| 16 | DCS | index into 104 codes |
| 17 | DCS (copy) | the editor writes the same index as byte 16 |
| 18 | power | 0 H, 1 M, 2 L |
| 19 | BCL | 0/1 |
| 20 | mode | 0x00 FM, 0x01 NFM, 0x02 AM, 0x03 NAM, 0x80 AUTO |
| 21 | heterodyne | 0 normal, 1 reverse |
| 23 | bell | 0/1 |
| 24–29 | name | byte = 0x30 + index in `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ *#+-/\=()$_`. Unused characters are 0x00; an unknown character becomes 0x54 (space). |
| 30 | dcsOff | 0/1 |
| 32 / 33 / 34 | standby / RX / TX color | 0–15 (CL0–CLF) |
| 56–57 | banks | u16 bit mask; bit *n* is bank *n*+1. The grid accepts banks 1–10 only. |
| 58–59 | pch | u16. `0x8000 | n` links common channel *n* (0–999); `0x0000` is none. |
| 22, 31, 35–55, 60–63 | unknown | Preserved |

- **Decoder rule (`ExpandMem`).** Any field outside its table makes the OEM
  editor treat the record as blank.
- **Delete.** Deleting a row writes 64 bytes of `0xFF`. The call channels
  cannot be deleted; they reset to the defaults shown below.
- **New rows.** A new row starts from 64 zero bytes.
- **Defaults.** The VHF call channel defaults to 145.000 MHz, UHF to
  433.000 MHz, and AIR to 118.000 MHz (`strVHFdef`, `strUHFdef`,
  `strAIRdef`).

## Stock CHIRP defects found

| Defect | Effect |
| --- | --- |
| No `AL~` wake before `AL~WHO`. | The first command after opening the port can fail. |
| Only `DR735TN` / `DR735TE` accepted. | J, EN, EE, GN, GE, RN and RE radios get "Unsupported radio model". |
| Uses the bridge's 0.25 s read timeout (the OEM uses 500 ms) and calls `exit(1)` on a short block. | In a frozen app `exit` is undefined, so the read dies with a `NameError` within about a second. This matches the 2026-11-19 forum report. |
| `AL~DR735J` failure ignored. | `errors.RadioError(...)` is created but never raised. |
| TSQL writes byte 14 from CHIRP `rtone` and byte 15 from `ctone`. | A TSQL channel can transmit the wrong tone. Channel 0 of the stock test image (W4HSV) shows this: 88.5 encode with 100.0 decode. |
| DCS byte 17 never written. | It keeps a stale value. |
| `can_delete = False`. | Channels cannot be deleted. |
| Names limited to 0-9, A-Z and space. | The radio supports 11 more symbols. |
| No banks or linked channel. | 10 banks and the pch link are not shown. |
| No extended channels, VFOs or settings. | Channels 1000–1413 cannot be reached. |
| No per-model band check before writing. | Out-of-range channels can reach the radio. |
