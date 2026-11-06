# NewChirp driver status

This is the authoritative local ledger for radios whose support is maintained
by NewChirp rather than upstream CHIRP. Update it whenever a driver is added,
changes transport, gains or loses write support, or completes hardware testing.

Last updated: 2026-11-06

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
| Yaesu FTX-1 | `drivers/newchirp_yaesu_ftx1.py` | Yaesu CAT serial, 4800-115200 auto-baud | 999 live memories | Yes, offline-tested | Hidden | Experimental |
| Yaesu FT-1D/2D/3D/5D clone family | `drivers/newchirp_yaesu_clone.py` | CHIRP Yaesu clone serial, 38400 8N1 | Completion-safe timeout; multi-bank mappings | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Radtel RT-950 | `drivers/newchirp_rt950.py` | CHIRP-compatible serial, 115200 8N1 + RTS/XON | Yes, designed | Disabled | Hidden | Experimental |
| Radtel RT-950 Pro, Bajeton BJ-9000 with nicFW950 | `drivers/newchirp_nicfw950.py` | nicFW serial, 38400 → 460800 8N1 | Yes | Changed blocks | Global settings and group names | Hardware-tested on one 6.00.16c unit; other versions/aliases experimental |
| Retevis RT97L | `drivers/newchirp_rt97l.py` | Stock USB serial, 9600 8N1 + DTR/RTS | Yes, hardware pending | Disabled | Hidden | Experimental |
| Kenwood TS-2000 | `drivers/newchirp_ts2000.py` | Kenwood live CAT serial, 9600 8N1 + RTS | Yes | Yes, longer write timeout | Standard | Hardware read verified; write retest pending |
| Kenwood TH-D75 | `drivers/newchirp_thd75.py` | Kenwood clone CAT serial, 9600-57,600 baud | Yes, echo-tolerant | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Kenwood TK-3401D | `drivers/newchirp_kenwood_tk3401d.py` | KPG-171D clone serial, 9600 then 19200 baud | Yes, provisional record scan | Disabled | Hidden | Experimental |
| Quansheng UV-K5 family | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | Yes, firmware-ID retry | Stock CHIRP policy | Stock CHIRP policy | Experimental |
| Quansheng UV-K1 / UV-K5 V3 (F4HWN 6.3) | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | 1,024 channels + 14 VFOs, offline-tested | Program/configuration region only, offline-tested | Hidden | Experimental |
| KSUN UV-K60 rebrand | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | Stock UV-K5-family profile | Stock UV-K5-family policy | Stock UV-K5-family policy | Experimental |
| Connect Systems CS750 | `drivers/newchirp_cs750.py` | NewChirp raw SCSI/RAP; CPS `.rdb` import | Yes, untested hardware | Disabled | Hidden | Experimental |
| Baofeng GM-32 | `drivers/newchirp_gm32.py` | UV-32 clone serial, 115200 8N1 | Yes | Yes | Yes, including bank names | Experimental |
| Baofeng DM-32UV | `drivers/newchirp_dm32uv.py` | CHIRP DM-32UV serial protocol, 115200 8N1 + DTR/RTS | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Baofeng UV-5RM Plus | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv5rm_plus.py` | UV-17-family serial, 115200 8N1 + DTR/RTS | OEM-style handshake retry; stock channel decode | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-17ProGPS | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv17progps_compat.py` | UV-17-family serial, 115200 8N1 | Malformed CTCSS values no longer abort channel decode | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-5G Mini | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv5g_mini.py` | UV-17-family serial, 115200 8N1 | Fixed GMRS frequencies; channels 15-22 retain stored duplex | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng GM-21 | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_baofeng_gm21.py` | UV-17-family serial; GM-5RH and UV-17Pro GPS handshakes | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| AnyTone 5888UV | `drivers/newchirp_anytone.py` | Stock AnyTone clone serial | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| AnyTone AT-D578UVIII Plus | `drivers/newchirp_anytone_d578uviii.py` | D578UV CPS serial, 115200 8N1 | 4000 channels + zones | Yes, offline-tested | Hidden | Experimental |
| TYT MD-UV380 | `drivers/newchirp_tyt_mduv380.py` | ST DfuSe USB 0483:DF11 + libusb | 3000 channels + zones | Yes, offline-tested | Hidden | Experimental |
| Baofeng UV-9G | Pinned CHIRP `baofeng_wp970i.py` with `drivers/newchirp_uv9g.py` | CHIRP WP970I clone serial, 9600 8N1 | Stock CHIRP driver | Stock CHIRP driver | Invalid service calibration values are read-only and preserved | Experimental compatibility override |
| Baofeng UV-9R | `drivers/newchirp_uv9r.py` | CHIRP WP970I clone serial, 9600 8N1 | Stock CHIRP driver | Retry for missing write ACK | Stock CHIRP driver | Experimental |
| TIDRADIO TD-H3 family | `drivers/newchirp_tdh3.py` | OEM-verified TD-H3 clone serial, 38400 8N1 | Invalid brightness normalized; five-attempt identity probe | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| TIDRADIO TD-H8 fourth-generation | `drivers/newchirp_tdh8_serial.py` | CHIRP TD-H8 serial, 38400 8N1 | HAM and generic G4 identities accepted, read-only | Disabled pending physical validation | Stock CHIRP driver | Experimental |
| Radioddity DB35-G | `drivers/newchirp_db35g.py` | OEM clone serial, 115200 8N1 | 80 channels + settings | Disabled pending hardware validation | Basic radio settings | Experimental |
| Midland MXT295 | `drivers/newchirp_mxt295.py` | CHIRP clone serial, 115200 8N1 | Yes, designed | Yes, hardware-tested | Radio & Modes | Hardware-tested |
| Wouxun KG-UVD1P / KG-UV2D | Pinned CHIRP `wouxun.py` with NewChirp bridge timing | CHIRP clone serial, 9600 8N1 | One-second block timeout | Stock CHIRP driver | Stock CHIRP driver | Experimental timing override |
| Wouxun KG-905G Plus | `drivers/newchirp_kg905g.py` | Wouxun clone serial, 19200 8N1, DTR on, RTS on | Yes, offline-tested | Yes, offline-tested | Hidden | Experimental |
| Wouxun KG-Q10H | `drivers/newchirp_kgq10h.py` | Wouxun encrypted clone serial, 115200 8N1, DTR on, RTS on | Yes, offline-tested | Yes, offline-tested | Hidden | Experimental |
| Icom IC-9700 | `drivers/newchirp_icom9700.py` | Icom CI-V serial, auto-baud from 4800 to 115200 | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Icom IC-7200 | `drivers/newchirp_icom_ic7200.py` | Icom CI-V serial, 19200 8N1 | Corrected memory grammar | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Icom IC-E90 / IC-T90A | `drivers/newchirp_icx90.py` | Legacy Icom clone serial, 9600 8N1 | Completion-safe full image; invisible-slot guard | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Icom IC-746PRO | `drivers/newchirp_icom_ic746pro.py` | Icom CI-V serial, 9600 8N1 | Stock IC-746 family logic | Stock IC-746 family logic | Stock IC-746 family logic | Experimental model profile |
| Icom ID-50 | `drivers/newchirp_icom_id50_id52.py` | Icom `IcomCloneFormat3` serial, 9600 8N1 | Yes, physical image verified | Disabled | Hidden | Experimental |
| Icom ID-52 | `drivers/newchirp_icom_id50_id52.py` | Icom `IcomCloneFormat3` serial, 9600 8N1 | Yes, transport verified | Disabled | Hidden | Experimental |
| Icom IC-41S | `drivers/newchirp_ic41s.py` | Legacy Icom clone serial, 9600 8N1 | Yes, hardware pending | Yes, experimental | Hidden | Experimental |
| Kenwood TM-D710GP | `drivers/newchirp_tmd710.py` | CHIRP TM-D710G clone serial | Stock driver | Stock driver | Stock driver | Regional identity compatibility |
| Kenwood TK-270G | Pinned CHIRP `tk760g.py` with `drivers/newchirp_kenwood_tk270g.py` | CHIRP Kenwood clone serial, 9600 8N1 | Stock driver; invalid bank metadata normalized | Stock driver | Stock driver | Experimental compatibility override |
| Motorola MOTOTRBO R7 | `lib/services/mototrbo_cps2_xml.dart` | CPS 2.0 Zone XML import | Conventional channels | Disabled | Import-only extras | Experimental |
| Retevis MA1 | Pinned CHIRP `th9800.py` | TYT clone serial, 38400 8N1 | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Retevis MA1 model A9305B | `drivers/newchirp_retevis_ma1_a9305b.py` | TYT addressed blocks, 9600 then 57600 8N1 | 1,000 channels | Yes, offline-tested | Hidden | Experimental |
| TYT TH-9800 | Pinned CHIRP `th9800.py` with `drivers/newchirp_th9800_compat.py` | TYT clone serial, 38400 8N1 | Reserved tone values no longer abort the read | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Yaesu VX-6 | Pinned CHIRP `vx6.py` with `drivers/newchirp_vx6_compat.py` | Yaesu clone serial, 19200 8N1 | Unprogrammable stored slots are treated as empty | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |

