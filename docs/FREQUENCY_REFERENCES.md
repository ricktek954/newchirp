# Frequency Reference Sources

The in-app reference is informational. National regulators can restrict
channels, modes, power, licensing, and transmit access even when a radio can
store a frequency.

## United States FRS / GMRS

- FCC 47 CFR Part 95 Subpart B (FRS) and Subpart E (GMRS)
- Existing `assets/GMRS_FRS_Frequency_Chart.pdf`
- Shared 462/467 MHz interstitial and main/repeater channel plan

## International Marine VHF

- ITU Radio Regulations Appendix 18
- Ship-transmit frequencies for the international marine channel plan,
  including simplex, duplex, DSC, distress, and calling channels
- Local administration restrictions still apply

## 27 MHz CB

- FCC 47 CFR Part 95 Subpart D
- Innovation, Science and Economic Development Canada RSS-210
- ACMA Citizens Band Radio Service class licence
- Ofcom UK CB radio rules
- Includes the common 40-channel AM/SSB plan and the UK 27/81 FM band
- Australian calling notes: 27.155 MHz LSB local calling and 27.355 MHz LSB
  DX calling

## Australian UHF CB

- Australian Communications and Media Authority CB radio class licence
- 80 channels in two interleaved 25 kHz grids offset by 12.5 kHz
- Repeater outputs on channels 1-8 and 41-48; paired inputs on channels
  31-38 and 71-78, 750 kHz higher
- Emergency, calling, telemetry/data, road/truck, and guard-channel
  restrictions must be checked against the current ACMA class licence

## PMR446 (Europe)

- CEPT ECC Decision (15)05 (446.0-446.2 MHz, channels 9-16 added from 2018)
- 16 analogue FM channels, 12.5 kHz spacing, 446.00625-446.19375 MHz
- Licence-free only on PMR446-approved radios with a fixed antenna and at
  most 500 mW ERP; no repeaters. Digital dPMR446/DMR446 channel plans are
  not listed.

## Generated assets

`scripts/generate_international_frequency_pdfs.py` creates:

- `assets/Marine_VHF_Frequency_Reference.pdf`
- `assets/CB_27MHz_Frequency_Reference.pdf`
- `assets/Australia_UHF_CB_Frequency_Reference.pdf`
- `assets/PMR446_Frequency_Reference.pdf`

The desktop frequency-reference page and its Print action use the matching
asset for the selected reference plan.
