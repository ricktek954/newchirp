# NewChirp driver status

This is the authoritative local ledger for radios whose support is maintained
by NewChirp rather than upstream CHIRP. Update it whenever a driver is added,
changes transport, gains or loses write support, or completes hardware testing.

Last updated: 2026-10-26

## Status definitions

| Status | Meaning |
| --- | --- |
| Experimental | Code exists and has offline tests, but no complete physical-radio validation |
| Hardware-tested | A complete operation was performed on the named model and the result was recorded |
| Released | The supporting NewChirp build has been published |
| Blocked | Work cannot continue without a specific external dependency |

## Driver inventory

| Radio | Driver | Transport | Read | Write | Settings | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Yaesu FTM-150R/E/ASP | `drivers/newchirp_ftm150.py` | CHIRP clone serial, 38400 8N1 | Yes | Yes | Hidden | Experimental |
| Radtel RT-950 | `drivers/newchirp_rt950.py` | CHIRP-compatible serial, 115200 8N1 + RTS/XON | Yes, designed | Disabled | Hidden | Experimental |
| Retevis RT97L | `drivers/newchirp_rt97l.py` | Stock USB serial, 9600 8N1 + DTR/RTS | Yes, hardware pending | Disabled | Hidden | Experimental |
| Kenwood TS-2000 | `drivers/newchirp_ts2000.py` | Kenwood live CAT serial, 9600 8N1 + RTS | Yes | Yes, longer write timeout | Standard | Hardware read verified; write retest pending |
| Connect Systems CS750 | `drivers/newchirp_cs750.py` | NewChirp raw SCSI/RAP; CPS `.rdb` import | Yes, untested hardware | Disabled | Hidden | Experimental |
| Baofeng GM-32 | `drivers/newchirp_gm32.py` | UV-32 clone serial, 115200 8N1 | Yes, CPS-derived | Yes, hardware pending | Yes | Experimental |

## Radio details

### Yaesu FTM-150R/E/ASP

- Maintained driver: `drivers/newchirp_ftm150.py`
- Device help: SCU-56 USB cable or CT-163 serial cable on the DATA jack
- Image model: `AH086`, based on the ADMS-17 v1.0.1 default image
- Transport: FTM-300DR family clone transport at 38400 8N1
- Implemented: channel read, channel write, standard channel fields
- Intentionally omitted: APRS, GPS, and digital settings
- Required validation: complete radio download, controlled channel edit and
  upload, then restore from a microSD ALL backup
- Current gap: no repository record yet confirms hardware validation of this
  NewChirp-maintained layout

### Radtel RT-950

- Maintained driver: `drivers/newchirp_rt950.py`
- Protocol notes: `docs/RT950_PROTOCOL.md`
- Evidence: official RT-950 CPS v1.3.0, native .NET metadata and CIL
- CPS artifact SHA-256:
  `605054c46ec17520b0f79b78585c3be431a6dcb95164dc638985455e813d7a1e`
- Transport: CHIRP serial path at 115200 8N1 with RTS/DTR and XON/XOFF
- Implemented: 960 channel records, frequencies, duplex, CTCSS/DCS, mode,
  power, scan-skip, GB2312 names, and documented channel extras
- Read strategy: 248 verified 128-byte blocks over CPS memory ranges through
  `0xC0FF`
- Read/write state: read implemented; every write entry point is disabled
- Hardware validation: a connected FTDI port opened but did not answer the
  RT-950 handshake, so no physical read has completed
- Next milestone: confirm the RT-950 is powered and in programming mode, then
  capture a complete successful read and export a test image

### Connect Systems CS750

- Maintained importer: `drivers/newchirp_cs750.py`
- Protocol notes: `docs/CS750_PROTOCOL.md`
- Evidence: official CSI CPS R4.01.010 / S8.00.10
- CPS installer SHA-256:
  `e55ee07f245baf41e35b1a867e50b8c1c7e49f11938c4c08716aefa5ff8a2639`
- Main executable SHA-256:
  `72b1b767f1ab4b90dff1d4ecfe9975710269e5d992a738a9e25923fde1c8d023`
- Transport: USB mass storage using vendor SCSI passthrough and RAP packets
- Device identity: SCSI vendor `STM     `, product `microSD Flash   `
- Implemented today: import of M100000/2000-channel CPS `.rdb` archives,
  ordered channel list, RX/TX frequencies, 6-bit channel names, and
  analog/DMR mode
- Read/write state: live read and CPS import are implemented; every write is
  disabled
- Missing decode: analog tones, DMR contacts/talkgroups, color code, time slot,
  scan lists, zones, and write verification
