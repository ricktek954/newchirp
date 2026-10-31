# NewChirp driver status

This is the authoritative local ledger for radios whose support is maintained
by NewChirp rather than upstream CHIRP. Update it whenever a driver is added,
changes transport, gains or loses write support, or completes hardware testing.

Last updated: 2026-10-31

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
| Yaesu FT-1D/2D/3D/5D clone family | `drivers/newchirp_yaesu_clone.py` | CHIRP Yaesu clone serial, 38400 8N1 | Completion-safe timeout | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Radtel RT-950 | `drivers/newchirp_rt950.py` | CHIRP-compatible serial, 115200 8N1 + RTS/XON | Yes, designed | Disabled | Hidden | Experimental |
| Retevis RT97L | `drivers/newchirp_rt97l.py` | Stock USB serial, 9600 8N1 + DTR/RTS | Yes, hardware pending | Disabled | Hidden | Experimental |
| Kenwood TS-2000 | `drivers/newchirp_ts2000.py` | Kenwood live CAT serial, 9600 8N1 + RTS | Yes | Yes, longer write timeout | Standard | Hardware read verified; write retest pending |
| Kenwood TH-D75 | `drivers/newchirp_thd75.py` | Kenwood clone CAT serial, 9600-57,600 baud | Yes, echo-tolerant | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Quansheng UV-K5 family | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | Yes, firmware-ID retry | Stock CHIRP policy | Stock CHIRP policy | Experimental |
| Connect Systems CS750 | `drivers/newchirp_cs750.py` | NewChirp raw SCSI/RAP; CPS `.rdb` import | Yes, untested hardware | Disabled | Hidden | Experimental |
| Baofeng GM-32 | `drivers/newchirp_gm32.py` | UV-32 clone serial, 115200 8N1 | Yes | Yes | Yes, including bank names | Experimental |
| Baofeng DM-32UV | `drivers/newchirp_dm32uv.py` | CHIRP DM-32UV serial protocol, 115200 8N1 + DTR/RTS | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Baofeng UV-9R | `drivers/newchirp_uv9r.py` | CHIRP WP970I clone serial, 9600 8N1 | Stock CHIRP driver | Retry for missing write ACK | Stock CHIRP driver | Experimental |
| TIDRADIO TD-H3 family | `drivers/newchirp_tdh3.py` | CHIRP TD-H3 clone serial, 38400 8N1 | Invalid brightness normalized | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Radioddity DB35-G | `drivers/newchirp_db35g.py` | OEM clone serial, 115200 8N1 | 80 channels + settings | Disabled pending hardware validation | Basic radio settings | Experimental |
| Midland MXT295 | `drivers/newchirp_mxt295.py` | CHIRP clone serial, 115200 8N1 | Yes, designed | Yes, hardware-tested | Radio & Modes | Hardware-tested |
| Wouxun KG-UVD1P / KG-UV2D | Pinned CHIRP `wouxun.py` with NewChirp bridge timing | CHIRP clone serial, 9600 8N1 | One-second block timeout | Stock CHIRP driver | Stock CHIRP driver | Experimental timing override |
| Icom IC-9700 | `drivers/newchirp_icom9700.py` | Icom CI-V serial, auto-baud from 4800 to 115200 | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Icom IC-E90 / IC-T90A | `drivers/newchirp_icx90.py` | Legacy Icom clone serial, 9600 8N1 | Completion-safe full image | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Icom ID-50 | `drivers/newchirp_icom_id50_id52.py` | Icom `IcomCloneFormat3` serial, 9600 8N1 | Yes, hardware pending | Yes, experimental | Provisional ID-4100-family map | Experimental |
| Icom ID-52 | `drivers/newchirp_icom_id50_id52.py` | Icom `IcomCloneFormat3` serial, 9600 8N1 | Yes, hardware pending | Yes, experimental | Provisional ID-4100-family map | Experimental |
| Icom IC-41S | `drivers/newchirp_ic41s.py` | Legacy Icom clone serial, 9600 8N1 | Yes, hardware pending | Yes, experimental | Hidden | Experimental |
| Motorola MOTOTRBO R7 | `lib/services/mototrbo_cps2_xml.dart` | CPS 2.0 Zone XML import | Conventional channels | Disabled | Import-only extras | Experimental |

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

