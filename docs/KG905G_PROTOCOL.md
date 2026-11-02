# Wouxun KG-905G Plus protocol

This note records the evidence behind `drivers/newchirp_kg905g.py`. The
driver is experimental. On 2026-11-02 a download matched the radio, and
one channel-name write was confirmed on the radio. The captures below
are the earlier Wouxun-program evidence for the byte map.

## Evidence

Captures stay in Downloads and are not committed.

- Read, 2026-11-02 09:33 PST:
  `/Users/randybrown/Downloads/KG_905G_Plus/905GplusREAD.pcap`
  `8f2196178c139f5a5571f69217ac74d63b101b994f8dda38eaba8b4a1cf4125c`
- Write, 2026-11-02 09:38 PST:
  `/Users/randybrown/Downloads/KG_905G_Plus/905GWRITE.pcap`
  `4283a39bea678eafff77191237e797491cfc55f64bb9ad902418e08c5197cfa3`
- CPS save, 2026-11-02 09:41 PST:
  `/Users/randybrown/Downloads/KG_905G_Plus/KG905G_PLUS.kg`
  `c35c7be56ad378d35c779540046d6593c6acd689d8309eb356ed5522ddfe21b0`

The `.kg` file is a third snapshot. It is not byte-identical to either
capture. Live clone does not import it. The wrapper is the Wouxun text
form: `xiepinruanjian` plus CR LF, then the Latin-1 image stored as
UTF-8, then CR LF. Decoded, that file is 50000 bytes.

The link matches the KG-Q336 rolling-XOR framing (seed `0x54`), not the
KG-935G framing (seed `0x57` at 19200 baud). Reference:
`https://raw.githubusercontent.com/ast/narm/main/docs/kgq336-codeplug.md`

## Serial session

- Cable: Wouxun K-plug. The capture adapter is a Silicon Labs CP210x
  (USB VID `0x10C4`, PID `0xEA60`).
- Format: 19200 baud, 8 data bits, no parity, one stop bit
- DTR asserted and RTS asserted. The captured CP210x setup writes baud
  `19200` (`0x00004B00`) and leaves both modem lines on before the first
  probe. A later 115200 setting in the same capture belongs to another
  USB device.
- No hardware or software flow control

Frame, both directions:

```text
7C | cmd | dir | len | encrypt(payload || checksum)
```

`dir` is `0xFF` from the computer and `0x00` from the radio. `len` is
the plaintext payload size and does not include the checksum byte. The
frame is `5 + len` bytes.

Commands used here: `0x82` read, `0x83` write, `0x81` end. Encrypt with
seed `0x54`: the first cipher byte is `seed XOR plain[0]`, and each
later cipher byte is `previous cipher byte XOR plain[i]`. Decrypt is
the inverse. The checksum is
`(cmd + dir + len + sum(payload) + adjust) & 0xFF`. `adjust` is chosen
from `payload[0] & 3`: `+3`, `+1`, `-1`, `-3`. An empty payload uses
`+3`.

The model probe is a read of physical `0x0040` for 64 bytes. On the
wire it is `7C 82 FF 03 54 14 54 53`. The computer sends it three
times, then reads one reply. The reply starts with `KG-905G+`. Later
reads are sent twice each, then one reply. End of session is one
`7C 81 FF 00 D7` and no reply.

A read reply is the address plus the data. A 64-byte read uses payload
length 66. A write sends the address plus the data. The radio answers
with command `0x83`, direction `0x00`, and the same two address bytes.
This radio writes 64-byte blocks. The Q336 write size of 32 does not
apply. A few blocks are shorter: `0x0640` is 16, `0x1DE0` is 16,
`0x2880` is 8, `0x3280` is 17, `0x3400` is 40, `0x30A0` is 62, and
`0x3540` is 40.

## Read and write map

The read is 172 blocks. The first is `0x0040`. The image covers through
`0x3700`. The exact list is `READ_BLOCKS` in the driver.

The write is those blocks except four that are read and not written:
`0x0040`, `0x0080`, `0x00C0`, and `0x0700`. The first three are factory
identity. `0x0700` overlaps the `0x06E0` block, which is the one that
holds memories 1 through 3. The Wouxun program reads `0x0700` during
the write handshake and does not write it.

Two written blocks also overlap, and the radio does not return the
same bytes for both:

- `0x1BE0` for 64 bytes ends with 32 zero bytes.
- `0x1C00` for 64 bytes starts with the channel names.

The flat image keeps the names. The driver stores the earlier 32 bytes
in a trailer (`KG905OVL`) and sends those bytes back with the `0x1BE0`
write. The names go out only with the `0x1C00` write. `0x1FE0` and
`0x2000` overlap as well. In this capture both copies are zero.

`0x0640` is a 16-byte record that is not one of the channel slots. It
is written back unchanged. `0x0740` is the start of the settings area.
Those bytes are preserved and are not shown as settings.

## Memories

The radio offers 400 memories. This capture supports memories 1
through 31 only. Memory 31 was present and empty. Memories 32 through
400 are not mapped. Do not guess addresses for them.

Memory `n` uses index `n - 1`. The record address is:

```text
adjusted = index + 13
address = 0x620 + (adjusted % 16) * 16 - (adjusted // 16) * 0x100
```

Index 0 is `0x06F0`. Index 30 is `0x04D0`. Each record is 16 bytes:

```text
ul32 rx frequency, in 10 Hz units, little-endian
ul32 tx frequency, same units
ul16 rx tone
ul16 tx tone
u8   power in the low 2 bits (0 = Low, 1 = High); other bits kept
u8   bit 0 wide (1 = FM, 0 = NFM), bit 5 scan add; other bits kept
u8   call group (a new channel uses 1)
u8   kept as read
```

Tone high nibble: `0` off, `4` DCS normal, `6` DCS inverted, `8`
CTCSS. CTCSS uses tenths of a hertz in the low 12 bits. DCS uses the
octal code converted to an integer. This is not the KG-935G tone
layout.

Names are 8 bytes at `0x1C08`, one name every 8 bytes. The capture
uses spaces or NUL bytes to fill the rest. A valid flag for index `i`
is at `0x3301 + i`. `0x9E` means the slot is used. `0x00` means empty.
FM broadcast presets start at `0x3400` and are not edited.

## GMRS transmit rules

Simplex must be one of the 22 GMRS simplex frequencies, with offset 0.
That includes the seven 467 MHz interstitial channels. A repeater must
be one of the eight GMRS repeater outputs, and the offset must be
exactly 5 MHz. Anything else is rejected. Interstitial channels are
stored narrow and Low. Receive-only was not present in the capture, so
the driver does not invent a receive-only encoding.

## What is still unknown

- Where memories 32 through 400 are stored
- The meaning of most settings bytes, including the single settings
  byte that changed between the read and the write capture
- The repeating table at `0x3066`
- The 16-byte record at `0x0640`
- Whether a frequency outside GMRS can be stored as receive-only
