# Kenwood KPG-56D / TK-270G protocol notes

Last updated: 2026-11-07

This document records the evidence recovered for the Kenwood TK-260G/270G/
272G/278G family and the safety findings affecting the NewChirp TK-270G
compatibility driver. It is an offline analysis, not a claim of physical-radio
validation.

## Artifact inventory

- OEM application: KPG-56D version 4.22
- Public package source:
  `https://www.qsl.net/yo4hfu/Files/KENWOOD_PROG/KPG-56D/KPG-56D%20v4.22.zip`
- Package SHA-256:
  `7168c25603ab592cb5f3061ac56f71f80c6a83dccede4fbd54165bda5ea023e4`
- Installer SHA-256:
  `ab9e0291a763efc32e84e7117f9a0fbc99b681c96df0bb27a66433a726667e5c`
- Main executable SHA-256:
  `51530de3587c72c7cd4a7d6808b7a202614affbcc63a9f66917b90b61d380b28`
- InstallShield header SHA-256:
  `ab902be9667d999c22044e69682d0347588dc6a9b9d9b1e83b59987f07a7d424`
- English help SHA-256:
  `2f2b57327778f4a71a4abf6271d397a59ce23cc2ec883e6cbd01c5af27226cca`
- Analysis tools: Ghidra 12.1.4, OpenJDK 25

The executable identifies the supported models
`TK-260G/270G/272G/278G` and contains separate `TK-270G[128CH]` identity
strings for the K, M, E, and NE/NT variants. The help text states that these
128-channel models support up to 128 channels divided among 128 groups
(`1 group with 128 channels` through `128 groups with 1 channel`).

## Serial configuration

Recovered static evidence:

- KPG-56D opens `\\.\COM<n>` through `CreateFileA`.
- Its configured mode string is `9600,N,8,2`.
- It sets binary mode, disables parity checking, applies communication
  timeouts, purges stale output before writes, and uses exact-count reads.
- The programming-mode opener tries 9600, 19200, 4800, 2400, and 1200 baud.

The pinned CHIRP transport currently uses 9600 baud with even parity and one
stop bit. That difference remains unresolved in this analysis because changing
the live serial configuration without an OEM capture or physical read/write
test would risk breaking transports that currently exchange data successfully.

## Protocol contract

Addresses are 16-bit and are transmitted most-significant byte first. The
programming data block used by this driver is 256 bytes. The 8-bit checksum is
the modulo-256 sum of the data payload.

| Operation | Host bytes | Response and completion | Retry / flow control | Evidence |
| --- | --- | --- | --- | --- |
| Enter programming mode | ASCII `PROGRAM` | One-byte response; `06` means accepted | Try 500 ms first, then 100 ms. On later attempts a `16` response is followed by a second 500 ms wait for `06`. Up to five attempts. | KPG56D.exe `0x0044f0c0` and string `0x004d9818`; E1 |
| Query identity | `02` | Eight identity bytes | Send `06`; then require one-byte `06` acknowledgement | KPG56D.exe `0x0044f340`; E1 |
| Read programming block | `52` (`R`), address high, address low | `57` (`W`) + 256 payload bytes + 1 checksum byte. A non-`W` response supplies one byte used to fill the whole block. | Validate the payload checksum. On mismatch send `15`, consume its response, and retry. On success send `06` and require `06`. Up to three attempts. | KPG56D.exe `0x0044f510`; E1 |
| Write non-uniform block | `57` (`W`), address high, address low, 256 payload bytes, checksum | One-byte response; `06` means accepted and `15` means checksum failure | Purge output first. Up to three attempts. | KPG56D.exe `0x0044f6f0`; E1 |
| Write uniform block | `5a` (`Z`), address high, address low, fill byte | One-byte response; `06` means accepted | KPG-56D uses `Z` whenever every byte in the block is identical, not only when the fill byte is `FF`. Up to three attempts. | KPG56D.exe `0x0044f6f0`; E1 |
| Leave programming mode | `45` (`E`) | One-byte `06` acknowledgement | Consume the response before closing | KPG56D.exe `0x0044f4d0`; E1 |

The pinned CHIRP driver already matches the `PROGRAM`, identity, `R`, `W`,
`Z`, checksum, acknowledgement, and 256-byte transfer rules. Its `Z` use is
more conservative than the CPS because it only encodes all-`FF` blocks as
empty. Its close sequence sends `E` without consuming the KPG-56D
acknowledgement.

## TK-270G bank-write defect

The pinned CHIRP `tk760g.py` implementation contains:

```python
for setting in mem.extra:
    if setting != "bank" or setting != "bnumb":
        setattr(_mem, setting.get_name(), not bool(setting.value))
```

That condition is always true. It processes `bank` and `bnumb` as inverted
booleans along with the intentionally inverted hardware flags. For a normal
channel in bank 1, this changes `bank` to zero. `_prep_data()` then excludes
the channel because bank zero is treated as invalid.

The NewChirp bridge calls `set_memory()` once for every active channel during
upload. Each call clears the current channel's bank assignment. After the
last channel is written, the generated channel count can be zero even though
the channel records still contain frequencies and names. That explains the
reported radio that appeared blank and had to be restored with KPG-56D.

The NewChirp driver now:

- Registers `NewChirpTK270G` as `Kenwood_TK-270G`, superseding CHIRP's class.
- Owns channel decode and write instead of monkeypatching CHIRP methods.
- Preserves raw image bytes during channel decode.
- Writes decoded `bank` and `bnumb` values directly.
- Removes `bank` and `bnumb` from the upstream extra-setting loop so those
  fields are not converted to booleans.
- Leaves the existing inverted boolean handling for beat shift, compander,
  and busy-channel lockout unchanged.
- Verifies generated channel and bank counts after every channel write, and
  stops before radio I/O if the bank table is inconsistent.

The regression fixture contains 36 active channels across four bank numbers.
A complete decode/write round trip verifies that every active channel retains
its original bank and bank index and that the generated counts remain nonzero.

## Evidence level and remaining work

- Artifact identity: E1.
- Base transport and block protocol: E1.
- Bank corruption cause: E1 plus an offline round trip reproducing the
  bridge's per-channel write sequence.
- OEM serial capture: not available.
- Physical read comparison: not available on this development host.
- Controlled physical write/read-back: not performed.

The next milestone is a controlled TK-270G test using the same saved image:
read with KPG-56D, read with NewChirp and compare all 32 KiB, write an unchanged
NewChirp image, read back with both applications, and verify the same channel
and group counts before enabling a release claim.