### Yaesu FT-1D/2D/3D/5D clone-read timing

- Maintained file: `drivers/newchirp_yaesu_clone.py`
- Scope: the shared upstream CHIRP Yaesu clone reader used by the FT-1D,
  FT-2D, FT-3D, and FT-5D families
- Transport: 38400 8N1 clone serial with the radio in CLONE mode
- Implemented: completion-first receive handling and a five-second idle limit
- Read/write policy: read timeout ordering only. Channel image layout, write
  behavior, and radio-specific fields are unchanged.
- Evidence: upstream CHIRP `yaesu_clone.py` and the 2026-10-29 NewChirp 1.0.23
  report from ka4hot@outlook.com. The FT5D completed its Send operation after
  a 3.2-second final chunk, but the upstream reader checked its two-second
  timeout before recognizing that the requested byte count was complete.
- Driver SHA-256:
  `0f144ce74ee905c6091a1c396fb249927b9998aa83e4febf3e401056f88a438d`
- Hardware validation: none for this timing override.
- Next milestone: FT5D owner retests a complete read with the cable on the
  same COM port throughout; if it still times out, capture the progress
  percentage and final read image size.

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
- Diagnostics: a 2026-10-31 macOS report received the expected one-byte ACK,
  16-byte `F` reply, and 12-byte `M` reply on the first handshake attempt,
  then the driver retried and replaced the deterministic model mismatch with
  a later no-response error. The driver now retries only genuine
  `RadioNoResponse` failures, so a model mismatch reports the actual received
  model code immediately.
- Next milestone: confirm the reported RT-950 model code, classify any
  variant that does not answer `BT-9000`, then capture a complete successful
  read and export a test image

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
- Field diagnostic 2026-10-27: NewChirp 1.0.20 opened the selected RT97L and
  COM port, but the radio returned no initial ACK. The published reference
  implementation retries with an STX wake-up when the ACK is missing;
  NewChirp 1.0.20 did not.
- Handshake change: NewChirp now waits up to three seconds for the initial
  ACK, then sends STX as a wake-up and waits up to one second. If ACK arrives,
  it starts the normal STX/identifier handshake. This path has offline serial
  coverage but no physical-radio confirmation.
- Remaining uncertainty: the channel byte map is provisional, global settings
  and password encoding are unknown, and no physical download has completed
- Next milestone: confirm the wake-up path on a physical RT97L, compare a
  complete physical image and official CPS export, then correct the channel
  flags and settings byte map

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
- Base radio: Baofeng UV-32. The GM-32 answers the same ident
  (`PROGRAMCOLORPROU`, fingerprint `UV32PRO`) and uses that memory map.
  Pick Baofeng GM-32 before a read. An image saved as UV-32 still opens as
  a UV-32.
- Evidence captures, kept in Downloads and not committed:
  - `/Users/randybrown/Downloads/gm32/Baofeng_UV-32_20261025.img`
    `92d5f133bde5303741b4f01a073e6927265871ccb3253df8d8a9a73295d3eb8c`
  - `/Users/randybrown/Downloads/gm32/gm32-read.pcap`
    `b647bfe1af426f74ea1def3b531a5504c61f55bcb4a4a679bb35308d4da0d338`
  - `/Users/randybrown/Downloads/gm32/gm32-write.pcap`
    `6fee9dafc5c6f282d1cd10b51a3c1905e44d026c8f6da204e32382811e0fa7ab`
- Read/write state: both implemented with exact CPS block ranges
- Write policy: GMRS 1-7 stay simplex. GMRS 8-14 may be simplex or
  receive-only, and they are stored narrowband on Low. GMRS 15-22 may be
  simplex, a +5 MHz repeater, or receive-only. Repeater inputs may be
  simplex or receive-only. Any other frequency is stored receive-only.
  A channel with no frequency is left empty.
- Read policy: the channel list shows the stored image. The editor and a
  write apply the GMRS rules.
- Cold-start symptom: an affected reporter stalls near the beginning of a
  download and then receives no response; the CPS asserts DTR/RTS while
  upstream UV-32 leaves them deasserted in NewChirp