## Radio details

### Baofeng UV-5RM Plus

- Maintained compatibility: `drivers/newchirp_uv5rm_plus.py`
- Protocol notes: `docs/BAOFENG_UV5RM_PLUS_PROTOCOL.md`
- Official CPS:
  `BAOFENG_UV-5RM_Plus_CPS_20240327.zip`, SHA-256
  `63fcd01605238017040647c4fe3a8d2cccf544d76440027511c1953255d2b13f`
- Extracted CPS executable SHA-256:
  `5fb0880f45602a56a55dfba6e9a20a7972ac9f75e4286fd8f406372e0343ae1d`
- Transport: 115200 8N1 with RTS and DTR asserted
- Implemented: the OEM retries `PROGRAMBFNORMALU` every second, up to five
  times, when a stray byte is returned instead of `0x06`
- Unprogrammed PTT-ID bytes (`0xFF`) are exposed as `Off` instead of aborting
  channel decode; a subsequent upload replaces the invalid byte with the
  valid Off value
- Read/write policy: keep the pinned CHIRP channel, settings, and upload logic
- Evidence: REA 6.5.0/Ghidra 12.1.4 static analysis of `Communication` and
  `FormProgress`, plus the 2026-11-02 NewChirp Linux report that returned one
  unexpected byte at the first handshake
- Additional evidence: the 2026-11-03 macOS report UID 388 opened an edited
  image and failed during upload because channel memory 0 stored `pttid=0xFF`
- Hardware validation: none for the retry override
- Next milestone: reporters retest the next normal build; the macOS reporter
  should confirm the edited channel library uploads and reads back correctly

### Baofeng UV-17ProGPS

- Maintained compatibility: `drivers/newchirp_uv17progps_compat.py`
- Driver SHA-256:
  `079a2c975ba08857a2f99f2e3ce0be7dcc1b56a2fdc03759a6b6edac36007126`
- Transport: pinned CHIRP `baofeng_uv17Pro.py`, UV-17-family serial at
  115200 8N1
- Decode policy: a stored CTCSS word outside CHIRP's supported tone table is
  exposed as no tone instead of aborting the entire channel map. The original
  image bytes remain unchanged.
- Write policy: stock CHIRP channel, settings, and upload logic. When an
  affected channel is edited without changing its tone settings, its malformed
  tone bytes are preserved rather than silently replaced.
- Evidence: upstream CHIRP fixture `Baofeng_UV-17ProGPS.img`, SHA-256
  `0a9966909fd2acde913f50370bf114d7bd02b60d785468764f611f623575cd68`,
  plus the 2026-11-06 report in email UID 468 where the downloaded image
  decoded as invalid `rtone=1717.0` (raw CTCSS word `0x4312`).
- Offline validation: channel decode succeeds with the malformed word, the
  image bytes remain unchanged, and editing another field preserves the
  malformed tone bytes.
- Hardware validation: pending for this compatibility override.
- Next milestone: the reporter retests Download From Radio in the next normal
  build, confirms the affected channel appears with no tone, and compares one
  edited non-tone field against the radio display before upload.

### Baofeng UV-5G Mini

- Maintained compatibility: `drivers/newchirp_uv5g_mini.py`
- Transport: pinned CHIRP `baofeng_uv17Pro.py`, UV-17-family serial at
  115200 8N1
- Implemented: factory GMRS frequencies remain fixed for channels 1-30.
  Channels 15-22 retain their stored simplex or +5 MHz repeater assignment
  instead of being forced to repeater operation. Channels 23-30 remain fixed
  repeater slots.
- Read/write policy: the compatibility override changes only CHIRP's decoded
  field mutability for channels 15-22. It does not change the serial protocol
  or the stock channel encoder.
- Evidence: upstream CHIRP fixture `Baofeng_UV-5G_Mini.img`, SHA-256
  `14c43f7aec329913b2734be669d4667c5d70805163e253062063c6b817656156`,
  plus the 2026-11-05 report that NewChirp forced channels 15-22 to repeater
  operation.
- Offline validation: the fixture round-trips channels 15-22 through simplex
  and +5 MHz repeater assignments while channels 23-30 remain immutable.
- Driver SHA-256:
  `4d7f0051a5d7e7f5960cb76fb6b6c4fd4df14711cdbd033f7fd3fddd4488bc29`
- Hardware validation: none for this compatibility override
- Next milestone: the reporter should use the next normal build to confirm a
  simplex edit on one of channels 15-22 transmits simplex, then confirm a
  +5 MHz assignment still transmits through a repeater.

### Baofeng UV-9G service settings

- Maintained compatibility: `drivers/newchirp_uv9g.py`
- Transport: pinned CHIRP WP970I clone serial at 9600 8N1
- Read policy: unchanged. Service squelch calibration values above the upstream
  display maximum of 123 are shown read-only instead of aborting settings load.
