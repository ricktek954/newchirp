# Radtel RT-950 Pro protocol notes

Last updated: 2026-11-20

The RT-950 Pro is a separate NewChirp model. It shares the RT-950/BT-9000
handshake and 32-byte channel encoding, but its CPS layout contains larger
settings segments and an additional `0x54/0x58` block.

## Evidence

### RT-950 Pro CPS (authoritative since 2026-11-19)

- Package: `RT-950PRO_CPS_Setup_v1.3.3.rar` (radtels.com, 2026-06-22),
  SHA-256 `96bf4f13089dd401e74f91d7a7c32d56d98300c1fb03daf2798b40d43fd5191f`
- Executable: `BT-RT950PRO_CPS.exe` (.NET), SHA-256
  `1a20aa5390345f879f64cfe8d3a299671ca0fb975c38bb191958840e9fa6441d`
- Traced: `KDH.RWDataOperation` (`HandShake`, `ReadRadioData`,
  `WriteRadioData`, channel encoders/decoders), `KDH.ChannelData`,
  `KDH.View.FormCHInfo` (option labels), `QtTables.DcsTable`

Findings that override the earlier community-derived map:

- 990 channels (`new Channel[990]`). The CPS channel bound 0x7BC0 is not a
  multiple of 128, so its address switch never fires and it reads and writes
  0x0000-0x7FFF in full.
- One block each at 0x8000 (VFO A/B/C) and 0x9000 (function settings parts
  1-3); DTMF 0xA000-0xA17F; modulation 0xB000-0xB0FF; zone names
  0xC000-0xC0FF; modulation names 0xD000-0xD2FF; APRS via `0x54` (read) /
  `0x58` (write) at 0x0000.
- The handshake requires model code exactly `RT-950`; the base RT-950
  reports `BT-9000`.
- Write frame `57 | addr:u16be | 80 | 128 bytes` (scrambled with the session
  symbol), radio answers `06`; on a 1000 ms timeout the CPS resends the same
  frame, up to 3 times. After the last block the CPS sends `E`.
- Channel record (`SetCHInfo_Parameter`): all `FF` when empty; RX/TX
  frequency as four little-endian BCD pairs in 10 Hz units, TX `FF` means TX
  off; RX tone at 8-9 and TX tone at 10-11 (CTCSS little-endian tone*10, DCS
  table index + 1 with high byte 0, off `00 00`); byte 12 signalling group
  0-14; byte 13 PTT ID (OFF/BOT/EOT/BOTH); byte 14 scramble<<4 | power
  (High/Middle/Low); byte 15 hopping<<7 | narrow<<6 | encryption<<4 |
  BCL<<3 | scan<<2 | AM; FHSS code bytes 16-18 read 18 first (first digit
  3 bits) with marker `A0` at 19; GB2312 name at 20-31 padded `FF`.
- There is no per-channel TX-enable bit: the CPS masks byte 15 bits 0-1
  with `% 2`.
- Transmit range (2026-11-20 trace): `FreqHelper.minFreq = 18`,
  `maxFreq = 1000`; `FormCHInfo` and `ChirpCsvHelper` accept RX and TX in
  18-1000 MHz with no amateur-band check. `FunConfigData`/`VFOData` expose
  no TX-inhibit or TX-band setting. A blank `TxFreq` is written as
  `FF FF FF FF` by `SetFreq_StrToHex` and decoded back to blank by
  `GetFreq_HexToStr`; that is the only per-channel transmit-off encoding.

- Bluetooth setting: `CbB_BTWriteSwitch` is function-settings part 1 byte
  `29`, decoded as `(dat[29] & 0xF) % 2` and encoded back to that byte. The
  CPS labels it "Bluetooth write frequency switch".

### Radtel phone app (static, 2026-11-20)

- Radtel's official RT-950 PRO product page explicitly advertises Bluetooth
  programming with a dedicated iOS/Android app.
- Google Play package: `com.uniapp.kdh.uniplugin_kdh`, app name
  `walkie-talkie tool`, developer `泉州科缔恒电子科技有限公司`, version
  `1.4.7` / version code `147`.
- Research download: APKPure XAPK SHA-256
  `d6af5ef1dec73133c11825e2d99c61a93b5c56d4622ca132e335208c45cfee69`;
  base APK SHA-256
  `5ec56b149e653f28019373a0898373521f991418eee21f3201285c34e62733cf`;
  armv7 `libapp.so` SHA-256
  `1c5b25e05445bf84144296b745c89431cec0d46e279f68e270d058cbcd80d94c`.
- APK signing certificate SHA-256:
  `229e7fed1797c84d16a331133d581288eb12347885440c5314da2b363e36c5a8`.
- Static Dart AOT strings show `flutter_blue_plus`, the FFE1 read/write path,
  `write_without_response`, `handleBluetoothData`, KDH secret-key generation,
  and the radio-family marker `K950`.