- Hardware validation: a read and a write were tested successfully on
  2026-10-25. The driver stays experimental. These captures show the
  UV-32 programming link.
- Website catalog: listed as experimental in both the Baofeng section and
  New Experimental Radio Support
- Next milestone: on later writes, confirm channels 8-14 stay simplex
  unless set receive-only, a non-GMRS channel such as the sample image
  channel 31 (HAMs, 470.550 MHz) becomes receive-only, and settings plus
  bank names survive.

### TIDRADIO TD-H3 family

- Maintainer: NewChirp override of the upstream CHIRP `TDH3`, `TDH3_HAM`, and
  `TDH3_GMRS` settings path
- Maintained file: `drivers/newchirp_tdh3.py`
- Transport: upstream CHIRP TD-H3 clone serial at 38400 8N1
- Implemented: all channel, settings, and write behavior from the pinned
  upstream TD-H3 drivers. The override normalizes a stored brightness value of
  `0xFF`, which upstream treats as list index `-251`, to the brightest valid
  display setting before building the settings UI.
- Read/write policy: channel layout and write sequencing are unchanged.
  Brightness normalization only changes an invalid value and prevents
  unrelated shortcut-key changes from failing during settings serialization.
- Evidence: pinned CHIRP `tdh8.py` SHA-256
  `6cc013c387f4728df4db826cd758fad805fd855e43bc44e70e2004aac845cc6c`;
  2026-10-30 NewChirp 1.0.25 report from caitlinfireblood@gmail.com. The radio
  stored `0xFF`; the upstream settings path reported an out-of-range index and
  blocked a short-key change from Lamp to Monitor.
- Hardware validation: none for the invalid-value normalization.
- Next milestone: the reporter confirms that brightness displays as level 5
  and the PF1 short-press Monitor setting writes successfully.

### Radioddity DB35-G

- Maintainer: NewChirp driver reverse engineered from the official Radioddity
  DB-35G Programming Software 20251029V3
- Maintained file: `drivers/newchirp_db35g.py`
- Transport: 115200 8N1 through the rear microphone programming port
- Handshake: `02 PROGRAM`, ACK `06`, then `02`, identity `SMP558 FF FF`,
  then ACK `06`
- Commands: 4-byte read/write headers followed by 16-byte pages. Read uses
  `R + address:u16be + length:u8`; write uses
  `W + address:u16be + length:u8 + data`; exit uses `62`.
- Memory map: 80 channel pages from `0x0000`, then the settings page at
  `0xE000`. NewChirp writes only those known pages and does not write the
  undocumented gap between them.
- Implemented: RX/TX frequency, CTSS/DCS including split tones, FM/NFM,
  low/high power, scan include/skip, busy lock, squelch, NRC level, timeout
  timer, key beep, Roger beep, and priority watch. Read is enabled.
- Read/write policy: write encoding is implemented and offline-tested, but
  upload is blocked in the driver until a physical radio read and controlled
  write are verified.
- Evidence: official CPS ZIP SHA-256
  `114a74ab0810f7eb0a05a00d5cf1f205de36e6a4c91f2718ab5850947822847d`;
  `model.xml` SHA-256
  `6ee2463d1aff8e782b1fbb48bf8ec6b256f3f900558fa3649f056de064df842f`;
  executable SHA-256
  `4833286753c3cf2538a5f95db28be9881d5ad9056ae9f4e48c05eea799f9750b`
- Driver SHA-256:
  `9e2091e6d5ed230c0c6f87a8ecb2374480783f481a9032940d98a9047aacbaf7`
- Hardware validation: none. The protocol, pages, tone values, and settings
  are covered by synthetic transport tests only.
- Next milestone: read a physical DB35-G, compare every channel and setting
  against CPS, then write one modified channel page and verify it by reading
  the radio back with CPS and NewChirp.

### Baofeng DM-32UV

