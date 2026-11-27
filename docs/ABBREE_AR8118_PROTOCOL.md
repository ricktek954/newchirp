# Abbree AR-8118 programming protocol

Status: **static analysis only** (no replay, no OEM capture, no radio).
Nothing here has been checked against a physical AR-8118 yet.

The AR-8118 is a 25 W VHF/UHF mobile. A third-party manual (PA0SNY, mailbox
UID 1050) says it is functionally the same as the Hiroyasu IC-980 Pro, the
"Mobile TM8118" and the KSUN 5200D, and that it is programmed over a USB-C
data cable with Abbree's SF-8118 software.

## Evidence

Both packages were downloaded from abbree.com/pages/abbree on 2026-11-27.
Copies are archived in ~/Downloads.

| Package | SHA-256 | Contents |
|---|---|---|
| `8118_136-174M_400-470M.rar` ("UV Dual Band AR-8118") | `9f94cedfce439bc820c4cf7574844bb6ece154de15fe06e35d4e8b67d14ffd68` | Two copies of `8118.exe` and `_config.ini`. **The outer `8118.exe` (SHA-256 `8db617348fdc0cca396074952b640a575e3316f63645c8979cff51e85975f62e`) is infected with the Synaptics/XRed worm** (xred.mooo.com, Synaptics.rar, EXEVSNX). The inner folder's `8118.exe` and both `._cache_8118.exe` files are the clean original (SHA-256 `48f29ab2c4bd02d50d8e6756d341e2cb11a13ce2311ea87ba1d35fdc23958cc3`). |
| `GMRS AR-8118 Programming Software.rar` ("GMRS AR-8118") | `2b9e552a9fe2c8df303b0cd15cf2816eedc9b9891c70006c879df9763e8c5dcd` | Inno Setup 5.5.0 installer `SF-8118.exe`, which unpacks to `app/SF-8118.exe` (SHA-256 `e4ff298ff75334d4d8f200153c1795419859b4b51b88c805a1ea35db2a0e024f`). No infection markers. |

Both programs are Borland C++ Builder applications with the same protocol
constants. The clean dual-band `8118.exe` was decompiled with Ghidra 12.2
headless. Published method names come from the VCL method table (for
example `ProgramStartClick` 0x41BE60, `Agr_HidWrite` 0x41BF54,
`Timer_RxTimer` 0x41FB78, `Read` 0x41DDB0, `Write` 0x41DBFC).

## Transport: USB HID, not serial

The CPS still links a serial component (YbCommDevice and VictorComm32), but
all traffic goes through `Agr_HidWrite`, which calls JVCL
`TJvHidDevice.WriteFile`. Replies arrive in the `OnDeviceData` handler
(`ShowRead` 0x41FAE4), which appends each input report to a receive buffer.

- **Finding the device:** `HidCtlEnumerate` (0x420428) picks the HID
  device whose product string is `ASER-471` and whose manufacturer string is
  `ASER _HID`. The CPS doesn't check VID or PID; it only shows them in its
  device list. The VID/PID is still unknown.
- **Output report size:** taken from `GetCaps` (OutputReportByteLength).
  The CPS fills it as `00` (report ID 0) followed by up to 0x40 payload
  bytes, zero padded.
- **Payloads over 0x40 bytes:** split into 0x3D-byte pieces, each sent as
  `00 4D <count> <index> <61 bytes>`. Channel and settings frames are at
  most 30 bytes, so normal reads and writes never use this.
- **Timeouts:** each step re-arms a 5000 ms timer (`Timer_TimeOut`). The
  connection request is retried 3 times before the CPS gives up.

## Session

| Step | CPS sends | Radio must answer |
|---|---|---|
| 1. Program request | `50 52 4F 47 52 38 31 FF` ("PROGR81\xff") | first byte `53` ("S") |
| 2. Identity | `02` | at least 8 bytes, starting `50 33 32 30 37` ("P3207") |
| 3. Acknowledge | `06` | `06` |
| 4. ID/password block | `52 C0 00 10`, `52 C0 10 10` | each `57 C0 xx 10` + 16 data bytes |
| 5. Reads or writes | see below | see below |
| 6. End | `45` ("E") | nothing |

