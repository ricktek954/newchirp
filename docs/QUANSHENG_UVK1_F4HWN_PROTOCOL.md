# Quansheng UV-K1 / UV-K5 V3 F4HWN 6.3 Protocol

Last updated: 2026-11-06

## Scope

This note covers the Quansheng UV-K1 and UV-K5 V3 running the open-source
F4HWN Fusion, FieldOps, Transfer, or Labs 6.3 firmware. It does not cover the
stock Quansheng 7.03.x image layout.

The reporter's radio returned this exact hello frame prefix:

```text
ab cd 28 00
03 69 30 e6 68 a5 45 17 6f 15 a3 76
3d 30 c7 b0 16 6c 14 e6 2e 91 0d 40 21 35 d5 40
```

Deobfuscating the body produces:

```text
15 05 24 00 46 34 48 57 4e 20 76 36 2e 33 2e 30
```

The returned firmware identity is `F4HWN v6.3.0`.

## Evidence

| Item | Evidence |
| --- | --- |
| Firmware source | `armel/uv-k1-k5v3-firmware-custom`, commit `3261ca7883d5b0b60c0905d8766612dee7b4191d`, release `v6.3.0` |
| Matching F4HWN CHIRP driver | `f4hwn.chirp.v6.3.0.py`, SHA-256 `a307886d90b6481b441c2cd34b622c8dacfc2080a34fc1e0ea2377054ee4ef96` |
| Firmware release URL | `https://github.com/armel/uv-k1-k5v3-firmware-custom/releases/tag/v6.3.0` |
| Reporter hello | `F4HWN v6.3.0`, Linux report UID 464 |
| Implementation evidence level | E1 static source tracing plus E2 replayable synthetic serial tests |

The F4HWN serial implementation and CHIRP driver agree on the command framing,
512-byte memory block, 128-byte transfer chunks, settings offsets, and UI field
encoding.

## Stock Quansheng CPS Is Not F4HWN

The current official stock CPS package was located and recovered without
executing its installer:

- Product page: `https://en.qsfj.com/support/downloads/8740`
- Archive: `UV-K1-CPS-Upgrade-Tool-Firmware-2026.06.08.zip`
- Archive SHA-256:
  `ad75ee648041a9f1d0236ea2dc25d4e1e17e69280387fe094c32f11d0331cc30`
- Setup Factory installer SHA-256:
  `4c093ae2b730f204ceba32812e6356ee4aec11b3460751904dc938b8c9b50b5d`
- Extracted CPS executable `PSCPS.exe` SHA-256:
  `01f3ed844b1543178c1d98ca9f66868b1e9a848d815f0ca49f8225239e045667`
- Extracted setup runtime hash:
  `irsetup.dat`, SHA-256
  `87d06327f2436e6aab29d0e8ff22b9a30617b4301acdef07abf0273775cd6e66`

The package is Setup Factory 9.1 with LZMA-compressed contents and contains the
stock CPS, `PSCPS.exe`, the 7.03.05 English firmware, and support libraries.
Its CPS is not a source for the F4HWN map. F4HWN is separate open-source
firmware and publishes its own matching CHIRP driver.

## Transport

- Baud: 38400, 8N1, no hardware or software flow control.
- Frame:
  `AB CD <body-length:u16le> <xor(body)> DC BA`.
- XOR key:
  `16 6C 14 E6 2E 91 0D 40 21 35 D5 40 13 03 E9 80`.
- Request body includes command, payload length, payload, and a
  CRC-16/XMODEM trailer before obfuscation.
- Reply body includes command and payload, without a trailing CRC in the
  observed radio replies.
- The host deobfuscates the reply and reads the declared body length directly.

## Protocol Contract

| Action/state | Host bytes | Response and completion | Next state |
| --- | --- | --- | --- |
| Start session | `14 05 04 00 6A 39 57 64` | `15 05 24 00` plus 36-byte payload; body length from the frame header | Accept only `F4HWN v6.3.x`; otherwise fail before memory access |
| Read EEPROM | `1B 05 08 00 <address:u16le> <length:u8> 00 6A 39 57 64` | `1C 05`, echoed address/length, then exactly `length` data bytes; complete from frame length | Advance by the returned payload length |
| Write EEPROM | `1D 05 <length+8:u8> 00 <address:u16le> <length:u8> 01 6A 39 57 64 <data>` | `1E 05` acknowledgment with echoed address | Advance after ACK |
| Reboot | `DD 05 00 00` | No reply | Close or reconnect after reboot |

The implementation sends 128-byte reads and writes. The final read is clipped
back to the documented `0xB190` image size even if the radio returns a full
block beyond it.

## Memory Map

| Address | Size | Contents |
| --- | ---: | --- |
| `0x0000-0x3FFF` | 16 KiB | 1,024 channel records, 16 bytes each |
| `0x4000-0x7FFF` | 16 KiB | 1,024 channel names, 16 bytes each |
| `0x8000-0x880D` | 2,062 bytes | Channel/VFO attributes, 2 bytes each |
| `0x880E-0x886D` | 96 bytes | 24 scan-list names, 4 bytes each |
| `0x9000-0x90D5` | 214 bytes | 14 VFO records |
| `0xA000-0xA177` | 376 bytes | Radio settings and F4HWN configuration |
| `0xA158-0xA15F` | 8 bytes | Packed F4HWN feature flags |
| `0xA170-0xA177` | 8 bytes | Scan-list MIX signature and mask |
| `0xB000-0xB18F` | 400 bytes | Per-unit calibration data |

The readable image length is `0xB190`. NewChirp uploads only
`0x0000-0xA177`; calibration and the reserved tail are preserved.

## Implemented Fields

- 1,024 channels and 14 band-specific VFO rows.
- Receive frequency, offset, duplex direction, receive/transmit CTCSS or DCS,
  FM/NFM/AM/NAM/USB mode, tuning step, and eight firmware power levels.
- TX lock, busy-channel lockout, frequency reverse, PTT ID, compander, and
  scan-list assignment.
- F4HWN radio-wide settings are not exposed yet. `has_settings` is false, so
  NewChirp cannot accidentally rewrite the version-tagged settings layout.

## Replay Coverage

`test/uvk1_f4hwn_driver_test.py` covers:

- exact obfuscated reporter hello bytes and decoded `F4HWN v6.3.0`;
- 128-byte block reads, including the final partial in-image bytes;
- field decode for channel name, frequency, mode, step, power, and scan list;
- edit/encode/decode round-trip for standard and radio-extra fields;
- writes ending exactly at `0xA178`, with no calibration-region write;
- rejection of F4HWN 5.x before any EEPROM read.

## Validation Status

Offline replay tests pass. No physical F4HWN 6.3 radio is connected to the
development host, so the profile remains experimental and writes require a
read-first backup and read-back confirmation by the reporter.
