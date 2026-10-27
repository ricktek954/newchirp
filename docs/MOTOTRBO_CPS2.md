# MOTOTRBO CPS 2.0 XML import

NewChirp's first MOTOTRBO R7 path is a read-only importer for conventional
channel XML copied or exported from Motorola CPS 2.0. It does not implement the
MOTOTRBO USB programming protocol and cannot upload to a radio.

## Why this starts with CPS2 XML

MOTOTRBO CPS 2.0 is distributed through Motorola Solutions' software
entitlement portal. A Motorola account with the software entitled to it is
required; the installer is not a public download. NewChirp therefore does not
redistribute or bundle the proprietary CPS or its binaries.

CPS2 exposes the selected Zone and its `ConventionalPersonality` entries as
XML when copied from the application. The public CPS2 field names and examples
were used as format evidence; no vendor installer or reverse-engineering code
is stored in this repository.

## Implemented

- Reads one or more CPS2 Zone XML sets from a saved `.xml` file.
- Imports each conventional channel in zone order with stable locations.
- Imports RX/TX frequency, simplex/offset/split or receive-only state, channel
  name, analog bandwidth, CTCSS/DCS modes, power, automatic-scan state, and
  CPS comments.
- Imports DMR channels with color code, timeslot, contact, RX group list, and
  privacy-key references as editable extra fields.
- Presents imported channels through NewChirp's normal Channel Library, where
  they can be inspected and exported as CHIRP CSV.

## Limitations

- No direct serial, USB, Bluetooth, or network communication with an R7.
- No upload or codeplug write-back.
- Zone membership is recorded in each channel comment; zones are flattened in
  the current Channel Library.
- Contacts and talkgroups are retained as references, not resolved into a full
  MOTOTRBO contacts/talkgroup database.
- CPS2 may vary fields by model and firmware. A redacted R7 export is required
  to validate model-specific fields before calling this support
  hardware-compatible.

## Test procedure

1. In CPS2, open the R7 codeplug.
2. Select a Zone containing conventional analog and digital channels.
3. Copy the Zone XML and save it as a `.xml` file.
4. In NewChirp, choose **Open file** and select the XML file.
5. Compare channel names, frequencies, tones, power, color codes, timeslots,
   contact references, RX group lists, and scan membership with CPS2.

Do not send the full codeplug publicly. Redact contacts, IDs, locations, and
credentials before sharing a sample for validation.