- Reusable transport: `scripts/newchirp_mass_storage.py` plus
  `tools/newchirp_scsi_mac.c`
- Transport adapters exist for macOS, Windows, and Linux behind one interface;
  only the macOS IOKit helper has been compiled on this host
- Next milestone: capture a `0x44010`-byte M100000 image from physical hardware
  and compare it byte-for-byte with a CPS export

### Retevis RT97L

- Maintained driver: `drivers/newchirp_rt97l.py`
- Protocol notes: `docs/RT97L_PROTOCOL.md`
- Evidence: public protocol analysis of the Windows RT97L programmer
- Public analysis tree:
  `378b6fb634edbd0b440c59fae201787b7473f599`
- Transport: stock USB serial cable at 9600 8N1 with DTR and RTS asserted
- Implemented: 256-byte live download and sixteen 16-byte channel records
- Decoded: RX/TX frequencies, CTCSS/DCS, power, scan status, and read-only
  per-channel squelch, channel mode, compand, scan-add, and channel-lock fields
- Read/write state: download implemented with synthetic serial tests; every
  write operation is disabled
- Remaining uncertainty: the channel byte map is provisional, global settings
  and password encoding are unknown, and no physical download has completed
- Next milestone: compare a complete physical image and official CPS export,
  then correct the channel flags and settings byte map

### Baofeng GM-32

- Maintained driver: `drivers/newchirp_gm32.py`
- Protocol notes: `docs/GM32_PROTOCOL.md`
- Evidence: official Baofeng BF-UVs Pro CPS v1.4.7 managed metadata and CIL
- CPS executable SHA-256:
  `9bd0a5eaa01d2cdda2ffe5b65d6cc7b7e71008f8fef99739794e5f02556ed06a`
- Transport: UV-32 clone serial at 115200 8N1
- Modem control: DTR and RTS asserted, matching the CPS; no flow control
- Implemented: shared UV-32 channel, VFO, DTMF, radio settings, and ten
  16-byte bank-name records
- CPS block map: `0x0000-0x803F`, `0x9000-0x903F`, `0xA000-0xA2BF`, and
  `0xD000-0xD03F`
- Read/write state: both implemented with exact CPS block ranges
- Cold-start symptom: an affected reporter stalls near the beginning of a
  download and then receives no response; the CPS asserts DTR/RTS while
  upstream UV-32 leaves them deasserted in NewChirp
- Hardware validation: pending; this profile must not be called
  hardware-tested until channel names, bank names, settings, and restore all
  pass a physical read-back
- Website catalog: listed as experimental in both the Baofeng section and
  New Experimental Radio Support
- Next milestone: have the reporter save an unedited image, perform a
  controlled name/bank/settings upload, and read the image back for comparison

### Kenwood TS-2000

- Maintainer: NewChirp override of the upstream CHIRP live CAT driver
- Maintained file: `drivers/newchirp_ts2000.py`
- Transport: Kenwood live CAT serial connection
- Evidence: CHIRP's `ts2000.py` driver and a field report from a TS-2000 owner
- Hardware verified: channel download succeeds
- Field issue: channel upload can exceed the shared Kenwood live driver's
  one-second command-response ceiling
- Change: NewChirp retains the upstream protocol implementation but allows up
  to five seconds for `MW`/`MC` write commands
- Write status: protocol-level tests pass; upload/read-back retest on physical
  hardware is required before calling the timeout fix hardware-verified
- Next milestone: TS-2000 owner retest with both a small loadset and the full
  258-channel loadset, followed by a read-back comparison

## Reusable NewChirp transport work

The CS750 is the first expected consumer of a transport layer that should not
be tied to CHIRP:

1. Enumerate removable mass-storage devices by SCSI vendor and product on
   macOS, Windows, and Linux.
2. Open raw block-device access without mounting or formatting.
3. Send 16-byte SCSI passthrough CDBs and transfer bounded buffers.
4. Build and validate generic RAP packets:
   `A1 | command:u16be | length:u16be | payload | checksum:u16be | A4`.
5. Apply a radio profile for command IDs, block size, image limits, and image
   parsing.
6. Support macOS, Windows, and Linux backends behind one interface.

The transport and RAP codec are offline-tested. A physical read is still
required before enabling writes.

## Documentation requirements for every new driver

Every NewChirp-maintained driver must record:

- Vendor, exact model, variants, and intended radio firmware
- Transport type, cable, serial settings, or USB identity
- Source of protocol evidence and proprietary artifact hashes
- Implemented channel and settings fields
- Read/write policy and every known unsupported field
- Hardware test result, including failure details
- Rollback or backup instructions before write support is enabled
- Website catalog status

Do not claim released or hardware-tested status from synthetic tests alone.
