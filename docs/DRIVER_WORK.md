# NewChirp driver work ledger

Generated from `database/driver_work/` by `python3 scripts/driver_work.py export`.

Use `python3 scripts/driver_work.py show <id>` for event history.

## Alinco

### DR-735

- **#94 bug | pending_validation | high:** DR-735T read fails after about one second on MX Linux
  Forum report: NewChirp sees the USB serial port but Read from radio fails after ~1 s. Stock CHIRP alinco_dr735t driver skips the OEM AL~ wake, accepts only DR735TN/TE, uses the bridge's 0.25 s timeout (OEM 500 ms) and calls exit(1) on a short block. Reverse engineering DR-735 Memory Editor 0.06 for a full override.
  Source: `forum` newchirp.net forum topic 56 post 194

## AnyTone

### 5888UV

- **#34 maintenance | experimental | normal:** Current driver status
  Transport: Stock AnyTone clone serial. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:58

### 778UV VOX

- **#w-20261120-9d64 bug | awaiting_user | normal:** PROGRAM comes back echoed in terminal caret notation on /dev/ttyACM0
  1.0.63 Linux: reply to PROGRAM was 'T^@^@^@^@^@^@^_^ST^PROGRAM' (26 bytes) instead of QX 06. Caret notation is a Linux terminal echo, so ttyACM0 is not answering as the radio (wrong device, a getty/ModemManager on the port, or an echoing cable).
  Source: `email` INBOX:829

### AT-D578UVIII Plus

- **#35 maintenance | experimental | normal:** Current driver status
  Transport: D578UV CPS serial, 115200 8N1. Read: 4000 channels + zones. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:59

## Baofeng

### 5RH Pro / UV-5RH Pro / UV-5RH Plus / UV-5RM Plus v2

- **#84 bug | awaiting_user | high:** Upload receives one-byte response after successful read
  NewChirp 1.0.57 read 21 channels from the radio, then the unchanged upload stopped on two 16-byte commands with incomplete one-byte responses.
  Source: `email` INBOX:718
- **#27 maintenance | experimental | normal:** Current driver status
  Transport: UV-5RH v2 encrypted clone serial, 115200 then 19200 8N1. Read: 640 channels + 10 zones, offline-tested. Write: Full image, offline-tested. Settings: Basic settings and zone names. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:51

### 5RM

- **#95 bug | investigating | high:** Upload fails on a slot with an out-of-range extra (PTT-ID 0xFF)
  macOS 1.0.58 CSV write: 'Failed to load pttid value 0: Value for 255 is out of range' then 'Could not prepare channel 7 (GMRS-21): None is not in list'. A programmed slot held PTT-ID 0xFF; the uninitialized extra made stock set_memory fail and blocked the whole upload.
  Source: `email` INBOX:783
- **#96 bug | awaiting_user | normal:** Every action fails instantly with 'Reported error: 1' on macOS 12
  NewChirp 1.0.54 on macOS 12.7.6: model-info (instructions) failed in ~50 ms with message '1' for read, write and settings. Not reproducible with the 1.0.54 bridge here; bundled Python minos is 10.15/11. Error text was an exception argument only.
  Source: `email` INBOX:785
- **#97 bug | closed | normal:** No response on both radios after writing a copied channel list
  Windows 1.0.57 COM7: PROGRAMBFNOR no response on radio 2 and then on the previously working radio 1, so the cable/port path rather than either radio. Reporter also asked how to select all channels (no Ctrl+A).
  Source: `email` INBOX:773,774
- **#w-20261122-ae46 bug | awaiting_user | normal:** First connection: PROGRAMBFNOR unanswered on COM3 (cable/port)
  Windows 1.0.66: three reads, each PROGRAMBFNOR with no response in 1.5 s; nothing reached the driver. Same pattern as closed #97 (cable/port). The 5RM now gets the UV-5R Mini port/cable checklist instead of bare 'No response from radio'.
  Source: `email` INBOX:891

### 5RX

- **#89 bug | awaiting_user | normal:** No response on macOS serial adapter
  NewChirp 1.0.56 received no response to its seven-byte identity command on a macOS usbserial adapter. Confirm the radio mode, cable voltage, adapter driver, and OEM CPS behavior.
  Source: `email` INBOX:736

### BF-F8HP-PRO

- **#100 bug | fix_committed | normal:** Zones not shown; radio scans all channels as one zone
  Forum topic 95 (1.0.58): zones (fixed 100-channel blocks) could not be seen or chosen, and the radio scanned every channel together. Stock CHIRP StaticBankModel sized banks with '/', raising TypeError, so the bridge dropped the zone model for 13 fixed-zone radios. Scanning across zones is controlled by the radio's Scan Zone Linking / Scan Link Zone 1-10 settings, which NewChirp exposes.
  Source: `forum` newchirp.net forum topic 95

### BF-V12D

- **#25 maintenance | experimental | normal:** Current driver status
  Transport: CPS-derived P3107 clone serial, 9600 8N1. Read: Original-firmware sequence traced; hardware pending. Write: Stock image/upload path. Settings: Stock channel decoder. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:49

### DM-32UV

- **#72 bug | fix_committed | high:** Airband receive-only validation
  Accept 108-136 MHz only when duplex is Off.
  Source: `email triage` 2026-11-16
- **#w-20261121-ab4d bug | pending_validation | high:** Write after inserting/moving a channel: blank channel left above it, write froze mid-upload
  Linux (Manjaro, KDE Wayland) 1.0.64: inserting a channel, or moving a channel added at the end up, then writing leaves a blank slot above the inserted channel; the write froze partway and needed a force quit; the radio rebooted and recovered. CPS cleanup restored the radio.
  Source: `email triage 2026-11-21` INBOX:863
- **#w-20261121-6314 bug | pending_validation | normal:** Channel names show leftover text after the NUL terminator ('Channel 1<NUL>t Mode')
  Forum file drop 12 (CSV, 43 channels) shows 9 names with a NUL followed by old bytes, e.g. 'Channel 1\x00t Mode' and 'RPT 15\x00 23'. Stock CHIRP's get_memory only strips trailing NUL/FF/space, so the leftover text shows in NewChirp and in CSV exports; zone get_name and the settings channel-name choices had the same trailing-only strip. The reporter described it as 'adds test to first channel on read'.
  Source: `forum file drop 12, 2026-11-20` forum-file-drop:12 sha256:8b526f78bb13ce4cb7a7e5a05a0dbebce6fbe42ae79b68c51caad4fffa8e40fb
