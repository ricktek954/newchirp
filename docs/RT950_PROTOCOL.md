# Radtel RT-950 experimental protocol notes

These notes document the interoperable facts used by
`drivers/newchirp_rt950.py`. The implementation is original NewChirp code; the
Radtel CPS executable and extracted vendor files are not part of this
repository.

## Evidence

- CPS: Radtel RT-950 English CPS v1.3.0
- Artifact: `BT-9000_CPS.exe`
- SHA-256: `605054c46ec17520b0f79b78585c3be431a6dcb95164dc638985455e813d7a1e`
- Format: .NET Framework 4.0 managed PE32
- Analysis: REA managed static metadata/CIL inspection plus targeted IL
  disassembly

## Serial setup

- 115200 baud, 8 data bits, no parity, one stop bit
- RTS and DTR asserted
- CPS serial handshake: `None` (no RTS/CTS or XON/XOFF flow control)

The current driver uses the same settings. The earlier note incorrectly
described the separately asserted RTS/DTR lines as hardware flow control.

## Programming handshake

1. Send ASCII `PROGRAMBT9000U`.
2. Read one byte and require `0x06`.
3. Send ASCII `F` and read/discard 16 bytes.
4. Send ASCII `M` and read 12 bytes. The trimmed model code is `BT-9000`.
5. Send the 25-byte randomized `SEND` authentication packet.
6. Read one byte and require `0x06`.

After a successful handshake, a read session sends 128-byte block commands and
ends with ASCII `E`.

The `SEND` packet contains:

- Bytes 0-3: ASCII `SEND`.
- Byte 4: a random encryption-symbol selector.
- Bytes 5-24: random indexes into a twenty-entry four-character symbol table.
- The selected symbol is four ASCII bytes and is retained for the session.

## Read framing

Request:

```
52 AH AL 80
```

- `0x52` is `R`.
- `AH:AL` is the big-endian memory address.
- `0x80` is the payload length.

Response: 132 bytes total. The CPS validates the two address bytes at offsets
one and two, then copies the 128-byte payload beginning at offset four. It does
not require a specific response command byte.

The 128-byte payload is encrypted with the four-byte symbol selected by the
`SEND` packet. Bytes equal to `0x00`, `0xFF`, the symbol byte, or its complement
are left unchanged; the remaining bytes are XORed with the rotating symbol.

The current Web Programmer reader allows 3.5 seconds for each 132-byte block
response. A macOS 1.0.36 report timed out after 2.0 seconds with zero bytes,
so the desktop driver uses the same 3.5-second response window.

The driver reads blocks from these ranges:

```
0x0000-0x77FF  channel records
0x8000-0x807F  VFO data
0x9000-0x907F  function settings
0xA000-0xA17F  DTMF data
0xB000-0xB07F  modulation data
0xC000-0xC0FF  zone names
```

Unread gaps are retained as `0xFF` in the CHIRP image.

## Channel records

There are 960 fixed 32-byte records at `0x0000`.

| Offset | Meaning |
| --- | --- |
| `0x00-0x03` | RX frequency, little-endian packed decimal in 10 Hz units |
| `0x04-0x07` | TX frequency, same encoding |
| `0x08-0x09` | RX tone |
| `0x0A-0x0B` | TX tone |
| `0x0C` | Signalling group, low nibble |
| `0x0D` | PTT ID, low nibble |
| `0x0E` | TX power in low nibble; voice inversion in high nibble |
| `0x0F` | Mode and feature flags |
| `0x10-0x13` | FHSS code |
| `0x14-0x1F` | 12-byte channel name encoded with GB2312 |

Frequency bytes hold a two-digit decimal value in BCD form, least-significant
group first. For example, 146.52000 MHz is represented by `00 20 65 14`, and
462.57500 MHz is represented by `00 75 25 46`.

A 2026-11-02 field image displayed a `462.575000` MHz channel as `7.525460`
MHz because the driver decoded these bytes in the opposite order.

Tone words use little-endian bytes:

- All zero or all `0xFF`: off
- High byte zero: DCS table index in the low byte, one-based
- Otherwise: CTCSS frequency in tenths of a hertz

The DCS table has 105 normal codes followed by the same 105 reversed codes.

Mode flags in byte `0x0F`:

- bit 0: AM receive modulation when set, FM otherwise
- bit 1: transmit disabled when set
- bit 2: scan add when set, scan skip otherwise
- bit 3: busy-channel lockout
- bits 4-5: encryption key
- bit 6: narrow FM
- bit 7: frequency hopping

Power values are `0 = High`, `1 = Middle`, and `2 = Low`.

## Write status

Writing is intentionally disabled. The CPS symbol-substitution encryption in
the write path, full settings semantics, and write update behavior have not
been independently validated. No upload should be added until those facts are
verified with a controlled physical-radio test.