- Write policy: unchanged for all normal settings. The invalid calibration
  values remain in the image and are skipped during a settings upload.
- Evidence: the 2026-11-03 Windows report UID 393 completed a 66-channel read,
  then failed while loading `squelch.vhf.sql4` through `sql9` with stored values
  124 through 129. The upstream `RadioSettingValueInteger(0, 123, value)`
  rejected the stored bytes.
- Offline validation: the upstream `Baofeng_UV-9G.img` fixture covers settings
  load, read-only invalid calibration entries, and preservation through
  `set_settings`.
- Hardware validation: none for this override
- Next milestone: the reporter retests settings upload in the next normal build
  and confirms the radio's ordinary settings remain intact

### TYT TH-9800

- Maintained compatibility: `drivers/newchirp_th9800_compat.py`
- Driver SHA-256:
  `4e472f1b772ebb61ea2ac03886d55d75d5646f57d24e476cd33e5bb1245ad62f`
- Transport: upstream CHIRP TYT clone serial at 38400 8N1
- Decode policy: preserve active channels when a stored CTCSS or DTCS field
  is outside CHIRP's supported range; use the 88.5 Hz or DTCS 23 default in
  the decoded memory while retaining the original image bytes
- Evidence: upstream CHIRP fixture `TYT_TH-9800.img`; the 2026-11-01 report
  showing `1666.5` rejected as an invalid `ctone`; and the 2026-11-06 report
  showing DTCS `1230` rejected as not in CHIRP's valid list
- Hardware validation: pending
- Next milestone: the 2026-11-06 reporter retests the download and, if it
  succeeds, compares one edited channel against the radio display before an
  upload/re-read cycle

### Yaesu VX-6

- Maintained compatibility: `drivers/newchirp_vx6_compat.py`
- Transport: upstream CHIRP Yaesu clone serial at 19200 8N1
- Decode policy: treat only a flagged memory whose stored frequency cannot be
  corrected to a supported tuning step as empty, retaining the original image
  bytes so untouched slots are not erased during an upload
- Evidence: upstream CHIRP fixture `Yaesu_VX-6.img` plus the 2026-11-02 report
  showing `666.666000 MHz` aborting the full read
- Hardware validation: pending
- Next milestone: retest with the reporter's saved image and confirm the
  channel count against the radio

### AnyTone AT-D578UVIII Plus

- Maintained driver: `drivers/newchirp_anytone_d578uviii.py`
- Protocol notes: `docs/ANYTONE_D578UVIII_PROTOCOL.md`
- Transport: AnyTone D578UV serial protocol at 115200 8N1
- Implemented: 4000 conventional channel records, RX/TX frequencies,
  FM/NFM/DMR mode, power, names, CTCSS/DCS, color code, time slot, contact
  index, RX-group index, receive-only, talkaround, and 250 ordered zones
- Preserved but not edited: contacts, RX-group members, scan lists, optional
  signalling, APRS, encryption, call lists, and radio-wide settings
- Official CPS evidence: `AT-D578UV_PLUS_PC_SOFTWARE.zip`, CPS 1.21 executable
  SHA-256
  `47737a24a496efdfe4924419ad81ab91317abcf30618801b7a4b631801b6146b`
- Implementation references: REA 6.5.0/Ghidra 12.1.4 analysis of the official
  CPS, QDMR commit `fb9c96af53f646c0706fa360209b2e0e6cd79a08`, and public
  D578UVIII Plus codeplug commit
  `65ec2c0700fdaae027536aeaa90f92bf116386ee`
- Driver SHA-256:
  `9f2a05c5c2f33a7cf53678dcab1a385d41fea514fc4c483e1b407c40c9119c30`
- Hardware validation: none
- Next milestone: physical channel/zone edit, upload, read-back, and comparison
  with the radio display and official CPS

### Yaesu FTX-1

- Maintained driver: `drivers/newchirp_yaesu_ftx1.py`
- Protocol notes: `docs/YAESU_FTX1_PROTOCOL.md`
- Transport: documented Yaesu CAT serial, auto-baud from 4800 through 115200
- Implemented: 999 live memories, frequency, 12-character name, FM/NFM/AM/
  USB/LSB/CW mode, standard repeater shift, CTCSS and DCS
- Not represented: nonstandard repeater splits and optional signalling
- Evidence: Yaesu FTX-1 CAT reference and public `cat-ftx1` commit
  `e77b599dbb27eff5b4bd49c01a689989cfcc9495`
- Driver SHA-256:
  `cbc60dc846bdaa78c55b1967f7f7ca0cf755c565e31d0c84f23a8a4738b7d6e9`
- Hardware validation: none
- Next milestone: physical empty-memory behavior, one controlled memory write,
  read-back, tone comparison, and repeater-shift verification

### TYT MD-UV380

- Maintained driver: `drivers/newchirp_tyt_mduv380.py`
- USB transport: `scripts/newchirp_usb_dfu.py`
- Protocol notes: `docs/TYT_MDUV380_PROTOCOL.md`
- Transport: ST DfuSe USB `0483:DF11`, 1024-byte blocks, with libusb
- Implemented: two complete codeplug segments, 3000 conventional channels,
  frequencies, FM/NFM/DMR mode, power, UTF-16LE names, CTCSS/DCS, color code,
  time slot, contact/group indexes, receive-only, talkaround, and 250 zones
- Preserved but not edited: contacts, RX-group members, scan lists, optional
  signalling, APRS, encryption, buttons, and radio-wide settings
- Evidence: official MD-UV380 CPS 2.42 executable SHA-256
  `62aa2101f75368ba61082fe3ceb999aa20573897f7b86a1ab616e47b390612bc`,
  REA 6.5.0/Ghidra 12.1.4, editcp commit
  `64fc5857ef0f33c1363a6e5d138964c9c21f663c`, and QDMR commit
  `fb9c96af53f646c0706fa360209b2e0e6cd79a08`
- Driver SHA-256:
  `37626dfbf0a556cd9f02bc7712c5581e805e7e39d1debe6fda4e9b1d87121f81`
- USB transport SHA-256:
  `3e6fdd3d76d7126757b062a00969921521f79bef2dd075bc5c3e8c87eae7597c`
- Hardware validation: none
- Next milestone: physical identify/read/edit/write/read-back test and
  libusb-runtime validation in native platform release builds

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
- Implemented: completion-first receive handling, a five-second idle limit,
  and multi-bank mapping classification for the radios whose CHIRP bank model
  stores independent membership lists
- Read/write policy: channel image layout and radio-specific fields are
  unchanged. The compatibility layer corrects bank-model metadata so a
  channel may remain in multiple radio banks instead of being rejected.
- Evidence: upstream CHIRP `yaesu_clone.py` and the 2026-10-29 NewChirp 1.0.23
  report from ka4hot@outlook.com. The FT5D completed its Send operation after
  a 3.2-second final chunk, but the upstream reader checked its two-second
  timeout before recognizing that the requested byte count was complete.
