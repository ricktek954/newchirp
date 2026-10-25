# NewChirp driver status

This is the authoritative local ledger for radios whose support is maintained
by NewChirp rather than upstream CHIRP. Update it whenever a driver is added,
changes transport, gains or loses write support, or completes hardware testing.

Last updated: 2026-10-25

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
| Connect Systems CS750 | `drivers/newchirp_cs750.py` | NewChirp raw SCSI/RAP; CPS `.rdb` import | Yes, untested hardware | Disabled | Hidden | Experimental |
| Midland MXT295 | `drivers/newchirp_mxt295.py` | CHIRP clone serial, 115200 8N1 | Yes, designed | Yes, hardware-tested | Radio & Modes | Hardware-tested |

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

### Midland MXT295

- Maintained driver: `drivers/newchirp_mxt295.py`
- Device help: MXPG15 USB-A to USB-C cable (CH340) on the radio base. Bluetooth mic off. 12 volt power.
- Image identity: `SMP558`
- Transport: clone serial at 115200 8N1. 107 channel slots of 32 bytes from `0x0000`, then one 32-byte block at `0xE000`. The gap is never written.
- Evidence: Randy's 2026-10-24 MXPG15 read and write, plus MXT Pro V1.0 (the programming program's Radio & Modes list)
- Read capture SHA-256: `3c17101b1e7c538daac06ed845480bcab399cd53aeb7ae422a3cc876537b0a77`
- Write capture SHA-256: `9d09bbd9e5b0a9a0ecdc9aa3dcdb3978dc13efefeda6c466b8cc14e4313b447f`
- MXT Pro setup SHA-256: `4e3abc15f9339875efa842973b9291797186624754e9bb389e7fb046118419b1`
- MXT Pro program SHA-256: `569602016f3857da1acfbab8ecfed2a1b86bd26819b0b74314b7e08c2b611a3d`
- Implemented: channel read and write, Midland channel numbers, and the Radio & Modes settings (VOX, Roger Beep, Call Tone, Backlight, Backlight Color, Repeater, Dual Watch Pro Channel, SQ Level, Key Beep, Mic Gain)
- GMRS limits: channels 1 through 22 stay on their FCC frequencies. The channel editor picks a receive channel from the 22 GMRS channels. Picking one starts simplex with offset 0. Choosing duplex + sets the offset to 5 MHz. Channels 1 through 7 stay simplex. Channels 8 through 14 stay receive only (duplex off). Channels 23 through 99 pick one of those 22 receive channels.
- Settings live in the first 10 bytes at `0xE000`. The other 22 bytes in that block are kept as read.
- Mic Gain is stored with the other settings. The Midland guide says it is only used by the MXT115P.
- Read/write state: a full image upload is implemented. NewChirp has written this radio several times, and those writes worked. Settings edits stay in the saved image until someone uses Write settings, which sends the whole image.
- Hardware validation: several NewChirp uploads to this MXT295 succeeded. The byte map was first checked against the captured read.
- Read warning: the Midland driver is experimental, download and check channels before an upload, and keep a backup of your radio from the Midland program. Steps: 12 volt power, Bluetooth mic off, MXPG15 on the radio base.
- Write warning: the Midland driver is experimental. Make a backup before using it to change the radio.
- Next milestone: none for a first write. That write has already succeeded more than once. The app still warns that the driver is experimental.
- Website catalog: not listed

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
