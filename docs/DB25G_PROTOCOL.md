# Radioddity DB25-G protocol notes

Last updated: 2026-11-07

## Status

This is static and replay evidence for the Radioddity DB25-G GMRS mobile
radio. The NewChirp driver uses the OEM CPS connection, read, and write
sequences. Hardware validation remains pending.

Evidence level:

- E1 for the serial lifecycle, handshake, receive framing, and write command
  construction from the official CPS call paths.
- E2 for the NewChirp transport through synthetic fragmented-response and
  retry tests.
- No E3/E4/E5 capture or physical-radio evidence yet.

## Software identity

- OEM application: Radioddity DB25-G GMRS CPS 20250903 (`3TXP` installer)
- Download source:
  `https://radioddity.s3.amazonaws.com/Radioddity_DB25_G_GMRS_CPS_20250903.zip`
- Local archive:
  `/Users/rlopez/Downloads/Radioddity_DB25_G_GMRS_CPS_20250903.zip`
- Archive SHA-256:
  `97e18276039ea344297fc7be2f4d45ec7433015ee547b3c1a46803418666a258`
- Inner CPS ZIP SHA-256:
  `701157b9b189d1bb54c686d50a9a320c45aa5a7847c30a0d030401a4e05d10f7`
- Installer bootstrap SHA-256:
  `978123c86b1cbc981770fbd8bdfc58ef4030f8d9b3adf06b71b928cc0394c073`
- `DB25_G_GMRS_CPS.exe` SHA-256:
  `f4e3affa512eca914888a888af156365a1b4f06df55da1a31d71a2b67a77ea87`
- `MSCOMM32.OCX` SHA-256:
  `51a1d6812e445c26c71465e2709e6d1ad587f8513002d662cd160f424f48b37c`
- `MSVBVM60.DLL` SHA-256:
  `2246b4feae199408ea66d4a90c1589026f4a5800ce5a28e583b94506a8a73dce`
- PE product/file version: `1.00`
- Runtime: 32-bit Visual Basic 6 native code with Microsoft Communications
  Control 6.0 (`MSCommLib.MSComm`)

REA 6.5.0 / Ghidra 12.1.4 identified 868 native procedures and 2,362 strings.
The VB6 decompiler recovered 760 procedures with no unplaced statements.
Both tools were used statically; the CPS was not executed.

## UI and transport call path

`Prog_read_Click` loads `Form_Comm_Read`; `Prog_write_Click` loads
`Form_Comm_Write`. Each form owns an `MSCommLib.MSComm` control.

Both forms configure the port as follows before opening it:

| Item | Value |
| --- | --- |
| Baud/settings | `9600,N,8,1` |
| InBufferSize | 1024 |
| InputLen | 1 |
| RThreshold | 1 |
| InputMode | binary |
| DTR/RTS/Handshaking | not configured by the CPS; MSComm defaults remain |

The serial receive handler reads one byte per `Input` call. A response is
assembled byte by byte using `InBufferCount`, so a complete logical frame can
arrive across multiple receive notifications. NewChirp preserves that rule by
accumulating until the exact declared frame length is available.

## Protocol contract

| Action/state | Host bytes | Response encoding and layout | Length/completion | Retry and next state |
| --- | --- | --- | --- | --- |
| Enter programming mode | `55 20 16 08 01 FF DC 02` | Binary 50-byte identity reply beginning with ACK `06`; contains model fingerprint | Exactly 50 bytes | CPS allows the initial request plus three timer-driven retries. Success advances to block 0. |
| Identify DB25-G | Same handshake | Fingerprint `VC7062` or `VC6182` appears inside the identity reply | Exact 50-byte reply | A mismatched fingerprint is an identification error. |
| Read 64-byte block | `06 53 <address:u16be> <length:u8>` | `ACK 06/05`, `X`, `<address:u16be>`, `<length:u8>`, `<length>` payload bytes | Returned length must equal 64; total response is 69 bytes | CPS validates the response before advancing address by 64. |
| Write 16-byte block | `06 58 <address:u16be> 10 <16 data bytes>` | Binary ACK `06` | One ACK byte | OEM write path advances by 16 bytes. NewChirp does not enable this operation yet. |

There is no checksum in the DB25-G clone frames recovered from this CPS.
Framing is binary throughout; responses are not ASCII-hexadecimal text.

## Radio read sequence

1. Configure `9600,N,8,1`, binary input, one-byte input threshold.
2. Send the eight-byte programming request.
3. Accept only a 50-byte identity reply containing `VC7062` or `VC6182`.
4. Read memory in 64-byte blocks using `S` requests.
5. Validate the ACK, returned `X` command, echoed address, and returned
   length before accepting payload bytes.
6. Decode the image using the DB25-G channel/settings structures already
   mapped by the pinned CHIRP family driver.

The CPS channel read screen requests 200 blocks from `0x0000` through
`0x31FF`. Its other radio pages issue the same `S` command against page bases
stored in the form data. NewChirp currently performs one linear read through
the 16 KiB image so the fields at `0x3200` through `0x3F75` are available to
the existing decoder. This extension uses the same validated block contract
but remains part of the physical-read validation milestone.

## Radio write sequence

The OEM write form builds 21-byte `X` frames with a 16-byte payload and
advances the address by 16 bytes. For the normal image it covers `0x3100`
bytes, or 784 blocks. The CPS explicitly remaps several high pages rather
than blindly writing the complete 16 KiB image.

NewChirp follows that normal OEM upload path: it writes 784 sixteen-byte
blocks from `0x0000` through `0x30FF` and does not write `0x3100` through
`0x3FFF`. The high-page remapping and calibration-preservation behavior of
the individual settings editors remains a physical validation item.

## Implementation

- Driver: `drivers/newchirp_db25g.py`
- Model identifier: `Radioddity_DB25-G`
- Serial settings: 9600 8N1, no hardware or software flow control
- DTR/RTS: not asserted, matching the OEM MSComm defaults
- Handshake attempts: 4 total (one request plus three OEM-style retries)
- Read timeout: 2 seconds per block; identity timeout: 4 seconds per attempt
- Read: enabled
- Write: enabled through the OEM `0x3100` upload range
- Settings: inherited DB25-G decode from the pinned CHIRP family layout as a
  cross-check; the serial path is NewChirp-owned

## Offline coverage

`test/db25g_driver_test.py` verifies:

- exact eight-byte programming request and 9600 8N1 setup;
- identity retry after two silent attempts;
- four-attempt failure guidance for a silent radio;
- fragmented 69-byte read responses;
- complete 16 KiB block traversal;
- bad ACK and mismatched address rejection; and
- all 784 OEM sixteen-byte write blocks and missing-ACK rejection.

## Remaining validation

1. Obtain a physical DB25-G read with `VC7062` or `VC6182`.
2. Compare every channel and exposed setting with the OEM CPS display.
3. Confirm the high memory pages required by the image decoder.
4. Capture one OEM write and compare `X` frame order, address remapping,
   ACK timing, and the persistent regions the CPS preserves.
5. Enable writes only after one controlled channel change is read back by
   both NewChirp and the OEM CPS.