- Field evidence 2026-11-01: a macOS FT-5D write was rejected because channels
  34 and 38 were present in multiple banks. The upstream `FT1BankModel` and
  `FT2BankModel` contain independent per-bank channel lists but were declared
  as single-bank models. The compatibility override now marks those models as
  multi-bank and corrects FT-5D clone instructions to use `[F MENU]`.
- Driver SHA-256:
  `48b2a466a0e6207352d699909b0ae70eb5d9cc6e6921d8c58acbcfd5ef32def0`
- Hardware validation: none for this timing override.
- Next milestone: FT5D owner retests the multi-bank write in the next normal
  build and confirms the bank memberships survive a radio read-back.

### Radtel RT-950

- Maintained driver: `drivers/newchirp_rt950.py`
- Protocol notes: `docs/RT950_PROTOCOL.md`
- Evidence: official RT-950 CPS v1.3.0, native .NET metadata and CIL
- CPS artifact SHA-256:
  `605054c46ec17520b0f79b78585c3be431a6dcb95164dc638985455e813d7a1e`
- Transport: CHIRP serial path at 115200 8N1 with RTS/DTR asserted and no
  hardware or XON/XOFF flow control
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
- Field evidence 2026-11-01: a macOS RT-950 read received `RT-950` from the
  model command after the `BT-9000` handshake was acknowledged. Both identity
  strings are now accepted as the same read-only RT-950 protocol; writes
  remain disabled until a complete physical read is validated.
- Field evidence 2026-11-02: a macOS 1.0.36 read completed the handshake and
  model alias, then received no bytes for the first 128-byte read block before
  the old two-second timeout. Re-analysis of the exact official CPS v1.3.0
  artifact recovered two missing facts: flow control is disabled, and a
  randomized 25-byte `SEND` authentication packet must be acknowledged before
  reads. The driver now performs that exchange, decrypts returned payloads with
  the selected session symbol, and allows the Web Programmer's 3.5-second
  block response window.
- Frequency encoding: receive and transmit frequencies are four little-endian
  base-100 fields. A 2026-11-02 field report showed `462.575000` MHz rendered
  as `7.525460` MHz because the bytes were decoded in the wrong order.
- Driver SHA-256:
  `9c8380c52d4344619b0000bfb452480eb7b960ec8ccb9d3c6d1c4854b7721a89`
- Next milestone: confirm the reported RT-950 model code, classify any
  variant that does not answer the `BT-9000` handshake, then capture a
  complete successful read and export a test image

### Retevis MA1 and MA1 model A9305B

- The original MA1 continues to use the pinned upstream CHIRP `th9800.py`
  implementation at 38400 baud. Its image is 65,296 bytes with 1,000
  channels, 6-character channel names, and per-channel settings. The driver
  provides read and write support but remains classified as experimental.
- The newer A9305B is a separate radio path. Retevis labels the distinction
  explicitly: the A9305B CPS is only for radios carrying a label showing
  `MA1 A9305B`.
- Maintained A9305B driver:
  `drivers/newchirp_retevis_ma1_a9305b.py`
- Driver SHA-256:
  `efecd7c568f2d162905943e5751eb85a71d875c5b83de07c56cc15c4aff39a85`
- Official CPS evidence:
  `MA1-A9305B Programming Software-V1.0.zip`, downloaded from Retevis'
  official software page. Archive SHA-256:
  `8febcc09f1c546bd9f632fcc7beea91e94ad05fba637fb99ddef85c98281ea18`
- Extracted CPS application: `TM-70WPlus.exe`, SHA-256:
  `d2acb13359329a64d923282e3bcfcc0576436d7cb5aa2db71e02327e8458dafb`
- Analysis used the requested REA project and its static .NET/CIL inspector.
  The CPS setup resource identifies `RadioName=MA1-A9305B V1.0` and
  `Baudradio=57600`; the application assembly contains the 9600-baud
  handshake, baud command, programming-code path, read/write/end commands,
  two's-complement block checksums, and the 1,000-channel table.
- Old MA1 CPS evidence: `MA1-Programming-Software.zip` V3.6. Archive SHA-256:
  `6a78cc7a29c8a3e7ccb11830d80c9dea6f203c7ac1a96a4140c90c74852b015b`.
  Its extracted WPF application assembly SHA-256:
  `4f817a2738ff7a332cdfd3f6a698b5cd01d5073f88a276ac2de1b6d7ad9125f1`.
- A9305B transport: 9600 8N1 handshake with DTR/RTS asserted, 57600-baud
  negotiation, then addressed `FE/FD` blocks. Reads use up to 240-byte blocks;
  frames mix binary delimiters with ASCII-hex fields. The five-byte command or
  response marker and final `FD` are binary; the address, length, payload, and
  trailing checksum field are uppercase ASCII hexadecimal. The CPS read path
  strips the response checksum without validating it, so reads are checked by
  marker, address, encoded length, complete payload, and terminator. The CPS
  write path uses an additive two's-complement checksum over the binary address,
  one-byte length, and payload. Responses may return fewer bytes than requested,
  so the driver follows the encoded length and advances by the actual payload
  returned. Writes use the CPS' 32-byte rows.
- A9305B memory map: channels 1-200 use 21-byte records at `0x0000`, active
  and skip bitmaps at `0x1180`/`0x11A0`, and 6+10-character names at
  `0x000F` and `0x2300`. Channels 201-1000 use records at `0x4000`, bitmaps
  at `0xB600`/`0xB680`, and 6+10-character names at `0x4015` and `0x8200`.
- A9305B implemented fields: receive/transmit frequency, duplex and
  odd-split, FM/NFM/AM/NAM, three power levels, 16-character names,
  CTCSS/DCS with polarity and cross modes, tuning step, scan skip,
  transmit inhibit, talk-around, and reverse. Unknown channel bits,
  signalling fields, factory/calibration data, and unproven settings bytes
  are preserved.
- A9305B writable ranges mirror the CPS and exclude
  `0x1680-0x19BF`, `0x2B80-0x31FF`, `0x3284-0x3FFF`, and
  `0xBED0-0xCFFF`.
- Offline validation: registration of both MA1 variants, channel decoding
  across both 200/800 sections, 16-character names, tone fields, active/skip
  bitmaps, model fingerprinting, complete binary and ASCII-hex read framing,
  short response packets, opaque read checksums, write-side block checksums,
  and complete write framing.
- Hardware validation: the OEM software successfully read and wrote the radio
  from two Windows 11 PCs with two different USB cables. Zoran's 2026-11-01
  NewChirp 1.0.33 read reached every protocol stage, but reported a 214-byte
  response where the driver expected a binary frame. Zoran's 2026-11-02
  NewChirp 1.0.37 test exposed that the first implementation also treated the
  binary response marker as ASCII text. Direct CIL tracing of
  `SendReadDatAddComPro` and `DisplayText` shows the mixed framing above.
  Zoran's 2026-11-05 NewChirp 1.0.38 test received a complete 494-byte block
  response at `0x0000`, but the radio returned checksum `F3` while NewChirp's
  write-side calculation expected `A2`. `DisplayText` strips that field without
  comparing it, so the driver now mirrors the CPS read policy and logs any
  difference at debug level. A successful physical read and comparison with
  the CPS-exported image remain pending.