- Maintainer: NewChirp override of the upstream CHIRP `DM32UV` driver
- Maintained file: `drivers/newchirp_dm32uv.py`
- Transport: 115200 8N1 with DTR and RTS asserted; no hardware flow control
- Implemented: all 4,000 channels, editable named zones with multi-zone channel
  membership, analog and DMR channel fields, contacts, RX groups, scan lists,
  privacy-key references, and settings provided by the pinned upstream CHIRP
  implementation
- Read/write policy: channel and zone writes use the upstream CHIRP image
  policy. NewChirp applies zone create, rename, and membership changes to the
  downloaded image before upload and returns the resulting mapping state to
  the editor. This override changes only serial timing, read-only handshake
  retry handling, and diagnostics.
- Serial policy: set one short device timeout per connection, enforce command
  deadlines in the read loop, retry the read-only PASSSTA query up to three
  times, retry SYSINFO up to three times, and retry fragmented `V`
  radio-information queries up to three times. Information queries allow up
  to 1.5 seconds for the header and two seconds for the body. A malformed
  final response reports its hexadecimal reply bytes.
- Evidence: upstream CHIRP commit
  `832d349e050fbdcde50185f77cdb34fbe5bab57a`, vendor CPS v1.60 protocol
  work recorded by the upstream driver author, and CHIRP issue 12652
  documenting intermittent DM-32UV failures with some FTDI adapters. The
  2026-10-28 report from kc8jxc@hotmail.com returned only the first byte of
  the `V00000007` information reply after the previous 0.5-second window.
  A second report from martinezr@gmail.com reached a slow, retried PSEARCH
  sequence and received a non-ACK SYSINFO reply.
- Driver SHA-256:
  `96bf74adfb0f561f17499c1687444ca47bbf7e14074c0e25732db9adb1beaa4f`
- Hardware validation: the upstream driver completed read and write tests on
  firmware DM32.01.01.047. This NewChirp timing and retry override has
  synthetic serial coverage but no physical revalidation. The NewChirp
  Banks / Zones editor has offline image coverage for rename, creation, and
  multi-zone membership; its radio write path has not been validated on
  physical hardware.
- Next milestone: retest with the affected adapters, record the SYSINFO reply
  or `V` query header and body bytes if it still fails, then repeat a complete
  read and verified write with both a working cable and the affected cable.
  Include a zone rename, a spare-zone creation, a channel in two zones, and a
  read-back comparison against the CHIRP CPS image.

### Quansheng UV-K5 family

- Maintainer: NewChirp override of the upstream CHIRP UV-K5 handshake helpers
- Maintained file: `drivers/newchirp_uvk5.py`
- Transport: UV-K5 framed serial at 38400 8N1
- Implemented: all channel, settings, and variant behavior from the pinned
  upstream CHIRP UV-K5 implementation
- Read/write policy: unchanged. Unknown firmware continues to use CHIRP's
  read-only restricted profile and remains blocked from memory or settings
  writes.
- Identification policy: retry a missing or non-printable firmware reply up to
  five times, accept a fully printable version field without requiring a
  trailing non-printable byte, and report bounded reply bytes if all attempts
  fail.
- Evidence: upstream CHIRP `uvk5.py` and the 2026-10-28 NewChirp 1.0.22 report
  from ira.hamilton@yahoo.com showing a complete 16-byte hello reply while the
  selected UV-K5 unsupported profile reported that it could not determine the
  firmware version
- Driver SHA-256:
  `f2c98269c04030de71c5e228edc036b5925137ba0b3af3e714c12025b88da3b4`
- Hardware validation: none for this identification override.
- Next milestone: affected owner retests after restarting the radio in normal
  mode; if it still fails, submit the hexadecimal `UV-K5 hello` reply and the
  firmware string shown by the radio.

### Baofeng UV-9R

- Maintainer: NewChirp override of the upstream CHIRP `UV9R` driver
- Maintained file: `drivers/newchirp_uv9r.py`
- Transport: CHIRP WP970I clone serial at 9600 8N1
- Implemented: all channel, VFO, settings, and memory-map behavior from the
  pinned upstream CHIRP `UV9R` implementation
- Read/write policy: read behavior is unchanged. Upload resends the identical
  16-byte block at the same address up to three times when the radio does not
  return the expected `06` acknowledgment. An exhausted retry reports the
  exact block address.