- **#w-20261122-f1fb bug | fix_committed | normal:** Frequencies off the tuning-step grid (145.16375 MHz) flagged as unprogrammable
  Linux 1.0.68: reading a codeplug built elsewhere flagged 30 channels, e.g. 145.163750 MHz -> nearest 145.165. The radio holds the frequency; the driver sets has_nostep_tuning (10 Hz storage), which CHIRP's validate_memory honors, but the bridge never exported it and the app's pre-write check applied the 2.5-100 kHz steps. Affects every has_nostep_tuning radio (22 driver files).
  Source: `email` INBOX:895 <84f2a5ed-80a4-2f1a-f7de-971c3e81b271@newchirp.net>
- **#24 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP DM-32UV serial protocol, 115200 8N1 + DTR/RTS. Read: Stock CHIRP driver; receive-only airband accepted. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:48
- **#91 release | awaiting_user | normal:** Windows SmartScreen cancels update download
  A Windows 11 user reports that the new-version download is cancelled because the installer is not commonly downloaded. Collect the exact browser warning and downloaded filename; no radio driver defect is indicated.
  Source: `email` INBOX:739

### GM-21

- **#80 bug | awaiting_user | normal:** No response to known handshakes
  Support diagnostics sent; waiting for cable, COM-port, and OEM programmer comparison.
  Source: `email` INBOX:701
- **#33 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial; GM-5RH and UV-17Pro GPS handshakes. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:57

### GM-32

- **#86 bug | hardware_tested | high:** GMRS repeater TX and RX tones decode blank
  NewChirp 1.0.57 read 33 channels but omitted TX and RX tones on a GMRS repeater channel. Capture raw NewChirp .img and CPS source data for the same unmodified channel.
  Source: `email` INBOX:725
- **#23 maintenance | experimental | normal:** Current driver status
  Transport: UV-32 clone serial, 115200 8N1. Read: Yes. Write: Yes. Settings: Yes, including bank names. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:47

### K67 Pro

- **#26 maintenance | experimental | normal:** Current driver status
  Transport: Shared K6/K63 CPS serial, 115200 8N1 + DTR/RTS. Read: 1,000 channels + sparse full image, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:50
- **#68 new_driver | pending_validation | high:** CPS-derived read-only driver and Web Programmer profile
  The shared K6/K63 CPS transport, sparse image, 1,000 channels, tones, and read-only browser profile are implemented. Physical validation is pending.
  Source: `email and official CPS` INBOX:692

### UV-17ProGPS

- **#30 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1. Read: Malformed CTCSS values no longer abort channel decode. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:54

### UV-29 Pro

- **#31 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial through the UV-28 Plus profile, 115200 8N1. Read: UV-28 Plus profile, offline fixture round-trip. Write: Stock UV-28 Plus policy. Settings: Stock UV-28 Plus policy. Ledger status: Experimental vendor alias; hardware validation pending.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:55

### UV-32

- **#82 bug | hardware_tested | high:** Channels 52-54 lose stored CTCSS during decode
  NewChirp 1.0.56 decodes channels 52-54 with no tone, while RT Systems UV-32 Programmer 5.00.29 shows CTCSS 103.5, 103.5, and 206.5. The exported CSV alone does not contain the raw tone words.
  Source: `email` INBOX:744
- **#98 bug | investigating | normal:** CSV import fails: 'Failed to decode data using encoding utf-8'
  Windows 1.0.58: opening a CSV saved by other software failed before parsing; reporter concluded CSV import is impossible. App read CSV strictly as UTF-8.
  Source: `email` INBOX:787
- **#w-20261120-abf7 bug | fix_committed | normal:** Write stops on blank CSV CrossMode
  NewChirp 1.0.54 write of a CSV stopped at channel 111: cross_mode '' not in CHIRP's valid list. A blank CrossMode cell imported as '' and the bridge set it on every channel. Same report shows the 136.5/151.4/156.7 'malformed' tone warnings fixed in 27e3bf07.
  Source: `email` INBOX:828

### UV-5G Mini

- **#32 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1. Read: Fixed GMRS frequencies; channels 15-22 retain stored duplex. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:56

### UV-5G Pro

- **#81 bug | awaiting_user | normal:** No response from radio
  Support diagnostics sent; waiting for cable, COM-port, and OEM programmer comparison.
  Source: `email` INBOX:710

### UV-5R

- **#77 bug | awaiting_user | normal:** No response from radio
  Support diagnostics sent; waiting for cable, COM-port, and OEM programmer comparison.
  Source: `email` INBOX:691
- **#w-20261120-a8df bug | fix_committed | normal:** Settings write fails on out-of-range factory squelch calibration
  1.0.61: squelch_new.vhf.sql9 = 124 is outside uv5r.py's 0-123, CHIRP leaves it unset and set_settings raises int(None), so no setting can be written. Radio is labelled UV-5RH Pro GPS but reads 45 channels with the UV-5R profile.
  Source: `email` INBOX:833

### UV-5R Mini

- **#w-20261122-e807 bug | fix_committed | normal:** Read stops when the radio misses one block reply; stock aborts instead of re-requesting
  Windows 1.0.66 (two attempts): COM7 answered PROGRAMCOLOR with 'P' (echoed command, so not the programming cable); COM6 read ~75 68-byte blocks, then one R request got no reply and the read failed. OEM CPS v1.0.7 resends an unanswered block request every 1 s up to five more times; stock CHIRP aborts on the first timeout.
  Source: `email` INBOX:885/886 <2f9de842-1d9b-dc3d-5a27-e45a36374471@newchirp.net> <69ebea44-574d-fd41-9a84-077b4c1c2697@newchirp.net>

### UV-5R8W

- **#102 bug | pending_validation | normal:** Web Programmer read times out on UV-5R8W (BF-F8HP magic)
  Forum report (Chromebook/Chrome): AR-5RM works but two UV-5R8W radios fail with 'expected 1 bytes, received 0' under both the UV-5R and UV-5R8W (BF-F8HP) profiles. The web identity loop tried the next magic immediately; CHIRP waits 2 s after a failed magic, and the BF-F8HP magic is tried second.
  Source: `forum` newchirp.net forum: Web programmer from Chromebook/Chrome works for AR-5RM but not UV-5R8W

### UV-5RH

- **#29 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1 + DTR/RTS. Read: OEM-style handshake retry; stock channel decode. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:53

### UV-5RM Plus

- **#w-20261119-70d8 bug | fix_committed | normal:** v2-firmware radio selected as UV-5RM Plus reports only No response
  Linux 1.0.61 /dev/ttyUSB0: PROGRAMBFNORMALU answered 41, 03, 41, 03 then nothing. 0x41 ('A') is the v2 firmware announce reply (docs/BAOFENG_5RH_PRO_PROTOCOL.md), so the radio needs the UV-5RM Plus v2 model.
  Source: `email` INBOX:801
