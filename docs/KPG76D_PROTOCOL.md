# Kenwood KPG-76D / TK-863G protocol notes

Last updated: 2026-11-13

## Status

The TK-863G transport and channel layout below were recovered from Kenwood
KPG-76D 1.00 and checked against a DAT image produced by the OEM CPS from the
uploader's radio. The NewChirp driver is experimental and read-only.

No NewChirp read or write has yet been performed on physical TK-863G hardware.
Enabling uploads requires a complete physical read, comparison with KPG-76D,
and a controlled write/read-back.

## Artifacts

- OEM programmer: Kenwood KPG-76D 1.00 for TK-373G/TK-863G.
- CPS archive: `kpg76d.zip`, SHA-256
  `94cfae17605565e92cf14135c7a391a450395e697f2a8d7053090b73df63cbee`.
- Analyzed executable: `kpg76d.exe`, SHA-256
  `2041afe2b14883ea1411d139227bb6c19ff4292c909c89599a812c475bafcfde`.
- Companion firmware programmer: `Fpro.exe`, SHA-256
  `d55a2b16dde751037d60c84ec27cc48e7a7d7e9e133fc565628ef51891c395c4`.
- Language/resources binary: `English/kpg76d.GID`, SHA-256
  `a0a6e02ed43664238a3cc1297ce929063e43b9b9b3c9e13201da2ec2f61f805c`.
- Uploader's CPS-read DAT: 32,880 bytes, SHA-256
  `5afb8f37a3a28a0882b98eb8d340e6caec64f1b8b53b742426cac52ca3b89434`.

The archive was extracted statically and its executables were not run.

## Radio identity

- The TK-863G model code is `M0863`.
- The format string identifies the CPS as KPG-76D 1.00.
- The TK-863G identity in the radio image is `TK-863G`.
- The model table supplies the 450-490 MHz frequency range.
- TK-373G uses `P0373` and is deliberately not accepted by this driver.

## Serial transport

The native Win32 CPS opens the selected COM port with `9600,N,8,2` and a
1,000 ms total read timeout. There is no XON/XOFF or hardware flow control.

The CPS probes the following speeds in order:

```text
9600, 19200, 4800, 2400, 1200
```

At 9,600 baud it sends `PROGRAM`, waits 500 ms, and expects ACK `0x06`.
Fallback probes use the CPS' 100 ms initial wait, `0x16` speed response, and a
second 500 ms wait for ACK.

### Read session

| Step | Host bytes | Radio response | Completion and checks |
| --- | --- | --- | --- |
| Enter programming mode | `PROGRAM` | `06` | One byte after the CPS delay |
| Identity | `02` | 8-byte model response | Must contain `M0863` |
| Acknowledge identity | `06` | `06` | Exact ACK required |
| Tuning information | `NRK` | `4E` + 32 data bytes + checksum | Byte 33 is the low eight bits of the sum of bytes 1-32 |
| Settle | None | None | Wait 3,000 ms |
| Start memory session | `7C` | 2 bytes | CPS reads both bytes before continuing |
| Acknowledge memory session | `06` after 500 ms | `06` | Exact ACK required |
| Read block | `52` + address as big-endian u16 | See below | Repeat through `0x7F00` |
| Leave programming mode | `45` (`E`) | `06` | One ACK |

`TUNING ` is a separate CPS tuning UI command. It is not sent by the codeplug
read path; codeplug reads use `NRK`, then `0x7C`.

### Memory block read

Request:

```text
52 <address:u16be>
```

Data response:

```text
57 <256 data bytes> <checksum>
```

- `0x57` is ASCII `W`.
- The checksum is the low eight bits of the sum of the 256 data bytes.
- The CPS sends ACK `0x06` after accepting the block and expects ACK in return.
- If the first response byte is not `W`, the CPS reads one fill byte and
  repeats it across all 256 bytes.
- A failed data checksum sends `0x15`, waits for its ACK, and retries the
  request. The CPS allows three total attempts.
- The CPS requests every 256-byte block from address zero through `0x7F00`.

### Write framing recovered but disabled

The CPS write routine uses:

```text
57 <address:u16be> <256 data bytes> <checksum>
59 <address:u16be> <fill byte> <checksum>
```