- Radio version: `M V136`
- Next milestone: complete an unedited physical read, save the raw backup,
  compare it with a CPS-exported image, then perform one channel edit,
  read-back, and restore test.

### Radtel RT-950 Pro, Bajeton BJ-9000 with nicFW950

- Maintained driver: `drivers/newchirp_nicfw950.py`
- Protocol and test procedure: `docs/NICFW950_PROTOCOL.md`
- Separate catalog entries: `Radtel_RT-950_Pro_nicFW950`,
  `Bajeton_BJ-9000_nicFW950`
- Model scope: standard RT-950 (non-Pro) excluded. Nicsure's release hub
  lists the RT-950 Pro; no non-Pro nicFW950 compatibility evidence is recorded.
- Evidence: user-supplied `nicfw_950_v4.py`, SHA-256
  `bb20f6252dba38bfa604f2ba0c0e465f0d98c67b73d1cfdc5071576dfdcc1f45`
- Driver SHA-256:
  `9fb5b5260c80c9cc3e5324daec441990816d70d08dd0a9c4035077b8bda5d751`
- Transport: 38400 baud negotiation to 460800 baud, 8N1, 128-byte blocks,
  address echoes and additive checksums; no stock CPS handshake or flow control.
  Retry only an initial baud ACK timeout, once after a three-second quiet
  interval, to recover the radio's idle baud reset after a previous download.
- Implemented: 999 channels, 30-character ASCII names, RX/TX frequencies,
  duplex/TX inhibit, seven power labels, FM/NFM/AM and native DSB/automatic
  extras, CTCSS/DCS with octal DCS storage, four A-Z groups in a channel extra
  (legacy Comment group letters remain supported), free-form notes in saved
  image metadata, global settings and 26 editable group names
- Read/write policy: read `0x50200..0x5FCFF`; only changed 128-byte blocks
  are written. Compare all affected blocks with the radio before the first
  write. Preserve reserved/VFO records, calibration, power-band data and gaps.
  Require commit ACK before requesting reboot. No wxPython UI dependency.
- Image baseline: rebuilt from saved CHIRP images in each bridge process so
  channel uploads and settings-only uploads share the same guarded behavior
- Offline validation: 23 driver tests, including real bridge JSON channel and
  settings upload paths, imported-note persistence and independent group edits,
  plus 7 stock RT-950/catalog regression tests passed. The note/group separation
  was verified offline; it did not add another physical-radio write.
  Two failures in the general upload suite were reproduced on unmodified
  upstream code (Windows temporary-file sharing and a BCL documentation assertion).
- Hardware validation, 2026-10-31: one user-provided unit already running
  nicFW950 **6.00.16c**, CH340 USB serial. Read 64,256 bytes and 209
  occupied channels. No-op channel/settings round-trip changed zero bytes.
  Channel-name, squelch and group-A-name writes each matched the complete
  expected raw image after reboot. All test edits were restored and verified;
  reserved/VFO records, calibration and power-band bytes matched the backup.
- Original raw-image SHA-256:
  `a928d10955de1096f5d99f2cfc07687695c0a2a23adb5f16b6a570003fb02ee6`
- Final raw-image SHA-256:
  `7514da597c1793c18731cbb3d4fc5958883c1ff3b508864c55b6841e82425339`
- Three settings bytes at `0x5F634`, `0x5F6A4` and `0x5F6EA` changed while
  the user selected slot B, channel mode and channel 1. Those user-confirmed
  operating-state changes were retained; later downloads were byte-identical.
- Immediate post-download renegotiation reproduced a missing ACK and
  recovered with exactly two baud requests and a three-second quiet interval
  (4.783 seconds total). Flash writes and commit commands are never retried.
- The unpopulated FM Receive Method field (`0xFFFF`) on this firmware was
  displayed using its default and remained unchanged throughout testing.
- The supplied standalone CHIRP reference was not executed. Validation is
  specific to this NewChirp port and this one unit, not every alias/version.
- Next milestone: upstream review and additional firmware/alias coverage.

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
- Driver SHA-256:
  `7fd6dc0cfacc0b574293862142b28826379edcf489de9ea49b2385010cd7f8f1`
- Transport: OEM-confirmed TD-H3 clone serial at 38400 8N1; the framing
  matches the pinned upstream CHIRP driver
- Implemented: all channel, settings, and write behavior from the pinned
  upstream TD-H3 drivers. The override normalizes a stored brightness value of
  `0xFF`, which upstream treats as list index `-251`, to the brightest valid
  display setting before building the settings UI.
- Read/write policy: channel layout and write sequencing are unchanged.
  Brightness normalization only changes an invalid value and prevents
  unrelated shortcut-key changes from failing during settings serialization.
- Identity routing: selecting the HAM or GMRS catalog entry now delegates to
  the TD-H3 family detector. The reported `P31183` identity therefore resolves
  to the generic TD-H3 profile even when a variant entry was selected.
- OEM CPS evidence: the official `TD-H3 GMRS` package dated 2025-03-31 was
  reverse engineered. It sends the same `PVOJH 5C 14` probe at 38400 8N1,
  enables RTS, uses 5-second serial timeouts, and retries the probe up to five
  times. NewChirp now matches the retry policy and clears stale input once
  before identification. See `docs/TIDRADIO_TD-H3_PROTOCOL.md`.
- Evidence: pinned CHIRP `tdh8.py` SHA-256
  `6cc013c387f4728df4db826cd758fad805fd855e43bc44e70e2004aac845cc6c`;
  2026-10-30 NewChirp 1.0.25 report from caitlinfireblood@gmail.com. The radio
  stored `0xFF`; the upstream settings path reported an out-of-range index and
  blocked a short-key change from Lamp to Monitor.
- Hardware validation: none for the invalid-value normalization.
- Next milestone: the reporter confirms that brightness displays as level 5
  and the PF1 short-press Monitor setting writes successfully.

### Baofeng GM-21 firmware variants

- Maintained compatibility: `drivers/newchirp_baofeng_gm21.py`
- Driver SHA-256:
  `17d6bfa54e271ff8b60ef40e4c10c79bbce0ca20dc4016a4922e2da7a7bf4def`
- Transport: pinned CHIRP UV-17-family clone serial at 115200 8N1 with
  DTR/RTS asserted.
- Handshake policy: try the field-confirmed `PROGRAMBFGMRS05U` GM-5RH
  handshake with the GM-5RH `F`/`M`/`SEND` magic sequence, then the existing
  `PROGRAMCOLORPROU` UV-17Pro GPS handshake with its own seven-byte-`M`
  sequence.
- Field evidence: a GM-21 with firmware 0.02 and hardware 01 rebooted or did
  not answer the original UV-17Pro GPS handshake. The same cable read and wrote
  the radio without errors when the GM-5RH profile was selected.
