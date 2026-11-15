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

## Australian UHF CB

- Australian Communications and Media Authority CB radio class licence
- 80 channels from 476.4250 to 477.4125 MHz with 12.5 kHz spacing
- Emergency, calling, and telemetry/data channel restrictions must be checked
  against the current ACMA class licence

## Generated assets

`scripts/generate_international_frequency_pdfs.py` creates:

- `assets/Marine_VHF_Frequency_Reference.pdf`
- `assets/CB_27MHz_Frequency_Reference.pdf`
- `assets/Australia_UHF_CB_Frequency_Reference.pdf`

The desktop frequency-reference page and its Print action use the matching
asset for the selected reference plan.
