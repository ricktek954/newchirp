# TIDRADIO TD-H3 CPS protocol

This document records evidence from the official TIDRADIO TD-H3 GMRS
programming package and the compatible upstream CHIRP transport. It covers the
legacy serial family identified as `TD-H3`, `TD-H3-HAM`, and `TD-H3-GMRS`, not
the newer USB HID TD-H3 Plus family.

## Evidence

- Vendor download page:
  `https://www.walkietalkiesoftware.com/portal/index/software_detail/id/68.html`
- Vendor archive:
  `TIDRADIO-TD-H3-GMRS-CPS-20250331.zip`
- Archive SHA-256:
  `ffb74466c3286b9d575752632bbf46fd3432d3ac69403b4d60b341f84038974c`
- Installer:
  `H3_GMRS_setup240104(1).exe`
- Installer SHA-256:
  `370d63846379ea04229895eba18592ffb8f541410149550b0b769d43b10de45d`
- Extracted CPS:
  `H3_GMRS.exe`
- CPS SHA-256:
  `a2b9c9b82aad8577184d641d7b0c252ec01fbbdb430b3e235574b3704a913b1f`
- Pinned upstream CHIRP `tdh8.py` SHA-256:
  `6cc013c387f4728df4db826cd758fad805fd855e43bc44e70e2004aac845cc6c`
- Evidence level: E1 for the OEM call paths and E2 for replay tests. No OEM
  USB capture or physical TD-H3 validation was available on this Mac.

The installer is a Setup Factory 8 executable. Its launcher locates a
`E0 E0 E1 E1 ... E7 E7` sentinel, reads a 576,000-byte obfuscated launcher,
XORs the first 2,000 launcher bytes with `0x07`, and extracts LZMA members from
the remaining Setup Factory archive. The proprietary files are not committed
to the repository.

## Identification

The host opens the selected COM port at 38400 baud, 8 data bits, no parity,
1 stop bit. The CPS enables RTS, supplies 5-second read/write timeouts, clears
the serial queues, and sends this seven-byte probe:

```text
50 56 4F 4A 48 5C 14
```

The radio acknowledges with `06`, accepts the follow-up `02` request, and
returns an eight-byte family identity. The HAM and GMRS identities are
`P31185 FF FF` and `P31184 FF FF`; the generic TD-H3 identity is
`P31183 FF FF`.

The CPS allows five probe attempts before reporting a connection failure.
NewChirp therefore clears stale input once and retries only when the probe
receives no acknowledgment. A received-but-invalid acknowledgment remains an
immediate protocol error.

## Data transfer

| Item | Host bytes | Response | Evidence |
| --- | --- | --- | --- |
| Probe | `50 56 4F 4A 48 5C 14` | `06` | CPS handshake state machine |
| Request identity | `02` | 8-byte model identity | CPS state `06` → `02` |
| Accept identity | `06` | `06` | CPS state after identity response |
| Read block | `52 <address:2> 20` | `57 <address:2> 20 <32 data> <checksum>` | CPS read state and CHIRP |
| Write block | `57 <address:2> 20 <32 data> <checksum>` | `06` | CPS write state and CHIRP |
| End transfer | `45` | `06` | CPS exit state |

Addresses are big-endian and aligned to 32-byte boundaries. The block checksum
is the low eight bits of the sum of the 32 data bytes. Reads and writes use
32-byte blocks.

## Safety and validation

The NewChirp override keeps the upstream CHIRP memory map and write policy.
The only transport change is the OEM-observed five-attempt identification
retry. Writes remain experimental until a physical read is compared with the
official CPS, followed by a controlled edit, upload, and read-back.
