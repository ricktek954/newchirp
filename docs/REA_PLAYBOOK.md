# Radio Driver Reverse-Engineering Playbook

Last updated: 2026-11-12

Use this process whenever a NewChirp driver is derived from an OEM
programming application. The goal is to avoid implementing a plausible
protocol that does not match the bytes on the serial port.

## Core rule

Do not treat a recovered memory map, command string, or protocol family as a
complete transport. For every operation, establish:

1. What the application sends.
2. How the radio's response is encoded on the wire.
3. How the application determines when the response is complete.
4. How it handles shorter, fragmented, delayed, or repeated responses.
5. How the next request or state transition is selected.

All five must have evidence before a driver implementation is considered
ready for physical testing.

## Required artifacts

Record these in a protocol document such as `docs/<RADIO>_PROTOCOL.md`:

- Official application name, version, download source, and SHA-256.
- Relevant executable and dependency SHA-256 values.
- Radio model, variant, firmware, and regional identity evidence.
- Complete protocol contract described below.
- Offline replay/test-vector coverage.
- Physical read validation and, separately, physical write/read-back
  validation.
- Unresolved fields and behaviors.

## Protocol contract

Create a row for every command or state transition. Do not stop at the list of
opaque command prefixes.

| Item | Required evidence |
| --- | --- |
| Action/state | The UI action or state-machine branch that starts the operation |
| Host bytes | Exact bytes or encoding formula sent to the radio |
| Response encoding | Binary, ASCII text, hexadecimal text, framing, or other |
| Response layout | Header, address, length, payload, checksum, terminator |
| Length rule | Formula based on requested length and/or returned length fields |
| Completeness rule | Fixed count, delimiter, returned length, callback threshold, or timeout |
| Fragmentation | Whether responses can arrive in multiple callbacks or packets |
| Checksum | Exact covered bytes and algorithm |
| Flow control | Baud rate, DTR, RTS, XON/XOFF, ACK rules, and timing |
| Retry behavior | What the OEM application retries and what advances state |
| Next state | How success and failure select the following operation |
| Evidence | Artifact hash, type/method token, CIL offset, capture, or hardware result |

A compact example:

```text
Read block
TX:      FE FE EE EF EB <address:4> <length:2> FD
RX wire: uppercase ASCII hex
RX text: 22 header chars + 2 * returned_length chars + 4 tail chars
Frame:   header:5 address:4 length:2 payload:N checksum:1 FD:1
Length:  use the returned length field; it may be shorter than requested
Next:    address += returned payload length
```

## REA workflow

### 1. Inventory the artifact

- Hash the downloaded archive and every extracted application/dependency.
- Identify native/managed runtime, architecture, and required libraries.
- Find strings, constants, resource tables, and embedded templates.
- Record uncertainty rather than inferring behavior from a filename.

### 2. Trace from user action to serial output

Start at the OEM UI action and follow calls until bytes enter the serial API.
Capture:

- initial serial settings and control-line changes
- command construction and encoding conversions
- delays, retries, and baud-rate changes
- state variables that decide which command is sent next

Do not begin with only the command constants. Constants without their state
machine are not a protocol.

### 3. Trace from serial input to decoded data

Follow the receive callback through every buffer and conversion stage:

```text
SerialPort receive callback
  -> byte threshold / packet assembly
  -> line or frame parsing
  -> text/hex/binary conversion
  -> header and length parsing
  -> checksum validation
  -> memory/field decoder
  -> next state
```

This is where binary commands and text responses can diverge. A command may be
sent as binary while its response is returned as ASCII hexadecimal.

### 4. Extract dynamic length and completion rules

Search for all of the following and compare them:

- `Read`, `ReadExisting`, `ReadLine`, `BytesToRead`
- `ReceivedBytesThreshold`
- string slicing around address or length fields
- `Substring`, bit shifts, `ToString(..., 16)`, and `Convert.ToByte(..., 16)`
- timeout timers and callback counters
- delimiter checks such as `FD`, CR, or LF

Write the completion rule as a formula. A fixed `requested_length + overhead`
rule is invalid unless the receive parser also proves the response always
returns the full requested length.

### 5. Build replay evidence before hardware

Create a fake transport whose responses use exactly the CPS wire encoding.
Test at least:

- maximum-size responses
- shorter responses with a valid returned length
- fragmented and delayed responses
- malformed checksums
- incorrect addresses and lengths
- missing and early terminators
- baud/control-line transitions

The fake transport must not simplify away the behavior under investigation.

### 6. Capture the OEM application when possible

