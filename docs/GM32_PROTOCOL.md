# Baofeng GM-32 protocol and memory map

This note records the evidence behind `drivers/newchirp_gm32.py`. The driver
keeps CHIRP's tested UV-32 transport and memory implementation, then enables
the GM-32's ten bank-name slots. It is experimental until a complete physical
read/edit/upload/read-back test succeeds.

## Evidence

- Vendor CPS: Baofeng BF-UVs Pro CPS v1.4.7
- CPS archive:
  `https://baofeng.s3.amazonaws.com/Baofeng_UV-32_CPS_v1.4.7.zip`
- Archive SHA-256:
  `d2635bde922a66a182efd00a9c6aae9e79c057648429d3f937fc28051f73fbb2`
- Installer SHA-256:
  `435f2ca868bc323775d717fa8ee46b80987a419078faadc116b216e5d5fef218`
- Main CPS executable SHA-256:
  `9bd0a5eaa01d2cdda2ffe5b65d6cc7b7e71008f8fef99739794e5f02556ed06a`
- Assembly identity: `BF-UVs CPS`, internal family `BF_H802_CPS`
- Static analysis: REA 6.5.0 managed metadata and CIL inspection

The proprietary CPS and extracted files are not stored in the repository.

## Serial session

- Serial format: 115200 baud, 8 data bits, no parity, one stop bit
- Modem control: DTR and RTS asserted; hardware and XON/XOFF flow control off
- Host identification: ASCII `PROGRAMCOLORPROU`
- Radio acknowledgment: `0x06`
- Frequency-range request: `F`, followed by 16 response bytes
- Model request: `M`, followed by the model response; CPS expects `UV32PRO`
- Programming command: a 25-byte `SEND!` packet selecting the CPS encryption
  symbol
- Final acknowledgment for the programming command: `0x06`

The CPS model selector includes `UV32PRO`; no separate `GM32` CPS profile is
present. Vendors describe the GM-32 as supported by the UV-32 programmer.
NewChirp's GM-32 profile asserts DTR and RTS to match the CPS. This differs
from the upstream UV-32 profile and is a likely contributor to the reported
download stall near 1 percent.

## Block transport

Payloads use 64-byte blocks and the existing UV-32 framing:

- Read: `52 | address:u16be | 0x40`; the radio returns a four-byte echo and
  64 payload bytes.
- Write: `57 | address:u16be | 0x40 | data[64]`; the radio returns `0x06`.

The CPS accesses these radio ranges:

| Range | Size | Purpose |
| --- | ---: | --- |
| `0x0000-0x803F` | `0x8040` | Channel records plus VFO data at `0x8000` |
| `0x9000-0x903F` | `0x0040` | Basic radio settings |
| `0xA000-0xA2BF` | `0x02C0` | ANI, call-code, DTMF, bank, and preload data |
| `0xD000-0xD03F` | `0x0040` | Power-on messages |

These ranges match CHIRP's existing UV-32 image layout. The CPS constructor's
separate 41,280-byte progress total includes address space that is not sent by
the block loop; it is not the radio image size.

## Channel records

The radio stores 1,000 channel records in ten banks of 100 channels. Each
record is 32 bytes:

| Offset | Size | Field |
| ---: | ---: | --- |
| `0x00` | 4 | RX frequency, decimal BCD in 10 Hz units |
| `0x04` | 4 | TX frequency, decimal BCD in 10 Hz units |
| `0x08` | 2 | RX CTCSS/DCS |
| `0x0A` | 2 | TX CTCSS/DCS |
| `0x0C` | 1 | signal group |
| `0x0D` | 1 | PTT ID |
| `0x0E` | 1 | power level and shared flags |
| `0x0F` | 1 | bandwidth, squelch mode, busy lock, scan, and FHSS flags |
| `0x10` | 4 | reserved / retained |
| `0x14` | 12 | channel name, GB2312-compatible bytes |

The CPS sets an empty RX frequency to `FF FF FF FF` and an absent name to
`FF` padding.

## Bank names and settings

- Bank names: ten 16-byte GB2312-compatible records from `0xA200` through
  `0xA27F`. These correspond to image offsets `0x8280-0x82FF`.
- Basic settings: one 64-byte record at `0x9000`, corresponding to image
  offset `0x8040`.
- Settings byte order in the CPS matches CHIRP's `settings_obj` order,
  including squelch, power-save, VOX, backlight, timeout, audio, display,
  scan, lock, alarm, DTMF, VFO scan, GPS, and side-key values.

## Validation status

Offline tests verify the image mapping, channel-name offset, bank-name
support, settings offset, and exact block addresses. Physical validation must
confirm:

1. A complete download succeeds without stalling.
2. Channel names persist after upload and read-back.
3. All ten bank names persist after upload and read-back.
4. A representative settings change persists after upload and read-back.
5. The original image can be restored after testing.
