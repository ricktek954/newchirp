# NewChirp driver work ledger

Generated from `database/driver_work/` by `python3 scripts/driver_work.py export`.

Use `python3 scripts/driver_work.py show <id>` for event history.

## Abbree

### AR8118

- **#w-20261126-044a new_driver | awaiting_user | normal:** Support request: Abbree AR8118
  Requested via a Baofeng 5RM bug report (no other details). Not in CHIRP (Abbree AR-518/AR-63/AR-730/AR-869 are) and no public CPS found. Asked for label photo/FCC ID, firmware, and the programming software that came with it.
  Source: `email` mailbox:UID 1035

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

- **#w-20261123-60bd bug | fix_committed | high:** Channels 129+ used a 1000-per-bank layout; QDMR/CPS layout is 128 per bank
  Found while adding the D878UVII. Channel 129 was read/written at 0x00802000 (channel-extension area) instead of 0x00840000. Reads of channels 129+ wrong; a write could overwrite extension records. Desktop and Web Programmer fixed. No hardware reports affected.
  Source: `analysis` QDMR fb9c96af d868uv_codeplug.cc:1618
- **#w-20261128-7604 bug | awaiting_user | normal:** Linux 1.0.79: port reported denied/in use after the read was already transferring
  Ubuntu 24.04, /dev/ttyACM0: read started 17:43:38, transfer began ~17:46:07 (184 frames in 5 s), then a permission-denied/in-use error at 17:46:15. The port had opened, so dialout is unlikely; suspect the device dropping and re-enumerating or ModemManager grabbing the CDC-ACM port. The message wrongly says "could not open".
  Source: `email` mailbox:UID 1082
- **#35 maintenance | experimental | normal:** Current driver status
  Transport: D578UV CPS serial, 115200 8N1. Read: 4000 channels + zones. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:59

### AT-D878UVII Plus

- **#w-20261124-24b4 bug | awaiting_user | normal:** No answer to PROGRAM on Windows COM9
  Windows 10 (19045), 1.0.71, COM9: read stopped at 'Radio returned 0 of 3 bytes while entering program mode'; trace shows PROGRAM and END with no response at all, so the radio never saw the command. Same session as QDMR (PROGRAM -> QX06 at 115200). Likely port/cable/GD virtual COM driver; first desktop read attempt of this experimental read-only driver.
  Source: `email triage 2026-11-24` INBOX:971
- **#w-20261123-2772 new_driver | experimental | normal:** Support the AT-D878UVII Plus (read-only first)
  Forum feature request (topic 'Can you configure a connection to Anytone AT-D878UVII PLUS', 2026-11-21). Owner tried the AT-D578UVIII Plus profile: the radio rebooted harmlessly (driver refuses non-D578 model IDs and leaves PC mode). Same AnyTone serial protocol; different memory map. Plan: official D878UVII Plus CPS REA cross-checked with QDMR's D878UV2 codeplug; read-only driver, website catalog entry and Web Programmer profile.
  Source: `forum` forum:878UVII-feature-request-2026-11-21

## Baofeng

### 5RH Pro / UV-5RH Pro / UV-5RH Plus / UV-5RM Plus v2

- **#84 bug | awaiting_user | high:** Upload receives one-byte response after successful read
  NewChirp 1.0.57 read 21 channels from the radio, then the unchanged upload stopped on two 16-byte commands with incomplete one-byte responses.
  Source: `email` INBOX:718
- **#27 maintenance | experimental | normal:** Current driver status
  Transport: UV-5RH v2 encrypted clone serial, 115200 then 19200 8N1. Read: 640 channels + 10 zones, offline-tested. Write: Full image, offline-tested. Settings: Basic settings and zone names. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:51

### 5RM

- **#95 bug | released | high:** Upload fails on a slot with an out-of-range extra (PTT-ID 0xFF)
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
- **#w-20261123-2763 bug | fix_committed | high:** Read fails: No attribute power in struct memory
  NewChirp 1.0.68 Windows read completed, then decode failed. Stock BaofengCommonHT.get_memory logs _mem.power (nonexistent) when lowpower is not 0/2 on tri-band radios, raising AttributeError. Affects 5RX, UV-S9X3, BF-A58S and any BaofengCommonHT radio with an out-of-range value; also unfixed upstream. Meaning of values 1/3 unknown (no image, CPS not obtainable from BTECH page without a browser).
  Source: `email` INBOX:922
