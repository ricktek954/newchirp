# KPG-23D / KPG-32D evidence (2026-11-26)

Files saved by the OEM programmers running in QEMU, with known values
typed in, and a byte log of a KPG-32D write against
`tools/rea/simulators/` (the predecessor of `kpg32d_radio.py`). See
`docs/KPG23_PROTOCOL.md`.

| File | What it is |
| --- | --- |
| `sample.u1f` | KPG-23D, TK-350 160ch 450-470 MHz; RX 460.0125 / 462.5625; default test frequencies at 0x0B00 |
| `sample.u4f` | KPG-23D, TK-350 160ch 400-430 MHz; default test frequencies |
| `uhf359.fdt` | KPG-32D, TK-359 450-470 MHz; 460.0125/465.000 and 455.500 simplex |
| `kpg32d_write_uhf359_2026-11-26.log` | KPG-32D "Write to radio" of `uhf359.fdt`: 10 `Z` fill frames, 13 `X` frames each followed by the `03` commit, `E`; result byte-identical |

The KPG-23D write log was overwritten during a follow-up NAK test; its
results (26 blocks, 0xFC00-0xFCFF skipped, byte-identical) are recorded in
`docs/KPG23_PROTOCOL.md` and the driver ledger, and the run can be repeated
with `kpg23d_radio.py sample.u1f`.
