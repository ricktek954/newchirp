# Baofeng BF-V12D P3107 Serial Protocol

Last updated: 2026-11-08

## Scope and artifact

This document covers the BF-V12D and related P3107-family digital radios. The
official vendor programmer is the Electron application from:

`https://baofeng.s3.amazonaws.com/Baofeng_V1D_CPS.zip`

- ZIP SHA-256:
  `c07f3664c7bf87721376042c53a06b29055fec0c2ccc3d6192c8d005b4582f72`
- Installer: `BF_Series_1.5.1.exe`
- Installer SHA-256:
  `6bf5c0feda83007e7d5bce468c059af499bd2fd89335422b28771d787e655a2a`
- Installed application version: `1.5.1`
- Electron renderer SHA-256:
  `73fce5e220a9983eaf001ff71dacd7f0db98a61f760736e56e1c23be555d9ed8`
- Electron main-process SHA-256:
  `311a8078899690f10ea7b22975ebe1644efa7ec35e3c3c713ca51429705e3231`

The renderer is a Vue application in an ASAR bundle. The main process owns the
SerialPort instance. The protocol below was traced from UI actions through the
renderer state machine and main-process serial writes.

Public supporting captures:

- Read capture SHA-256:
  `f9b043be72d9aa53071498d731c9ccf475f2e77cf4ef2d374d18d0f729d2e251`
- Single-channel write capture SHA-256:
  `81f03d3e796b4e410dbb176b2b14c89019ba8bb52376a8633d2352632443eb9a`

## Transport

The CPS opens the selected port at 9,600 baud, 8 data bits, no parity, one
stop bit, no flow control. Community hardware evidence says the radio requires
a standard Baofeng K-type cable and does not work with an FTDI cable.

The serial port carries binary requests. Responses arrive as binary bytes and
may be split across multiple receive callbacks. The CPS reassembles data using
a 16 ms idle gap and validates fixed response lengths in its application state
machine.

## Unlock sequence

For the P3107 `V12D` profile, the CPS sends the following fixed sequence:

| Step | Host bytes | Expected response | Meaning |
| --- | --- | --- | --- |
| 1 | `02 75 63 62 66 70 77 64` | ACK `06` | Enter read/write password flow |
| 2 | `10 C5 EA 35` | ACK `06` | Password or unlock seed |
| 3 | `51 30 34 31 4F 54 55 77 4D 41 3D 3D 00 00 00 00` | ACK `06` | Fixed model token `Q041OTUwMA==` |
| 4 | `02 70 72 4F 47 52 41 4D` | Four-byte radio ID | `02prOGRAM` |

The four-byte ID in the public V12D capture is `00 0A 01 10`. Byte 1 is the
P3107 serial/model ID `0x0A`; it is not a firmware password.

The same bytes and responses are present in the public read and write captures.
The CPS retries this password sequence; NewChirp uses five one-second attempts.

The encoded model token is not a user-entered secret in this CPS build. The
renderer derives it from its fixed model configuration and sends it as ASCII
hex through its generic `port-write` bridge.

## Clone session

After the radio ID is validated, the V12D uses protocol A (`80 82`):

| Operation | Host bytes | Expected response |
| --- | --- | --- |
| Protocol select | `02 80 82 4F 47 52 41 4D` | ACK `06` |
| Identity | `02` | `P3107 F7 00 00` |
| Identity ACK | `06` | ACK `06` |
| Probe read | `52 01 30 08` | `57 01 30 08` plus eight data bytes |
| Probe ACK | `06` | ACK `06` |
| Read block | `52 <address:u16be> 08` | `57 <address:u16be> 08 <8 data bytes>` |
| Read ACK | `06` | ACK `06` |
| Exit | `45` | ASCII `46` (`F`) on supported firmware |

For writes, the CPS first exits read mode with `E`, then sends the write-mode
identity sequence:

`02 80 82 4F 47 52 41 4D`, `02`, identity, `06`, then the preamble. Each write
frame is `57 <address:u16be> 08 <8 data bytes>` followed by ACK `06`.

## Memory map

The legal image is `0x03E0` bytes. For V12D, the sparse read sequence is:

- `0x0000-0x010F`
- `0x02B0-0x02BF`
- `0x0330-0x033F`
- `0x0380-0x03DF`

The address step is eight bytes with three jumps:

- `0x0108 -> 0x02B0`
- `0x02B8 -> 0x0330`
- `0x0338 -> 0x0380`

The CPS writes the written-image ranges from `0x0000` through `0x03DF`, with
the same address jumps. The sparse window at `0x0330-0x033F` is read-only and
is not synthesized from user settings.

The V12D has 16 channel records. Each record begins at:

`0x0010 + (channel_index * 0x10)`

The channel fields are RX frequency, TX frequency, RX tone, TX tone, scan,
power, bandwidth, intercom/encryption mode, busy lock, hopping, and encryption
key. The full field map is available in the public
`V12D_PROTOCOL_MAP.md` artifact. Settings occupy the `0x02B0` and `0x03C0`
regions.

## Firmware variants

This protocol is confirmed by the public V12D read and write captures.
Separate units reporting firmware `V1.19` or `V2.02` have a newer password
handshake. On those units:

- current CHIRP fails with `No ACK on model identifier`;
- Baofeng BF_Series CPS 1.5.1 returns either
  `Password verification handshake failed` or
  `Read/write frequency password error`;
- the CPS can sometimes read the firmware/version response but cannot obtain
  the channel data.

The official CPS source contains no alternate unlock branch for those firmware
versions. Consequently there is no evidence-backed method yet to read newer
variants. NewChirp fails closed and reports the firmware limitation rather
than attempting a guessed password or an unsafe write.

## Evidence status

- E1: renderer and main-process call paths traced from BF_Series 1.5.1,
  including serial framing, fixed unlock requests, response reassembly, model
  selection, memory map, and clone state machine.
- E2: CPS-derived byte-exact replay tests for the unlock sequence, response
  splitting, retries, and catalog replacement.
- E3: public OEM serial captures for one earlier-firmware unit.
- E4: not performed by NewChirp on physical hardware.
- E5: none.

The next milestone is a physical read using a standard K-type cable on a
supported firmware unit, followed by a controlled one-channel write and
read-back. Supporting V1.19/V2.02 requires a working OEM serial capture or a
documented password/challenge exchange; the existing CPS cannot supply it.