- **#28 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1 + DTR/RTS. Read: OEM-style handshake retry; stock channel decode. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:52

### UV-5RM Plus v2

- **#w-20261119-d555 bug | awaiting_user | high:** Writes to zones 2-3 reported in zone 1
  Reporter (first v2 hardware read) says frequencies written in zone 2 or 3 land in zone 1, and edits cannot span zones before a write. Offline bridge replay places a zone 2 edit at channel 65 and CPS V1.17 uses the same zone*64+slot IDs. Added EnZone (0x73 bit 2) handling; need the reporter's image and what the radio shows.
  Source: `email` INBOX:807

### UV-82WP

- **#78 bug | awaiting_user | normal:** COM port unavailable
  Support diagnostics sent; waiting for cable, COM-port, and OEM programmer comparison.
  Source: `email` INBOX:695

### UV-9G

- **#37 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP WP970I clone serial, 9600 8N1. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Invalid service calibration values are read-only and preserved. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:61

### UV-9R

- **#38 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP WP970I clone serial, 9600 8N1. Read: Stock CHIRP driver. Write: Retry for missing write ACK. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:62

## Binqi

### BQ-889 analog

- **#67 maintenance | experimental | normal:** Current driver status
  Transport: USB/AT probe, baud auto-detect. Read: Read-only transport probe; no channel decoder. Write: Disabled. Settings: Hidden. Ledger status: Experimental probe.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:91

## Connect Systems

### CS750

- **#76 bug | fix_committed | high:** Windows raw-disk access denied
  Use a read-only Windows physical-drive handle and explain the Administrator requirement on error 5.
  Source: `email triage` 2026-11-16
- **#22 maintenance | experimental | normal:** Current driver status
  Transport: NewChirp raw SCSI/RAP; CPS `.rdb` import. Read: Yes, untested hardware; Windows opens read-only. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:46

## Icom

### IC-41S

- **#58 maintenance | experimental | normal:** Current driver status
  Transport: Legacy Icom clone serial, 9600 8N1. Read: Yes, hardware pending. Write: Yes, experimental. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:82

### IC-7100

- **#73 bug | fix_committed | high:** Unknown CI-V mode aborts download
  Display reserved modes as read-only and block upload before I/O.
  Source: `email triage` 2026-11-16
- **#53 maintenance | experimental | normal:** Current driver status
  Transport: Icom CI-V serial, auto-baud. Read: Opaque mode bytes decode read-only. Write: Disabled for opaque channels. Settings: Stock IC-7100 settings. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:77

### IC-7200

- **#52 maintenance | experimental | normal:** Current driver status
  Transport: Icom CI-V serial, 19200 8N1. Read: Corrected memory grammar. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:76

### IC-746PRO

- **#55 maintenance | experimental | normal:** Current driver status
  Transport: Icom CI-V serial, 9600 8N1. Read: Stock IC-746 family logic. Write: Stock IC-746 family logic. Settings: Stock IC-746 family logic. Ledger status: Experimental model profile.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:79

### IC-910

- **#w-20261119-c2a9 bug | fix_committed | high:** Read stops on unset CTCSS tone (rtone 0.0)
  Live CI-V read aborted with '0.0' is not a valid value for 'rtone' (1.0.60, IC-910H; reporter also has an IC-740). CHIRP's GUI isolates the bad channel; NewChirp's single-pass read stopped. drivers/newchirp_icomciv_tone_compat.py makes non-standard tone values read as 88.5 Hz for every CI-V memory frame.
  Source: `email` INBOX:810

### IC-9700

- **#w-20261120-8a28 bug | fix_committed | normal:** Switching to the 430 band fails with Unknown file format
  1.0.61 read 28 channels from the radio, then choosing '430 band (99 channels)' re-read the one-band live CSV snapshot as a clone image and failed.
  Source: `email` INBOX:825
- **#51 maintenance | experimental | normal:** Current driver status
  Transport: Icom CI-V serial, auto-baud from 4800 to 115200. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:75

### IC-E90 / IC-T90A

- **#54 maintenance | experimental | normal:** Current driver status
  Transport: NewChirp ICF clone transport, 9600 8N1. Read: Four identity attempts; checksum-validated contiguous full image; invisible-slot guard. Write: NewChirp clone-in boundary, 362 32-byte blocks, required `E6 00`. Settings: Stock ICX90 decoder. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:78

### IC-F60V

- **#w-20261119-dada new_driver | awaiting_user | normal:** IC-F60V commercial VHF handheld support
  Feature request from a 1.0.61 user. Not in CHIRP. Needs the Icom CS-F60 programming software and a radio image or capture.
  Source: `email` INBOX:816

### ID-50

- **#56 maintenance | experimental | normal:** Current driver status
  Transport: Icom `IcomCloneFormat3` serial, 9600 8N1. Read: Yes, physical image verified. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:80

### ID-52

- **#57 maintenance | experimental | normal:** Current driver status
  Transport: Icom `IcomCloneFormat3` serial, 9600 8N1. Read: Yes, transport verified. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:81

## Kenwood

### TH-D75

- **#13 maintenance | experimental | normal:** Current driver status
  Transport: Kenwood clone CAT serial, 9600-57,600 baud. Read: Yes, echo-tolerant. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:37

### TH-F6

- **#w-20261121-f514 bug | awaiting_user | normal:** Read fails: ID handshake answered but 'Unexpected response from radio' (1.0.23)
  Windows 10, NewChirp 1.0.23, serial COM4. 12 CR/ID probe rounds; ID gets a reply but the driver rejects it. A second report shows 'FormatException: Missing extension byte', the non-UTF-8 radio reply crashing 1.0.23's output decoding (current releases decode with allowMalformed). Needs an update to the current release and a fresh report showing the radio's ID reply.
  Source: `email triage 2026-11-21` INBOX:860 INBOX:861

### TK-270G

- **#75 bug | fix_committed | high:** Transient block checksum rejection
  Retry the identical block up to three times, then close programming mode.
  Source: `email triage` 2026-11-16
- **#83 bug | fix_committed | high:** Upload rejects erased bank index sentinel
  A downloaded image containing bank index 128 on an active channel is rejected during unchanged upload before radio I/O. Normalize erased bank metadata before rebuilding bank tables.
  Source: `email` INBOX:723
