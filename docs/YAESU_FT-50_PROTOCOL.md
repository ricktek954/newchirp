# Yaesu FT-50 ADMS-1E transport notes

Last updated: 2026-11-16

## Scope and evidence level

This note records the first native reverse-engineering pass over the Yaesu
FT-50 Windows programmer. The current evidence is E1: a static call path from
the ADMS-1E UI/state machine to the Win16 serial APIs. No OEM capture or
controlled physical write/read-back is claimed.

Yaesu's official legacy FT-50R product page identifies the programming
accessory as `ADMS-1E`, "Windows Programming Cable and Software". Yaesu no
longer provides the software installer from that page. An archived three-part
package was obtained from eServiceInfo and was not executed.

## Artifact inventory

| Artifact | SHA-256 |
| --- | --- |
| `Yeasu_ADMS-1E_Software.part1.rar` | `767f1a1e84914faca36e1df3e71d9adde49fb01b5026d4a8afc9d3cb5e24d085` |
| `Yeasu_ADMS-1E_Software.part2.rar` | `ccaf4b7731a854266ee747710e1714fffc4bc6fedb623ea0b4faf069964f8af0` |
| `Yeasu_ADMS-1E_Software.part3.rar` | `6b7cf1eb5c1ecad2c16e953b42d099f6b9eb83a9186c4295eecf222d7c91548b` |
| `ADMS-1E.nrg` | `7298bf7c640799eabe9f7dc4bd955d94235493262b68fdfc66155392fa6a12c2` |
| ISO `setup.exe` | `b7e2584dfadf9c3dfb7603548607b669eaea179bdff980eeb63885cb3296e4f5` |
| `PROGRAMDIR/Wft50.exe` | `06f0be506b59153059d130e4fb5948049f0a40dd44f6df051097b9272f17945b` |
| `PROGRAMDIR/Wft50.hlp` | `9f432d0fe6ff8bc5663620ef21b9554e2d98ac9e734daaa664f91a999529de81` |

The outer archive also contains a third-party `VX-5 Patch.exe`. It is not part
of the FT-50 application and was not executed or used as evidence.

## Serial lifecycle

ADMS-1E's `Wft50.exe` is a 16-bit Windows New Executable. The relevant
functions and imports are:

| Address | Observation |
| --- | --- |
| `1040:0a0d` | Opens the selected COM port, reads its DCB, builds a DCB from a string, and calls `SetCommState` |
| `1060:2c01` | Literal serial setting `9600,n,8,2` |
| `1030:0686` | Calls `ReadComm` |
| `1030:06b1` | Calls `WriteComm` for one byte at a time |
| `1030:05ca` | Waits using `timeGetTime`; the byte writer requests a 3 ms delay |
| `1030:0718` | Adds selected bytes and returns the low eight bits |
| `1030:0766` | Read-dialog state-machine dispatcher |
| `1030:123b` | Write-dialog state-machine dispatcher |

The serial framing is therefore **9,600 baud, no parity, 8 data bits, 2 stop
bits**. The pinned CHIRP FT-50 driver declares only `BAUD_RATE = 9600`; its
headless host previously opened the port with pyserial's default of one stop
bit.

## Transfer observations

- The read state machine requests 10, 16, 112, 16, 16, 1776, 1776, and 1-byte
  segments, matching the pinned CHIRP `_block_lengths`.
- The OEM write helper sends one byte per `WriteComm` call and leaves 3 ms
  between bytes.
- The current NewChirp bridge uses the stock CHIRP channel layout, checksum,
  block ordering, and upload path. This pass did not establish a different
  memory map.
- The OEM state machine contains explicit receive-timeout, checksum, bad-data,
  and negative-acknowledgement branches. Exact ACK/NACK placement and retry
  transitions still need replay and OEM-capture verification.

## Integration decision

NewChirp now honors a driver-level `SERIAL_STOPBITS` override and sets it to
`2` for `Yaesu_FT-50`. This corrects the directly observed OEM serial framing
without changing CHIRP's channel encoder or upload sequencing.

## Remaining validation

1. Capture an ADMS-1E read from a physical FT-50R at the wire level.
2. Compare each response length, ACK/NACK byte, checksum, and retry transition
   with the static state machine.
3. Confirm a NewChirp read backs up the full codeplug and matches the OEM
   export.
4. Perform one controlled unused-channel write, power-cycle, read back, and
   verify the change persisted.

Until step 4 succeeds, FT-50 write support remains experimental.