- 1.0.40 field report: the GM-21 entry accepted `PROGRAMBFGMRS05U` but then
  used the UV-17Pro GPS follow-up magic, causing the first clone read to return
  eight bytes instead of 68. Selecting GM-5RH still succeeded. The override
  now keeps each identification string paired with its matching magic sequence.
- Channel layout remains the pinned CHIRP GM-21 layout and settings path.
- Next milestone: confirm the compatibility override reads and writes that
  radio through the GM-21 catalog entry.

### TIDRADIO TD-H8 fourth-generation serial

- Maintained file: `drivers/newchirp_tdh8_serial.py`
- Transport: pinned CHIRP TD-H8 serial protocol at 38400 8N1
- Identities: `TDH84GEH`, observed in the 2026-11-01 NewChirp 1.0.30 report
  from 99kelly@comcast.net; `TDH84GEN`, observed in 2026-11-05 NewChirp
  1.0.37 reports from hils73@hotmail.com and nymetssuck@gmail.com
- Implemented: identity resolution against the later `0x1FEF` TD-H8 address
  space and read-only image download/offline editing
- Read/write policy: writes remain disabled until a physical read, controlled
  write, and read-back validate this fourth-generation address space
- Next milestone: reporter retests the read and supplies the saved image if
  channel decoding differs

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

### Quansheng UV-K1 / UV-K5 V3 (F4HWN 6.3)

- Maintained profile: `QuanshengUVK1F4HWN63` in
  `drivers/newchirp_uvk5.py`
- Protocol notes: `docs/QUANSHENG_UVK1_F4HWN_PROTOCOL.md`
- Identity: the reporter's hello deobfuscates to `F4HWN v6.3.0`
- Firmware evidence: `armel/uv-k1-k5v3-firmware-custom` release `v6.3.0`,
  source commit `3261ca7883d5b0b60c0905d8766612dee7b4191d`, and the matching
  F4HWN CHIRP driver SHA-256
  `a307886d90b6481b441c2cd34b622c8dacfc2080a34fc1e0ea2377054ee4ef96`
- Transport: UV-K5 framed protocol at 38400 8N1, 128-byte chunks
- Memory: `0xB190`-byte image, 1,024 channels, 1,024 channel names, 1,031
  attributes, 24 scan lists, and 14 VFO records
- Implemented: channel and VFO read/write, frequency, offset, duplex, CTCSS,
  DCS, mode, tuning step, power, TX lock, busy-channel lockout, frequency
  reverse, PTT ID, compander, and scan-list assignment
- Read/write policy: require `F4HWN v6.3.x`; write only
  `0x0000-0xA177`; preserve calibration at `0xB000-0xB18F`
- Settings: hidden until the complete F4HWN settings layout has dedicated
  validation. Firmware and scan-list MIX data remain untouched by channel
  edits.
- Evidence: static tracing of the F4HWN firmware serial paths and matching
  official CHIRP driver, plus replay tests derived from the reporter's exact
  obfuscated hello and synthetic EEPROM traffic
- Hardware validation: none. Offline protocol and image tests pass.
- Next milestone: reporter downloads and saves an image, edits one unused
  channel, uploads it, reconnects, reads it back, and confirms the channel on
  the radio before wider write support is enabled.

### KSUN UV-K60 rebrand

- Compatibility profile: `KSUNUVK60` in
  `drivers/newchirp_uvk5.py`
- Transport: pinned CHIRP Quansheng UV-K5 framed serial at 38400 8N1
- Implemented: the complete stock UV-K5-family channel, settings, read, and
  write path under the selectable `KSUN_UV-K60` model identifier
- Read/write policy: unchanged from the selected pinned UV-K5 profile. Known
  UV-K5-family firmware prefixes use the normal driver; unknown firmware uses
  CHIRP's read-only restricted profile.
- Evidence: HamTech M0FXB community documentation identifies the KSUN UV60
  family as UV-K5-family hardware, and the 2026-11-05 submission uses the same
  family protocol. No NewChirp physical read or write comparison exists yet.
- Driver SHA-256:
  `ef1a5561b2bc2e64b8273faec2db8510d5ca29434a9ffce6f44547d59d7cb83a`
- Hardware validation: none
- Next milestone: select `KSUN UV-K60`, download the full image, compare its
  channel and settings fields with the stock UV-K5 profile, then perform a
  controlled write and read-back before promoting it beyond experimental.

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

### Kenwood TK-3401D

- Maintained driver: `drivers/newchirp_kenwood_tk3401d.py`
- Protocol notes: `docs/KPG171D_PROTOCOL.md`
- Model: Kenwood TK-3401D dPMR446/analogue PMR446
- Device help: Kenwood-compatible USB programming cable. Close KPG-171D
  before starting a transfer.
- Transport: KPG-171D command protocol, starting at 9600 8N2 and continuing
  at 19200 baud
- Implemented: model identification, a zero-key session, 64 KiB addressed
  read, 128-byte block acknowledgements, complete raw-image retention, and a
  provisional PMR446 record scan for the 32 channel slots
- Read policy: read-only. The complete image is retained even if the channel
  decoder cannot identify it.
- Write policy: disabled. The physical direction flags, tones, power, keys,
  zones, and dPMR-specific fields have not yet been confirmed.
- Evidence: KPG-171D `1.10.1.0` executable SHA-256
  `3bd15b126fa0776e7f4206ed81931bba1ca4f5884cc81d1f719c1ec9331fb6fd`;
  REA 6.5.0 and Ghidra 12.1.4 analysis of the handshake, identity checksum,
  addressed reads, writes, and programming-mode exit
- Driver SHA-256:
  `48325e592ab71d1d2d6f029484f547082ee0e0598a5e7c0a6401132310d16fd8`
- Hardware validation: none. Offline tests cover identification, the 128-byte
  address sequence, PMR446 record discovery, and blocked upload.
- Next milestone: perform a physical TK-3401D read, compare the discovered
  records and names with KPG-171D, then map the remaining fields before
  considering any upload capability.
- Website catalog: must be listed as experimental.

### Kenwood TK-270G bank metadata

- Maintained compatibility: `drivers/newchirp_kenwood_tk270g.py`
- Transport: pinned CHIRP Kenwood Series 60G clone serial at 9600 8N1
- Issue: an active channel with an unprogrammed bank index above 127 aborts
  channel decode when upstream constructs its 0-127 bank-index setting
- Correction: normalize an invalid index to the channel's zero-based position
  and move it to bank 1, matching the driver's existing defaults for `0xFF`
- Evidence: the 2026-11-03 Windows report UID 391 read 24 channels, then
  failed its write with `bnumb value 128 not in range 0-127`
- Offline validation: the upstream `Kenwood_TK-272G.img` fixture is
  re-identified as a TK-270G for the shared Series 60G layout and covers the
  invalid-index normalization
- Hardware validation: none for this override
- Next milestone: the reporter retests upload in the next normal build, then
  reads the radio back and verifies the edited channels and bank assignments