- **#w-20261120-8af9 bug | fix_committed | high:** Last channel missing after write: 0-based bank positions collide with KPG 1-based positions
  1.0.63 writes without error but the last channel in the list (ch 25) is not usable on the radio (INBOX:855). Evidence: CHIRP's OEM-style TK-760G sample image stores each record's bnumb as the 1-based position within its bank, matching the 0x300 table (bank, pos, bank-1, slot). NewChirp (from stock tk760g) assigns new channels bnumb = slot-1 and normalizes the 0x80 sentinel (reporter's ch 24, INBOX:808) to slot-1, i.e. 0-based. With KPG-programmed channels at positions 1..N, the newcomer duplicates position N and position N+1 is empty, so the last channel drops. _prep_data rebuilds 0x300 by slot order and never updates record bnumb. Secondary suspect: 0x7000 per-channel flags filled by count, not slot. Plan: renumber each bank's records 1..n (existing valid order first, then new channels) and build 0x300 from that order; confirm with the reporter's image.
  Source: `email` INBOX:855
- **#60 maintenance | experimental | normal:** Current driver status
  Transport: Kenwood Series 60G clone serial, 9600 8E1. Read: NewChirp decode with raw-preserving invalid-index normalization. Write: NewChirp write path with bank-state validation and transient checksum retry; offline-tested. Settings: Stock driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:84

### TK-3401D

- **#14 maintenance | experimental | normal:** Current driver status
  Transport: KPG-171D clone serial, 9600 then 19200 baud. Read: Yes, provisional record scan. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:38

### TK-350

- **#71 bug | awaiting_user | high:** Identity request receives zero bytes
  Zero identity bytes were observed on COM3 and COM4. The driver now retries the bounded 0x02 identity request three times for late PC mode.
  Source: `email` INBOX:727-728
- **#15 maintenance | experimental | normal:** Current driver status
  Transport: KPG-23D clone serial, 9600 8N1, 0xF000 addressed blocks. Read: Yes, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:39

### TK-359

- **#79 bug | awaiting_user | normal:** No identity response in PC mode
  Support diagnostics sent; waiting for cable, COM-port, and OEM programmer comparison.
  Source: `email` INBOX:699-700
- **#16 maintenance | experimental | normal:** Current driver status
  Transport: KPG-32D clone serial, 9600 8N1, 0xF000 addressed blocks. Read: Yes, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:40

### TK-863G

- **#17 maintenance | experimental | normal:** Current driver status
  Transport: KPG-76D clone serial, 9600 8E2 with OEM baud fallback. Read: 128 channels + full 32 KiB image, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:41

### TM-D710P / TM-D710GP

- **#70 bug | pending_validation | high:** D710P identity compatibility and eight-character names
  Rear PC port reads on a TM-D710A; a RepeaterBook HMK file with names within the eight-character limit wrote successfully. Longer names are blocked before radio I/O.
  Source: `email` INBOX:717
- **#59 maintenance | open | normal:** Current driver status
  Transport: CHIRP TM-D710/TM-D710G clone serial. Read: Hardware-read via rear PC port on one TM-D710A. Write: Hardware write succeeded with 8-character names. Settings: Stock driver. Ledger status: Identity compatibility; read-back pending.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:83

### TS-2000

- **#12 maintenance | hardware_tested | normal:** Current driver status
  Transport: Kenwood live CAT serial, 9600 8N1 + RTS. Read: Yes. Write: Yes, longer write timeout. Settings: Standard. Ledger status: Hardware read verified; write retest pending.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:36

## KSUN

### UV-K60 Plus

- **#21 maintenance | experimental | normal:** Current driver status
  Transport: MH-580 clone serial, 38400 8N1. Read: Sparse `0x2A00` image, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:45

### UV-K60 rebrand

- **#20 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: Stock UV-K5-family profile. Write: Stock UV-K5-family policy. Settings: Stock UV-K5-family policy. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:44

## Midland

### MXT295

- **#46 maintenance | hardware_tested | normal:** Current driver status
  Transport: CHIRP clone serial, 115200 8N1. Read: Yes, designed. Write: Yes, hardware-tested. Settings: Radio & Modes. Ledger status: Hardware-tested.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:70

## Motorola

### MOTOTRBO R7

- **#61 maintenance | experimental | normal:** Current driver status
  Transport: CPS 2.0 Zone XML import. Read: Conventional channels. Write: Disabled. Settings: Import-only extras. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:85

## NewChirp

### Desktop

- **#w-20261120-393e enhancement | fix_committed | normal:** Collapsible Channel Library summary cards
  UV-32 owner asked to collapse the Channels / Scan enabled / Needs attention cards to see more channels.
  Source: `email` INBOX:834

### Desktop app

- **#w-20261122-685e enhancement | fix_committed | low:** Print the channel list
  5RH Pro owner asked to print channels. The Print button only prints the GMRS/FRS reference; workaround: Save as... CSV and print from a spreadsheet.
  Source: `email` INBOX:889

### Linux desktop

- **#101 release | released | normal:** Linux 1.0.61 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 50f17c3c. The release restores read-only fixed-zone display for BF-F8HP-PRO and related radios; public manifest reports 1.0.61; package SHA-256 values are b32b6dc5ea2edcf1a7f6f29e0cae249357dd0ebe462b76cfbcd16757eee8ac27, 74ba479102c025ff4b3f65d7337f57467428c3bbe7b3c9cc8d0d828c1e084e41, c4306b569fc9f551b4b74f217663f16ec664f481ddf59b81ba3b1678470bac61, and e839269b1d6421b31ebc445dc21da7cb6638019dbf0d4b97315bf02edfaa10e1.
  Source: `release` desktop:50f17c3c
- **#w-20261119-3094 release | released | normal:** Linux 1.0.62 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 0d09b292. The release adds the Wouxun KG-689E/KG-699E driver, Icom CI-V no-tone recovery, TK-270G and 5RH Pro fixes, UV-5RM Plus v2 reply handling, and F4HWN module image support. Public manifest reports 1.0.62. Package SHA-256 values: 34dfca976a39e621ae7797bdb4148f1e1ae2c753df18feb2046320d72206e7aa, 9e8a8be6dc45c6342d7a9c9cfd89b3d88193acbd736edd7d7885bffa0aebd240, 8d313037c55f62f07455d2a996fae07fb06fbcdf45399895465b6177fd87502e, and 44c1585e5113f0300681dd19c1e564dbbe09bc0a7a912cb323a46d1a609a273f.
  Source: `release` desktop:0d09b292
- **#w-20261119-250d release | released | normal:** Linux 1.0.63 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 5c2c607f. The release adds the read-only Icom IC-F50V/F60V memory-capture profile, fixes fixed-zone write blocking after channel moves, and preserves radio-mapping memberships across location remaps. Public manifest reports 1.0.63. Package SHA-256 values: 01b9ab23a869829a58024cb1c086e753f1a39cf870b546a1cc4f6c309aa78898, 70a5f484b2ac85112e50c1468b3bd3d10cbd063e79300868ddf9de117909dc0b, 99b578e21654e28859f5cdd15f270d1be5f3c9e46e5a9463c694f3f8507dc15b, and 8ed7d2c954dfd349affa9f8aae3a22cc27c32573e05eb17da35904dc58c7779a.
  Source: `release` desktop:5c2c607f
- **#w-20261120-4857 release | released | normal:** Linux 1.0.64 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 12c4633d. The release fixes blank cross modes, preserves unloadable CHIRP settings, restores live band switching, adds collapsible channel-summary metrics, and carries CSV and bridge compatibility fixes. Public manifest reports 1.0.64. Package SHA-256 values: c58f4ef279e260f131eb700d651d4063e289999cf4bc7083cfde2a6529bcd0be, d4e13e4a0cacf24cc90cd428cd4633544588a7d8b4e69be75888d493211720c4, 26048b9b36e63eefe3016811d5232f6b6acf399f0a39a603e93ea5092127132e, and 05e0c9c23db86200c80924bdbdf86804126365d817e5f655dfa27f3e1073cf9f.
  Source: `release` desktop:12c4633d
- **#w-20261120-f0fb release | released | normal:** Linux 1.0.65 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 014df59b. The release integrates the approved RepeaterBook API relay, expands read-only Icom IC-F50V/F60V channel support, handles echoing cables on the Wouxun KG-689E, and carries related UI and error-reporting fixes. Public manifest reports 1.0.65. Package SHA-256 values: f3cf598266edcd1c75944703cbb3e4699afb82cf6282c8054e797922d3e1df9e, fd1af91bc3a84bbcb267fb0a3e19ec35c8d3a7b92b5407e1fb6415c14102210e, c0849973a05f21de913201ff4c3de253b9020e52af0f55a8dc162253a9349f20, and f1aca0d1b313ce5db5145407ff811cfb3f4979dadb611d9382e1cec3f4ae9958.
  Source: `release` desktop:014df59b
- **#w-20261120-0fa6 release | released | normal:** Linux 1.0.66 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 268f70cd. The release re-enables Radtel RT-950 Pro writes after physical read/write validation and adds receive-only channel handling and UI safeguards for marine and protected channels. Public manifest reports 1.0.66. Package SHA-256 values: d7135ce5062bff886b418a42b8e8c6fe5f06ce00f85bea4fd1acd7235ef9948f, 8c409604d642e68a1c764062699008d936990c523f7e3ea53f10f3998419b200, 1d8a92db199f83e240203ce9f6dbbd14e1b0e730474961b0ddefc0d9c0f0b8d9, and 3a6c8d357568ccc7873efe7974cd6ed335a10d3edfad066a910eb13f8a7feb47.
  Source: `release` desktop:268f70cd
- **#w-20261121-41b6 release | released | normal:** Linux 1.0.67 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 99175783. The release preserves moved channel extras through insertions, numbers TK-270G bank positions from 1 like KPG-56D, and adds RT-950 Pro Bluetooth read diagnostics. Public manifest reports 1.0.67. Package SHA-256 values: d8e8be645be49740dd6cec9ff6e7c14f989c542683235495b0ec9573e3116f79, c8bbf9c8ef4d3acede49c3fcd636fe0c7c6b498d2be49f3bd88ab0f19a9a2ed8, 85ef5b9c0ca708ee8590b926737328097cea642316f863525ecf724bfcf84a8b, and 4906d358a09bfbe57d3177bcc58a49686e63a8e6bc549dbfa4e7f6eb22d0780b.
  Source: `release` desktop:99175783
- **#w-20261121-1690 release | released | normal:** Linux 1.0.68 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 360773be. The release ends DM-32UV channel and zone names at the first NUL so stale padding no longer leaks into edited names. Public manifest reports 1.0.68. Package SHA-256 values: a60af27ff15691a98a88057f2f9b6213ed026dc0c65fc410e4d2add9c18ee3e8, 0ea65c3d2163d403923df814d4276c96407275f24b589298abf824677a3c7419, 4e5c027498b788f4c1747a0fa5f06482d1e04bcac51ea9c1ddd9d8ed0a798d0f, and b56ba89d36e0f513f73b2014809e4ecff49a8e8e58d0bd809b9bad76497c625d.
  Source: `release` desktop:360773be

### macOS desktop

- **#w-20261120-696e release | released | normal:** macOS 1.0.63 published
  Published a universal signed, notarized, stapled DMG from source commit 847db298. It adds approved RepeaterBook API search through the server relay, IC-F50V/F60V capture support, KG-689E/699E fixes, and cumulative 1.0.63/1.0.64/1.0.65 compatibility changes. Artifact SHA-256: 0496ad47204d606a09555d4c27fcc5fc88f1bd6a101b14d6865cbe00f692477a. Notarization: baac68f6-92f7-4154-b680-3b3a6c57adc1. Live manifest reports macOS 1.0.63.
  Source: `release` desktop:847db298
- **#w-20261120-2135 release | released | normal:** macOS 1.0.64 published
  Published a universal signed, notarized, stapled DMG from source commit 2fc54348. It includes the RT-950 Pro write/transmit correction, approved RepeaterBook API search through the server relay, IC-F50V/F60V capture support, KG-689E/699E fixes, and cumulative driver/UI/bridge compatibility changes. Artifact SHA-256: 05ccb46548ff27de481610d6b41c0a5cc0515504eb9617c5c9763e1bf2c0a8cb. Notarization: dbd06c9d-66de-4d3f-a19b-5e2c1117dca5. Live manifest reports macOS 1.0.64.
  Source: `release` desktop:2fc54348
- **#w-20261121-e47b release | released | normal:** macOS 1.0.65 published
  Published a universal signed, notarized, stapled DMG from source commit 8f56c3da. It includes the DM-32UV shifted-insert extras fix, TK-270G one-based bank positions, current RT-950 Pro work, approved RepeaterBook API search through the server relay, and cumulative driver/UI/bridge compatibility changes. Artifact SHA-256: 6dedceb731cc6bebfa76de76aaaea62cc8e4e4729fc9d5fe4064afce27404bd5. Notarization: b9931c3b-064a-4b8b-b22d-8508e72bdf2f. Live manifest reports macOS 1.0.65.
  Source: `release` desktop:8f56c3da
- **#w-20261121-5acc release | released | normal:** macOS 1.0.66 published
  Published a universal signed, notarized, stapled DMG from source commit ee72c09e. It includes the DM-32UV channel/zone NUL-termination fix, current RT-950 Pro behavior, approved RepeaterBook API search, and cumulative driver/UI/bridge compatibility changes. Artifact SHA-256: 0087cb989e126669d63be4f5eaa94ca80dbc41ecd03b2d81b1091359723893b9. Notarization: a48065c5-5e65-488c-aa7a-0c19fe5c3755. Live manifest reports macOS 1.0.66.
  Source: `release` desktop:ee72c09e

## Quansheng

### UV-K1 & UV-K5 V3 (F4HWN)

- **#w-20261119-7381 enhancement | fix_committed | normal:** F4HWN 7.0.0 firmware profile
  F4HWN 7.0.0 released 2026-11-19. Built-in profile supports v6.3.x only and refuses other F4HWN versions before I/O. Needs analysis of the 7.0 CHIRP module memory map.
  Source: `email` INBOX:809

### UV-K1 (F4HWN 6.3)

- **#w-20261119-8c78 bug | fix_committed | normal:** Image from F4HWN's CHIRP module refused as unsupported model
  Linux 1.0.61: the F4HWN module (imports wx) cannot load, and an image saved by it ('UV-K1 & UV-K5 V3 (F4HWN)', 0xB190 bytes, f4hwn.chirp.v6.3.0.py sha256 a307886d...) was rejected as 'Unsupported model'. Same layout as the built-in profile, which was built from that module.
  Source: `email` INBOX:798

### UV-K1 / UV-K5 V3 (F4HWN 6.3)

- **#19 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: 1,024 channels + 14 VFOs, offline-tested. Write: Program/configuration region only, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:43

### UV-K5 family

- **#18 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: Yes, firmware-ID retry. Write: Stock CHIRP policy. Settings: Stock CHIRP policy. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:42

## QYT

### KT7900D

- **#w-20261122-7972 bug | awaiting_user | normal:** Programming command came back as 8 bytes (likely cable echo, radio silent), shown as 'Bad ack'
  Windows 1.0.66: the 8-byte MSTRING_KT8900D magic returned exactly 8 bytes within the 1.5 s timeout instead of the 50-byte ACK+ident, so btech._do_ident reported 'Bad ack from radio'. Same length as the command, so most likely the cable echo with no radio reply (radio off, cable not fully seated, or wrong port/cable). Bytes not logged in 1.0.66. Trace now labels echo-only replies and the error explains them.
  Source: `email` INBOX:881 <89c3682f-beb1-0f59-885f-48fc9ea7afcb@newchirp.net>

## Radioddity

### DB25-G

- **#42 maintenance | experimental | normal:** Current driver status
  Transport: OEM DB25-G CPS clone serial, 9600 8N1, no DTR/RTS. Read: CPS retry handshake; block framing. Write: 16-byte blocks through 0x30FF; hardware pending. Settings: Stock decoder cross-check. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:66

### DB35-G

- **#74 hardware_validation | awaiting_user | high:** Physical write validation
  Writes remain disabled until an OEM backup, physical read, and controlled inactive-channel write/read-back are supplied.
  Source: `email triage` 2026-11-16
- **#43 maintenance | experimental | normal:** Current driver status
  Transport: OEM clone serial, 115200 8N1. Read: 80 channels + settings. Write: Disabled pending hardware validation. Settings: Basic radio settings. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:67

### GA-510 V2

- **#41 maintenance | experimental | normal:** Current driver status
  Transport: OEM CPS v1.00.36, 57,600 8N1, DTR/RTS. Read: Dynamic five-block `0x5000` image, offline-tested. Write: Mapped 64-byte blocks, offline-tested. Settings: Stock V2 decoder. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:65

### GM-30

- **#88 bug | awaiting_user | normal:** Programming mode returns empty response
  Two GM-30 radios program successfully, but the third returns an empty response to PSEARCH and programming entry on COM7. Compare the same cable and OEM CPS against the failing radio.
  Source: `email` INBOX:734

### GS-10B

- **#w-20261121-c071 bug | awaiting_user | normal:** No response from radio on first read (Windows 1.0.65)
  New GS-10B; five PROGRAMBT80U handshakes on COM5 (earlier COM6) got no reply. Stock CHIRP beta driver radtel_rt900.RadioddityGS10B. Likely cable/seating/port; awaiting OEM-software comparison.
  Source: `mailbox` INBOX:868 <c62a9252-214b-ed41-09c3-a171cfe39eec@newchirp.net>

### GS-5B 1.XX

- **#45 maintenance | experimental | normal:** Current driver status
  Transport: OEM GS-5B Pro CPS v1.1.3 serial, 115200 8N1, DTR/RTS on. Read: 512 channels, offline-tested. Write: All mapped pages, offline-tested. Settings: Preserved, hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:69

### X1 Pro GMRS

- **#44 maintenance | experimental | normal:** Current driver status
  Transport: OEM X1 Pro CPS serial, 115200 8N1, no DTR/RTS. Read: Settings + 30 channel pages, offline-tested. Write: Settings + all 30 channel pages, offline-tested. Settings: Full exposed settings page. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:68

## Radtel

### RT-860

- **#9 maintenance | experimental | normal:** Current driver status
  Transport: iRadio/Iradio clone serial, 115200 8N1 + DTR. Read: 1,024 channels + 256 zones, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:33

### RT-880G

- **#87 bug | awaiting_user | normal:** No response from radio
  Six five-byte read commands received no response from NewChirp 1.0.56 on COM3. Confirm the cable appears as a USB serial device, test the OEM CPS, and report the adapter driver/provider.
  Source: `email` INBOX:733

### RT-950

- **#7 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP-compatible serial, 115200 8N1 + RTS/XON. Read: Yes, designed. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:31

### RT-950 Pro

- **#85 bug | awaiting_user | high:** Stock firmware image aborts on invalid packed frequency
  The read completed and produced an image, but channel decoding stopped at a packed-frequency byte 0xFF. A raw image is required to distinguish empty records from a Pro layout mismatch.
  Source: `email` INBOX:720
- **#w-20261120-43e0 bug | awaiting_user | normal:** RT-950 Pro owner selected RT-950; PROGRAMBT got no response
  1.0.62 Windows COM6, model Radtel_RT-950, three PROGRAMBT tries silent. Notes say 'radtel rt 950 pro', so the RT-950 model was likely the wrong choice.
  Source: `email` INBOX:845
- **#w-20261120-8265 bug | awaiting_user | normal:** macOS read fails at port open with (22, 'Invalid argument')
  1.0.62 on macOS 26.6.2, /dev/cu.usbserial-1420 and /dev/tty.usbserial-1420. EINVAL before any radio traffic (no trace), so pyserial open/termios/RTS-DTR ioctl was rejected by the adapter driver at 115200. Same owner's IC-F60V capture worked in the Web Programmer, possibly with a different cable. App shows the raw errno instead of a cable/driver explanation.
  Source: `email` INBOX:846
- **#w-20261120-9877 bug | fix_committed | high:** After a write, radio beeps on PTT and will not transmit
  Owner of two RT-950 Pros: the one programmed today (likely Web Programmer; desktop failed at port open, w-20261120-8265) beeps on PTT and does not transmit; the unprogrammed one is fine. Experimental write sends the full CPS block set, settings included. Candidates: TX off on the channel, TX outside the radio's TX range (owner's IC-F60V channels are 450-469 MHz commercial), busy lock, or a settings block changed by the write. Need: tool used, channel/frequency, whether any channel transmits, the pre-write backup and a fresh read.
  Source: `email` INBOX:849