A successful serial capture from the official CPS is the strongest oracle.
Capture one read and one write when the hardware is available. Store hashes and
redacted protocol summaries, not user channel contents or private codeplugs.

Compare:

- exact host bytes
- inter-command timing
- response wire encoding
- response packet sizes
- ACK placement
- serial settings and control lines

### 7. Implement in layers

Keep these layers separate in code and tests:

1. Serial lifecycle and flow control.
2. Command encoding.
3. Response framing and wire decoding.
4. Checksums and identity validation.
5. Memory map and field semantics.
6. User-facing editing and write policy.

Do not let confidence in layer 5 imply confidence in layers 1-4.

## Evidence levels

Use the lowest level that accurately describes the current evidence:

| Level | Evidence |
| --- | --- |
| E0 | Name/string or UI label only |
| E1 | Static call path with exact addresses and constants |
| E2 | Replayable synthetic transport derived from the static call path |
| E3 | Working OEM serial capture on physical hardware |
| E4 | Complete NewChirp read compared with OEM data |
| E5 | Controlled NewChirp write and read-back verified |

Do not label a driver hardware-validated until E4 for reads and E5 for writes.

## Definition of ready to implement

All of these should be true:

- The UI-to-serial and serial-to-decoder call paths are traced.
- Every operation has a protocol contract row.
- Response wire encoding is known.
- Returned-length and fragmentation behavior is known.
- Timeouts and control-line transitions are known.
- Synthetic replay tests can represent the OEM traffic.
- Unknowns are explicitly isolated and do not affect write safety.

If any transport item remains unknown, keep the driver read-only or avoid
implementing that operation.

## Definition of complete

- Offline tests cover full and partial frames, errors, and boundaries.
- `flutter analyze`, Flutter tests, and Python tests pass.
- `docs/DRIVER_STATUS.md` records evidence and read/write policy.
- A physical read succeeds without exceptions.
- Decoded channels and fields are compared with OEM output.
- A write is enabled only after a controlled edit and successful read-back.

## Case study: Retevis MA1-A9305B

The first A9305B implementation recovered the correct commands, checksums, and
memory map from the official CPS, but assumed read responses were binary and
always contained the requested payload length plus 13 frame bytes.

The CPS receive path showed a different rule:

- Read data is returned as uppercase ASCII hexadecimal text.
- `GetDataTxRxBytePro` derives a two-characters-per-byte length.
- `serialPort1_DataReceived` assembles the response using the serial threshold.
- `DisplayText` converts every received byte to hexadecimal text before
  checking the `FEFEEFEEE4` response prefix.
- `SaveReadDataPro` accepts shorter frames and advances by the returned payload.

A field read returned 214 bytes. The old driver interpreted that as a partial
253-byte binary frame. In the actual protocol it was complete:

```text
214 ASCII characters = 2 * (94-byte payload + 13 frame bytes)
```

The lesson is not "the CPS was wrong" or "the radio behaved differently."
The missing evidence was the receive-side conversion and dynamic length path.

A later 1.0.38 report showed a complete 494-byte response whose returned
checksum `F3` did not match the `A2` value derived from the CPS write-side
checksum algorithm. `DisplayText` discards the last two characters after
converting the response without checking that checksum. Recovering a checksum
algorithm from one direction is not evidence that the application validates it
in the other direction. The driver must preserve the CPS' actual read policy:
validate framing, address, returned length, payload, and terminator while
treating the returned checksum field as part of the frame that the OEM ignores.

A 2026-11-10 channel comparison exposed a second partial trace. The driver had
the correct channel byte for power, but interpreted bits 4-5 while the CPS used
bits 6-7. The same byte's bits 4-5 are the bandwidth field. `DisdataGridViewPro`
masks power with `0xC0` and shifts right by six; the CPS write path shifts the
selected power index left by six. A read/write field trace therefore has to
record the mask, shift, label table, and surrounding fields together. Zoran's
OEM CPS view and exported `.icf` now agree with the corrected decode for every
reported channel.

## Review questions

Before approving a reverse-engineered driver, answer:

1. Did we trace both directions of every operation?
2. Is the response encoding independently established from the command encoding?
3. Are response sizes fixed, requested, returned, or delimiter-based?
4. Can a valid response be shorter than requested?
5. Can a frame arrive in more than one serial callback?
6. What causes the OEM application to retry versus advance state?
7. Which conclusions are static-only, replayed, OEM-captured, or
   hardware-validated?
8. Are writes still disabled if any safety-relevant layer is uncertain?
