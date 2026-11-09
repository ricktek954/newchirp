# Marine VHF frequency templates

NewChirp provides built-in marine VHF templates without relying on CHIRP's
marine stock CSV files. The template is selected by regulatory plan rather
than postal code: marine VHF channel assignments are national or international
and do not change by ZIP code.

## Supported plans

### United States

The US plan is based on:

- [47 CFR 80.371(c)](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-80/subpart-E/section-80.371),
  the VHF public correspondence ship/coast frequency pairs.
- [47 CFR 80.373(f)](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-D/part-80/subpart-E/section-80.373),
  the VHF channels for port operations, commercial,
  non-commercial, navigation, distress, environmental, maritime-control, and
  Coast Guard use.
- [NOAA Weather Radio](https://www.weather.gov/nwr/) channels WX1 through WX7.

The US template contains 56 channels. Public-correspondence pairs use the
coast transmit frequency as the receive frequency and the ship transmit
frequency as the radio's transmit frequency. US simplex channels use the
published "A" designator where applicable. Coast Guard-only, US
Government-only, DSC, AIS, and weather rows are receive-only.

### International

The International plan follows the systematic ITU Radio Regulations
[Appendix 18](https://www.itu.int/pub/R-REG-RR) channel layout and includes
channels 1 through 28 and 60 through 88, plus AIS receive channels. National
administrations may change permitted use, channel availability, and power
limits, so this plan is a starting point rather than a country-specific legal
authorization.

## Safety policy

Receive-only is the default for both plans because most amateur transceivers
are not type-accepted for marine-band transmit. The user must explicitly
enable ship transmit. Channels that are receive-only or prohibited for voice
remain transmit-disabled even when that option is enabled.

The template does not claim that a radio, antenna installation, or operator is
authorized for marine VHF transmission. Users must comply with the applicable
national licensing, equipment, channel-use, and power rules.

## Data invariants

Automated tests enforce these invariants:

- All identifiers fit an eight-character radio name field.
- Names are unique within each plan.
- Receive frequencies stay within 156.000-162.550 MHz.
- Ship transmit frequencies stay within 156.025-157.425 MHz.
- US channel 24 receives on 161.800 MHz and transmits on 157.200 MHz.
- DSC, AIS, and weather rows cannot transmit.
- The template is receive-only unless the user explicitly enables ship
  transmit.