It retries a rejected write up to three times. The NewChirp driver does not
emit these frames. The complete ownership and safety policy for settings,
identity, radio-specific calibration, and unlisted regions has not yet been
validated on hardware.

## DAT and memory layout

The OEM DAT is 0x8070 bytes:

```text
0x0000-0x006F  KPG-76D DAT wrapper
0x0070-0x806F  0x8000-byte radio image
```

The first image bytes contain KPG-76D metadata. The channel table is at radio
offset `0x02F0` and contains 128 consecutive 32-byte records. The radio
identity `TK-863G` is at image offset `0x58D0`.

Channel record:

| Offset | Size | Meaning | Evidence |
| --- | --- | --- | --- |
| `0x00` | 1 | Channel marker, `FF` when unused | DAT record scan |
| `0x01` | 4 | RX frequency, little-order packed BCD of 10 Hz units | CPS getter and DAT |
| `0x05` | 4 | TX frequency, same encoding | CPS getter and DAT |
| `0x09` | 2 | RX/TX hardware defaults, observed `35 32` | Preserved |
| `0x0B` | 2 | RX QT/DQT word, little-endian | CPS getter and DAT |
| `0x0D` | 2 | TX QT/DQT word, little-endian | CPS getter and DAT |
| `0x0F` | 8 | Channel name | CPS getter |
| `0x1A` | 2 | Channel option bits | CPS getter/setter trace |
| `0x1C` | 4 | Remaining channel fields | Preserved |

Frequency bytes `50 87 17 45` decode as packed BCD `45178750`, or 451.7875
MHz. A CTCSS word `CA 06` decodes as 0x06CA and 173.8 Hz.

The CPS channel getter at `0x4386C0` proves:

- RX frequency is at record `+0x01`.
- TX frequency is at record `+0x05`.
- RX and TX tone words are at `+0x0B` and `+0x0D`.
- The name is the eight bytes at `+0x0F`.
- Byte `+0x1A` bit 3 is the channel-spacing selector; 1 is wide and 0 is
  narrow.
- Byte `+0x1B` bit 5 records whether TX differs from RX. The CPS explicitly
  clears this bit when RX and TX frequencies compare equal.

Other per-channel bits are preserved in the image but are not exposed until
their UI labels and semantics are mapped fully.

## Static trace

Relevant `kpg76d.exe` functions:

| Address | Recovered operation |
| --- | --- |
| `0x401000` | Serial object construction and `9600,N,8,2` setup |
| `0x402130` | `PROGRAM` and baud probing |
| `0x4023B0` | `0x02` identity query and ACK exchange |
| `0x402D40` | `NRK` 34-byte tuning read and checksum |
| `0x403110` | three-second wait, `0x7C`, and memory-session ACK |
| `0x402580` | `R`/`T` 256-byte block read, fill handling, checksum, retry |
| `0x402540` | `E` programming-mode exit |
| `0x402760` | disabled write framing |
| `0x4386C0` | channel record field getter |
| `0x439040` | channel option-bit setter |

## Driver policy

- Read the complete 32 KiB image and reject a different Kenwood model.
- Accept the OEM 0x8070-byte DAT wrapper when the signature and model match.
- Decode frequency, offset, name, mode, CTCSS, DTCS, and cross tones.
- Preserve every channel byte, including fields not exposed in the UI.
- Do not mutate the image while decoding.
- Reject every upload and channel write.

## Offline validation

`test/kenwood_tk863g_driver_test.py` covers:

- driver registration and read-only policy;
- the OEM DAT wrapper and 128-channel offset;
- the supplied channel encoding for a repeater, simplex channel, and empty
  slots;
- wrong-model identity rejection;
- all 128 addressed reads with responses fragmented into three-byte chunks;
- block checksum failure, `0x15`, and retry;
- exact `PROGRAM` and `E` session framing.

## Remaining work

1. Perform a complete physical read with NewChirp on a TK-863G.
2. Compare every decoded channel, tone, offset, and bandwidth value with
   KPG-76D.
3. Map and label the remaining option, scan, power, compander, signalling, and
   group fields.
4. Validate all writable memory regions and write-response behavior.
5. Enable a controlled write only after the physical read and read-back agree.
