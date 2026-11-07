# Retevis RA89 CPS Protocol

Last updated: 2026-11-07

This document records the evidence behind
`drivers/newchirp_ra89.py`. The implementation is derived from Retevis's
official programming software. The pinned upstream CHIRP `th_uv88.py` profile
was used as a comparison oracle after the OEM call paths and vendor sample maps
were decoded.

## Artifact inventory

- Official download page: <https://www.retevis.com/downloads/software>
- Official package:
  `RA89-Programming-Software.zip`
- Package SHA-256:
  `ba792a74a122f33c4b70405aae0ab35018efa3e75842b8efe4e94f360015a500`
- Inner installer:
  `RA89_20230909_V108.exe`
- Installer SHA-256:
  `610cbca1ba74cde6fed09ea7ff8639a23f7bced111210569f4c86c14ab61194e`
- Extracted main .NET application `7` SHA-256:
  `d313f027c3310ca5166cdcfe98022e6f59d98716584487e5b47210825b0ea3c6`
- Supporting .NET DLL `3` SHA-256:
  `37d20f74ad239fcae32afbcde42e6e1deeda49519ebf6d12a27a12bbdcdb5895`
- Vendor sample ICF file `4` SHA-256:
  `cd5fb8f5ad492d6e28bc6db108547558176783ea965e32cfcbd5da30b01ed811`

The analysis was static. No CPS executable was run, and no OEM or private
codeplug contents are committed.

## Radio and serial configuration

- VENDOR: Retevis
- MODEL: RA89
- Internal serial identity: `UV99`
- Baud rate: 57,600
- Data bits: 8
- Parity: none
- Stop bits: 1
- RTS: asserted
- DTR: asserted
- Hardware/software flow control: none
- Inter-command delay: 15 ms
- OEM per-command response window: 3 seconds after a frame is sent

`serialPortResSetPro` at IL offset `0x97998` sets 8 data bits, one stop bit,
no parity, RTS, DTR, and ASCII encoding. `setting.ini` selects 57,600 baud.

The 1.0.44 RA89 failure occurred before the handshake response. NewChirp's
pinned CHIRP path did not assert DTR/RTS. The OEM application does. The
NewChirp driver therefore uses the same control-line state as the CPS.

## Session transport

All binary lengths below are lengths after the CPS hexadecimal-string builder
is converted by `SendComDatPro`.

| Action | Host bytes | Response | Next state |
| --- | --- | --- | --- |
| Identify | `FE FE EE EF E0 55 56 39 39 FD` | 36 bytes | Capture response code field |
| Programming code | `FE FE EE EF E7 <8 ASCII hex chars> FD` | 7-byte ACK | Used when the captured code is `3435`; the no-code value is `FFFFFFFF` |
| Set baud | `FE FE EE EF E6 55 56 39 39 04 FD` | 7-byte ACK | Reopen/select 57,600 baud |
| Enter read | `FE FE EE EF E2 55 56 39 39 FD` | 7-byte ACK | Start block reads |
| Enter write | `FE FE EE EF E3 55 56 39 39 FD` | 7-byte ACK | Start ordered block writes |
| Read block | `FE FE EE EF EB <addr:4> <len:2> FD` | `len + 13` bytes | Address advances by returned payload length |
| Write block | `FE FE EE EF E4 <addr:4> <len:2> <payload> <checksum:1> FD` | 7-byte ACK | Address advances by 32 |
| End session | `FE FE EE EF E5 55 56 39 39 FD` | 7-byte ACK | Close transfer |

The common 7-byte ACK is:

```text
FE FE EF EE E6 00 FD
```

The reliable identify response starts with:

```text
FE FE EF EE E1 55 56 39 39
```

and ends with `FD`. `DisplayText` captures four characters at
`len(response)-14 .. len(response)-10`. Completion waits for exactly 36 bytes.
The OEM receive callback does not advance or assemble a partial response:
`serialPort1_DataReceived` requires
`BytesToRead == ReceivedBytesThreshold`.

NewChirp improves on that limitation with an accumulated exact read. Short or
fragmented callbacks are accepted until the expected byte count arrives or the
three-second deadline expires.

## Block framing

For a 32-byte read, the host sends 12 bytes and the radio returns 45:

```text
FE FE EF EE E4 <address:4> <returned-length:2> <payload:N> <checksum:1> FD
```

The returned frame length is `N + 13`. Address and returned length are
big-endian binary values. The OEM application accepts a returned payload no
larger than the request and advances by the returned length.

The write checksum covers:

```text
address:4 big-endian + length:2 big-endian + payload:N
```

It is a byte sum modulo 256, complemented modulo 256. A zero sum produces zero
checksum.

The OEM receive path converts each byte to uppercase hexadecimal text and then
removes the final checksum field without comparing it to the write-side
algorithm. NewChirp likewise validates the marker, echoed address, returned
length, frame size, payload, and `FD` terminator, but records rather than rejects
a read-side checksum mismatch.

## Memory map

| Range | Meaning | Policy |
| --- | --- | --- |
| `0x0000-0x1067` | 200 channel records, 21 bytes each | Read/write |
| `0x1068-0x113F` | Remaining channel/settings workspace | Preserve |
| `0x1140-0x115F` | VFO/MR work modes | Core selected fields editable |
| `0x1160-0x117F` | Basic/advanced settings | Known fields editable |
| `0x1180-0x1199` | 200-bit active-channel bitmap | Read/write |
| `0x11A0-0x11B9` | 200-bit scan-skip bitmap | Read/write |
| `0x1680-0x193F` | Factory/calibration/runtime protected region | Never written |
| `0x191E` high nibble | Region code | Read-only presentation |
| `0x1940-0x195F` | Startup text lines, 16 bytes each | Editable |
| `0x1960-0x1C2F` | 200 channel names, 10 bytes each | Read/write |
| `0x2180-0x21DF` | 24 FM preset records | Preserved, not exposed |
| `0x21E0` | FM preset mask and current frequency | Preserved, not exposed |
| `0x22A0` | Full image size | Fixed |

### Channel record

Each channel record is 21 bytes:

| Offset | Encoding |
| --- | --- |
| `0-3` | RX frequency, little-endian u32 in 10 Hz units |
| `4-7` | TX frequency, little-endian u32 in 10 Hz units; `FFFFFFFF` means TX inhibited |
| `8-9` | Scramble high nibble and RX tone/12-bit DCS value, stored big-endian |
| `10-11` | RX/tx DCS polarity flags and TX tone/12-bit DCS value, stored big-endian |
| `12` | Power, bandwidth, and bus-lock fields |
| `13` | Optional signaling, name-display flag, and unknown bits |
| `14` | PTT-ID, step, and unknown bits |
| `15-20` | First six name characters |

The extra 10 name characters are in the separate name table. The first six
characters are prefixed before the extra name, so blank six-byte prefixes
become visible spaces. NewChirp preserves that OEM ordering rather than silently
trimming from the left.

The vendor sample map validates the record interpretation with active channels
at 435.230, 438.050, 439.075, 144.950, 145.000, 400.0625, and 400.075 MHz.
Their RX and TX words are duplicated and their tone words are `FF0F`, matching
the decoded off-tone representation.

## Implementation and write policy

Implemented:

- First-class `NewChirpRA89Radio` registration under `Retevis_RA89`, replacing
  the inherited CHIRP profile at runtime.
- OEM handshake, optional programming-code exchange, baud setup, read/write
  mode, exact and fragmented-safe reads, checksum generation, ACKs, and exit.
- 200 channel records, RX/TX frequencies, duplex/split/off, names, active and
  skip flags, CTCSS/DCS and cross tones, power, FM/NFM/WFM, options, and step.
- Core radio settings, startup text, side keys, and work-mode selections.
- Full-image writes in 32-byte blocks except `0x1680-0x193F`.

Not exposed:

- FM broadcast presets.
- Unknown calibration/runtime fields.
- Rare service and signaling fields without established UI semantics.

## Evidence status

- Static OEM CPS analysis: E1.
- Synthetic OEM-wire replay and fragmented reads: E2.
- Physical OEM CPS serial capture: not collected.
- Physical NewChirp read compared with the CPS: pending.
- Controlled NewChirp write/read-back: pending.

The reporter's next test should begin with a read and an unedited image backup.
A write should be attempted only after the downloaded channels and settings are
compared with the CPS or the radio display.