- **#w-20261124-c2eb bug | awaiting_user | high:** Read decodes fail: invalid CTCSS word 6532.8 (rxtone 0xFF30)
  Windows 11 (build 26340), 1.0.71, COM3: read completed (power fix working) then decode failed: '`6532.8' is not a valid value for `ctone''. Stock BaofengCommonHT decodes any tone word >= 0x0258 as CTCSS value/10. Settings also logged 'Failed to load scode value 0: Value for 15 is out of range' (non-fatal). No .img attached.
  Source: `email triage 2026-11-24` INBOX:969

### BF-F8HP

- **#w-20261123-e801 bug | released | normal:** Write never completed, later attempts found the port reserved
  Windows 1.0.67: read and two writes worked; a write started 04:37 logged no completion; later attempts failed 'port reserved by another program', consistent with a hung bridge still holding COM3.
  Source: `email` INBOX:920
- **#w-20261124-c288 bug | closed | normal:** COM5 unavailable: Prolific PL2303TA driver refuses Windows 11
  Windows 11 (build 26300), 1.0.71: 'could not open COM5'; reporter notes Device Manager says the Prolific PL2303TA does not support Windows 11. User-side cable driver, FAQ #cable-driver.
  Source: `email triage 2026-11-24` INBOX:966

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
- **#w-20261121-ab4d bug | released | high:** Write after inserting/moving a channel: blank channel left above it, write froze mid-upload
  Linux (Manjaro, KDE Wayland) 1.0.64: inserting a channel, or moving a channel added at the end up, then writing leaves a blank slot above the inserted channel; the write froze partway and needed a force quit; the radio rebooted and recovered. CPS cleanup restored the radio.
  Source: `email triage 2026-11-21` INBOX:863
- **#w-20261121-6314 bug | pending_validation | normal:** Channel names show leftover text after the NUL terminator ('Channel 1<NUL>t Mode')
  Forum file drop 12 (CSV, 43 channels) shows 9 names with a NUL followed by old bytes, e.g. 'Channel 1\x00t Mode' and 'RPT 15\x00 23'. Stock CHIRP's get_memory only strips trailing NUL/FF/space, so the leftover text shows in NewChirp and in CSV exports; zone get_name and the settings channel-name choices had the same trailing-only strip. The reporter described it as 'adds test to first channel on read'.
  Source: `forum file drop 12, 2026-11-20` forum-file-drop:12 sha256:8b526f78bb13ce4cb7a7e5a05a0dbebce6fbe42ae79b68c51caad4fffa8e40fb
- **#w-20261122-f1fb bug | released | normal:** Frequencies off the tuning-step grid (145.16375 MHz) flagged as unprogrammable
  Linux 1.0.68: reading a codeplug built elsewhere flagged 30 channels, e.g. 145.163750 MHz -> nearest 145.165. The radio holds the frequency; the driver sets has_nostep_tuning (10 Hz storage), which CHIRP's validate_memory honors, but the bridge never exported it and the app's pre-write check applied the 2.5-100 kHz steps. Affects every has_nostep_tuning radio (22 driver files).
  Source: `email` INBOX:895 <84f2a5ed-80a4-2f1a-f7de-971c3e81b271@newchirp.net>
- **#w-20261123-9a28 bug | closed | normal:** Firmware DM32.00.01.048: tone 0x3E08 decoded as 3e8 Hz, whole read failed
  Read completed; decode failed with 30000000.0 not valid for rtone. 0x3E08 is not BCD; stock formats it as '3e08' and parses scientific notation. CPS v1.60 offers CHIRP's 50 tones; OEM data from another radio stores BCD. Image not attached.
  Source: `email` INBOX:907
- **#w-20261128-5455 bug | released | normal:** Write stops on one short 4 KiB flash read ("Bad reply reading flash at 020000")
  macOS 1.0.77, firmware DM32.NRF.01.049, CH340-style /dev/cu.usbserial: two full reads succeeded, then during the write one 0x1000-byte flash read returned 4007 of 4102 bytes after 5 s and the stock driver stopped. Reads are idempotent; the block read is now retried up to 3 times.
  Source: `email` mailbox:UID 1087
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

### UV-21Pro GPS

- **#w-20261126-76d8 bug | awaiting_user | normal:** No response from radio (triage)
  Win 1.0.73 COM7: PROGRAMCOLOR no reply; notes say radio is a 'uv1'; same cable read a UV-82; exact model needed
  Source: `email` INBOX:993

### UV-21Pro V2

- **#w-20261125-1eff bug | awaiting_user | normal:** PROGRAMBFNOR unanswered on COM1
  Windows 10 (19045), 1.0.72, COM1: no reply to PROGRAMBFNOR. COM1 is normally a built-in or virtual serial port, not a USB programming cable.
  Source: `email triage 2026-11-25` INBOX:982

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
- **#w-20261123-23e2 bug | released | normal:** PROGRAMCOLORPROU answered 0x40; stopped as 'Unexpected response'
  Windows 1.0.67. BF-UVs Pro CPS v1.4.7 discards non-ACK bytes and resends the handshake every 1 s up to 5 times.
  Source: `email` INBOX:915
- **#w-20261124-70d9 bug | awaiting_user | normal:** Android Bluetooth: connects but cannot read
  Forum topic 59 posts 208-210: first device failed with UniversalBle unknown error 147; second device connected GATT (trace truncated by the forum after the 1800/1801 services); user reports it connected but cannot read. Need the full Bluetooth diagnostics.
  Source: `forum topic 59 (INBOX:942/944/945)` 
- **#w-20261124-91a3 bug | awaiting_user | normal:** COM13 replies do not look like a UV-32 (repeating pattern, then '-' bytes)
  Windows 1.0.70 COM13: PROGRAMCOLORPROU got '02 24 00 03 00 10 00 03' x2, then silence; a retry got repeated 0x2D. Likely a Bluetooth serial port or other device, not the programming cable.
  Source: `email INBOX:951/952` 

### UV-3R

- **#w-20261125-e5ec bug | released | normal:** Silent radio reports a Python 'cannot access local variable e' error
  Stock uv3r_prep re-raises e after the except block; Python 3 has cleared it. Seen in INBOX:985 while trying models.
  Source: `email` INBOX:985

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
- **#w-20261124-0d1e bug | awaiting_user | normal:** macOS 1.0.68: FTDI cable, no reply to any UV-5R magic
  All wake-up/ident commands got zero bytes back; cable seating or port. Sent plug/volume/port/update steps
  Source: `email` INBOX:959
- **#w-20261125-6f0d bug | awaiting_user | normal:** Read stops at settings block 0x1EC0 after the channels (radio refuses the jump back)
  1.0.73 macOS. 50 BB FF 20 12 07 25 handshake, ident AA 30 76 04 00 05 20 DD. Version reads and channels 0x0000-0x17C0 answered; 0x1EC0 after the channels got no reply. Same as UV-5R, BF-F8HP, UV-5RX3. UV-5RX CPS never reads the settings block after the channels. Fix: read the settings block before the channels.
  Source: `email` INBOX:985

### UV-5R Mini

- **#w-20261122-e807 bug | released | normal:** Read stops when the radio misses one block reply; stock aborts instead of re-requesting
  Windows 1.0.66 (two attempts): COM7 answered PROGRAMCOLOR with 'P' (echoed command, so not the programming cable); COM6 read ~75 68-byte blocks, then one R request got no reply and the read failed. OEM CPS v1.0.7 resends an unanswered block request every 1 s up to five more times; stock CHIRP aborts on the first timeout.
  Source: `email` INBOX:885/886 <2f9de842-1d9b-dc3d-5a27-e45a36374471@newchirp.net> <69ebea44-574d-fd41-9a84-077b4c1c2697@newchirp.net>
- **#w-20261124-87c9 bug | fix_committed | normal:** PROGRAMCOLORPROU answered 'P' (echoed command); stock stops as 'Unexpected response'
  Windows 1.0.70 COM5 (same cable/port read a UV-5RM fine) and macOS 1.0.70: the first handshake byte was 0x50, the start of the echoed PROGRAMCOLORPROU. CPS v1.0.7 HandShake reads byte by byte, ignores non-ACK bytes and resends every 1 s up to 5 times; stock CHIRP reads one byte and aborts. Likely plug not fully seated on the Mini.
  Source: `email INBOX:948/950` 

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
- **#w-20261126-978f bug | awaiting_user | normal:** Read sits at the start on COM4 (v2 and stock profiles), then COM3 not available
  1.0.75 Windows 10 (26100): reads with UV-5RM Plus v2 and UV-5RM Plus on COM4 stayed at 1% for ~30 s each; a later try on COM3 failed because that port does not exist. Report was from the COM3 error, so no trace of the stalled reads. Asked for setup checks and a report from the failing COM4 read.
  Source: `email` mailbox:UID 1040
- **#28 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1 + DTR/RTS. Read: OEM-style handshake retry; stock channel decode. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:52

### UV-5RM Plus v2

- **#w-20261119-d555 bug | fix_committed | high:** Writes to zones 2-3 reported in zone 1
  Reporter (first v2 hardware read) says frequencies written in zone 2 or 3 land in zone 1, and edits cannot span zones before a write. Offline bridge replay places a zone 2 edit at channel 65 and CPS V1.17 uses the same zone*64+slot IDs. Added EnZone (0x73 bit 2) handling; need the reporter's image and what the radio shows.
  Source: `email` INBOX:807

### UV-5RM Pro

- **#w-20261125-2905 new_driver | hardware_tested | normal:** Support the UV-5RM Pro (firmware 1.0.94)
  Windows 11 (26300), 1.0.72, COM5, model 5RH Pro selected: the 16-byte magic was answered e0 then 41, and the 8-byte command 4e ('N'), so the radio talks but refuses the 5RH Pro handshake. Owner reports UV-5RM PRO, firmware 1_0_94, hardware 1_0_0. Not in CHIRP. Next: OEM CPS REA.
  Source: `email triage 2026-11-25` INBOX:978

### UV-82

- **#w-20261123-17cf bug | awaiting_user | normal:** Radio stops answering after five successful writes
  Windows, 1.0.69, COM7: one read and five writes succeeded 14:40-16:24, then every ident attempt got no reply (write and read). Same port and session; points to plug seating, battery or the radio needing a power cycle.
  Source: `email:INBOX:928-930` <229ff3ec-97d4-953c-d854-ae317736d42b@newchirp.net>
- **#w-20261126-7f13 bug | awaiting_user | normal:** Writing an older saved image: 'Image not supported by radio' gives no way forward
  Win 1.0.73: read radio (21 ch), then opened a saved .img (86 ch) and wrote it; stock uv5r refuses because the image's aux area differs from this dropped-byte radio. Correct safety behavior; message now explains the CSV route. FAQ #image-from-another-radio.
  Source: `email` INBOX:991

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

- **#w-20261128-ac5c bug | awaiting_user | normal:** First physical read: cable echoes the identify frame, radio silent
  Windows 1.0.77 COM3: "Icom identify (10 bytes) | echo only". The attached image is our CS-41S sample (SHA-256 eb3dd05b...), not the radio. CS-41S user manual: connect the cable to [SP] first, then power on with [VOL]; NewChirp prompts said the opposite order. Prompts fixed; ask the owner to retry in that order.
  Source: `email` mailbox:UID 1090
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

### IC-7400

- **#w-20261126-bfc0 bug | closed | normal:** Read times out: no CI-V echo, no radio reply
  1.0.75 Windows COM3 (same cable as the reporter's IC-910): one stray byte, then no echo and no reply to 1a/00 at 66h. A CI-V interface that does not echo is usually not on a powered bus (radio off or cable not seated) or the USB adapter needs replugging. Asked for setup checks.
  Source: `email` mailbox:UID 1031

### IC-746PRO

- **#55 maintenance | experimental | normal:** Current driver status
  Transport: Icom CI-V serial, 9600 8N1. Read: Stock IC-746 family logic. Write: Stock IC-746 family logic. Settings: Stock IC-746 family logic. Ledger status: Experimental model profile.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:79

### IC-910

- **#w-20261119-c2a9 bug | closed | high:** Read stops on unset CTCSS tone (rtone 0.0)
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

- **#w-20261126-7766 bug | awaiting_user | normal:** Read succeeds but channel map decode fails: list index out of range
  1.0.74 Windows read the full image (28246 wire bytes) then the stock icx90 get_memory indexed a table with an out-of-range bitfield (mode 2 bits/3 values, tone mode 3/4, step 4/13, tones 6/50, DTCS 8/104). No image attached. Lookups are now bounded and logged so one channel cannot stop the list; the image is needed to identify the field.
  Source: `email` mailbox:UID 1017
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

### ID-5100

- **#w-20261123-6995 bug | fix_committed | normal:** Read fails: 'DTCS-T' is not in valid list
  Stock id5100.py decodes tone mode 8 as 'DTCS-T' (DTCS encode only) and 2/4 as '2??'/'4??' (pocket beep), none valid CHIRP tone modes, so one such channel aborts the whole channel decode. Override maps DTCS-T to Cross 'DTCS->', pocket-beep TSQL/DTCS to TSQL/DTCS (kept on unchanged write-back), undefined values to no tone, and offers TSQL-R/DTCS-R. Covers ID-4100 too. No image attached.
  Source: `email` INBOX:940 <64a8cf78-71ea-6553-ee6d-dbdeb1de4f93@newchirp.net>
- **#w-20261126-fdb2 bug | awaiting_user | normal:** No response from radio (triage)
  Win 1.0.73 COM5: Icom identify got no reply; cable/clone-mode details needed
  Source: `email` INBOX:1002

### ID-52

- **#57 maintenance | experimental | normal:** Current driver status
  Transport: Icom `IcomCloneFormat3` serial, 9600 8N1. Read: Yes, transport verified. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:81

## Kenwood

### TH-D7

- **#w-20261124-db43 bug | awaiting_user | normal:** TH-D7G read as TH-D7 stops at 'Radio reports TH-D7G' with no next step
  Windows 10, 1.0.62, COM9: model TH-D7 selected; kenwood_d7 ID check got TH-D7G and raised 'Radio reports TH-D7G (not TH-D7)'. CHIRP has a separate Kenwood_TH-D7G driver; the user needs that model, but the error did not say so.
  Source: `email triage 2026-11-24` INBOX:967

### TH-D75

- **#w-20261123-e0ef bug | awaiting_user | normal:** No reply to ID on macOS USB (notes say TH-75A)
  1.0.70 macOS /dev/cu.usbmodem: no reply to ID at 9600-57600. Notes say TH-75A (no PC programming) but the CDC port fits a TH-D75. Likely setup: KISS/TNC or GPS PC Output (Menu 405) on the USB port, another app holding the port, or a charge-only cable. Asked to confirm the model.
  Source: `email:INBOX:935` <1871f05d-91dc-1a87-21db-010a43348b40@newchirp.net>
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
- **#w-20261120-8af9 bug | released | high:** Last channel missing after write: 0-based bank positions collide with KPG 1-based positions
  1.0.63 writes without error but the last channel in the list (ch 25) is not usable on the radio (INBOX:855). Evidence: CHIRP's OEM-style TK-760G sample image stores each record's bnumb as the 1-based position within its bank, matching the 0x300 table (bank, pos, bank-1, slot). NewChirp (from stock tk760g) assigns new channels bnumb = slot-1 and normalizes the 0x80 sentinel (reporter's ch 24, INBOX:808) to slot-1, i.e. 0-based. With KPG-programmed channels at positions 1..N, the newcomer duplicates position N and position N+1 is empty, so the last channel drops. _prep_data rebuilds 0x300 by slot order and never updates record bnumb. Secondary suspect: 0x7000 per-channel flags filled by count, not slot. Plan: renumber each bank's records 1..n (existing valid order first, then new channels) and build 0x300 from that order; confirm with the reporter's image.
  Source: `email` INBOX:855
- **#60 maintenance | experimental | normal:** Current driver status
  Transport: Kenwood Series 60G clone serial, 9600 8E1. Read: NewChirp decode with raw-preserving invalid-index normalization. Write: NewChirp write path with bank-state validation and transient checksum retry; offline-tested. Settings: Stock driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:84

### TK-3101

- **#w-20261126-565d new_driver | awaiting_user | normal:** Support the Kenwood TK-3101
  Owner request; not in upstream CHIRP. Need the OEM programming software and a sample data file to REA.
  Source: `email` INBOX:999

### TK-3401D

- **#14 maintenance | experimental | normal:** Current driver status
  Transport: KPG-171D clone serial, 9600 then 19200 baud. Read: Yes, provisional record scan. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:38

### TK-350

- **#71 bug | released | high:** Identity request receives zero bytes
  Zero identity bytes were observed on COM3 and COM4. The driver now retries the bounded 0x02 identity request three times for late PC mode.
  Source: `email` INBOX:727-728
- **#w-20261126-dc72 bug | pending_validation | high:** Full read completes but shows 0 channels
  1.0.74 read the whole image from the owner's TK-350 but every slot showed empty. The driver hid channels outside 450-470 MHz. KPG-23D files saved in QEMU for 450-470 (sample.u1f) and 400-430 MHz (sample.u4f) prove the word encoding is band-independent; the band digit sits at 0x0D05 (P350n). Fix decodes all UHF bands; Web Programmer updated.
  Source: `email` mailbox:UID 1011
- **#w-20261127-edf2 bug | awaiting_user | high:** 5 kHz channels decoded and written as 6.25 kHz (edited ch114 will not transmit)
  Owner's 1.0.76 write of ch114 to 430.0125 left the radio on 353.020/344.010: record byte 13 bits 5 (RX) / 6 (TX) select 6.25 vs 5 kHz steps and ch114 is a 5 kHz channel (80). NewChirp ignored the bits. Channel 121 add refused as designed; CSV re-import refused (no tones).
  Source: `email` mailbox:UID 1055,1056
- **#w-20261127-eff6 bug | closed | high:** Edited ch1 (430.0875/433.0875/431.0875 simplex) has no RX or TX
  1.0.77 Windows: ch1 changed from 433.000/434.600 tone 77.0 to simplex 430.0875 + Tone 114.8, then 433.0875 no tone, then 431.0875 + 114.8; owner reports no RX/TX. Records (a6 40 ce 5c / 86 42 ae 5e / 46 41 6e 5d, byte13 E0) use the same encoding as the radio's own working simplex ch81-110; only ch1 and ch114 bytes differ from the original image; frequencies inside the radio's original 427.475-438.55 span. Cause not found offline; controlled test requested.
  Source: `email` mailbox:UID 1060
- **#w-20261127-dc5d enhancement | open | normal:** DQT (DCS) tone read/write
  Owner requests DCS/DQT tones. QT words with bits 15-14 != 11 are DQT and not decoded; needs KPG-23D trace of the DQT word encoding before writes.
  Source: `email` mailbox:UID 1067
- **#w-20261127-75b5 enhancement | open | normal:** Add channels to empty slots (ch121+, 15-channel radio ch16)
  Owner tried adding ch121/122 on the 120-channel radio and importing a 24-row CSV into a second TK-350 (P350S 00, 15 channels, 449 MHz); both refused by design. Needs the CPS channel/scan tables (0x0D40 bitmap, channel count) traced. Owner also asks for the CPS's 'Full 160ch UHF 327-550 MHz' range (driver allows 400-520).
  Source: `email` mailbox:UID 1066
- **#15 maintenance | experimental | normal:** Current driver status
  Transport: KPG-23D clone serial, 9600 8N1, 0xF000 addressed blocks. Read: Yes, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:39

### TK-359

- **#79 bug | released | normal:** No identity response in PC mode
  Support diagnostics sent; waiting for cable, COM-port, and OEM programmer comparison.
  Source: `email` INBOX:699-700
- **#w-20261126-95c9 bug | awaiting_user | high:** Z fill reply rejected; channel records decoded from the wrong offset
  Real TK-359 answers uniform blocks with Z + echo + one fill byte (KPG32D.EXE 0x16468, Z at DS:0x32DF); 1.0.74 rejected it. Channel records are 32 bytes at 0x3400 with flag-byte frequencies (bit7 6.25 kHz, bit0 step bit 16), verified with uhf359.fdt saved by KPG-32D (460.0125/465.000, 455.500); the old decode read unused offset 0.
  Source: `email` mailbox:UID 1014
- **#16 maintenance | experimental | normal:** Current driver status
  Transport: KPG-32D clone serial, 9600 8N1, 0xF000 addressed blocks. Read: Yes, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental read-only.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:40

### TK-863G

- **#w-20261124-dbed bug | fix_committed | normal:** Read stops at 0x7C memory session: 0 of 2 bytes
  Linux 1.0.72: PROGRAM, M0863 identity and a valid NRK record, then no reply to 0x7C. KPG-76D 0x403110 sets a 3000 ms read timeout (SetCommTimeouts helper 0x401340, not a sleep), sends 0x7C immediately and reads 2 bytes; the driver slept 3 s and then allowed 1 s. CPS framing is 9600,N,8,2; the driver used even parity.
  Source: `email INBOX:943` 
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

- **#w-20261128-2bb1 bug | released | normal:** CSV with every line wrapped in quotes rejected as having no Frequency column
  Windows 1.0.66: a GMRS-provided CHIRP.csv failed with "no Frequency column (columns found: Location,Name,Frequency,...)". The columns are listed without spaces, so the whole header was one quoted cell: the file has each line wrapped in quotes (a spreadsheet that kept each line in column A). Decode now re-splits one-field rows.
  Source: `email` mailbox:UID 1084
- **#w-20261120-393e enhancement | fix_committed | normal:** Collapsible Channel Library summary cards
  UV-32 owner asked to collapse the Channels / Scan enabled / Needs attention cards to see more channels.
  Source: `email` INBOX:834
- **#w-20261123-d293 enhancement | fix_committed | normal:** Write settings to radio disabled after a write
  Owner programming several identical radios had to edit and revert a setting to re-enable the button. Button now stays enabled; with no edits it confirms writing the whole snapshot again.
  Source: `email:INBOX:931` <001f01dd7b6e$3f4d9150$bde8b3f0$@gmail.com>
- **#w-20261124-8c3d enhancement | released | normal:** Write greyed out for a channel file opened before reading the radio; status text did not explain
  Read-first rule kept (avoids writing an old stored image's settings); status text now says to read the radio first
  Source: `email` INBOX:958
- **#w-20261124-970b enhancement | released | normal:** PMR446 (Europe) table in the Frequency Reference
  16 analogue channels with ECC/DEC/(15)05 licence-free conditions and printable PDF
  Source: `email` INBOX:960
- **#w-20261125-b6b9 enhancement | awaiting_user | normal:** Import CSV with No./Channel Name/Channel Type/RX Frequency[MHz] columns
  Windows 11 (26300), 1.0.72, model 5RM: CSV from an associate rejected as not CHIRP format; columns No., Channel Name, Channel Type, RX Frequency[MHz], TX Frequency[MHz], Power, Band Width, Scan List (a vendor CPS export, likely DMR-style 'Channel Type'). Needs the file to identify the CPS and add an importer.
  Source: `email triage 2026-11-25` INBOX:981

### Desktop app

- **#w-20261126-0c01 bug | released | normal:** Find Repeaters: results scroll bar does not scroll the list on Windows
  1.0.75 Windows 11: the visible vertical bar belonged to the dialog page and sat over the results list's edge, so dragging it did not move the results; only Tab reached more. Results list now has its own interactive bar inset from the page bar; Windows-platform widget test drags it.
  Source: `email` mailbox:UID 1036
- **#w-20261122-685e enhancement | released | low:** Print the channel list
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
- **#w-20261122-0a10 release | released | normal:** Linux 1.0.69 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 5dd9aa67. The release adds the experimental Retevis RA87 driver; fixes Retevis RT22 identification and Web Programmer mapping; adds the UV-5R Mini driver and OEM-style block retry; decodes Yaesu VX-170/VX-177 split tones; adds channel-list PDF printing; hardens radio-key clone readiness and stale-input flushing; fixes TK-270G bank counts; and updates UV-K60 Plus and F4HWN 7.0 behavior. Verification: all 249 Flutter tests passed; 597 Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; package payloads include the four release drivers and omit GLVND/EGL/GLES loaders; the embedded version and public Linux 1.0.69 manifest were verified. Package SHA-256 values: 18890608dadda95a0b4601cb376acd983958dc0947a075b7daa823d77c4060e0, f47c61949b62b60b276e6462d433ffb7a172f81c27dc9ca1e97cc98feae6ada8, 15be796f559b3f184308e8dd74899f79b5e9a6c2cc527dc6dd9bf178792f20d8, and fd7164a91f42a7d0a45871512e826b28de5f4cb503757be9cac6facbba7e9abe.
  Source: `release` desktop:5dd9aa67
- **#w-20261123-9236 release | released | normal:** Linux 1.0.70 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 76de9782. The release adds a write watchdog that ends stalled radio operations, treats malformed or out-of-range tone fields as no tone without rewriting them on DM-32UV, RT-950, and UV-17ProGPS images, and retries the UV-32/UV-5RM Plus handshake. It carries the latest Android USB and proxy broken-pipe triage plus all intervening driver-work records. Verification: flutter analyze passed; all 249 Flutter tests passed with the bundled Python 3.13 runtime; 605 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.70 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the changed drivers and bridge code and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.70. Package SHA-256 values: 2bdae61e142ec25efc3199a71ec3a95e782b9342253c7c7c638186f23d12d66a, d2cd41886d279e467f7aefba08d03cea6f0ea09b4cd2e3b77f33bc80d2c15f7c, d7faf36fcabe83dd02b1d0df1c4cb0b5077b21f31bd26dc52d2c2ef62ea0fcbe, and 895ec1bb9cc2b7706c35c7b918ac5ae1eb8b1372c2390a69f6c39e5ed2e4a68f.
  Source: `release` desktop:76de9782
- **#w-20261123-6cd4 release | released | normal:** Linux 1.0.71 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 98309c23. The release adds the read-only AnyTone AT-D878UVII Plus driver, fixes AnyTone D578 channel-bank sizing, adds the read-only Quansheng UV-K5 Robzyl RO-KO 512K profile, encodes Baofeng 5RX/UV-S9X3 channel power as the CPS does, and keeps unknown Baofeng power values readable without rewriting them. Verification: flutter analyze passed; all 249 Flutter tests passed with the bundled Python 3.13 runtime; 618 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.71 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the new drivers and power handling and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.71. Package SHA-256 values: 61d3e9b6f5f2d9a013bfd7e963ce2ea808d1c104fd2c865bbe58cb58cfaaa6dc, 67059796d48aa5c4daef76db0fa69d178a65564d78ca8dc2893ccca8771c45a4, 9796efebdab17374cb56d99f0e41598a5ac5fd4859caaf7f0e852dd620e7f019, and dcd91cc86a283a4ca415007d033048954755c3bb7d5f3f54c1fd650274f1aeea.
  Source: `release` desktop:98309c23
- **#w-20261123-bf5e release | released | normal:** Linux 1.0.72 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 6704d9bb. The release preserves the selected radio zone when replacing the channel list and allows repeat radio-settings writes. It also carries the RT22 tone and deployment updates plus the UV-5RM Plus zone, UV-82, KG-689, and settings-button report and reply records. Verification: flutter analyze passed; all 249 Flutter tests passed with the bundled Python 3.13 runtime; 618 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.72 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.72. Package SHA-256 values: 6903bbc19dc4a0d8ebf826287451e96696220a4df08540ba2ee271f4373c6605, 60a74750fb66bacf1b2cc2d02c6ea9c27cca40d5fcea53fcdde216f4f86d5c89, eaf12f5fe21c997b87f29aca8c979e0db680d1cac73402fc4add9117a01b5049, and e34cc9ce28b344bf3f82fb7351631947eff5c1c14a0f7f708737b2f6a5fe7396.
  Source: `release` desktop:6704d9bb
- **#w-20261124-4419 release | released | normal:** Linux 1.0.73 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit b8dd8004. The release adds Spanish and French beta interface translations, offers channel-name shortening for radio limits, resynchronizes FT-70D clone reads on the AH51G identifier, decodes Icom ID-5100 DTCS-T and pocket-beep tones, adds the TIDRADIO TD-H9 Normal/HAM/GMRS driver on the TD-H8 G4 transport, matches OEM memory-session timing for TK-863G, updates UV-5R Mini handshakes, and reuses loaded bridge drivers across reloads. Verification: flutter analyze passed; all 253 Flutter tests passed with the bundled Python 3.13 runtime; 636 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.73 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the TD-H9, UV-5RM Plus, TK-863G, and bridge updates and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.73. Package SHA-256 values: 3f0b742e9fe3e0b188d1a574d3c9d9743d60c2855fcfb735930c6c6762f0a914, bea404982c8bec2ec63f107888f129dcf8eaa63997d06cf942ad3967402b5189, 49739a2e85308e9a6ea3273c72100d958753cb0c4f7fecf832505d122f7eaade, and 93b0f1e1225f6033e6d532561454473602872f87e48317ec71a37fa379b6b56e.
  Source: `release` desktop:b8dd8004
- **#w-20261124-a1bc release | released | normal:** Linux 1.0.74 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 76519b2d. The release adds the experimental Ferrite RT-950 Pro link-protocol driver and web profile; renders corrupt Baofeng tone words as no tone; names the refused channel and write progress for live-radio refusals; adds FT-60 clone/cable guidance, sibling-model selection, and AnyTone USB guidance; prefers XWayland on Linux; adds the PMR446 frequency reference; and includes TH-D7G, UV-5R Mini, AT-D878UVII Plus, 5RX, and Wayland follow-up fixes. Verification: flutter analyze passed; all 254 Flutter tests passed with the bundled Python 3.13 runtime; 653 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.74 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include Ferrite, Baofeng tone handling, PMR446, and bridge updates and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.74. Package SHA-256 values: c07aade70cc9efb115336f5a09e78a4ed3b64bfa90feec8f2b5c07d986ddbe87, 06e3fa3c80c5ce7eb2fcde11dd5645cdfa53c1ebae087c85e3917597448008d5, 02658d6459f53b684bbe42f9b102980884e8cc1b99d64e4071c5a072f7c67978, and 294483a0c8f92ca825332cec669b6c21db239294b7f60e56ffadef931e2163a6.
  Source: `release` desktop:76519b2d
- **#w-20261125-d644 release | released | normal:** Linux 1.0.75 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 79b693a5. The release fixes RT-950 Pro Ferrite zone reads by ending READ_MANY cleanly when the radio returns an empty non-advancing answer, and preserves an undecodable Baofeng 5RX S-CODE value for the repair step instead of stopping the write. Verification: flutter analyze passed; all 254 Flutter tests passed with the bundled Python 3.13 runtime; 654 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.75 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include both fixes and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.75. Package SHA-256 values: 05fb23dda2e7de0bee2c1166b2bea1c61590d0439ea714a9bf6628ac06d2b8b9, 7fa461d62bd8d4676a712abcf9ddb7a5933ba67258947c035bd8b96bbe66ee46, 31ea654a6247256626d95140cbdc22ddf5c9428a10fe5aeed7e7c08085b9029d, and 49b6a837b90cf2b33899d0db2ab866e9a6a672cfee3ea807d039eb6599c72495.
  Source: `release` desktop:79b693a5
- **#w-20261126-83e1 release | released | normal:** Linux 1.0.76 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit ab66c0d7. The release adds the KPG-23D TK-350 session and KPG-32D TK-359 session with OEM DTR/RTS behavior; reads UV-5R settings before channels for radios that reject the jump back; reports the real UV-3R handshake error; accepts a 32-byte MD-UV380 DFU identity while keeping memory reads strict; retries the TK-863G 0x7C memory session like KPG-76D and reports received bytes; and explains the safe CSV route when a full image belongs to a different UV-5R radio. Verification: flutter analyze passed; all 254 Flutter tests passed with the bundled Python 3.13 runtime; 672 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.76 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the new KPG, UV-5R, UV-3R, DFU, bridge, and TK-863G changes and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.76. Package SHA-256 values: 3170f5a782647293747f5a93a64b2a297deb5b03a8d17be0b1edd2ca73cf6f49, 1aca797940d07b5949a188fde408b89fc22791f888c91cc2314c55230b83f73c, 467a9aa3a7032934dbcf982269fc73733e39088abe136a8bde5e13afa5a6a059, and 275d66593a360bc2702856a17e4a7f4ddf3744c1182b89a2241e418f7369f957.
  Source: `release` desktop:ab66c0d7
- **#w-20261126-87b7 release | released | normal:** Linux 1.0.77 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 8a24cd2f. The release decodes TK-350 channels across all UHF bands instead of hiding them, handles the TK-359 uniform Z-plus-fill block and uses the KPG-32D 32-byte channel records with flag-byte frequencies, and bounds IC-E90 table lookups so one out-of-table channel value cannot stop the channel list. Verification: flutter analyze passed; all 254 Flutter tests passed with the bundled Python 3.13 runtime; 677 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.77 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the TK-350, TK-359, and IC-E90 decoder changes and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.77. Package SHA-256 values: aefe1289b33eeb5a9b998daa62dcfbef05c804855d1e908b1802e7a5b75cef5e, 5225239ab8b6a64065bafa629426dae4cee1b104d8cabe77143e20aac9c939d8, 1e5b76ee86a5582ecff4f9d49e0ce54830ff2b2bff35b23596a87cabffb3de7d, and 919db7e723e3f47231f7758483b5014a48154c727f9382bd3d834faa4a46f485.
  Source: `release` desktop:8a24cd2f
- **#w-20261126-c9a6 release | released | normal:** Linux 1.0.78 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 3d16733f. The release decodes channels one at a time and reports undecodable slots instead of failing the whole list, lets bug reports attach the radio image, enables the experimental TK-350 write path and decodes/preserves its CTCSS tones, adds the UV-5RM Pro plain-PROGRAM synchronization fallback, and gives the Find Repeaters results list its own scroll bar. Verification: flutter analyze passed; all 257 Flutter tests passed with the bundled Python 3.13 runtime; 693 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.78 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the per-channel decode, image-report, TK-350, UV-5RM Pro, and Repeater UI changes and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.78. Package SHA-256 values: 25bdf0a5781d8d773cc9404e84e2a890d8c11a543bf3b9557137224ffe13c60a, b6faf0562f8d81e9190868fae5d92ef1f7d231b3dc37ecac28ac1fae3e1ce569, 2ceb67a0294f180f582495d2c7c6db5d3c5529495a0aff47b81098159954756a, and 6d4f7c15b3e23b48f19033e354baa0c3c5c2e9c2e5d7cc1549af3f6fb3d6c013.
  Source: `release` desktop:3d16733f
- **#w-20261127-df60 release | released | normal:** Linux 1.0.79 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit d1665f13. The release adds the Quansheng TK11 OEM login/session flow before uploads, decodes and writes TK-350 5 kHz channels by their step bits and writes CTCSS tones, and makes UV-5RM Pro/5RH Pro announce at 19200 first while skipping stray bytes before the sync acknowledgement as the v1.12 CPS does. Verification: flutter analyze passed; all 257 Flutter tests passed with the bundled Python 3.13 runtime; 701 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.79 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the TK11, TK-350, and UV-5RM Pro changes and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.79. Package SHA-256 values: a6864bd263e2b32b15cc66dd76f164c86ee2bb7426a62fb069e65f8290a6f64f, 3e349d34dbcf5ccf185e6ac6baf201bdfde4f3f96e9da87cef4299c3bfd7e50f, 306aecb74cff4af8c3d4b3df2170a3928b9689fa8eeb68e35de0eecb729353a6, and 6190fa6a17e928b68b4de5b15f00fe44c30c24c782cf1bcbc46c64c8d9bd0804.
  Source: `release` desktop:d1665f13
- **#w-20261128-d9da release | released | normal:** Linux 1.0.80 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit 35d6776a. The release adopts upstream CHIRP f28d9202 with 99 upstream commits, adds the upstream-review and pinned-catalog export tooling, keeps NewChirp driver precedence, fixes TK-359 6.25 kHz decoding/name order/TX display, aligns MD-UV380 DFU writes with dmrconfig/QDMR, retries short DM-32UV flash reads, and accepts CSV files whose rows are each wrapped as one quoted field. New upstream radios include BTECH UV-PRO, Kenwood TH-K20/TM-D750, Yaesu FTM-150E, and Zastone ZT-D9000. Verification: flutter analyze passed; all 258 Flutter tests passed with the bundled Python 3.13 runtime; 722 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; DEB, RPM, and Pacman metadata and embedded version 1.0.80 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads include the new CHIRP pin, TK-359, MD-UV380, DM-32UV, and CSV changes and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.80. Package SHA-256 values: 99f674f668593f80018e8b0ade7319e5b6dd4139909de0271672d2a137430c85, e84f7f06660edbcd060c2219d58eeb71e500d1b3a1df9349485c4e6282c71764, 08b83b009d6cef8e809f4940a45431c0f4927f65b4a32fbbda7462e9ffbe82eb, and cba2d247e5f505818554568d8a0410f3e36c9a5b7f18fc6e47f959cd11ae1c37.
  Source: `release` desktop:35d6776a
- **#w-20261128-88a4 release | released | normal:** Linux 1.0.81 published
  Published DEB, RPM, AppImage, and Pacman packages from source commit c2a12382. The release keeps NewChirp drivers in a dedicated newchirp_drivers folder beside CHIRP and loads them after upstream drivers, so all 75 NewChirp driver IDs take precedence in packaged builds; it adds the driver-bundle verification gate to Linux packaging and carries the upstream CHIRP f28d9202 changes. Verification: flutter analyze passed; all 259 Flutter tests passed with the bundled Python 3.13 runtime; 726 bundled Python tests passed with two fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum GLIBC 2.18; the bundle-driver gate loaded 621 models across 64 vendors with zero problems and preserved all 75 NewChirp IDs; DEB, RPM, and Pacman metadata and embedded version 1.0.81 were verified; DEB and AppImage Xvfb smoke tests passed; the AppImage launched under host Wayland and X11; package payloads contain the dedicated driver folder, have no newchirp driver mixed into chirp/drivers, and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the Linux platform manifest reports 1.0.81. Package SHA-256 values: bb1f8418f44788925b849a337b28a4858a06e3842158dedfe1b4447cb2be62f8, 588deec35d4aec9c0492bceb0c919efeb29bdc581a25ce64abef45d5869cedfa, c92a8c92ed1aa227f2cf1c3b05603c9d9fc4c9e9bbee833bdbfaf6984c06ae23, and 67b02634b02030d07fb0860a253b6e2418e097e736c94f7862a708d077a16e6a.
  Source: `release` desktop:c2a12382

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
- **#w-20261122-cd4e release | released | normal:** macOS 1.0.67 published
  Published a universal signed and notarized DMG from source commit 8e03e24b. It includes the cumulative driver, UI, bridge, trace, printing, and write-progress fixes after 1.0.66, including FTM-300DR and F4HWN 7.0, RT22, DM-32UV progress/cancel, UV-K60 Plus, RA87, UV-5R Mini, VX-170, TH-350, and no-step tuning work. Artifact SHA-256: 250f68ae8fe5d2be54e0e73956277e5ba114c5f6dd4258eb35763e41722b7f22. Apple notarization: 653b46a8-5cd8-43e5-bea0-da202daa2832. The DMG launched from the mounted image; local/server/public hashes matched and the live manifest reports macOS 1.0.67.
  Source: `release` desktop:8e03e24b
- **#w-20261123-22e6 release | released | normal:** macOS 1.0.68 published
  Published a universal signed and notarized DMG from source commit 48f56627. It includes stalled-write watchdog termination with diagnostic details, safe decoding of unreadable DM-32UV and RT-950 tone values, UV-32 handshake retries, Android USB broken-pipe handling, and the cumulative 1.0.67 driver, UI, bridge, trace, printing, and write-progress changes. Artifact SHA-256: 3fd6068c5750adcb1d3a53928e41cddaab789394989d60ee9b76f321e334c47d. Apple notarization: ad8c3d81-e2f2-493a-a972-cb34f65952ea. The DMG launched from the mounted image; local/server/public hashes matched and the live manifest reports macOS 1.0.68.
  Source: `release` desktop:48f56627
- **#w-20261123-218b release | released | normal:** macOS 1.0.69 published
  Published a universal signed and notarized DMG from source commit 0f7f9048. It adds the read-only UV-K5 Robzyl RO-KO 512K profile, AT-D878UVII Plus support with the D578 second-bank mapping fix, Baofeng 5RX OEM power encoding, safe handling of unknown Baofeng power values, and the cumulative 1.0.68 watchdog, tone, UV-32, Android USB, driver, trace, printing, and write-progress changes. Artifact SHA-256: 38aae79413d8775d704a5b9197f828f11f982ebc354f9ec702560f71cdf298ab. Apple notarization: baa15c49-30d7-4b03-986b-a30fc5dbe577. The DMG launched from the mounted image; local/server/public hashes matched and the live manifest reports macOS 1.0.69.
  Source: `release` desktop:0f7f9048
- **#w-20261123-8e17 release | released | normal:** macOS 1.0.70 published
  Published a universal signed and notarized DMG from source commit b6fbc544. It preserves the active radio zone when replacing the channel list, allows repeated radio-settings writes, adds RT22 tone and UV-5RM Plus zone fixes, applies UV-82 and KG-689 settings-button corrections, and carries the cumulative 1.0.69 drivers, watchdog, tone handling, Android USB, UI, bridge, trace, printing, and write-progress changes. Artifact SHA-256: 93c57aea40bf5d03f6fa65007a7d0a4af14f41b1b9a11f1b5423cc801a9d2202. Apple notarization: c763ad92-b1db-4a94-9110-757a471ab3f0. The DMG launched from the mounted image; local/server/public hashes matched and the live manifest reports macOS 1.0.70.
  Source: `release` desktop:b6fbc544
- **#w-20261124-7616 release | released | normal:** macOS 1.0.71 published
  Published a universal signed and notarized DMG from source commit 876c765b. It adds TIDRADIO TD-H9 Normal, HAM, and GMRS profiles on the TD-H8 G4 transport, matches TK-863G OEM memory-session timing, improves UV-5R Mini echo and handshake recovery, preserves the selected zone during list replacement, and includes the cumulative 1.0.70 UI, driver, bridge, Android USB, trace, printing, and write-progress changes. The bridge now reuses loaded NewChirp driver modules for the same file path instead of re-registering duplicate classes. Artifact SHA-256: cb0bc91f4c1268cd13859170ca329e08c8ba65c606840d68c6541538e8b2ae8b. Apple notarization: 11a7e4f4-f0b4-4bec-bffa-e89561f2a606. The DMG launched from the mounted image; local/server/public hashes matched and the live manifest reports macOS 1.0.71.
  Source: `release` desktop:876c765b
- **#w-20261124-fc58 release | released | normal:** macOS 1.0.72 published
  Published a universal signed and notarized DMG from source commit d502504e. It adds the experimental Ferrite protocol driver for the RT-950 Pro, a PMR446 frequency reference, FT-60 clone-entry guidance, sibling-model selection guidance, safe reading of corrupt Baofeng tone words, 5RX tone handling, AnyTone USB-port guidance, and refused-channel plus live-write progress diagnostics. Verification: analyzer clean; 254 Flutter tests passed; 653 Python tests passed with 2 fixture-dependent skips; embedded version 1.0.72 / 72; arm64 and x86_64 Python 3.13.15; CHIRP 21e42e4518c167548af90ed7f9edf75e516c491a; 274 driver modules; 608 selectable models across 62 vendors; strict codesigning and Gatekeeper accepted; mounted-app launch passed; local/server/public SHA-256 matched. Artifact SHA-256: e3fb1bff88d84731222a4e54506bcf470bf1da48bd5324e6f06e1e246cbe812e. Apple notarization: 1fd6915b-24e2-40c2-927e-104e67879ff8. The live manifest reports macOS 1.0.72.
  Source: `release` desktop:d502504e
- **#w-20261125-ff23 release | released | normal:** macOS 1.0.73 published
  Published a universal signed and notarized DMG from source commit 5e734229. It adds the experimental Ferrite RT-950 Pro link-protocol driver and web profile, completes Ferrite empty-read and zone ranges, preserves driver extras it cannot decode for safe repair, and carries the corrupt Baofeng tone, 5RX S-CODE, refused-channel progress, FT-60, sibling-model, AnyTone USB, XWayland, PMR446, TH-D7G, and UV-5R Mini work. Verification: analyzer clean; 254 Flutter tests passed; 654 Python tests passed with 2 fixture-dependent skips; embedded version 1.0.73 / 73; arm64 and x86_64 Python 3.13.15; CHIRP 21e42e4518c167548af90ed7f9edf75e516c491a; 274 driver modules; 608 selectable models across 62 vendors; strict codesigning and Gatekeeper accepted; mounted-app launch passed; local/server/public SHA-256 matched. Artifact SHA-256: cca9e2081060d0c389ed40e0c400a696bb7f76b13037929422d733321aa1659f. Apple notarization: 83014a33-40e8-4065-abba-40cf4b8585f6. The live manifest reports macOS 1.0.73.
  Source: `release` desktop:5e734229
- **#w-20261126-9868 release | released | normal:** macOS 1.0.74 published
  Published a universal signed and notarized DMG from source commit e7a0fc5e. It adds the OEM-traced KPG-23D TK-350 and KPG-32D TK-359 sessions with BIOS DTR/RTS behavior, the UV-5R/UV-3R aux-first download and UV-3R error reporting, the MD-UV380 short DFU identity read, the TK-863G memory-session retry, and the image-mismatch CSV guidance. Verification: analyzer clean; 254 Flutter tests passed; 672 Python tests passed; bridge upload tests passed; embedded version 1.0.74 / 74; arm64 and x86_64 Python 3.13.15; CHIRP 21e42e4518c167548af90ed7f9edf75e516c491a; 277 driver modules; 608 selectable models across 62 vendors; strict codesigning and Gatekeeper (Notarized Developer ID) accepted for the DMG and mounted app; local/server/public SHA-256 matched. Artifact SHA-256: 631e58676db11984579fc0587417fde00cb366444127e8367aee99833141aa7d. Apple notarization: e999d8f9-3def-43fc-8596-cec6e8e91115. The live manifest reports macOS 1.0.74.
  Source: `release` desktop:e7a0fc5e
- **#w-20261126-6e6d release | released | normal:** macOS 1.0.75 published
  Published a universal signed and notarized DMG from source commit 0407d809. It adds the TK-350 all-UHF-band channel decode, TK-359 Z fill-block handling and KPG-32D channel records, and the IC-E90 bounded decode (one out-of-table value no longer stops the channel list). Verification: analyzer clean; 254 Flutter tests passed; 677 Python tests passed (2 fixture skips); bridge upload tests passed; embedded version 1.0.75 / 75; arm64 and x86_64; 277 driver modules; bundled kpg23, icx90 and bridge hashes match source; strict codesigning and Gatekeeper (Notarized Developer ID) accepted for the DMG and mounted app; local/server/public SHA-256 matched. Artifact SHA-256: 45c4bb356db503ad51d77727e0202acaec093f94b904d05c8c6da8b274c34337. Apple notarization: 83493bc5-6950-4b58-8f57-0fb76d591fd8. The live manifest reports macOS 1.0.75.
  Source: `release` desktop:0407d809
- **#w-20261126-0e54 release | released | normal:** macOS 1.0.76 published
  Published a universal signed and notarized DMG from source commit 026cd8fc7. Since 1.0.75: UV-5RM Pro plain-sync fallback and model entry; TK-350 experimental write (traced KPG-23D session, existing-channel edits, identity check, waits for identity ACK) and CTCSS tone decode; TK-359 read baseline for future writes (write still disabled); per-channel decode with an undecodable-channel notice; bug reports can attach the radio image; Find Repeaters results get their own working scroll bar. Verification: analyzer clean; 257 Flutter tests; full Python suite passed (2 fixture skips); bridge upload tests passed; embedded version 1.0.76 / 76; arm64 and x86_64; 277 driver modules; bundled kpg23, icx90, 5rh_pro and bridge hashes match source; strict codesigning and Gatekeeper (Notarized Developer ID) accepted for the DMG and mounted app; local/server/public SHA-256 matched. Artifact SHA-256: a5f4841b88a874c81d0b9bd22fde2c43e1805b8a576529b0ec955af51c7869bf. Apple notarization: a4f926ae-93ba-4438-ad7c-1e034f1c2c2c. The live manifest reports macOS 1.0.76.
  Source: `release` desktop:026cd8fc7
- **#w-20261127-a334 release | released | normal:** macOS 1.0.77 published
  Published a universal signed and notarized DMG from source commit 0e9a4242b. Since 1.0.76: TK-350 5 kHz channels decoded and written by their byte-13 step bits, CTCSS tone writes, and frequency edits no longer refused by the tone check; UV-5RM Pro handshake follows CPS v1.12 (19200 announce first, stray bytes before the ACK skipped); Quansheng TK11 upload opens its own session and checks every block; every lib/ function documented. Verification: analyzer clean; 257 Flutter tests; 701 Python tests passed (2 fixture skips); embedded version 1.0.77 / 77; arm64 and x86_64; 278 driver modules; bundled kpg23, 5rh_pro, tk11_upload and bridge match source; strict codesigning and Gatekeeper (Notarized Developer ID) accepted for the DMG and mounted app; local/server/public SHA-256 matched. Artifact SHA-256: 1feead825b8d8a9e2fc5c3ec5181139babc2d17008007ed908a2718cad7d879c. Apple notarization: 8e4766d8-b1ba-48ba-b9db-81f3fdab5206. The live manifest reports macOS 1.0.77.
  Source: `release` desktop:0e9a4242b
- **#w-20261128-5f92 release | released | normal:** macOS 1.0.78 published
  Published a universal signed, notarized and stapled DMG from source commit 11391df2f. Since 1.0.77: CHIRP pin f28d9202 (99 upstream commits, new radios incl. BTECH UV-PRO, Kenwood TH-K20/TM-D750, Zastone ZT-D9000); NewChirp drivers keep precedence in packaged builds (FTX-1, FTM-150E, RA89 had resolved to upstream in the built app); UV-5RM Pro graduated; TK-359 6.25 kHz decode and name order; MD-UV380 DFU write aligned with dmrconfig/QDMR; DM-32UV short-read retry; quoted-line CSV import; IC-41S prompts; FTM-150E entry. Verification: analyzer clean; 258 Flutter tests; 87/87 Python test files; embedded 1.0.78 / 78; arm64 and x86_64 runtimes load 621 models / 64 vendors with no NewChirp ID lost; bundled drivers and bridge match source; Gatekeeper (Notarized Developer ID) accepted DMG and mounted app; mounted-app launch passed; local/server/public SHA-256 matched. Artifact SHA-256: fdc039f4223b1b1cfe664d16f24ea5ddcc02f38502ebf89a4310594e50482055. Apple notarization: 007ae547-cc4a-4b30-8f31-960b866f2ac1. The live manifest reports macOS 1.0.78.
  Source: `release` desktop:11391df2f
- **#w-20261128-6ebc release | released | normal:** macOS 1.0.79 published
  Published a universal signed, notarized and stapled DMG from source commit e568a752b. Since 1.0.78: NewChirp drivers bundled in their own newchirp_drivers/ folder and loaded after CHIRP's (structural precedence; chirp/drivers holds no NewChirp files), the app finds that folder, the bridge skips stale newchirp files in chirp/drivers, and user modules load last. Verification: analyzer clean; 259 Flutter tests; 87/87 Python test files; embedded 1.0.79 / 79; arm64 and x86_64; CHIRP f28d9202; release gate check_bundle_drivers.py ok on both runtimes (75 NewChirp driver IDs, none lost; 621 models / 64 vendors); Gatekeeper (Notarized Developer ID) accepted DMG and mounted app; mounted-app launch passed; local/server/public SHA-256 matched. Artifact SHA-256: 6170206440c3c8cf765136fe62188ed659e921e60236b58d8649642a01913d6b. Apple notarization: 1d52c383-e5b5-46c5-b73a-5eb3cb966644. The live manifest reports macOS 1.0.79.
  Source: `release` desktop:e568a752b

### Upstream CHIRP

- **#w-20261128-d1f0 maintenance | released | normal:** Adopt upstream CHIRP f28d9202 (99 commits past pin 21e42e45)
  First upstream review (docs/upstream_reviews/2026-11-28-f28d9202f.md): all NewChirp source patches apply; 84/86 Python and 12/12 Dart test files pass. Blockers: DM-32UV _Link.xfer signature changed upstream (our PASSSTA/SYSINFO retry wrapper breaks); upstream added its own Yaesu FTX-1 driver (ours collides; static_bank_zones test fails) and FTM-150E (next to our FTM-150R). 16 changed upstream drivers that our code extends need review; 14 radios would be added.
  Source: `review` docs/upstream_reviews/2026-11-28-f28d9202f.md

### Website

- **#w-20261125-daa3 bug | fix_committed | high:** myGMRS sign-in returns 503: server credentials missing
  Desktop 1.0.72 report: Sign in to myGMRS shows 503 'not configured'. Live /api/mygmrs/oauth/start answers 503. /opt/newchirp/.env.mygmrs is missing and the running process (restarted 2026-11-20 15:29 EST) has empty MYGMRS_CLIENT_ID/SECRET. Newest backup holding the file: /root/newchirp-before-shirt-20261112111101.tgz.
  Source: `email triage 2026-11-25` INBOX:983

## Quansheng

### TK11

- **#w-20261126-bb70 bug | awaiting_user | normal:** No response from radio (triage)
  Read on COM1 (likely the PC's built-in serial port, not the cable): UV-K5 hello got 0 bytes
  Source: `email` INBOX:995
- **#w-20261126-0461 bug | fix_committed | normal:** Read works, write fails: upload never opens a session
  1.0.75 Windows 10 (26100), TK11(8) firmware 5.00.18, COM3: read 16 channels, write's first 536-byte frame got no reply, retry got 16 unframed bytes. Stock do_upload skips the 0x1F4 connect; OEM CPS 2.19 connects before every write.
  Source: `email` mailbox:UID 1044

### UV-K1 & UV-K5 V3 (F4HWN)

- **#w-20261119-7381 enhancement | released | normal:** F4HWN 7.0.0 firmware profile
  F4HWN 7.0.0 released 2026-11-19. Built-in profile supports v6.3.x only and refuses other F4HWN versions before I/O. Needs analysis of the 7.0 CHIRP module memory map.
  Source: `email` INBOX:809

### UV-K1 (F4HWN 6.3)

- **#w-20261119-8c78 bug | fix_committed | normal:** Image from F4HWN's CHIRP module refused as unsupported model
  Linux 1.0.61: the F4HWN module (imports wx) cannot load, and an image saved by it ('UV-K1 & UV-K5 V3 (F4HWN)', 0xB190 bytes, f4hwn.chirp.v6.3.0.py sha256 a307886d...) was rejected as 'Unsupported model'. Same layout as the built-in profile, which was built from that module.
  Source: `email` INBOX:798

### UV-K1 (F4HWN)

- **#w-20261125-79f9 bug | awaiting_user | normal:** UV-K5 hello unanswered (0 bytes) on Windows COM4
  Windows 11 (26300), 1.0.72, COM4: five UV-K5 hellos got 0 bytes, so no firmware version. Cable/port/seating.
  Source: `email triage 2026-11-25` INBOX:977

### UV-K1 / UV-K5 V3 (F4HWN 6.3)

- **#19 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: 1,024 channels + 14 VFOs, offline-tested. Write: Program/configuration region only, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:43

### UV-K5 family

- **#w-20261128-260c bug | awaiting_user | normal:** Firmware V-N3.40 not recognized; unsupported fallback decode fails (list index out of range)
  Windows 1.0.70: hello reports firmware V-N3.40; stock, OSFW and egzumer profiles refuse it; the read-only unsupported profile downloaded the image but decoding failed with "list index out of range". Need the saved .img and where the firmware came from.
  Source: `email` mailbox:UID 1081
- **#18 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: Yes, firmware-ID retry. Write: Stock CHIRP policy. Settings: Stock CHIRP policy. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:42

### UV-K5 V1 (Robzyl RO-KO 512K)

- **#w-20261123-211e new_driver | experimental | normal:** Read-only profile for Robzyl RO-KO firmware on a 512K-EEPROM UV-K5 V1
  Forum file drop (2026-11-22, '512k_CHIRP_UV-K5_V1_ROBZYL-KO.py', SHA-256 06df9e84441162d9e65e044f7cecb3b6308c69c3d6a1cef6c3d09de5fd2086ef): community CHIRP module for Robzyl RO-KO firmware on a UV-K5 V1 with an upgraded 512 Kbit EEPROM. 0xA100-byte map, 999 channels at 0x2000, attributes 0x5E80, 16-char names 0x6280. Module reviewed: no exec/network/file/obfuscation; non-ASCII is Cyrillic. It writes without checking firmware, which would overrun a stock 8 KB EEPROM. Plan: verify against Robzyl firmware source; read-only profile gated on firmware identity.
  Source: `forum` file-drop:512k_CHIRP_UV-K5_V1_ROBZYL-KO.py

## QYT

### KT7900D

- **#w-20261122-7972 bug | awaiting_user | normal:** Programming command came back as 8 bytes (likely cable echo, radio silent), shown as 'Bad ack'
  Windows 1.0.66: the 8-byte MSTRING_KT8900D magic returned exactly 8 bytes within the 1.5 s timeout instead of the 50-byte ACK+ident, so btech._do_ident reported 'Bad ack from radio'. Same length as the command, so most likely the cable echo with no radio reply (radio off, cable not fully seated, or wrong port/cable). Bytes not logged in 1.0.66. Trace now labels echo-only replies and the error explains them.
  Source: `email` INBOX:881 <89c3682f-beb1-0f59-885f-48fc9ea7afcb@newchirp.net>

### KT8900

- **#w-20261124-a24a bug | awaiting_user | normal:** No response on COM1 (built-in port, not the CH340 cable)
  Windows 1.0.66: user installed CH340 driver but selected COM1; one 8-byte magic, no reply. Setup issue.
  Source: `email INBOX:946` 

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

### UV-5G Plus

- **#w-20261125-38b3 bug | awaiting_user | normal:** PROGRAMBFGMR unanswered on Windows COM3
  Windows 11 (26300), 1.0.71, COM3: read got no reply at all to PROGRAMBFGMR within 1.5 s (no echo). Cable/port/seating.
  Source: `email triage 2026-11-25` INBOX:976

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
- **#w-20261123-f57b bug | released | normal:** Channel 26 tone 0x5750 (2235.2) stopped the read
  Windows 1.0.67: channel 26 TX frequency byte 0x6f and tone 0x5750; the CPS GetCTCSS_HexToStr shows '2235.2' for it too, so the radio holds those values. Also 0x0800-style words decoded as tones where the CPS shows OFF.
  Source: `email` INBOX:919
- **#w-20261123-a8d2 bug | fix_committed | normal:** Android USB read: 'SocketException: Broken pipe' on the local proxy hides the real error
  NewChirp Android (newchirpmobile) over a USB-C adapter, profile 'Radtel RT-950' (owner's radio is an RT-950 Pro): Read radio shows SocketException Broken pipe errno 32 on 127.0.0.1. The Dart USB proxy (usb_radio_service.dart) wrote after the Python side (chirp_mobile.py) closed, so the underlying Python error is not shown. Also the wrong profile (RT-950 vs RT-950 Pro) may be selected.
  Source: `email` INBOX:913
- **#w-20261126-8d5d bug | awaiting_user | normal:** Ferrite read: no answer to wake bytes or HELLO
  1.0.75 Windows 10 (19045), COM15, Radtel_RT-950_Pro_Ferrite: 03, 00 and the 23-byte HELLO all unanswered. Ferrite answers HELLO, so likely stock Radtel firmware, Ferrite Console holding the port, or wrong port.
  Source: `email` mailbox:UID 1045
- **#w-20261120-36d6 enhancement | released | normal:** Stock-firmware RT-950 Pro over Bluetooth
  Add experimental read-only Android Bluetooth support for the stock RT-950 Pro. The stock CPS 1.3.3 exposes a BT Write switch at function-settings byte 29; iOS/Android programming is advertised but the exact BLE wire behavior still requires app or hardware evidence. Bluetooth writes remain disabled.
  Source: `email` INBOX:854
- **#8 maintenance | experimental | normal:** Current driver status
  Transport: RT-950/BT-9000 clone serial, 115200 8N1 + RTS/DTR. Read: 960 channels + Pro map, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:32
- **#w-20261124-4400 new_driver | experimental | low:** Ferrite firmware (FerriteFW 0.9.x) support
  Open-source RT-950 Pro firmware, PolyForm Noncommercial; programmed only by Ferrite Console over the cable; protocol spec in github.com/FerriteFW/docs. Channel layout differs from nicFW950.
  Source: `forum` topic86-post211

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

- **#w-20261122-8452 bug | released | normal:** Download refuses an RA87 whose 8-byte ident differs from the two captured fingerprints
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

- **#w-20261121-badb bug | pending_validation | normal:** Newer (2025+) RT22 units fail identification
  Older RT22s read; newer units ACK PROGRGS and return an 8-byte ID that matches none of RT22Radio._fileid (P32073, P3\0\0\03, P3207!, 00..F8FF). Trace hid the bytes. Same pattern as upstream CHIRP #6747 (open since 2019). Do not accept an unknown ID blindly: newer units may differ internally. Need the ID bytes and an OEM-software file from a newer unit.
  Source: `mailbox` INBOX:871 <c77a8516-ea89-dc83-e8ac-f177629e63c3@newchirp.net>

### RT85

- **#w-20261126-8c7c bug | awaiting_user | normal:** No response from radio (triage)
  Owner selected RA85 (GA-510 family, PROGROMWLTU) for an RT85; CHIRP supports Retevis RT85 (th_uv88)
  Source: `email` INBOX:996

### RT97L

- **#11 maintenance | experimental | normal:** Current driver status
  Transport: Stock USB serial, 9600 8N1 + DTR/RTS. Read: Yes, hardware pending. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:35

### RT97L GMRS

- **#99 new_driver | investigating | high:** RT97L GMRS needs its own programming protocol
  Windows 1.0.58: RT97L driver gets no ACK even after STX wake-up. Reporter says the GMRS RT97L uses different OEM software and the standard RT97L Custom software cannot connect either. Reporter uploaded the GMRS programming software and a 2048-byte data file through the site file drop.
  Source: `email` INBOX:786; file drops 9-11

## TIDRADIO

### TD-BL1 adapter

- **#w-20261127-31d2 bug | awaiting_user | normal:** Android app does not list the adapter after it was paired in Android settings
  UV-5R owner: Android Bluetooth sees and pairs the Tidradio adapter, but NewChirp's scan never shows it. The app only lists advertising devices (service filter, then unfiltered after 4 s); an adapter already connected by the system usually stops advertising. Workaround: forget it in Android settings and connect from the app. Possible fix: also list system-connected devices (UniversalBle.getSystemDevices).
  Source: `email` mailbox:UID 1053
- **#w-20261128-ad06 bug | awaiting_user | normal:** Mobile connect fails "Operation Not Supported" on Android 8.1, Android 16 and iPadOS 17.7
  Adapter is found by scan; connect fails with universal_ble operationNotSupported (GATT 0x06 request not supported) on three devices, while ODMaster connects. Which step (subscribe ff21, handshake write ff22, MTU) is unknown; need the Bluetooth diagnostics report.
  Source: `email` mailbox:UID 1078

### TD-H3 family

- **#39 maintenance | experimental | normal:** Current driver status
  Transport: OEM-verified TD-H3 clone serial, 38400 8N1. Read: Invalid brightness normalized; five-attempt identity probe. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:63

### TD-H3 Plus

- **#w-20261128-0ea3 new_driver | awaiting_user | normal:** Support request: TIDRADIO TD-H3 Plus
  Windows 1.0.77 general report: "please add support for tidradio td h3 plus". Upstream CHIRP lists TD-H3 / TD-H3-HAM / TD-H3-GMRS only. Ask for a read attempt with the TD-H3 profile (read-only) and the label/firmware.
  Source: `email` mailbox:UID 1088

### TD-H8 fourth-generation

- **#40 maintenance | experimental | normal:** Current driver status
  Transport: ODMaster-verified TD-H8 G4 clone serial, 38,400 8N1. Read: Normal, HAM, and GMRS G4 identities; 151-channel physical read. Write: Official 170-page map, offline-tested. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:64

### TD-H9

- **#w-20261124-dfcb new_driver | pending_validation | normal:** TD-H9 identity TDH9 is unsupported
  macOS 1.0.70 with TD-H8 G4 selected: PVOJH\x1c\x14 -> 06, 02 -> 'TDH9\xff\xff\xffN', then 'Unsupported model'. ODMaster 2.6.4 IndexFragment reads TD-H9 with H8ReadUtil (same as TD-H8/TD-H3); its per-model map comes from the public readProtocol service (not bundled). Next: fetch the TD-H9 read/write templates and compare with the G4 map.
  Source: `email INBOX:949` 

## TYT

### MD-UV380

- **#w-20261126-8502 bug | hardware_tested | normal:** USB DFU identity reply of 32 bytes stops the read
  macOS 1.0.73: 'USB DFU transfer returned 32 of 64 bytes' on the 0xA2 identity upload. dmrconfig requests 64 and accepts any length; model name is in the first 32 bytes. Identity now accepts a short reply; memory reads stay strict.
  Source: `email` INBOX:986
- **#w-20261128-e650 bug | released | high:** Write stops with libusb "Pipe error" (USB stall) before any erase
  macOS 1.0.77: two writes (23 channels, then 1 channel) failed with "Pipe error" ~6 s after the write started (channel preparation), before the erase changed anything; the following read matched the earlier image except the edit. Transport diverged from dmrconfig/QDMR: download/upload-idle treated as ready instead of aborted to dfuIDLE, no programming-mode re-entry before erase, 2 s timeouts, and any status stall after an erase was fatal (QDMR ignores those errors).
  Source: `email` mailbox:UID 1083
- **#36 maintenance | experimental | normal:** Current driver status
  Transport: ST DfuSe USB 0483:DF11 + libusb. Read: 3000 channels + zones. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:60

### TH-350

- **#w-20261122-ad5b bug | awaiting_user | normal:** Channel names shifted across channels: likely TH-350 US radio read as base TH-350
  Linux 1.0.68 read of 40 channels: frequencies correct, names start in one channel and continue in the next, some blank. Base TYT_TH-350 reads 5-byte names at 0x0A30; TYT_TH-350_US reads 8-byte names at 0x0930. Layouts are otherwise identical and match_model cannot tell them apart, so a US radio read as base gives exactly this. Reporter is in the US and used RT Systems. Ask them to read with TH-350 US and send the .img.
  Source: `email` INBOX:894 <42a19195-c6bb-739c-d71e-2dba89860053@newchirp.net>

### TH-9800

- **#w-20261123-8b91 bug | awaiting_user | normal:** COM3 not available on first read (Windows 11)
  Brand-new radio, first connection, 1.0.69 on Windows 11: Windows could not open COM3 before any radio traffic. Likely the cable driver (TH-9800 cables are usually Prolific PL2303, refused by current Windows drivers) or a wrong/stale port. User-side; FAQ #cable-driver and #which-port.
  Source: `email:INBOX:934` <503cda7b-824d-8942-b8fe-f0aa878fc509@newchirp.net>
- **#w-20261126-f3d3 bug | awaiting_user | normal:** No response from radio (triage)
  macOS 1.0.73: no reply on usbserial-RTADM13B after a BF-F8HP read on another cable; cable and clone setup needed
  Source: `email` INBOX:1005
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

### KG-UV9D Plus

- **#w-20261123-4b54 bug | closed | low:** No response until the volume was set to about halfway
  Owner found the radio only talks to the cable with volume around 50%. User-side cause; FAQ #wouxun-volume and a KG-UV9 'no response' hint added.
  Source: `email` INBOX:909

### KG-UV9GX Plus

- **#w-20261122-cac2 enhancement | released | low:** Owner could not find the KG-UV9GX Plus; it uses the KG-UV9GX profile
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

- **#w-20261122-ddc6 bug | released | normal:** [BAND] pressed before the port is open: ID block lost, then 'No response from radio'
  Windows 1.0.66, two attempts: the only exchange is the ACK CHIRP writes after _safe_read, which it sends even when nothing arrived. Old CHIRP worked. NewChirp shows the prompt ('After clicking OK, press [BAND]') and only then starts the bridge, which loads all drivers before opening the port; the bridge's ready cue covered only [PTT]/[Send], so an immediate [BAND] press sends the image to a closed port and the radio waits for an ACK. Affects every 'After clicking OK, press [KEY]' Yaesu clone radio (FT-1D, VX-3/6/7/8, FT-817, FT-857, FT-7800, FT-8800, FT-90, FT-1802, FT-1500M, FT-70D, FTM-3200D, FTM-7250D, FT-450).
  Source: `email` INBOX:880 <1dccdb08-b5b6-c3ec-6e24-d7acc8d754c4@newchirp.net>

### FT-1D/2D/3D/5D clone family

- **#5 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP Yaesu clone serial, 38400 8N1. Read: Completion-safe timeout; multi-bank mappings. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:29

### FT-2900R

- **#w-20261127-b76c bug | awaiting_user | normal:** Read stops after 'press MHz' with a header error
  Forum topic 56 post 218: FT-2900 read reaches the 'press SET MHz' step then fails with a header error. Stock ft2900 requires the 10-byte ID to equal one IDBLOCK; FT-2900E (41 02) and TX-modified (C7 01) radios send others, and CHIRP keeps the E class unregistered. Need the received header (in-app report) and the radio's label variant.
  Source: `forum` forum:topic/56#post-218

### FT-50

- **#69 bug | hardware_tested | high:** Two-stop-bit transport and odd-split write
  The OEM ADMS-1E uses 9600 8N2. A 1.0.56 name-only write and restore committed correctly and preserved all other channels.
  Source: `email` INBOX:722
- **#6 maintenance | hardware_tested | normal:** Current driver status
  Transport: Yaesu clone serial, 9600 8N2. Read: Odd-split channels decode; reporter image verified. Write: Hardware-tested name write and restore; odd-split field write pending. Settings: Stock FT-50 settings. Ledger status: Experimental; partial hardware validation.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:30

### FT-60

- **#w-20261124-55e8 bug | awaiting_user | normal:** Read gets no response from radio (zero bytes) on Windows COM4
  Windows 11 (build 26200), 1.0.67, COM4: five reads 20-110 s each all end in RadioNoResponse; CHIRP ft60 _download received zero bytes every time, so the radio never sent its header. Points to clone mode not entered (F8 CLONE selected without pressing F/W), the cable, or the port rather than timing.
  Source: `email triage 2026-11-24` INBOX:962

### FT-70D

- **#w-20261123-00d7 bug | fix_committed | normal:** Checksum Failed [0000-FEC9 (@FECA)] on read
  1.0.70 Windows COM4: first read got no response (BAND pressed early), the next read completed but failed the checksum. ADMS-10 1.0.1.0 REA: protocol is 10-byte AH51G ID, ACK, 65216 data + 1 checksum byte (sum of ID+data), identical to CHIRP's layout; ADMS validates the AH51G ID, CHIRP does not, so a stray byte ahead of the ID shifts the image and fails the checksum. Override flushes input, resyncs on AH51G, and explains the checksum failure.
  Source: `email` INBOX:937, INBOX:938 <c86ed89e-048b-0454-48f6-ce6ff79ee70f@newchirp.net>
- **#w-20261123-2df0 enhancement | fix_committed | normal:** Offer to shorten names longer than the radio allows
  VX-7 channels (8-char names) imported into an FT-70D (6-char) block writing until ~100 names are edited by hand. Added a 'Shorten N names to X' action on the attention banner with a preview, duplicate warning and one-step undo.
  Source: `email` INBOX:939

### FT-991A

- **#4 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu CAT serial, 4800-38400 auto-baud. Read: 117 live memories. Write: Known channel fields, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:28

### FTM-150R/E/ASP

- **#2 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP clone serial, 38400 8N1. Read: Yes. Write: Yes. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:26

### FTM-300DR

- **#w-20261122-1af9 bug | awaiting_user | normal:** First clone frame failed checksum after repeated read attempts
  Linux 1.0.68: reads started on ttyUSB2, ttyUSB3, then ttyUSB2 again; the last failed 'Block failed checksum' about 20 s in. Radio-initiated clone of 131-byte frames; a misaligned or stale first frame fails its checksum. The FTM-300 prompt ('press the DIAL knob') got no 'press now' cue.
  Source: `email` INBOX:899

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

- **#w-20261122-28ff bug | released | normal:** Read of a 193-channel codeplug from another tool fails to decode: list index out of range
  Linux 1.0.68: clone download completed and saved /tmp/newchirp-5h4w6vr4.img, then channel decoding failed with IndexError. FT-7800-family get_memory indexes TONES (6-bit field, 50 tones), DTCS_CODES (7-bit, 104), TMODES (3-bit, 5), DUPLEX (3-bit, 5) and power levels (2-bit, 3) without bounds checks; a value written by the other tool probably overflows one. The image was not attached (reports cannot carry files) and /tmp may be cleared on reboot. Need the .img to identify the field.
  Source: `email` INBOX:893 <1d1f2c4e-65b8-b971-2ae4-7cb3b6ce4c66@newchirp.net>

### VX-6

- **#66 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu clone serial, 19200 8N1. Read: Unprogrammable stored slots are treated as empty. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:90