- **#w-20261120-36d6 enhancement | released | normal:** Stock-firmware RT-950 Pro over Bluetooth
  Add experimental read-only Android Bluetooth support for the stock RT-950 Pro. The stock CPS 1.3.3 exposes a BT Write switch at function-settings byte 29; iOS/Android programming is advertised but the exact BLE wire behavior still requires app or hardware evidence. Bluetooth writes remain disabled.
  Source: `email` INBOX:854
- **#8 maintenance | experimental | normal:** Current driver status
  Transport: RT-950/BT-9000 clone serial, 115200 8N1 + RTS/DTR. Read: 960 channels + Pro map, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:32

### RT-950 Pro, Bajeton BJ-9000 with nicFW950

- **#w-20261120-0a9e bug | awaiting_user | normal:** Android Bluetooth read: no reply to nicFW950 block read
  Android app, nicFW950 profile over BLE (FFE1, MTU 23, write-without-response session). Driver sends nicFW read aa 30 00 02 05 00 00 (block 0x50200); radio returns 0 of 135 bytes after 15 s; unchanged-block probe fails the same way. BLE link itself is healthy. Most likely the radio runs stock Radtel firmware (nicFW-only command; same pattern as INBOX:781). The mobile app offers Bluetooth only for nicFW950; stock RT-950 Pro is USB cable only. Over BLE the first exchange is the block read, so the friendly 'not running nicFW950' message from the serial baud handshake never appears.
  Source: `email` INBOX:854
