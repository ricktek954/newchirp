# KSUN UV-K60 Plus / MH-580 protocol notes

Last updated: 2026-11-14

## Status

The KSUN UV-K60 Plus uses a separate `0x2A00`-byte image and must not use the
existing UV-K5 compatibility alias. A read-only driver is implemented in
`drivers/newchirp_uvk60plus.py`. No write support should be enabled from the
current evidence set.

The radio label supplied by the reporter identifies:

```text
Brand: KSUN
Type: X-TFSI V5: UV60dplus
Serial: 26UV60DPLUS00798
```

## Artifacts

- OEM CPS: `MH-580` version 0.2, dated 2025-10-24
- CPS ZIP SHA-256:
  `790507b60b875259a1a2ba665ca39f5be31793870722706494123ddd7e8b2ac9`
- Extracted `MH-580.exe` SHA-256:
  `b241af593ba2b327a0b155bd287813df37becaa275294bae5ca77b5c3a19e79f`
- Supplied OEM image SHA-256:
  `08ae6361a20c5cfa15612fbeeea6f6f5e8f62834e4165dc671e062e88af1ffbb`
- Supplied NewChirp CSV SHA-256:
  `6ed0874d22dc8a5fe020f687966dd56a05814025c9ce0f3fc9bb3d4ad70c807b`
- Supplied user module SHA-256:
  `1b7c8927b90843f4f6cd17bc9da5465a7cf74d350022195400b288dac266d6d0`

The user module was reviewed statically and was not executed.

## Serial session

Static tracing of `MH-580.exe` established:

- Serial settings: 38,400 baud, 8 data bits, no parity, one stop bit.
- Entry magic: `50 7B 4F 4A 49 7D 45` (`P{OJI}E`).
- Entry acknowledgment: `06`.
- Identity request: `02`.
- Identity response: eight bytes beginning `50 33 31 31` (`P311`).
- Identity acknowledgment: `06`, followed by an optional `06` response.
- Read request: `52 <address:u16be> 20` (`R` plus 32-byte length).
- Read response processing stage: 37 bytes.
- Read frame from the supplied working module:
  `57 <address:u16be> 20 <32-byte payload> <payload checksum>`.
- End request: `45` (`E`), followed by the OEM's 1,000 ms delay.

The OEM reader starts at address `0x0000`, advances in 32-byte pages, skips
the unused range at `0x1F40`, resumes at `0x2000`, and stops after `0x2A00`.

The supplied module treats the final byte as the unsigned sum of the 32
payload bytes modulo 256. The static receive path confirms the 37-byte
completion threshold but does not yet prove whether the OEM accepts or rejects
a bad checksum, so this rule remains independently replayable evidence rather
than a complete checksum policy.

The first page request is:

```text
52 00 00 20
```

## Image layout

- Complete image size: `0x2A00`.
- Exposed ranges: `0x0000-0x1F40` and `0x2000-0x2A00`.
- Channel records start at `0x0010`.
- Channel record size: 16 bytes.
- Channel count: 128.
- A record begins with RX and TX frequencies encoded as eight decimal digits
  in byte-reversed BCD. Each least-significant decimal digit represents 10 Hz.
- Record bytes `8:10` and `10:12` contain RX and TX CTCSS values as
  byte-reversed BCD in tenths of a hertz; `FF FF` means no tone.
- A TX frequency of `FF FF FF FF` means receive-only.
- A plausible name table begins at `0x2000`, with 16-byte records. The first
  four bytes are a fixed header in the supplied image and the remaining twelve
  bytes hold a space-padded name.

## Evidence conflict

The supplied OEM image contains only 17 valid channel records, at locations
1-17. Their RX frequencies, TX frequencies, offsets, and tones match rows 1-17
of the supplied CSV exactly.

Rows 18-97 from the CSV have no corresponding frequency encodings anywhere in
the supplied OEM image. Therefore the OEM image and the 97-channel CSV do not
represent the same radio state. They cannot safely be used together as a
before/after memory-map oracle.

The supplied user module decodes channel records correctly for locations 1-17,
but its name address (`0xD40 + (channel - 1) * 8`) is zero-filled in the OEM
image and does not match the apparent `0x2000` name table. That module should
not be merged as-is.

The replacement driver uses the independently recovered `0x0010` channel
base and `0x2000` 16-byte name table. It preserves all OEM bytes and exposes
only channel frequency, TX direction/offset, CTCSS, and name fields.

## Channel maps (2026-11-22)

The first same-state pair arrived on 2026-11-21: a NewChirp read
(`KSUN_UV-K60-Plus.img`, SHA-256
`197dd91a1d1893f593590b48376975460a1aa6abf5e8caf8681fd79bc7dcb8ea`) and the
owner's MH-580 file of the same radio (`MH-580-UVK60PLUS-21_11_26.txt`, a
raw `0x2A00` image despite the extension, SHA-256
`0f99b996e3f5221a533f3b2ba6ba89bfe902b87e2a67e9a3dbe67b65a1352fa1`). They
are byte-identical except:

- `0x0540-0x061F`, channel records 84-97: valid-looking factory records
  (145.500 ... 435.700 MHz, GBK name 号机) in the radio read, `FF` in the
  MH-580 file. MH-580 shows 83 channels; NewChirp showed 97.
- `0x1F40-0x1FFF`: the gap neither reader requests (`FF` vs `00` fill).

Both `0x1A00` and `0x1A20` hold a 128-bit map (bit n-1 = channel n, LSB
first): `FF x10 07`, i.e. channels 1-83. The earlier OEM dump's maps mark
exactly its 17 channels. Records whose bits are clear are deleted channels.
The two maps are identical in both samples, so which is "in use" and which
may be the scan list is unproven; NewChirp shows a channel when either map
marks it (correct under either reading, provided the scan list is a subset
of the channels in use). Channel 38 (135.458 MHz RX, 50.000 MHz TX) is the
same in both files, so it is radio content, not a decode error.

## Next evidence required

1. Save the fresh NewChirp image produced from this exact radio before changing
   channels. The CSV alone is insufficient.
2. Save the OEM CPS data after successfully reading the same radio, without
   editing it.
3. Confirm that both captures contain the same active channel count.
4. Compare channel names, tones, duplex directions, and option bytes.
5. Perform a fake-transport replay of every read page and checksum boundary.

Writes remain disabled until a controlled single-channel write and read-back
can be compared with the OEM CPS.

## Verification

- E1: static `MH-580.exe` call-path analysis recovered the entry, identity,
  page-read, address progression, termination, and `0x2A00` bounds.
- E2: synthetic replay covers fragmented 37-byte replies, sparse address
  progression, BCD frequencies and tones, names, and bad checksums.
- The supplied OEM image decodes to 17 active records with RX/TX values and
  tones matching CSV rows 1-17.
- E4: one same-state NewChirp read and MH-580 file (2026-11-21) agree on
  every byte both read, apart from MH-580 blanking unmapped records 84-97.
- E5: writes are disabled.
