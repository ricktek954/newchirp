# Kenwood KPG-171D / TK-3401D protocol notes

Last updated: 2026-11-01

## Status

This is reverse-engineering evidence for the experimental Kenwood TK-3401D
dPMR446/analogue PMR446 radio. The corresponding
`drivers/newchirp_kenwood_tk3401d.py` driver is read-only.

The serial transport is implemented and covered by an offline test. The
32-channel codeplug map and dPMR-specific channel fields still require
validation from a physical radio read.

## Software and models

- OEM programmer: Kenwood KPG-171D
- Analysed executable: KPG-171D `1.10.1.0`, built 2017-10-18
- Executable SHA-256:
  `3bd15b126fa0776e7f4206ed81931bba1ca4f5884cc81d1f719c1ec9331fb6fd`
- Analysis tools: REA 6.5.0 and Ghidra 12.1.4
- TK-3401D is a 32-channel, two-zone analogue PMR446/dPMR446 radio.
- The KPG-171D executable also contains model strings for NX-240/NX-340,
  EX-4437/EX-4438, TK-2402, and TK-3402 variants.

The TK-3401D model identifiers embedded in the CPS are:

- `PTK 3401`
- `PTK-3401`
- `PTKS3401`

The exact identifier returned by the radio is not yet known.

## Transport

The CPS uses the same command/acknowledgement family as the existing CHIRP
Icom-independent Kenwood NX-x00 and TK-x140 drivers:

- Serial framing is command-oriented rather than the Icom `FE`/`FD` framing.
- `PROGRAM` starts the shared programming session.
- The CPS tests 9600, 19200, 38400, 57600, 4800, 2400, and 1200 baud.
- The NX-x00 family implementation establishes the useful sequence as
  `PROGRAM`, an initial `0x16` speed/programming response, a switch to
  19200 baud, then `0x06`.
- `0x06` is the normal command/data acknowledgement.
- `0x02` is used before an identity exchange. The KPG-171D CPS reads a
  48-byte identity record for this family.
- `P` requests 10 further identity bytes.
- `URK` requests a 34-byte model-information record.

The CPS wire layer XORs every transmitted and received byte with one
session-wide key. The key is derived from local time unless the program INI
contains `noencryption`, in which case the key is zero. The existing NX-x00
protocol can explicitly negotiate a zero key after the initial handshake.
Variable-key negotiation is not yet understood well enough for a safe driver.

## Core memory commands

The following operations were recovered from the read and write routines at
CPS code addresses `0x423a70` and `0x423d90`.

### Read

The normal read request is:

```text
52 ADDR_HI ADDR_LO LEN
```

Observed properties:

- `0x52` is ASCII `R`.
- `ADDR_HI:ADDR_LO` is a 16-bit big-endian address.
- Normal transfer length is `0x80` bytes.
- The first response byte is `W` (`0x57`) for a populated block.
- A populated response consists of a three-byte response header followed by
  128 data bytes.
- After processing a block, the client sends `0x06` and expects `0x06`.
- The CPS starts at address zero and increments by `0x80` until its expected
  image length is reached.

The image-length field and any sparse-range handling remain unresolved.

### Write

The bulk write request is:

```text
59 ADDR_HI ADDR_LO LEN DATA... CHECKSUM
```

Observed properties:

- `0x59` is ASCII `Y`.
- Address is 16-bit big-endian.
- Individual writes are no larger than `0x40` bytes.
- Checksum is the low eight bits of the sum of the data bytes.
- The CPS retries a rejected write up to five times before failing.

## Additional commands

The CPS contains these additional command paths:

| Value | Meaning or observed use | Confidence |
| --- | --- | --- |
| `0x02` | Read identity record | High |
| `0x06` | Acknowledgement / continue | High |
| `0x16` | Initial programming-speed response | High |
| `0x45` (`E`) | Leave programming mode | High |
| `0x50` (`P`) | Read ten identity bytes | High |
| `0x52` (`R`) | Read addressed memory | High |
| `0x59` (`Y`) | Write addressed memory | High |
| `0x71` (`q`) | CPS codeplug transfer | Medium |
| `0x90` | Identification/settings exchange | Medium |
| `+TAR`, `+TOR`, `+TDS` | Tuning-data operations | Medium |

## Driver implementation

The initial driver:

- reads a full 64 KiB image in 128-byte addressed blocks;
- negotiates the clear/zero-key session used by the CPS `noencryption` mode;
- retains the complete image if its provisional record scan fails;
- uses the common 4-byte PMR446 frequency representations to locate up to 32
  channel records;
- exposes discovered frequencies and nearby printable names; and
- blocks every upload.

The record scan is intentionally labeled provisional in the logs. It is meant
to obtain a physical image and make the first read useful while the exact
vendor field map is validated.

## Remaining work

1. Obtain a complete raw image from a TK-3401D after a successful read.
2. Confirm the installed model identifier and firmware version.
3. Determine the image length and sparse-memory ranges.
4. Map the two zones, 32 channel records, analogue PMR446 frequencies,
   CTCSS/DCS, power, scan, and programmable keys.
5. Map dPMR channel fields such as digital/analogue selection, talkgroups,
   contacts, and call settings.
6. Implement read-only support first and compare every decoded field with the
   CPS display.
7. Enable uploads only after a controlled edit and radio read-back agree.

The repository must not claim hardware-tested support until those steps are
completed.