- **#10 maintenance | hardware_tested | normal:** Current driver status
  Transport: nicFW serial, 38400 → 460800 8N1. Read: Yes. Write: Changed blocks. Settings: Global settings and group names. Ledger status: Hardware-tested on one 6.00.16c unit; other versions/aliases experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:34

## Retevis

### MA1

- **#62 maintenance | experimental | normal:** Current driver status
  Transport: TYT clone serial, 38400 8N1. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:86

### MA1 model A9305B

- **#63 maintenance | experimental | normal:** Current driver status
  Transport: TYT addressed blocks, 9600 then 57600 8N1. Read: 1,000 channels. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:87

### RA87

- **#w-20261122-8452 bug | fix_committed | normal:** Download refuses an RA87 whose 8-byte ident differs from the two captured fingerprints
  Windows 1.0.66: PROGRAM echoed+ACK, 0x02 returned 1-byte echo + 8-byte ident, then 'Radio identification failed'. The ident bytes are not in the trace (pre-1.0.68). OEM CPS read handshake accepts any 8 bytes (RX VA x8) and identifies the model by byte 0x1F05 (5A/79/A5 per band version); the ident is the image's 0x1F00-0x1F07 block, so byte 5 is that model byte.
  Source: `email` INBOX:888 <47d79ef8-296c-98ac-64fd-6d375374a1f8@newchirp.net>