- Evidence: upstream CHIRP `baofeng_wp970i.py` and the 2026-10-29 NewChirp
  1.0.24 report from mww512@yahoo.com. The second radio completed a 92-channel
  read but did not acknowledge the first upload block; another UV-9R Pro could
  both read and write.
- Driver SHA-256:
  `3aa4900f5f747bee95996ce530286a93bd0a6612d8d39f8b1d70727d0aac24e1`
- Hardware validation: none for this retry override. The upstream layout has
  existing hardware use, but the reported newer unit has not completed a write.
- Next milestone: affected owner retests an unmodified read image. If writing
  still fails, upload that image and the vendor CPS installer so the changed
  chipset’s write command can be reverse engineered.

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
- Settings: the TS-2000 does not expose radio-wide settings through CHIRP.
  NewChirp now reports that state without first downloading all 290 channels.
- Diagnostics: serial errors include a bounded CAT trace with the failed
  operation and memory location, elapsed time, refusal/no-response result,
  and detected radio ID. Channel contents are not recorded.
- Write status: protocol-level tests pass; upload/read-back retest on physical
  hardware is required before calling the timeout fix hardware-verified
- Next milestone: TS-2000 owner retest with both a small loadset and the full
  258-channel loadset, followed by a read-back comparison and submission of
  the generated communication trace if either write fails

### Kenwood TH-D75

- Maintainer: NewChirp override of the upstream CHIRP `THD75Radio` driver
- Maintained file: `drivers/newchirp_thd75.py`
- Transport: Kenwood PC/CAT commands through the TH-D75 USB programming cable;
  auto-baud from 9600 through 57,600, then clone transfers at 57,600
- Implemented: all channel, D-STAR, bank, and MCP-D75 image behavior provided
  by the pinned upstream CHIRP driver
- Read/write policy: unchanged from upstream CHIRP. This override changes only
  CAT response handling.
- CAT policy: accept a two-second reply window and ignore one exact command
  echo before accepting the radio response. A missing second response still
  fails normally.
- Evidence: upstream CHIRP `thd74.py` and the 2026-10-29 NewChirp 1.0.23 report
  from n0kyn@outlook.com showing ID-like replies at every baud without a
  recognized model response
- Driver SHA-256:
  `afd8176a9f3389addfee863462086938aa59cda57e7d361feda9dde04a85ab91`
- Hardware validation: none for this echo/slow-response override.
- Next milestone: affected owner retests with MCP-D75 closed and the same
  COM port selected throughout. If it still fails, submit the new ID reply
  text so the adapter echo behavior can be distinguished from radio settings.

### Icom IC-9700

- Maintainer: NewChirp override of the upstream CHIRP live CI-V driver
- Maintained file: `drivers/newchirp_icom9700.py`
- Transport: Icom CI-V over USB serial, 8N1, no hardware flow control
- Baud detection: 19200, 115200, 9600, 38400, 57600, and 4800
- Implemented: all channel fields, band views, satellite view, and settings
  provided by the pinned upstream CHIRP `Icom9700Radio` implementation
- Read/write policy: unchanged from upstream CHIRP. This override only
  validates the connection and does not alter channel memory encoding.
- Connection policy: a baud rate is accepted only after a CI-V memory response
  has the controller address `E0`, radio address `A2`, command `1A`, and
  subcommand `00`. Band and satellite views reuse the parent connection.
- Evidence: pinned CHIRP source
  `21e42e4518c167548af90ed7f9edf75e516c491a`, upstream IC-9700 CI-V format,
  and the 2026-10-29 NewChirp 1.0.23 report from luc@avl.be showing incomplete
  responses on COM13
- Driver SHA-256:
  `ab65a5b0699585d042257b727dc18003d0d5c41f649ed83dfdff659973d5a4d0`
- Hardware validation: none. The field report did not complete a read.
- Next milestone: luc retests after confirming CI-V address `A2h`, USB baud
  rate 115200, `Unlink from [REMOTE]`, and `CI-V Transceive off`; then record
  a successful multi-band read and separate read/write validation

### Icom IC-E90 / IC-T90A clone completion

