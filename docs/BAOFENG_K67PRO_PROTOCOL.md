# Baofeng K67 Pro CPS protocol

## Scope and evidence

This document records the serial transport and image fields used by the
experimental Baofeng K67 Pro driver in
`drivers/newchirp_baofeng_k67pro.py`.

Evidence is currently static analysis of the official Baofeng K6/K63 CPS:

- The CPS was unpacked without executing it.
- The managed `BF-K6 CPS.exe` IL was inspected for serial setup, handshake,
  read, write, frequency, tone, channel, and address-range behavior.
- No OEM serial capture, replay capture, saved physical image, or
  NewChirp-controlled physical read is available yet.
- Baofeng's official download page lists the CPS under `K6/K63`, not
  `K67 Pro`. A third-party CPS tutorial associates K67 Pro with this same
  download, but that is not official model validation.

Therefore the K67 Pro name and image decoder are experimental. This evidence
does not prove that every radio sold as K67 Pro uses the same firmware or
memory map.

## Proprietary artifacts

- Official Baofeng download page:
  `https://www.baofengradio.com/pages/download`
- CPS ZIP:
  `https://baofeng.s3.amazonaws.com/BAOFENG_K6_CPS_1.1.2_20240913.zip`
- ZIP SHA-256:
  `3f9c52ece3a8b6726fba4135b5a0f458b5d81f47d2e83af75045e82d8931b917`
- Installer SHA-256:
  `62b3cd09bedc8c5d789e293743363efe7434fec2fe631959954e3ca80d91162e`
- Extracted `BF-K6 CPS.exe` SHA-256:
  `a9017b8b840c4e00e9d575077dc2d44f465ccab2f30fba6dbb4c18e58f08e271`

The ZIP filename and installer report CPS 1.1.2. The executable About string
instead reports `v1.1.1`; both values are retained here rather than treating
them as interchangeable.

## Serial transport

- Baud rate: 115200
- Framing: 8 data bits, no parity, 1 stop bit
- Flow control: none observed
- DTR: asserted
- RTS: asserted
- Cable: standard Baofeng K-type USB programming cable

The CPS opens the port with both control signals asserted. The desktop driver
reports `WANTS_DTR` and `WANTS_RTS`; the Web Programmer tries the same signal
combination as part of its normal session retry policy.

## Session

### Entry

The host sends the ASCII bytes:

```text
50 52 4f 47 52 41 4d 42 46 2d 4b 36 50 52 4f 55
```

This is `PROGRAMBF-K6PROU`. The expected radio acknowledgement is one byte:

```text
06
```

### Identity

The host then sends ASCII `F` (`46`). The CPS waits for at least 16 bytes and
then waits for an additional 15 bytes, reading all currently available bytes
at each stage. The 31-byte exchange contains the ASCII marker `K6PROU`.

The second identity chunk is parsed by the CPS as
`<model>+<five digits>`. The known model entry associated with this CPS path is
`1702/06`. Exact chunking can vary with OS and cable buffering, so the drivers
read the 31-byte total with a completion timeout and validate the marker rather
than depending on callback boundaries.

### Exit

The host sends ASCII `E` (`45`) after a successful download. The analyzed read
path does not require a response at this stage.

## Read operation

One 64-byte block request is:

```text
52 | address:u16be | 40
```

The expected response is exactly 68 bytes:

```text
52 | returned_address:u16be | 40 | payload[64]
```

The driver rejects a response whose command byte, address, or payload length
does not match the request. The CPS sends blocks sequentially and monitors the
reply size rather than using a trailing checksum.

The K67 Pro driver reads these address ranges:

```text
0000-7cff  channel records and general program data
7d00-7d3f  two additional 32-byte channel records
9000-907f  identity/settings region
a000-a2bf  program settings
c000-c03f  additional settings
d000-d03f  engineering or model data
```

Unread gaps remain `0xff` in the in-memory image. The logical image size is
`0xd040` bytes.

