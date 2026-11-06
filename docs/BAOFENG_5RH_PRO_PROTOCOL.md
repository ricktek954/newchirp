# Baofeng 5RH Pro v2 CPS protocol

Last updated: 2026-11-06

These notes cover the official Baofeng 5RH PRO CPS V1.17 and the
NewChirp-maintained driver in `drivers/newchirp_baofeng_5rh_pro.py`.
This firmware generation is not compatible with the plaintext
`PROGRAMBFNORMALU` protocol used by the similarly named legacy UV-5RH.

## Evidence inventory

- Official download page:
  <https://www.baofengradio.com/pages/download>
- CPS listing: **UV-5RM Plus GPS**, Programming Software
- Archive: `Baofeng_UV-5RM_Plus_GPS_CPS_V1.17.zip`
- Archive SHA-256:
  `12dbcbce64381d03e1922e481ddc7455da04755244efa5090bcdd372528318cb`
- Installer: `5RH PRO Setup.exe`, SHA-256
  `d6b26e894d7d89720f825a6b3e9dfb6a719689fbcbdc20b3ba1ecda889e451d0`
- Extracted application: `CPS.exe`, SHA-256
  `0a455577b791204c42f538b04e23bfd83fef4d509f8826d753a5379d92981300`
- Symbols: `CPS.pdb`, SHA-256
  `a684a7ccb6ad639abc789b1e77be2e2ddfa1286fc7245e1617d7756ce15b7e0e`
- Runtime: 32-bit .NET Framework Windows Forms; assembly version
  `1.0.1.6`
- Method/type evidence: CIL and PDB method names recovered with `dnfile` and
  `dncil`; the application was not run.
- Independent cross-check: public CHIRP PR 1625 head
  `5a9398231b580e2125f0f2b8fa9ffa612f586b6e`, whose
  `baofeng_5rh_pro.py` reports hardware validation on a 5RH Pro with GPS,
  firmware `v2_0_09`. That external hardware evidence is not a NewChirp
  physical validation.

## UI-to-serial call path

1. `MainForm.mS_Program_Read_Click` at RVA `0x36fe4` creates the CPS data
   protocol object in read direction.
2. `MainForm.mS_Program_Write_Click` at RVA `0x36f14` creates it in write
   direction.
3. `MainForm.Task_ProcessCommunication` at RVA `0x26700` starts
   `DataProtocol.DoIt`.
4. `DataProtocol.DoIt` at RVA `0x3b400` runs `handShake`, then
   `readInfo` or `writeInfo`.
5. A successful read runs `DataToRead`, which calls the device, channel,
   settings, zone, scan, DTMF, two-tone, five-tone, MDC, emergency, APRS,
   and GPS-book decoders.

## Serial configuration

`DataProtocol.ConfigComPort` at RVA `0x2655c` configures:

- 8 data bits
- no parity
- one stop bit
- 8 KiB read and write buffers
- DTR and RTS asserted

`Setting.ini` defaults to 19,200 baud. The CPS announce stage tests the
configured rate and reopens at 115,200 if the radio does not answer. Two
radios observed by the public CHIRP contributor answer at 115,200 and one
at 19,200. The NewChirp driver tries 115,200 first, then 19,200.

## Handshake contract

| Step | Host bytes | Response | Completeness | Next state |
| --- | --- | --- | --- | --- |
| Announce | `T_Info`: 12 × `00`, then 4 × `FF` | one byte `41` (`A`) | exactly one byte | Sync |
| Sync | `PROGRAM` XOR seed, followed by the seed byte | `41` XOR seed | exactly one byte | Password |
| Password | eight `FF` bytes XOR seed | `41` XOR seed | exactly one byte | Model information |
| Information | `INFORMATION` XOR seed | 16 bytes XOR seed | fixed 16 bytes | Direction |
| Direction | `52` XOR seed for read, `57` XOR seed for write | `41` XOR seed | exactly one byte | Block transfer |

Evidence:

- `DataProtocol..ctor` RVA `0x3b2a8` initializes `T_Info`,
  `HEADER_SYNC`, `HEADER_INFO`, and `END_INFO`.
- `DataProtocol.handShake` RVA `0x3b540` generates the session seed, selects
  baud, validates each ACK, and selects read/write direction.
