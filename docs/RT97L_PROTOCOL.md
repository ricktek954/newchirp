# Retevis RT97L experimental protocol notes

These notes document the interoperable facts used by the read-only
`newchirp_rt97l.py` driver. They were derived from public protocol analysis of
the Windows RT97L programmer and independent verification with synthetic
serial tests. Vendor binaries and reverse-engineering code are not included
in this repository.

## Evidence

- Radio: Retevis RT97L GMRS repeater
- Related model reported by the same protocol: CX-525
- Public protocol notes:
  `https://github.com/briankwest/rt97l-tool/blob/main/docs/protocol.md`
- Public protocol tree inspected:
  `378b6fb634edbd0b440c59fae201787b7473f599`
- The public tool has no declared license, so NewChirp does not copy its code.
  This driver is an independent implementation of the documented wire format.

## Serial setup

- 9600 baud, 8 data bits, no parity, one stop bit
- DTR and RTS asserted
- Device response timeout: approximately 1 second; NewChirp allows 2 seconds

The stock programming cable uses a USB-to-serial adapter with a DB9 connector.

## Handshake

1. The radio sends ACK `0x06` when programming mode opens.
2. The host sends STX `0x02`.
3. The radio returns an 8-byte identifier beginning with ASCII `P3` and ending
   in `0xFF`.
4. The host sends ACK, and the radio returns ACK.

NewChirp does not flush the serial input before step 1 because doing so can
discard the initial ACK.

## Read framing

The configuration image is 256 bytes. It is read in eight 32-byte blocks.

Request:

```
52 | address:u16be | 20
```

Response:

```
57 | address:u16be | 20 | data[32]
```

The host sends ACK after every block, then reads the radio's ACK before
requesting the next block. ASCII `E` (`0x45`) ends the session.

## Provisional channel layout

The 256-byte image appears to contain sixteen 16-byte channel records:

| Offset | Meaning |
| --- | --- |
| `0x00-0x03` | Receive frequency, eight BCD digits in 10 Hz units |
| `0x04-0x07` | Transmit frequency, same encoding |
| `0x08` | Transmit tone/code index |
| `0x09` | Receive tone/code index |
| `0x0A` | Power, channel-mode, and compand flags |
| `0x0B` | Squelch level; `0xFF` means off |
| `0x0C` | Scan-add and channel-lock flags |
| `0x0D-0x0F` | Unconfirmed or reserved |

Tone index `0` is off, `1-50` selects the standard CTCSS table, `51-155`
selects normal DCS codes, and `156-260` selects the corresponding inverted
DCS codes.

The receive/transmit roles, flag bits, tone table, global-setting location,
and password fields still require validation against physical hardware and an
official programmer capture. The current driver therefore:

- Implements live download and channel decoding
- Exposes unknown fields only as read-only extra information
- Does not expose global settings
- Rejects every write operation

## Next validation milestone

Capture one complete image from a physical RT97L and compare it with the same
configuration saved by the official CPS. Record:

- Every channel's RX and TX frequency
- CTCSS and DCS values in both directions
- Power, squelch, scan, lock, channel mode, and compand
- Password field behavior
- The complete 256-byte raw image

Upload support must remain disabled until the read map is confirmed and a
controlled write/read-back test succeeds.
