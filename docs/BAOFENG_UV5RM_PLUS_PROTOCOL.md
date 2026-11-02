# Baofeng UV-5RM Plus Protocol Evidence

Last updated: 2026-11-02

This document records the official-CPS evidence for the Baofeng UV-5RM Plus
family and the NewChirp compatibility decision. The application identifies
itself as `T6UV Series EN CPS` and uses the internal namespace `BF_H802_CPS`.

## Official artifact

- Official product page:
  `https://www.baofengradio.com/products/uv-5rm-plus`
- Official download page:
  `https://www.baofengradio.com/pages/download`
- CPS URL:
  `https://baofeng.s3.amazonaws.com/BAOFENG_UV-5RM_Plus_CPS_20240327.zip`
- CPS archive SHA-256:
  `63fcd01605238017040647c4fe3a8d2cccf544d76440027511c1953255d2b13f`
- Installer: `T6UV Series EN CPS setup.exe`, Inno Setup 5.6 payload
- Installer SHA-256:
  `5ec618e8685cdc96be90fbf3551ee402d7a89796c37f16819405b7f835b65905`
- Extracted CPS: `T6UV Series EN CPS.exe`, .NET Framework 4.0, CIL-only
- Extracted CPS SHA-256:
  `5fb0880f45602a56a55dfba6e9a20a7972ac9f75e4286fd8f406372e0343ae1d`
- CPS assembly MVID: `4109b04e-070d-4d86-965a-848c34dd84a0`

The original ZIP and extracted installer payload are archived under
`~/Downloads/BAOFENG_UV-5RM_Plus_CPS_20240327*`.

## REA evidence

- REA: 6.5.0
- Ghidra: 12.1.4, with the official arm64 native decompiler built from source
- .NET metadata and CIL inventory: `rea inspect-managed-artifact` and
  `rea inspect-managed-members`
- C# reconstruction: ILSpy 11.2.0.10050
- Relevant type: `BF_H802_CPS.Communication`
- Relevant methods: `DoIt`, `HandShake`, `Read`, `Write`
- Serial setup: `BF_H802_CPS.FormProgress.ConfigSerialPort`
- Evidence level for the protocol below: E1, static call path and constants

No OEM serial capture or physical NewChirp comparison is available yet.

## Serial setup

The official CPS configures the port before opening it:

- 115200 baud
- 8 data bits
- no parity
- one stop bit
- RTS enabled
- DTR enabled
- one-second state-machine retry timer
- five retries

## Handshake contract

| Step | Host bytes | Expected response | Completion rule |
| --- | --- | --- | --- |
| 1 | ASCII `PROGRAMBFNORMALU` | `06` | One byte equal to `0x06` |
| 2 | `46` | 16 bytes | Exactly 16 bytes |
| 3 | `4D` | At least 15 bytes | ASCII model/version text containing `+` |
| 4 | 25-byte encrypted `SEND` packet | `06` | One byte equal to `0x06` |

The OEM application sends `PROGRAMBFNORMALU` again after a one-second timeout,
up to five attempts. A stray byte that is not `0x06` does not immediately
abort the OEM transaction.

The encrypted `SEND` packet is variable:

- Bytes 0-3 are ASCII `SEND`.
- Byte 4 encodes a selector in the high nibble and low bits.
- Bytes 5-24 contain selector indices.
- One of twenty four-character symbols is selected and used to XOR the payload.
- The complete table and packet generator are recorded in the reconstructed
  `Communication` type from the exact CPS hash above.

## Read contract

Each read request is four bytes:

```text
52 <address-high> <address-low> 40
```

This is ASCII `R`, a 16-bit big-endian address, and a 64-byte block length.

Each response is 68 bytes:

```text
52 <address-high> <address-low> 40 <64-byte payload>
```

The response payload is decoded with the four-byte symbol selected during the
handshake. Bytes equal to `0x00`, `0xFF`, the symbol byte, or its complement
are preserved. All other bytes are XORed with the rotating symbol.

The CPS advances by 64 bytes. It skips unused gaps in the address map rather
than treating every address from zero to 53,312 as contiguous.

## Write contract

Each write request is 68 bytes:

```text
57 <address-high> <address-low> 40 <64-byte payload>
```

This is ASCII `W`, a 16-bit big-endian address, and a 64-byte block length.
The radio acknowledges successful writes with `06`. The end transaction sends
ASCII `E` (`0x45`).

## Memory map

| Start | Data |
| ---: | --- |
| `0x0000` | 500 channel records, 64 bytes each |
| `0x8000` | VFO A and VFO B records in one 64-byte block |
| `0x9000` | Function and radio-wide settings |
| `0xA000`-`0xA140` | DTMF ID and 20 contact/group records |
| `0xD000` | Power-on display lines |

The first 32 payload bytes of a channel block encode one channel; the second
32 bytes encode another channel. Channel fields include RX/TX frequency,
CTCSS/DCS, signal group, PTT ID, power, bandwidth, squelch mode, busy lock,
scan add, FHSS, and a 12-byte GB2312 name.

## NewChirp decision

The pinned CHIRP `BaofengUV5RMPlus` driver already sends the same
`PROGRAMBFNORMALU` request, reads one byte, and requires `0x06`. Therefore the
reported one-byte failure is before any channel-map difference.

NewChirp now mirrors the OEM recovery behavior for this exact model by retrying
the handshake at one-second intervals, up to five attempts, when a stray byte
is returned. It also records the returned one-byte value in the diagnostic
trace. The channel and write implementation remains the pinned CHIRP driver
until a physical retest or OEM serial capture proves another difference.

Next milestone: reporter retests the next normal Linux build. If it still
fails, capture the exact one-byte reply and one OEM read in the Windows VM.