### RA89

- **#90 bug | awaiting_user | normal:** No response to handshake
  NewChirp 1.0.57 received no response to the TYT handshake on Linux /dev/ttyUSB0. Confirm the cable model and whether the OEM CPS can read the radio.
  Source: `email` INBOX:738
- **#64 maintenance | experimental | normal:** Current driver status
  Transport: OEM addressed blocks, 57,600 8N1, DTR/RTS on. Read: 200 channels + core settings. Write: Yes, offline-tested. Settings: Core settings and startup text. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:88

### RT22

- **#w-20261121-badb bug | fix_committed | normal:** Newer (2025+) RT22 units fail identification
  Older RT22s read; newer units ACK PROGRGS and return an 8-byte ID that matches none of RT22Radio._fileid (P32073, P3\0\0\03, P3207!, 00..F8FF). Trace hid the bytes. Same pattern as upstream CHIRP #6747 (open since 2019). Do not accept an unknown ID blindly: newer units may differ internally. Need the ID bytes and an OEM-software file from a newer unit.
  Source: `mailbox` INBOX:871 <c77a8516-ea89-dc83-e8ac-f177629e63c3@newchirp.net>

### RT97L

- **#11 maintenance | experimental | normal:** Current driver status
  Transport: Stock USB serial, 9600 8N1 + DTR/RTS. Read: Yes, hardware pending. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:35

### RT97L GMRS

- **#99 new_driver | investigating | high:** RT97L GMRS needs its own programming protocol
  Windows 1.0.58: RT97L driver gets no ACK even after STX wake-up. Reporter says the GMRS RT97L uses different OEM software and the standard RT97L Custom software cannot connect either. Reporter uploaded the GMRS programming software and a 2048-byte data file through the site file drop.
  Source: `email` INBOX:786; file drops 9-11

## TIDRADIO

### TD-H3 family

- **#39 maintenance | experimental | normal:** Current driver status
  Transport: OEM-verified TD-H3 clone serial, 38400 8N1. Read: Invalid brightness normalized; five-attempt identity probe. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:63

### TD-H8 fourth-generation

- **#40 maintenance | experimental | normal:** Current driver status
  Transport: ODMaster-verified TD-H8 G4 clone serial, 38,400 8N1. Read: Normal, HAM, and GMRS G4 identities; 151-channel physical read. Write: Official 170-page map, offline-tested. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:64

## TYT

### MD-UV380

- **#36 maintenance | experimental | normal:** Current driver status
  Transport: ST DfuSe USB 0483:DF11 + libusb. Read: 3000 channels + zones. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:60

### TH-350

- **#w-20261122-ad5b bug | awaiting_user | normal:** Channel names shifted across channels: likely TH-350 US radio read as base TH-350
  Linux 1.0.68 read of 40 channels: frequencies correct, names start in one channel and continue in the next, some blank. Base TYT_TH-350 reads 5-byte names at 0x0A30; TYT_TH-350_US reads 8-byte names at 0x0930. Layouts are otherwise identical and match_model cannot tell them apart, so a US radio read as base gives exactly this. Reporter is in the US and used RT Systems. Ask them to read with TH-350 US and send the .img.
  Source: `email` INBOX:894 <42a19195-c6bb-739c-d71e-2dba89860053@newchirp.net>

