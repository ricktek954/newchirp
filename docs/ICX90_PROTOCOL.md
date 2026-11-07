# Icom IC-E90 / IC-T90A clone protocol

The IC-E90 and IC-T90A use the legacy Icom ICF clone transport and a fixed
`0x2D40`-byte memory image. NewChirp owns the transport instead of inheriting
CHIRP's immediate-stream upload path because the CS-T90A CPS retries identity,
waits for serial echo when present, and waits for clone completion.

## Evidence

- Software: **Icom CS-T90A Cloning Software**, revision 1.0 (2002)
- Downloaded archive:
  `/Users/rlopez/Downloads/CS-T90A-251201-001044.ZIP`
- CPS ZIP SHA-256:
  `c520827dd586f4bcd4304c999699b01c723ee0d4cbc0fbb0f07b6d04892d0fae`
- Main executable `CST90A.exe` SHA-256:
  `aae6ea1353a3b0f85379bf30eb66a69fc7814a5a370a555acee2579d64ff7adf`
- Help file `CS-T90A.HLP` SHA-256:
  `8e47186f685265f254d4fb60a0c7beb8d2b0c787fd7918d2f1484bf0d6903ae9`

The archive is a RadioSoftware distribution of the Icom installer. Its
`file_id.txt` identifies CS-T90A for IC-T90A/IC-T90E. The internal Icom CPS
executable matches the previously analyzed hash. The installer was never run.
The executable and archive remain external evidence and are not committed.

REA coverage:

- VB6 object inventory identifies `clsCmcIcf3Drv`, `clsCmcIcf3Sequence`, and
  `clsCmcRadio` as the clone implementation classes.
- The Communication class exposes `easyCloneInitInfo`, `easyCloneInfo`,
  `easyCloneRead`, `easyCloneWrite`, and `easySendE8`.
- The low-level class exposes `Send`, `RetrySend`, `waitAnswer`, `waitEcho`,
  `retryCount`, `sizDataOfPacket`, `ClearRxBuffer`, and explicit error state.
- UTF-16 literals include serial framing `,N,8,1`, the ASCII hexadecimal
  completion marker `49636F6D20496E632E` (`Icom Inc.`), and the CPS completion
  text `Clone writing succeeded.`
- Ghidra resolves the clone-write UI path through `FUN_00436651` and the
  low-level result dispatcher through `FUN_00438fb5`.

## Image and transport

- Protocol: legacy Icom ICF clone mode
- Model bytes: `25 07 00 01`
- Image size: `0x2D40` / 11,584 bytes
- Channel records: 500
- Serial encoding: hexadecimal ICF data frames
- Normal transfer rate: 9,600 8N1

The public upstream IC-E90 reference image used during offline validation has
SHA-256:
`67a9eb3a2c90c3891aad981299e4bd4c3b09c9df6bd45d70e95d077593766a1b`.

## Protocol contract

| Action/state | Host bytes | Response rule | Next state |
| --- | --- | --- | --- |
| Identify | `FE FE EE EF E0 00 00 00 00 FD` | `E1`; payload starts `25 07 00 01`; 39 bytes observed on IC-E90 | Retry up to four times; then read or write |
| Start clone out | `FE FE EE EF E2 25 07 00 01 FD` | `E4` data frames, then optional `E5` | Assemble image |
| Start clone in | `FE FE EE EF E3 25 07 00 01 FD` | Radio changes from `CLONE` to `CL IN`; echo may appear first | Settle, then stream blocks |
| Data block | `FE FE EE EF E4 <ASCII payload> FD` | Echo only when using an echoing cable | Next 32-byte block |
| Data payload | uppercase hex of `address:u16be, length:u8, data, checksum` | Reply is ASCII hex of the same structure | Contiguous address validation |
| Checksum | `0x00 - sum(address + length + data)` | Must match byte before `FD` after hex decode | Reject mismatch |
| End | `FE FE EE EF E5 Icom Inc. FD` | `E6`, payload `00` for success | Complete |
| Read completion | 362 contiguous 32-byte data frames | Accept normal `E5`; also accept full coverage if a revision omits it | Image complete |

`E8` high-speed setup is implemented by the CPS class but is not used for this
model. The recovered normal-speed path does not establish a separate `E3`
response frame; completion is the `E6` after `E5`. The radio's `CL IN`
transition is the physical state indication; a failed or lost identity query
leaves it displaying `CLONE`, while a write begun from `CL OUT` is in the
previous transfer direction.

A NewChirp report captured a 39-byte model response followed by 28,261 bytes of
clone traffic. That byte count is consistent with the complete fixed image plus
ICF framing and is not a truncated channel table.

Some IC-E90 revisions finish sending the complete image without leaving the
generic ICF parser with a recognizable final end frame. The driver therefore
accepts a download once:

1. every byte of the fixed `0x2D40` image has been received; and
2. the decoded data frames cover the image contiguously from address zero.

A normal `Icom Inc.` end frame remains accepted when present. Incomplete,
out-of-order, checksum-invalid, or sparse images fail.

## Physical evidence and failure mode

The 2026-11-07 report from Tony G4WIF established the decisive hardware state:

- A fresh clone session displays `CLONE`.
- NewChirp read the radio, moved it to `CL OUT`, and it returned to `CLONE`
  after the read.
- A power-cycled radio still displayed `CLONE` and did not change during two
  failed write attempts. The app reported no response from the radio.
- After an all-reset cleared the radio, CHIRP Next wrote successfully and the
  display changed to `CL IN`.
- NewChirp 1.0.45 then read the clean radio, changed one name from `Dummy` to
  `DUMMY`, wrote successfully, and again received `CL IN`.

This means the write failure occurred before image streaming: the radio never
accepted the clone-in direction. The inherited path performed one identity
query and immediately streamed data after `E3`. NewChirp now retries identity,
clears stale serial input, consumes cable echo, waits for the clone-in
turnaround, and requires `E6 00` before reporting success.

## Validation limits

The reference image round-trips byte-for-byte through the inherited ICX90 field
layout. Offline tests cover identity retries, echoed and non-echoed cables,
normal and missing download end frames, checksum rejection, sparse/truncated
rejection, complete 362-block writes, clone-in ordering, and completion
timeouts. The new transport still requires a physical retest on Tony's radio
before it is promoted beyond experimental.