## Write operation observed in the CPS

The CPS constructs a 68-byte write frame:

```text
57 | address:u16be | 40 | payload[64]
```

It waits for ACK `06`. The desktop and browser drivers do not transmit this
operation yet. Writes remain disabled until a physical read, an untouched
backup, one controlled inactive-channel write, and a complete read-back verify
the field mapping and unaffected regions.

## Channel records

The image starts with a 1,000-entry channel array. Each record is 32 bytes.
Desktop memory number 1 maps to CPS array index 0 and image offset `0x0000`;
memory number 1000 maps to image offset `0x7c80`.

| Offset | Size | Meaning |
| --- | ---: | --- |
| 0 | 4 | Receive frequency, little-endian packed BCD |
| 4 | 4 | Transmit frequency, little-endian packed BCD |
| 8 | 2 | Receive CTCSS/DCS |
| 10 | 2 | Transmit CTCSS/DCS |
| 12 | 1 | Signal group |
| 13 | 1 | PTT ID |
| 14 | 1 | High nibble scramble, low nibble power |
| 15 | 1 | Bandwidth, squelch mode, busy lock, scan add, FHSS |
| 16-19 | 4 | Unmapped in this driver and preserved |
| 20 | 12 | GB2312 channel name |

### Frequency encoding

Each BCD byte contains two decimal digits. The bytes are stored least
significant group first. Decoding reverses the four bytes, parses them as an
eight-digit decimal integer in 100 Hz units, and multiplies by 100:

```text
00 52 46 01 -> decimal 01465200 -> 146.520000 MHz
50 97 22 01 -> decimal 01229750 -> 122.975000 MHz
```

The channel frequency resolution is 100 Hz.

### CTCSS and DCS

The CPS tone table contains:

```text
0-50     51 CTCSS entries
51-154   104 normal-polarity DCS entries
155-258  104 reverse-polarity DCS entries
```

For a channel tone word:

- zero means no tone;
- a nonzero high byte is a CTCSS value in tenths of a hertz;
- high byte zero and low byte `1` means the first normal DCS entry, `D023N`;
- low bytes `105` through `208` select the reverse-polarity entries.

The CPS provides independent receive and transmit tone words, so cross tones
and different receive/transmit DCS codes are representable.

### Channel flags

Byte 15 uses these known bits:

- bit 6: wide bandwidth;
- bit 3: busy-channel lock;
- bit 2: scan add;
- bit 0: FHSS.

Bit 4 is the squelch mode. The current read-only driver exposes only the
fields it can map safely to CHIRP and preserves all other bytes.

The current image decoder exposes:

- 1,000 channel slots;
- receive and transmit frequency, including transmit-disabled and split
  memories;
- independent receive/transmit CTCSS and DCS, including polarity;
- wide/narrow FM and airband AM presentation;
- High/Low power labels;
- scan skip;
- GB2312 names.

Settings pages, signal-group meaning, PTT-ID meaning, scramble, squelch mode,
busy lock, FHSS, and byte 16-19 semantics are not yet exposed.

## Validation policy

The maintained desktop driver and browser profile are read-only and
experimental. Offline tests cover:

- raw little-endian BCD frequency vectors;
- all sparse read ranges and the 68-byte block framing;
- channels 1 and 1000 at the correct array offsets;
- CTCSS and DCS table decoding;
- AM airband presentation;
- full 1,000-channel parsing;
- registration and disabled uploads.

The next milestone requires a physical K67 Pro owner to:

1. Read the radio through NewChirp and save the unedited image.
2. Confirm the reported identity bytes and compare at least several radio
   channels with the decoded names, frequencies, tones, power, and bandwidth.
3. Save the same radio's image through Baofeng CPS and compare addresses and
   channel records.
4. Enable writes only after a separate reviewed implementation writes one
   inactive channel and verifies a complete read-back.