### Kenwood TM-D710GP regional identity

- Maintained file: `drivers/newchirp_tmd710.py`
- Transport and layout: unchanged pinned CHIRP TM-D710G clone protocol
- Implemented: accepts the regional `D710GP` clone identity returned when the
  programming cable is connected through the TM-D710 control head
- Evidence: 2026-11-01 NewChirp 1.0.30 report from ke5etc@yahoo.com; the
  complete command handshake reached `ID TM-D710GP` instead of `TM-D710G`
- Hardware validation: read/write validation on this identity is pending
- Next milestone: perform a complete read and controlled write with the
  control-head connection required by the Kenwood programmer

### Icom IC-746PRO

- Maintained driver: `drivers/newchirp_icom_ic746pro.py`
- Transport: Icom CI-V serial, 9600 baud, 8N1
- Model distinction: the original IC-746 uses CI-V address `0x56`; the
  IC-746PRO uses `0x66`. Sending IC-746 commands to address `0x56` leaves an
  IC-746PRO silent even when the cable and port are working.
- Implemented: exact IC-746PRO model identity and CI-V address, using the
  established IC-746 family live-memory implementation for channel fields and
  write policy.
- Evidence: Hamlib's public `ic746.c` definitions list address `0x56` for the
  IC-746 and `0x66` for the IC-746PRO; the NewChirp report from
  kn5eee@proton.me showed CI-V address `0x56` selected for a radio reported as
  an IC-746PRO.
- Offline validation: exact model registration, CI-V destination address,
  frame construction, and separation from the original IC-746 profile.
- Hardware validation: none.
- Next milestone: read the IC-746PRO with CI-V address `66h` and
  CI-V Transceive off, then perform one controlled memory edit and read-back.

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
  write behavior. The override changes download completion and treats memories
  marked `invisible_channel` as empty before decoding stale channel fields.
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
- Field image 2026-11-02: Klas supplied a 11,769-byte CHIRP image,
  SHA-256
  `356041292a5b3edb9204c023359798981c19e406ccd02b5f87993ff3d770cc26`.
  NewChirp failed on stale data in memories 83 and 89; both carry
  `invisible_channel=1`, but upstream attempted to decode tone mode `4`.
  With the visibility guard, the image loads 82 visible channels and no
  parser exception.
- Driver SHA-256:
  `c7bebdcea4e70092fcd112e17997f1ea4f260b6c97831c6bc4c89309055d5233`
- Hardware validation: none for this override. Offline tests cover complete
  image coverage without an end frame, normal end-frame completion, and
  truncated rejection. The public 500-channel image also loaded successfully
  during manual validation.
- Next milestone: Klas retests the committed fix with the same OPC-478UD port,
  confirms that the read completes after the full image arrives, and verifies
  the displayed channels before any upload.

### Icom IC-7200 memory grammar compatibility

- Maintainer: NewChirp override of the upstream CHIRP `Icom7200Radio`
- Maintained file: `drivers/newchirp_icom_ic7200.py`
- Transport: Icom CI-V serial at 19200 8N1
- Implemented: the upstream live-memory channel, mode, filter, and read/write
  behavior with a corrected shared `MemFrame` field grammar
- Issue: pinned upstream `MEM_FORMAT` omits the comma after `unknown:3`, causing
  every CI-V memory response to fail with
  `syntax error in input:3: split:1` before channel decode
- Correction: the override supplies the same 11-byte frame layout with valid
  bit-field continuation punctuation and installs it only for the IC-7200
- Evidence: 2026-11-02 NewChirp 1.0.34 report from nevesperes@gmail.com on
  Windows COM3. The radio returned repeated 19-byte CI-V `1A 00` status
  responses before the parser error.
- Driver SHA-256:
  `375110fc403edb71a475d7573a63ea456c4ea79179495071b5acbd47058cd4c7`
- Hardware validation: none for this override
- Next milestone: reporter retests a complete IC-7200 read, then verifies one
  controlled channel edit and read-back

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
- Implemented: live model identification, full-image read, download-end
  truncation, model/revision checking, and 500 physical ID-50 channel records
  with channel availability, names, frequency, mode, duplex direction, offset,
  CTCSS, tuning step, output level, scan skip, and D-STAR callsigns
- Channel map: each record is 51 bytes. Receive frequency and positive offset
  are 32-bit big-endian Hertz at offsets 0 and 4. The 16-byte Shift-JIS/ASCII
  name starts at offset 12. Byte 9 is the physical mode selector: `00` FM,
  `03` AM, and `05` DV. Byte 10 packs scan skip in the high nibble and tuning
  step in the low nibble. Byte 11 packs duplex in the high nibble (`00` off,
  `01` minus, `02` plus) and output level in the low nibble. Byte 28 selects
  the tone mode (`00` off, `01` tone, `0B` TSQL); offsets 30 and 31 are the
  transmit and receive CTCSS indexes. D-STAR UR, RPT1, and RPT2 calls occupy
  offsets 30, 37, and 44 as 7-byte packed Icom callsigns in DV records.
  A separate 500-byte channel-availability table starts at image offset
  `0xA632`; `00` exposes the memory to CHIRP and `FF` marks a retained but
  unavailable factory record as empty.
- Unresolved fields: DTCS, reverse/cross-tone modes, remaining packed flags,
  zones, and settings. Unrecognized mode-selector values are logged and
  exposed as FM so they cannot abort a download.
- Read/write policy: reads are enabled and writes are explicitly disabled
  until the unresolved fields are validated with controlled physical images.
  Clone upload code remains in the driver for later validation but is not
  reachable from a normal write operation.
- Evidence: static REA/Ghidra analysis of Icom CS-50 1.03 (`CS50.exe` SHA-256
  `b9ce2ccc067560f8db8922f74889d5a4ecb88832ae1cba6760d6006a0f890470`) and
  CS-52 1.23 (`CS52.exe` SHA-256
  `50bd026943aeed5375e625a7eee65ec4d3c057a03097bfea3b668354a3daa933`);
  both contain `IcomCloneFormat3`, the Icom clone frame handlers, serial port
  setup, and the corresponding ID-50/ID-52 model strings. A physical ID-50
  image supplied by Nick Hale has size 229,669 bytes (`0x38125`) and SHA-256
  `908f22ecfa95b4e1eb6993f3dec123499cbd90a6e64f4099f44c46b2dff1d5db`;
  the two supplied read attempts are byte-identical. Radio firmware is CPU
  `1.05`, DSP `1.01`, and GPS `13196`.
- Field image 2026-11-01: Nick Hale's NewChirp 1.0.32 Windows read produced
  229,669-byte image `newchirp-7b9wb35_.img`, SHA-256
  `42b0f30169073cf679f283b0b3e776e8f29eb21e0b808d3882e128bc80ab67e1`.
  Comparing it with the previous verified image and the CS-50 built-in
  channel templates established the tone, duplex, tuning-step, output-level,
  and scan-skip packing. The same image's `0xA632` table has 29 zero entries
  followed by 471 `FF` entries, matching Nick's 29 saved memories. The radio
  retains factory AM records after the last available memory, so frequency
  validity alone cannot determine whether a channel is present.
