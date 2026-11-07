# Radioddity GA-510 V2 Programming Protocol

Last updated: 2026-11-07

This document records the official CPS evidence and transport used by
`drivers/newchirp_ga510_v2.py` for the newer GA-510 V2 hardware.

## Evidence inventory

| Artifact | SHA-256 |
| --- | --- |
| `GA-510_CPS_v1.00.36.zip` | `e4e9638dd86e88a05299ed38886ccfc2b2d8a05942e565fc8d6392718b5067f5` |
| CPS installer `Setup v1.00.36 en.exe` | `524eabfc551382165b184e91c170534dfd5a3d69f5b249e5fe435f8da258d774` |
| Installed native CPS executable | `28e865070f5a46024b4f5e30458b9b044689dc99c6f1c5a68a6ba127ef6631b9` |
| `2020-02-20 Radioddity GA-510 Programming Software.zip` | `13f94d56afde01619844c9e0c6431e35478778984808157be81674b219fe4372` |
| CHIRP V2 fixture `Radioddity_GA-510_V2.img` | `ab9848966a53ad26fd065d5d7101e77109120113ba467664b90a4c8c3d64ce4a` |
| Pinned CHIRP `ga510.py` reference | `6f6ce28ccc07fc62fa873db19127785fd456cc0c11a979ffcac3e44266c1ca15` |
| User manual PDF | `66daa6fcd03cbf56f6ee38b1a58cb465869762b8e91b938c522b083e3c9f1012` |

The official CPS package and manual are retained in `/Users/rlopez/Downloads/`.
The CPS is a native 32-bit MFC application. Its serial path was traced at
these executable addresses:

- Serial configuration/open: `0x41B000`
- Raw write: `0x41A100`
- Timed exact read: `0x41A270`
- `PSEARCH`: `0x418DF0`
- `PASSSTA`/`PASWORD`: `0x419010`
- `DMR1702`: `0x4192B0`
- `SYSINFO`: `0x4193C0`
- Memory-info query: `0x419EB0`
- Memory-size query: `0x419D90`
- Unlock command: `0x41A0B0`
- Addressed read: `0x419C50`
- Addressed write: `0x419FF0`

## Serial settings

The V2 CPS opens the programming port at 57,600 baud, 8 data bits, no parity,
and one stop bit. It asserts both DTR and RTS through `EscapeCommFunction`.
There is no hardware or software flow control.

The CPS uses its own polling receive loop. The NewChirp driver therefore
accumulates exact response lengths with short serial reads and enforces a
deadline, rather than trusting one pyserial `read()` call to return the whole
frame.

## Session state machine

| Action/state | Host bytes | Response and completion rule | Next state |
| --- | --- | --- | --- |
| Search identity | `50 53 45 41 52 43 48` (`PSEARCH`) | Exactly 8 bytes; first byte `06`; up to 3 attempts with a 500 ms timeout | `PASSSTA` |
| Programming status | `50 41 53 53 53 54 41` (`PASSSTA`) | Exactly 3 bytes; first byte `50` (`P`) | Optional password, then `SYSINFO` |
| Optional unlock | `50 41 53 57 4F 52 44` (`PASWORD`) | Exactly 1 byte, `06` | `SYSINFO` |
| System information | `53 59 53 49 4E 46 4F` (`SYSINFO`) | Exactly 1 byte, `06`; byte `15` means busy | `DMR1702` |
| DMR identity | `44 4D 52 31 37 30 32` (`DMR1702`) | Exactly 1 byte, `06` | Identity follow-up |
| Identity follow-up | `02` | Exactly 8 bytes, beginning with `06` | Identity confirm |
| Identity confirm | `06` | Exactly 1 byte, `06` | Three memory-info queries |
| Memory-info 0 | `56 00 00 0A 0D` | Three-byte header beginning `56`, returned length at byte 2, payload, then `06` answered by `06` | Next query |
| Memory-info 0x10 | `56 00 10 0A 0D` | Same framing as memory-info 0 | Next query |
| Memory-info 0x20 | `56 00 20 0A 0D` | Same framing as memory-info 0 | Memory-size query |
| Memory size | `56 00 00 00 0A` | Three-byte header beginning `56`, payload, then `06` / `06` | Unlock |
| Memory unlock | `FF FF FF FF 0C` | No response is expected | DMR identity again |

`PASSSTA` controls the password marker: read mode checks response byte 1 and
write mode checks response byte 2. A marker of `A5` invokes the static OEM
`PASWORD` command.

## Memory map and data operations

The CPS requests one-byte descriptors from the end of physical 4 KiB pages,
starting at `0x1FFF` and continuing through `0x6FFF`. A descriptor stores the
logical page number as two decimal digits in hexadecimal nibbles. For example,
`0x16` means logical block 16.

The supported V2 image is assembled from five logical 4 KiB blocks in this
order:

```text
2, 4, 6, 16, 24
```

That produces a `0x5000`-byte CHIRP image. The physical page containing each
logical block is selected from the radio's descriptor map; physical addresses
are not assumed to be stable between sessions.

Addresses on the wire are 24-bit little-endian values.

| Operation | Host bytes | Response |
| --- | --- | --- |
| Read block | `52 <address:le24> <length:u8>` | Exact `length + 5` bytes: five-byte request echo plus payload; then host sends `06` and expects `06` |
| Write block | `57 <address:le24> <length:u8> <payload>` | Exactly one byte, `06`; `15` means rejected/busy |

Reads and writes use 64-byte blocks. The descriptor read is the same operation
with length 1.

## Relationship to the CHIRP driver

Stock CHIRP exposes the V2 memory layout and channel decoding through
`ga510.RadioddityGA510v2`. NewChirp reuses that pinned memory structure and
fixture for channel/settings compatibility, but the transport implementation
is now independently owned and traced from CPS v1.00.36.

The main differences from the bundled CHIRP transport are:

- NewChirp follows the complete CPS session order and fixed response lengths.
- The explicit memory unlock and second `DMR1702` identity stage are included.
- The three memory-info queries and `0x5000`-byte image contract are explicit.
- Physical 4 KiB page placement comes from the descriptor map.
- Every read/write payload and completion byte is validated.
- The generic `Radioddity_GA-510` selector probes V2 first, then falls back to
  the legacy 9,600-baud GA-510 protocol.

## Evidence level and validation

Current evidence is E1/E2:

- E1: official CPS native call-path analysis, serial constants, command
  strings, DCB settings, and fixed lengths.
- E2: synthetic serial replay covering the complete handshake, both selector
  entries, five-block download, mapped writes, descriptor reads, ACKs, and a
  real upstream V2 image fixture.

No OEM serial capture or physical NewChirp read/write has been completed on
this exact hardware variant. The first physical test must save an OEM CPS
backup, read with NewChirp, compare all channels and settings, then perform one
controlled write followed by a full read-back.
