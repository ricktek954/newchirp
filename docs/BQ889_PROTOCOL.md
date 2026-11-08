# Binqi BQ-889 analog transport probe

Last updated: 2026-11-08

## Scope and safety

This is a read-only transport probe, not yet a channel driver. No BQ-889
analog write command has been recovered or tested. The selectable NewChirp
entry is:

- Vendor: `Binqi`
- Model: `BQ-889 Analog Probe`
- Driver: `drivers/newchirp_bq889_probe.py`
- Read policy: identify the USB/AT endpoint and capture firmware and analog
  read responses.
- Write policy: disabled.

## Hardware evidence

- FCC ID: `2BNNE-BQ-889`
- FCC-equivalent model: `AI-889`
- Manufacturer: Quanzhou Binqi Electronic Technology Co., Ltd.
- Main board marking: `BQ-889_MAIN_V2.3`
- Analog transceiver: Beken `BK4819`
- Manual: UHF 420–450 MHz, 12.5/25 kHz, 4 W, analog sub-tone, power, and
  bandwidth indicators

FCC artifacts:

| Artifact | SHA-256 |
| --- | --- |
| Internal photos | `5ee18814740d83ebbec22d917e88fe372ea5ab7b0d6628f133e3b6a1885d48e8` |
| User manual | `61c5f8f39494d535f03333ef8d74e414fadde496247d33f957db9218eea547be` |
| WWAN test report | `3e813ac2e58fabc81a6b1e0bfd8d093b859e536786f83983c2dae6882b11e5c1` |

## Related software evidence

KSUN publishes `POC写号通用工具V6.2_BLT`:

- Archive SHA-256:
  `9e2d4a316225e1e5837d535b53c7fa1d9a34c625af96723a222b22304fab5577`
- Retained copy:
  `/Users/rlopez/Downloads/KSUN_POC_Write_Tool_V6.2_BLT.zip`
- Runtime: .NET Windows application using `System.IO.Ports`
- Relevant UI: `Write the simulated frequency(used by the customer)`,
  `Read Simulation`, `Write Simulation`, and channel import/export
- Relevant fields: send/receive frequency, send/receive CTCSS, bandwidth,
  power, busy lock, frequency hopping, scrambling, and companding

Static strings identify the following candidate read commands:

| Action | Host text |
| --- | --- |
| Basic modem check | `AT` |
| Firmware | `AT*READVER` |
| Modem version | `AT+CGMR` |
| Analog settings | `AT+HSQ=R` |
| Analog band/settings | `AT+HXTO=R` |
| Analog channel data | `AT+HCHDATA=R` |

The application also contains write-side strings, including `AT+HSQ=` and
`AT+HCHDATA=`. Those commands are deliberately excluded from the NewChirp
probe.

## Evidence level

Current level: **E0**. The command and UI strings are static evidence from a
related POC utility. The UI-to-serial call path, response wire encoding,
response length rule, completion rule, checksums, retry policy, and BQ-889
compatibility have not been established.

## Probe behavior

The driver:

1. Tries `AT` at 115200, 9600, 38400, 57600, 19200, and 230400 baud.
2. If any baud responds, sends only the six read commands above.
3. Writes a bounded raw transcript to the system temporary directory.
4. Stops with a diagnostic message containing the baud rate, commands that
   returned data, and the transcript path.
5. Never opens an upload path, writes a codeplug, sends a bare `=`, or sends a
   SET/write command.

## Next milestone

Frank Lopez Sr. should select `Binqi BQ-889 Analog Probe`, use a USB-C data
cable, and run Download From Radio. The returned transcript must establish:

- whether a COM/tty endpoint exists;
- the working baud rate and control-line requirements;
- which read commands answer;
- the exact `AT+HCHDATA=R` framing and length rule;
- whether the channel records contain the expected frequency, tone,
  bandwidth, power, busy-lock, hopping, scrambling, and companding fields.

Only after those response rules are documented should an experimental
channel decoder be added. Physical write validation remains a separate later
milestone.