- Maintainer: NewChirp override of the upstream CHIRP `icx90.py`
- Maintained file: `drivers/newchirp_icx90.py`
- Protocol notes: `docs/ICX90_PROTOCOL.md`
- Models: Icom IC-E90 and IC-T90A
- Transport: legacy Icom ICF clone serial at 9600 8N1
- Image: model bytes `25 07 00 01`, fixed size `0x2D40`
- Implemented: the upstream channel, bank, settings, special-memory, read, and
  write behavior. The override changes download completion only.
- Read policy: a download is successful when decoded frames cover the entire
  `0x2D40` image contiguously. This handles IC-E90 revisions that omit or
  malform the generic final end frame after sending the complete image. A
  normal end frame is still accepted.
- Write policy: unchanged from upstream CHIRP.
- Evidence: official CS-T90A CPS archive SHA-256
  `725c37e44a781b972af49fca6b48f9190b0cd2f757e42af05eb79a7992a90038`;
  executable SHA-256
  `aae6ea1353a3b0f85379bf30eb66a69fc7814a5a370a555acee2579d64ff7adf`;
  a field report received 39 bytes of model data followed by 28,261 bytes of
  clone traffic before the generic end-frame wait failed.
- Driver SHA-256:
  `2d78ec1f745d424b09b6cdd7d8d832f5af4ea27cd5015a2415118007331256ac`
- Hardware validation: none for this override. Offline tests cover complete
  image coverage without an end frame, normal end-frame completion, and
  truncated rejection. The public 500-channel image also loaded successfully
  during manual validation.
- Next milestone: Klas retests the committed fix with the same OPC-478UD port,
  confirms that the read completes after the full image arrives, and verifies
  the displayed channels before any upload.

### Icom ID-50 and ID-52

- Maintained driver: `drivers/newchirp_icom_id50_id52.py`
- Models: Icom ID-50 and ID-52
- Device help: Icom USB programming cable. Close CS-50 or CS-52 before
  starting a NewChirp transfer.
- Transport: Icom clone serial using the `IcomCloneFormat3` family protocol.
  Frames use `FE FE` framing and `FD` termination; commands `E0` through `E6`
  cover identification, model data, clone in/out, data, end, and completion.
  The driver uses raw escaped payloads and the high-bit transform recovered
  from the CPS.
- Serial settings: 9600 baud, 8 data bits, no parity, one stop bit
- Implemented: live model identification, full-image read, full-image write,
  download-end truncation, model/revision checking, and the provisional
  ID-4100-family channel, bank, basic settings, and D-STAR map
- Read/write policy: reads and writes are both enabled because this driver is
  explicitly experimental. The connected model ID is stored in NewChirp image
  metadata and must match before a saved image may be uploaded.
- Evidence: static REA/Ghidra analysis of Icom CS-50 1.03 (`CS50.exe` SHA-256
  `b9ce2ccc067560f8db8922f74889d5a4ecb88832ae1cba6760d6006a0f890470`) and
  CS-52 1.23 (`CS52.exe` SHA-256
  `50bd026943aeed5375e625a7eee65ec4d3c057a03097bfea3b668354a3daa933`);
  both contain `IcomCloneFormat3`, the Icom clone frame handlers, serial port
  setup, and the corresponding ID-50/ID-52 model strings.
- Driver SHA-256:
  `ea4514858db4f851e139fa4d3cde1437645ba941cca852b46d7329ecb0ddcf13`
- Hardware validation: none. Offline tests cover registration, model
  discovery, read framing, end truncation, upload framing, and clone
  acknowledgement.
- Next milestone: perform an unedited physical download for each model, save
  the image and model ID, compare the channel/D-STAR regions against this
  provisional map, then perform and read back a one-channel edit.
- Website catalog: must be listed as experimental for both radios.

### Icom IC-41S

- Maintained driver: `drivers/newchirp_ic41s.py`
- Protocol notes: `docs/IC41S_PROTOCOL.md`
- Model: Icom IC-41S only. The CS-41S Rev. 1.3 package contains no IC-41W
  model evidence.
- Device help: Icom OPC-478/U/UC programming cable; close CS-41S before a
  transfer.