Other magic strings in the same table are used by other modes and must not
be sent by NewChirp: `PROCODE\xff` (mode 0x0B, "DL") and `SROAPP\x01\xff`
(mode 0x0C, MCU firmware update).

**Password:** byte 0 of the 0xC000 block is the password length; `00` or
`FF` means no password. Otherwise the CPS decodes the block and asks the
user for the password (`Agr_PasswordError`). NewChirp should refuse a radio
with a password rather than try to bypass it.

**Read frame:** `52 hi lo len` ("R"). The reply is `57 hi lo len` + `len`
data bytes ("W"). The CPS checks only that the first reply byte is `57`, so
NewChirp should also check the address and length.

**Write frame:** `57 hi lo len` + data. The radio must answer `06`.

## Read and write order (CPS)

Read (`Read` 0x41DDB0):

1. 0x0000-0x001F in 0x10-byte blocks: the channel-used bitmap.
2. 0xA000-0xA05F in 0x10-byte blocks: VFO A at 0xA000, VFO B at 0xA030.
3. 0xB000-0xB0AF in 0x10-byte blocks (the CPS loops while address < 0xB0AA):
   settings, including band limits at 0xB048-0xB057.
4. Only the channels marked used in the bitmap, each a 0x1A-byte read.

Write (`Write` 0x41DBFC) sends the used channels first, then the bitmap,
0xA000-0xA05F, 0xB000-0xB0AF, and 0xC000-0xC00F only when a flag is set.
Unused channels are not written.

**Channel address** for channel n (1-240):
`0x1000 + (n // 31) * 0x1000 + (n % 31) * 0x1A`.
Channels 241 and 242 always count as used (probably VFO or call channels;
not yet confirmed).

**Bitmap:** channel n is used when `bitmap[n >> 3] & (1 << (n & 7))` is set.

## Channel record (0x1A bytes)

| Offset | Field |
|---|---|
| 0-3 | RX frequency, u32 little-endian, Hz |
| 4-7 | TX frequency, u32 little-endian, Hz |
| 8-9 | RX tone word, u16 little-endian |
| 10-11 | TX tone word, u16 little-endian |
| 12 | bits 0-2: squelch/signalling mode (raw; values 0-4 seen in the CPS); bits 3-4: busy lock |
| 13 | bit 0: unknown toggle; bit 1: compander; bits 2-3: encryption; bit 4: 1 = wide, 0 = narrow; bit 5: 1 = high power, 0 = low; bit 7: 1 = scan add |
| 14 | bits 0-3: scrambler (0 = off) |
| 15 | bits 4-5: RX tone type; bits 6-7: TX tone type |
| 16-25 | Name, 10 bytes |

**Frequency entry:** the CPS rounds to 5 kHz when the value divides evenly,
otherwise to 6.25 kHz. It clamps to the radio's band limits:

- VHF: from the u32 at 0xB048 to the u32 at 0xB04C.
- UHF: from the u32 at 0xB050 to the u32 at 0xB054.

The dual-band package name says 136-174 / 400-470 MHz. Another routine
clamps to 134-520 MHz.

**Tone type** (2 bits):

- 0: off; the word is `FFFF`.
- 1: CTCSS; the word is Hz × 10. The CPS accepts 30.0-259.9.
- 2: DCS normal; the word is `0x2800 +` the three-digit octal code.
- 3: DCS inverted; same encoding as normal.

## Still to confirm on a radio

- The USB VID/PID and the HID report sizes.
- The exact reply to "PROGR81": only its first byte is checked.
- The meaning of channels 241/242 and of byte 12 bits 0-2 and byte 13 bit 0.
- The settings layout at 0xA000 and 0xB000 beyond the band limits.
- Whether the GMRS model uses the same layout. Its CPS uses the same
  protocol constants, but its band limits and GMRS channel rules have not
  been compared.