- This is application identity and static path evidence only. No OEM BLE byte
  capture or complete decompiled call path is available yet. The app does not
  prove that the stock serial frame is unchanged over BLE.

### Earlier base RT-950 CPS

- Package: `RT-950_EnCPS_Setup_v1.3.0.rar`
- Executable: `BT-9000_CPS.exe`
- Executable SHA-256:
  `605054c46ec17520b0f79b78585c3be431a6dcb95164dc638985455e813d7a1e`
- Resource assembly SHA-256:
  `3c17d6cf42ffda4fa32dfdcf845e8a328dff627987ab88d25e3a12b0b68298a7`

The OEM CPS establishes the shared handshake, randomized `SEND`
authentication, rotating symbol substitution, block framing, channel field
layout, tone encoding, and frequency encoding documented in
`RT950_PROTOCOL.md`.

### RT-950 Pro reference driver

- File: `radtel_rt950pro.py`
- SHA-256:
  `359e673eeafa8ccee20d222276cc4d57194f2a826a443a4cb4b710a81297f2e5`
- Origin: community CHIRP development driver by Nathan G. Barguss, MIT
  licensed
- Evidence level: static reference, not OEM ground truth

This driver supplied the larger Pro read map and confirms that the radio uses
the same transport family as the base RT-950. NewChirp's implementation does
not import or bundle the reference file.

## Transport

- 115200 baud, 8N1
- RTS and DTR asserted
- Hardware and XON/XOFF flow control disabled
- Initial `PROGRAMBT9000U` ACK window: 3.0 seconds
- `F` response: 16 bytes
- `M` response: 12-byte model code
- `SEND`: 25-byte randomized authentication request followed by ACK `0x06`
- Read request: `<command> <address:u16be> 0x80`
- Read response: echoed address plus 128 encrypted payload bytes
- End command: ASCII `E`

The first ACK timeout was increased from the base driver's 1.5 seconds because
the physical Pro reaches Program mode but returned no bytes within the shorter
window.

### Android Bluetooth

- Service/characteristic observed from the reporter: `FFE0` / `FFE1`, MTU 23,
  notification plus write-with/without-response support.
- The stock radio requires its BT Write menu setting. The current hypothesis
  is that the radio ignores programming traffic when that switch is off.
- NewChirp sends the same stock raw frames over BLE: four-byte `0x52/0x54`
  read requests and fixed 132-byte responses. BLE has no physical baud or
  modem-control transition, so the Android bridge does not perform USB setup.
- No BLE-specific terminator or checksum change is implemented. The OEM app
  confirms a BLE programming path, but its exact on-wire frame has not been
  recovered; keeping the stock frame is an E1 implementation hypothesis
  pending a physical comparison.
- Bluetooth read is experimental and unvalidated on hardware. A zero-byte
  handshake or first-block response tells the owner to enable BT Write and
  choose the stock or nicFW950 profile according to the startup screen.
- Bluetooth write is not implemented. The Android UI and driver both refuse an
  upload before sending a radio command.

## Superseded Pro read map (before CPS 1.3.3)

| Command | Radio address | Length | Image address | Content |
| --- | ---: | ---: | ---: | --- |
| `0x52` | `0x0000` | `0x7800` | `0x0000` | 960 channel records |
| `0x52` | `0x8000` | `0x0100` | `0x8000` | VFO settings |
| `0x52` | `0x9000` | `0x0100` | `0x9000` | Function settings |
| `0x52` | `0xA000` | `0x0200` | `0xA000` | DTMF data |
| `0x52` | `0xB000` | `0x0200` | `0xB000` | Modulation parameters |
| `0x52` | `0xD000` | `0x0300` | `0xD000` | Modulation names |
| `0x54` | `0x0000` | `0x0080` | `0xC000` | APRS data |

The complete read is 259 blocks. The saved CHIRP image is `0xD300` bytes with
unread gaps preserved as `0xFF`.

## Channel records

The Pro retains the RT-950's 960 fixed 32-byte records:

- RX and TX frequencies: four little-endian base-100 fields in 10 Hz units
- RX and TX tones: two-byte CTCSS/DCS words
- Signalling group, PTT ID, power, scrambler, encryption, busy lock, scan,
  transmit enable, modulation, bandwidth, FHSS, and a 12-byte GB2312 name

## Read/write policy

- USB: the CPS-derived read/write path remains enabled as experimental. Writes
  require an image read from the current radio and send the CPS block map.
- Android Bluetooth: read-only. Uploads are refused by the Android controller
  and by the driver before a radio command is sent.
- Physical Bluetooth read validation: none.
- Physical Bluetooth write validation: none, and the operation is deliberately
  unavailable.

Next milestone: a stock-firmware owner enables BT Write, selects
`Radtel RT-950 Pro`, completes a full Android Bluetooth read, and sends the
Bluetooth diagnostics. Bluetooth writes require a complete physical read and a
separate dropped-link recovery design review.