- Transport: legacy Icom clone serial with hexadecimal `E4` payloads,
  checksums, 9600 8N1 normal speed, and the `Icom Inc.` end frame.
- Image: model header `29280000`, map revision 1, 16-byte records, decoded
  size `0x7D80`.
- Implemented: full-image read and write, RX frequency, exact split TX
  frequency, eight-character names, empty channels, and channel-count-aware
  memory bounds.
- Preserved without editing: tone words, channel flag bits other than active
  and duplex, zone table, settings, scan lists, SelCall, and key assignments.
- Evidence: official CS-41S Rev. 1.3 CPS ZIP SHA-256
  `9d93ade74ca671a1a037bb39fc5f040cbe1e24ab1447d19747e0230aef23502f`;
  executable SHA-256
  `1b47aae5605044dfb45b937ee4326f0ec108306bf106575ac17ea7e29528d0d5`;
  populated sample ICF SHA-256
  `eb3dd05b5e4add4bcfeeddb6de8e86f1e2c6cdb2785469b71750891d608ddb9a`.
- Driver SHA-256:
  `5f884d58a8bd3dea5d5d8dc4da2137877f5eff9b2d6b97c110851ad4d4dd247c`
- Read/write state: both enabled for this experimental driver.
- Hardware validation: none. Offline tests cover CPS image parsing, channel
  editing, split operation, empty channels, model matching, and preservation
  of unknown tone bytes.
- Next milestone: capture an unedited physical read, compare it byte-for-byte
  with CS-41S, edit one simplex and one split channel, write them, and verify
  the result with both CS-41S and NewChirp.
- Website catalog: listed as experimental in New Experimental Radio Support.

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

### Wouxun KG-UVD1P / KG-UV2D

- Driver: pinned upstream CHIRP `chirp/drivers/wouxun.py`, with NewChirp's
  bridge applying a one-second serial timeout
- Transport: CHIRP Wouxun clone serial at 9600 8N1
- Implemented: the upstream KG-UVD1P channel image, settings, and write path.
  Upstream describes this driver as covering KG-UVD1P, UV2, and UV3 family
  radios, including the KG-UV2D.
- Read policy: the identification and transfer sequence is unchanged. The
  longer timeout only allows the first 64-byte page to finish arriving instead
  of failing with `Failed to read full block (67!=68)`.
- Write policy: stock CHIRP behavior. The timing override does not change the
  image layout or write sequence.
- Evidence: CHIRP `wouxun.py` SHA-256
  `8bbb0edf5587cbeccb2a586d7a2b560f9fd4fb062cc45a9a080ff640f315b790`
  and `wouxun_common.py` SHA-256
  `50db3fe632e704950c3ffe4f0d7091c4053fce0360035ac684587bd15daf2b9e`;
  2026-10-30 NewChirp 1.0.23 report from dhartzog31@gmail.com. The radio
  completed identification, then returned 67 bytes for the first 68-byte
  block response.
- Hardware validation: none for the timeout override.
- Next milestone: the KG-UV2D owner power-cycles the radio and retests a full
  read. If the block is still short, capture whether Wouxun CPS can read it and
  provide the first response header bytes so the protocol variant can be
  separated from a cable timing issue.

### Motorola MOTOTRBO R7

- Importer: `lib/services/mototrbo_cps2_xml.dart`
- Format notes: `docs/MOTOTRBO_CPS2.md`
- Evidence: public MOTOTRBO CPS 2.0 Zone XML structure and field names
- Transport: file import of XML copied or exported from CPS 2.0
- Implemented: conventional channel names, RX/TX frequencies, duplex,
  receive-only state, analog CTCSS/DCS, bandwidth, power, scan state, comments,
  and DMR color code, timeslot, contact, RX group list, and privacy-key
  references
- Read/write state: XML import only; direct radio communication and upload are
  disabled
- Hardware validation: none. The official CPS 2.0 installer requires a
  Motorola account with software entitlement and has not been downloaded or
  bundled by NewChirp.
- Next milestone: import a redacted R7 CPS 2.0 Zone XML sample, compare every
  field with CPS2, then research direct programming only if a physical R7,
  entitled CPS installation, and compatible cable are available

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
