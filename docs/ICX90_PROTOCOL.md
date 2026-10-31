# Icom IC-E90 completion-safe clone notes

The IC-E90 and IC-T90A use the legacy Icom clone transport and a fixed
`0x2D40`-byte memory image. This note records the completion behavior recovered
from the official CS-T90A programming software and a NewChirp field report.

## Evidence

- Official software: **Icom CS-T90A Cloning Software**
- Downloaded archive:
  `/Users/rlopez/Downloads/cs_t90a.zip`
- CPS ZIP SHA-256:
  `725c37e44a781b972af49fca6b48f9190b0cd2f757e42af05eb79a7992a90038`
- Main executable `CST90A.exe` SHA-256:
  `aae6ea1353a3b0f85379bf30eb66a69fc7814a5a370a555acee2579d64ff7adf`
- Help file `CS-T90A.HLP` SHA-256:
  `8e47186f685265f254d4fb60a0c7beb8d2b0c787fd7918d2f1484bf0d6903ae9`

The CPS identifies itself as software for **IC-T90A and IC-E90** and contains
the `||Icom Inc.` completion marker. REA/Ghidra recovered the native VB6
transfer routine and its completion/end-frame handling. The CPS executable and
archive remain external evidence and are not committed.

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

## Completion behavior

A NewChirp report captured a 39-byte model response followed by 28,261 bytes of
clone traffic. That byte count is consistent with the complete fixed image plus
ICF framing and is not a truncated channel table.

Some IC-E90 revisions finish sending the complete image without leaving the
generic ICF parser with a recognizable final end frame. The compatibility
override therefore accepts a download once:

1. every byte of the fixed `0x2D40` image has been received; and
2. the decoded data frames cover the image contiguously from address zero.

A normal `Icom Inc.` end frame remains accepted when present. Incomplete or
sparse images still fail. Upload behavior and the channel layout are unchanged.

## Validation limits

Offline tests cover full coverage without an end frame, the normal end-frame
path, truncated-image rejection, and registration as the active IC-E90 driver.
The public 500-channel reference image was also loaded successfully during
manual validation. Physical IC-E90 read/write validation remains required.