- Driver SHA-256:
  `d05cf80346574e2cdabbf2d38df11036417a0eb8236da699a77835200de8b20c`
- Hardware validation: the ID-50 completed the clone download twice and all
  500 records decode without an exception. The latest supplied image exposes
  the 29 available memories as 24 FM and 5 DV; 12 are DUP+, 9 are DUP-, 15 use
  TONE, 8 use TSQL, and all report scan skip off. Twenty use low output and
  nine use high output. The retained factory AM records in unavailable slots
  are now hidden. No upload has been attempted. ID-52 still needs an
  equivalent physical image.
- Field evidence 2026-10-31: Nick Hale's ID-50 (Windows, NewChirp 1.0.28,
  COM4) completed a 55-byte model handshake and the clone-in transfer. The
  provisional ID-4100 parser then rejected a decoded mode. The saved clone
  image established the real 51-byte map and the mode-selector byte.
- Next milestone: Nick verifies that only the 29 available memories appear and
  checks Tone, power, skip, Duplex, and tuning-step values in the next normal
  build; obtain an equivalent ID-52 image; then
  validate DTCS, reverse/cross tones, zones, settings, write encoding, and a
  controlled one-channel write/read-back before enabling uploads.
- Website catalog: must be listed as experimental for both radios.

### AnyTone 5888UV

- Maintainer: NewChirp compatibility override of CHIRP's
  `AnyTone5888UVRadio`
- Maintained file: `drivers/newchirp_anytone.py`
- Issue: the upstream driver decodes `sqlMode` as a three-bit value but
  indexes a five-item list. Raw values 5 through 7 therefore abort the channel
  read with `IndexError`.
- Fix: unknown SQL values are exposed as `Off`, preserving the downloaded
  channel while leaving the unknown radio setting unchanged. The upstream
  `RadioSettingValueList` compatibility warning is also suppressed.
- Hardware validation: none. The 2026-10-31 macOS report from
  `2muchsql@gmail.com` completed the clone download and exposed the invalid
  value during channel decoding.
- Next milestone: the reporter confirms the channel list opens and verifies
  settings before any write.

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

### Wouxun KG-905G Plus

- Maintained driver: `drivers/newchirp_kg905g.py`
- Protocol notes: `docs/KG905G_PROTOCOL.md`
- Driver SHA-256:
  `fc4748422a39080c1cee91a253b2a9fe505c4ec63ad0c284938248428f5833a8`.
- Official programming software:
  `kg-905g_plus_setup_v2.1.1_20250514_.zip`, SHA-256
  `3a18b2d66313caad25a06dd5ed77dfe1ea33f41bea92b3e22242697e638a617a`.
- Installer SHA-256:
  `204534cdb8637ce19b0a326be3a6a1585a019e3fec35f8136b0c8e07f3b12b70`.
- Extracted CPS SHA-256:
  `5139fc67b4ed0a1dedffa6113200fc7120508dc9f72f454631098c30d6e1a83d`.
- Transport: Wouxun clone serial, 19200 8N1, DTR asserted, RTS asserted,
  64-byte blocks, rolling-XOR framing, and CPS checksum adjustment.
- Image: `0x4000` bytes. The model/firmware region at `0x0340` is read-only.
- Implemented: all 400 channels, 8-character names, receive/transmit
  frequencies, CTCSS/DCS and cross tones, power, AM/FM and wide/narrow mode,
  scan add, and empty slots. Unknown channel bits and all settings bytes are
  preserved.
- Read policy: the serial/model region followed by the eight program-data
  ranges assigned by `ReadFreqData_Init`.
- Write policy: write the eight program-data ranges used by the CPS and never
  write the model/firmware region. Simplex is limited to the 22 GMRS simplex
  frequencies. Repeaters require a GMRS output and an exact +5 MHz offset.
  The seven 467 MHz interstitial channels are narrow and Low.
- Offline validation: encrypted frame vector, complete read coverage, all 400
  channel bounds, record/name/valid-flag layout, tones, modes, unknown-bit
  preservation, write-range coverage, image validation, and malformed-image
  no-write safety.
- Hardware validation: pending for this CPS-based implementation. A
  contributor reported one channel-name write using an earlier map, but that
  does not validate this driver's full read, write, or read-back path.
- Read warning: keep an unedited official CPS backup before an upload.
- Next milestone: save a complete physical read, compare it with the official
  CPS export, and verify all 400 slots and preserved settings in a controlled
  write/read-back.
- Website catalog: not listed

### Wouxun KG-Q10H

- Maintained driver: `drivers/newchirp_kgq10h.py`
- Protocol notes: `docs/KGQ10H_PROTOCOL.md`
- Driver SHA-256:
  `2e16877778f29f660db9934797f5c912b4de86ccccdad150f3a1c184209f254d`
- Official programming software:
  `kg-q10h_setup_v2_1_.02.02_20231115_.zip`, SHA-256
  `a83483f9393fc4ff794faa2c0a703017a0f3bec7f054f62767bb2548b60807e7`
- Installer SHA-256:
  `7f2bdd283ef839d5ef61b6b6b20dd5ae2c13c754cdbeabb0a2f30654a8aa816b`
- Extracted CPS SHA-256:
  `2314ca128659c470ab4a8ca592d0751cb4f8b1e9f48fc8418871cd055a194ed6`
- Transport: Wouxun encrypted clone serial, 115200 8N1, DTR/RTS asserted,
  64-byte reads and 32-byte writes
- Image: `0x8000` bytes. The CPS reads a 256-byte identity region at `0x0340`
  but never uploads it.
- Implemented: 999 channels, 12-byte names, receive/transmit frequencies,
  CTCSS/DCS and cross tones, four power levels, FM/NFM/AM, and scan skip.
  Unknown channel bits and all hidden program-memory regions are preserved.
- Read policy: read the identity region followed by the nine program-data
  ranges assigned by `ReadFreqData_Init`.
- Write policy: write only those nine program-data ranges and never write the
  identity/calibration region. Transmit is limited to the KG-Q10H amateur
  bands.
- Evidence: REA 6.5.0 managed metadata/CIL inspection of the official CPS.
  The IL traces cover serial setup, request construction, chained encryption,
  receive fragmentation and completion, checksum validation, retry timing,
  identity parsing, channel serialization, and all memory-region boundaries.
- Offline validation: CPS frame vectors, fragmented responses, all checksum
  and address checks, all read/write boundaries, 1,000-slot bounds, tones,
  modes, power, unknown-bit preservation, and malformed-image no-write tests.
- Hardware validation: pending. The upstream prototype claimed physical
  round trips, but its seed and checksum differed from the official CPS and
  do not validate this implementation.
- Next milestone: open the reporter's saved image, complete a physical read,
  compare channels with the CPS, then perform one controlled write/read-back.
- Website catalog: add as experimental when this driver is released.

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
