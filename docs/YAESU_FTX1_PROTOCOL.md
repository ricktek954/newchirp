# Yaesu FTX-1 CAT memory notes

Last updated: 2026-11-01

## Status

Experimental live CAT memory support is implemented in
`drivers/newchirp_yaesu_ftx1.py`.

No physical FTX-1 has yet been used to validate a complete memory read,
controlled edit, write, and radio-display comparison.

## Evidence

- Yaesu FTX-1 CAT reference supplied by the public `cat-ftx1` project
  (`e77b599dbb27eff5b4bd49c01a689989cfcc9495`)
- Public `cat-ftx1` implementation of the FTX-1 CAT transport and live
  radio-information behavior
- Yaesu commands `ID`, `MR`, `MT`, `MW`, `MC`, `CT`, and `CN`

## Transport

The radio uses ASCII CAT commands terminated by `;`. The driver probes
115200, 38400, 19200, 9600, and 4800 baud and requires identification answer
`ID0840;`.

Auto Information is disabled with `AI0;` while NewChirp is operating.

## Memory records

Read request:

```text
MRnnnnn;
```

Memory answer fields:

- five-digit memory number
- nine-digit frequency in Hz
- clarifier direction and four-digit offset
- RX and TX clarifier flags
- operating mode
- VFO/memory/QMB selector
- tone mode
- two reserved digits
- simplex/plus/minus shift

Write request:

```text
MWnnnnnFREQUENCY+CLARIFIERRXCLARTXCLARMODEMEMORYTONERESERVEDSHIFT;
```

Memory names use:

```text
MTnnnnnNAME;
```

The driver supports names up to 12 ASCII characters.

## Tones

`MC` temporarily selects the requested main-channel memory. `CT` reports the
CTCSS/DCS mode and `CN` reports the tone number. The previously active channel
is restored after reading or writing the tone.

Yaesu's documented 50-entry CTCSS table and 104-entry DCS table are included
in the driver.

## Implemented fields

- frequency
- memory name
- FM, NFM, AM, USB, LSB, and CW modes
- standard band-dependent repeater shift
- CTCSS encode-only, CTCSS encode/decode, and DCS

The radio does not expose an arbitrary split through the basic `MR`/`MW`
record, so nonstandard repeater splits are not represented. Optional
signalling, scope settings, and radio-wide menu settings are not edited.

## Remaining validation

1. Confirm the true empty-memory `MR` response on hardware.
2. Confirm that `MW` with a zero frequency removes or blanks a memory without
   affecting adjacent records.
3. Compare CTCSS/DCS selection and standard repeater shifts against the radio
   display.
4. Make one controlled memory edit, write it, read it back, and verify it on
   the radio before declaring hardware-tested support.