### TH-9800

- **#65 maintenance | experimental | normal:** Current driver status
  Transport: TYT clone serial, 38400 8N1. Read: Reserved tone values no longer abort the read. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:89

## Wouxun

### KG-689

- **#93 new_driver | awaiting_user | normal:** Legacy KG-689E programming support
  Forum requester has a 2m KG-689 absent from CHIRP and NewChirp. Wouxun Download Center groups KG-689E and KG-699E under a 2010 programming package. Need exact label, cable/port details, and a saved OEM codeplug or radio image.
  Source: `forum` TOPIC:93

### KG-905G Plus

- **#49 maintenance | experimental | normal:** Current driver status
  Transport: Wouxun clone serial, 19200 8N1, DTR on, RTS on. Read: Yes, offline-tested. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:73

### KG-Q10H

- **#50 maintenance | experimental | normal:** Current driver status
  Transport: Wouxun encrypted clone serial, 115200 8N1, DTR on, RTS on. Read: Yes, offline-tested. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:74

### KG-UV8D

- **#48 maintenance | experimental | normal:** Current driver status
  Transport: Wouxun clone serial, 19200 8N1, 64-byte blocks. Read: Reserved DCS words no longer abort channel decode; raw bytes preserved. Write: Stock CHIRP driver, offline round-trip. Settings: Stock CHIRP settings. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:72

### KG-UV9GX Plus

- **#w-20261122-cac2 enhancement | fix_committed | low:** Owner could not find the KG-UV9GX Plus; it uses the KG-UV9GX profile
  Request to add the KG-UV9GX+ (cable, not Bluetooth). Already supported: CHIRP Wouxun_KG-UV9GX on desktop and the Web Programmer KG-UV9GX serial profile; the website catalog says 'KG-UV9GX Plus (use KG-UV9GX)'. The desktop picker search 'KG-UV9GX Plus' found nothing; a search hint now covers it.
  Source: `email` INBOX:896

### KG-UVD1P / KG-UV2D

- **#47 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP clone serial, 9600 8N1. Read: One-second block timeout. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental timing override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:71

## Yaesu

### FT-1900R

- **#w-20261121-fd47 bug | awaiting_user | normal:** Read fails: 'Failed to read header' (macOS 1.0.61)
  macOS 13.7.8, NewChirp 1.0.61, FTDI cable /dev/cu.usbserial-AE9NJ8YH, Yaesu_FT-2900R_1900R driver. Two reads 14-23 s each ended with 'Failed to read header': the radio sent no clone header. That is the usual sign it was not put into clone mode or not told to send (hold MHz(PRI) at power-on, then press LOW(ACC) after clicking Read). Setup is suspected; not a confirmed driver defect.
  Source: `email triage 2026-11-21` INBOX:862

### FT-1D

- **#w-20261122-ddc6 bug | fix_committed | normal:** [BAND] pressed before the port is open: ID block lost, then 'No response from radio'
  Windows 1.0.66, two attempts: the only exchange is the ACK CHIRP writes after _safe_read, which it sends even when nothing arrived. Old CHIRP worked. NewChirp shows the prompt ('After clicking OK, press [BAND]') and only then starts the bridge, which loads all drivers before opening the port; the bridge's ready cue covered only [PTT]/[Send], so an immediate [BAND] press sends the image to a closed port and the radio waits for an ACK. Affects every 'After clicking OK, press [KEY]' Yaesu clone radio (FT-1D, VX-3/6/7/8, FT-817, FT-857, FT-7800, FT-8800, FT-90, FT-1802, FT-1500M, FT-70D, FTM-3200D, FTM-7250D, FT-450).
  Source: `email` INBOX:880 <1dccdb08-b5b6-c3ec-6e24-d7acc8d754c4@newchirp.net>

### FT-1D/2D/3D/5D clone family

- **#5 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP Yaesu clone serial, 38400 8N1. Read: Completion-safe timeout; multi-bank mappings. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:29

### FT-50

- **#69 bug | hardware_tested | high:** Two-stop-bit transport and odd-split write
  The OEM ADMS-1E uses 9600 8N2. A 1.0.56 name-only write and restore committed correctly and preserved all other channels.
  Source: `email` INBOX:722
- **#6 maintenance | hardware_tested | normal:** Current driver status
  Transport: Yaesu clone serial, 9600 8N2. Read: Odd-split channels decode; reporter image verified. Write: Hardware-tested name write and restore; odd-split field write pending. Settings: Stock FT-50 settings. Ledger status: Experimental; partial hardware validation.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:30

### FT-991A

- **#4 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu CAT serial, 4800-38400 auto-baud. Read: 117 live memories. Write: Known channel fields, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:28

### FTM-150R/E/ASP

- **#2 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP clone serial, 38400 8N1. Read: Yes. Write: Yes. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:26

### FTM-7250D

- **#92 bug | fix_committed | high:** Power controls disappear after CSV import and stale channels remain
  After a CSV library replacement, radio capabilities were discarded, hiding transmit power across every band. Full-image upload also relied on an incomplete cleared-location set, so removed channels could remain in the radio image.
  Source: `email` INBOX:746
- **#1 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP Yaesu clone serial, 38400 8N1. Read: Stock CHIRP driver. Write: Corrected Low/Mid/High encoding. Settings: Not exposed by stock driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:25

### FTX-1

- **#3 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu CAT serial, 4800-115200 auto-baud. Read: 999 live memories. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:27

### VX-170

- **#w-20261122-28ff bug | fix_committed | normal:** Read of a 193-channel codeplug from another tool fails to decode: list index out of range
  Linux 1.0.68: clone download completed and saved /tmp/newchirp-5h4w6vr4.img, then channel decoding failed with IndexError. FT-7800-family get_memory indexes TONES (6-bit field, 50 tones), DTCS_CODES (7-bit, 104), TMODES (3-bit, 5), DUPLEX (3-bit, 5) and power levels (2-bit, 3) without bounds checks; a value written by the other tool probably overflows one. The image was not attached (reports cannot carry files) and /tmp may be cleared on reboot. Need the .img to identify the field.
  Source: `email` INBOX:893 <1d1f2c4e-65b8-b971-2ae4-7cb3b6ce4c66@newchirp.net>

### VX-6

- **#66 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu clone serial, 19200 8N1. Read: Unprogrammable stored slots are treated as empty. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:90