- The CPS uses a random seed in `1..255` (`seed = random.Next(1, 255)`) and
  writes it as the final byte of the sync request.
- The 16-byte information response is ASCII after XOR decoding to the
  first `FF`. The CPS code checks for `BF-K6`, the internal family identity.

## Clone frames

### Read

The CPS reads `DpDataLen = 0xC000` bytes as twelve 4,096-byte blocks:

| Item | Value |
| --- | --- |
| Host bytes | `[52, address_hi, address_lo, 00]`, each XOR seed |
| Response | 4,100 bytes |
| Discarded prefix | first 4 bytes |
| Payload | 4,096 bytes, each XOR seed |
| Address increment | +4,096 |
| Completion | exactly 4,100 bytes available |
| Timeout | 4 seconds per block |

After the final block, the host sends `END\0` XOR seed and waits for one
ACK byte.

Evidence: `DataProtocol.readInfo` RVA `0x3bdf4`.

### Write

| Item | Value |
| --- | --- |
| Host bytes | `[57, address_hi, address_lo, 00]` plus 4,096 payload bytes, all XOR seed |
| Response | one byte, `41` XOR seed |
| Address increment | +4,096 |
| Completion | twelve acknowledged blocks |
| Final step | `END\0` XOR seed |

Evidence: `DataProtocol.writeInfo` RVA `0x3c050`.

`writePicInfo` is a separate boot-image operation and is not part of a
normal channel/settings upload.

## Memory map

The decoded image is 49,152 bytes (`0xC000`).

| Offset | Size | Meaning |
| ---: | ---: | --- |
| `0x0000-0x000F` | 16 | Device header |
| `0x0010-0x002F` | 32 | Four RX frequency ranges |
| `0x0030-0x004F` | 32 | Four TX frequency ranges |
| `0x0050-0x0057` | 8 | Firmware version |
| `0x0058-0x005F` | 8 | Hardware version |
| `0x0060-0x006F` | 16 | Programming date |
| `0x0080-0x797F` | 30,720 | 640 channel records, 48 bytes each |
| `0x7A20-0x7A6F` | 80 | Channel-used bitmap |
| `0x7A80` | 1 | Populated zone count |
| `0x7A90-0x7E87` | 1,520 | Ten 152-byte zone records |
| `0x7980-0x79FF` | 128 | General settings |
| `0x81A0-0x81EF` | 80 | Channel scan-skip bitmap |

Evidence: `DataProtocol.ConvertDevice` RVA `0x3c4d0`,
`DataProtocol.ConvertChn` RVA `0x3cc38`,
`DataProtocol.ConvertSetting` RVA `0x3d688`,
`DataProtocol.ConvertZone` RVA `0x3ded4`, and their corresponding conversion
methods.

Each channel record stores two little-endian BCD frequencies, RX/TX tones,
power and modulation flags, a 16-character GB2312 name, and preserved
firmware/CPS fields. The driver exposes only fields with established
semantics and preserves undecoded bytes when editing an existing channel.

## NewChirp read/write policy

- The driver is registered as an Experimental model family.
- Read uses the CPS frame contract above.
- Write uses the same 4,096-byte full-image block sequence and rebuilds the
  ten fixed channel-to-zone slices before upload.
- A channel that was already programmed preserves unknown signaling,
  emergency, APRS, and other bytes. A previously unused slot is initialized
  before its exposed fields are written.
- Boot-image upload is implemented as the separate unencrypted
  `Picture\xFF` protocol and is not exercised by channel programming.

## Validation and remaining work

- Static evidence: complete for the handshake, read, write, and image-block
  transport described above (E1).
- Replay evidence: synthetic transport tests cover announce fallback,
  seeded handshake, 4,100-byte frames, twelve read blocks, channel edits,
  and zone rebuilding (E2).
- External hardware evidence: the public CHIRP PR reports a physical
  5RH Pro with GPS on firmware `v2_0_09`, including read and upload/read-back.
- NewChirp hardware evidence: none yet.
- Next milestone: have the reporter select **Baofeng UV-5RH Pro** or
  **Baofeng 5RH Pro**, save the first successful read, compare the displayed
  channels with the radio, then perform a controlled edit and read-back.
- Unresolved: other password values, boot-image write validation on
  NewChirp, undocumented setting bits, and firmware revisions other than
  `v2_0_09`.
