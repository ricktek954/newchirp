# NewChirp driver work ledger

Generated from `database/driver_work.sqlite3` on 2026-11-18.

Use `python3 scripts/driver_work.py show <id>` for event history.

## AnyTone

### 5888UV

- **#34 maintenance | experimental | normal:** Current driver status
  Transport: Stock AnyTone clone serial. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:58

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

### 5RX

- **#89 bug | awaiting_user | normal:** No response on macOS serial adapter
  NewChirp 1.0.56 received no response to its seven-byte identity command on a macOS usbserial adapter. Confirm the radio mode, cable voltage, adapter driver, and OEM CPS behavior.
  Source: `email` INBOX:736

### BF-V12D

- **#25 maintenance | experimental | normal:** Current driver status
  Transport: CPS-derived P3107 clone serial, 9600 8N1. Read: Original-firmware sequence traced; hardware pending. Write: Stock image/upload path. Settings: Stock channel decoder. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:49

### DM-32UV

- **#72 bug | fix_committed | high:** Airband receive-only validation
  Accept 108-136 MHz only when duplex is Off.
  Source: `email triage` 2026-11-16
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

- **#86 bug | awaiting_user | high:** GMRS repeater TX and RX tones decode blank
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

- **#82 bug | awaiting_user | high:** Channels 52-54 lose stored CTCSS during decode
  NewChirp 1.0.56 decodes channels 52-54 with no tone, while RT Systems UV-32 Programmer 5.00.29 shows CTCSS 103.5, 103.5, and 206.5. The exported CSV alone does not contain the raw tone words.
  Source: `email` INBOX:744

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

### UV-5RH

- **#29 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1 + DTR/RTS. Read: OEM-style handshake retry; stock channel decode. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:53

### UV-5RM Plus

- **#28 maintenance | experimental | normal:** Current driver status
  Transport: UV-17-family serial, 115200 8N1 + DTR/RTS. Read: OEM-style handshake retry; stock channel decode. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:52

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

### IC-9700

- **#51 maintenance | experimental | normal:** Current driver status
  Transport: Icom CI-V serial, auto-baud from 4800 to 115200. Read: Stock CHIRP driver. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:75

### IC-E90 / IC-T90A

- **#54 maintenance | experimental | normal:** Current driver status
  Transport: NewChirp ICF clone transport, 9600 8N1. Read: Four identity attempts; checksum-validated contiguous full image; invisible-slot guard. Write: NewChirp clone-in boundary, 362 32-byte blocks, required `E6 00`. Settings: Stock ICX90 decoder. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:78

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

### TK-270G

- **#75 bug | fix_committed | high:** Transient block checksum rejection
  Retry the identical block up to three times, then close programming mode.
  Source: `email triage` 2026-11-16
- **#83 bug | fix_committed | high:** Upload rejects erased bank index sentinel
  A downloaded image containing bank index 128 on an active channel is rejected during unchanged upload before radio I/O. Normalize erased bank metadata before rebuilding bank tables.
  Source: `email` INBOX:723
- **#60 maintenance | experimental | normal:** Current driver status
  Transport: Kenwood Series 60G clone serial, 9600 8E1. Read: NewChirp decode with raw-preserving invalid-index normalization. Write: NewChirp write path with bank-state validation and transient checksum retry; offline-tested. Settings: Stock driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:84

### TK-3401D

- **#14 maintenance | experimental | normal:** Current driver status
  Transport: KPG-171D clone serial, 9600 then 19200 baud. Read: Yes, provisional record scan. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:38

### TK-350

- **#71 bug | fix_committed | high:** Identity request receives zero bytes
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

## Quansheng

### UV-K1 / UV-K5 V3 (F4HWN 6.3)

- **#19 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: 1,024 channels + 14 VFOs, offline-tested. Write: Program/configuration region only, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:43

### UV-K5 family

- **#18 maintenance | experimental | normal:** Current driver status
  Transport: UV-K5 framed serial, 38400 8N1. Read: Yes, firmware-ID retry. Write: Stock CHIRP policy. Settings: Stock CHIRP policy. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:42

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
- **#8 maintenance | experimental | normal:** Current driver status
  Transport: RT-950/BT-9000 clone serial, 115200 8N1 + RTS/DTR. Read: 960 channels + Pro map, offline-tested. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:32

### RT-950 Pro, Bajeton BJ-9000 with nicFW950

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

### RA89

- **#90 bug | awaiting_user | normal:** No response to handshake
  NewChirp 1.0.57 received no response to the TYT handshake on Linux /dev/ttyUSB0. Confirm the cable model and whether the OEM CPS can read the radio.
  Source: `email` INBOX:738
- **#64 maintenance | experimental | normal:** Current driver status
  Transport: OEM addressed blocks, 57,600 8N1, DTR/RTS on. Read: 200 channels + core settings. Write: Yes, offline-tested. Settings: Core settings and startup text. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:88

### RT97L

- **#11 maintenance | experimental | normal:** Current driver status
  Transport: Stock USB serial, 9600 8N1 + DTR/RTS. Read: Yes, hardware pending. Write: Disabled. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:35

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

### TH-9800

- **#65 maintenance | experimental | normal:** Current driver status
  Transport: TYT clone serial, 38400 8N1. Read: Reserved tone values no longer abort the read. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:89

## Wouxun

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

### KG-UVD1P / KG-UV2D

- **#47 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP clone serial, 9600 8N1. Read: One-second block timeout. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental timing override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:71

## Yaesu

### FT-1D/2D/3D/5D clone family

- **#5 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP Yaesu clone serial, 38400 8N1. Read: Completion-safe timeout; multi-bank mappings. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:29

### FT-50

- **#69 bug | pending_validation | high:** Two-stop-bit transport and odd-split write
  The OEM ADMS-1E uses 9600 8N2. A 1.0.56 name-only write and restore committed correctly and preserved all other channels.
  Source: `email` INBOX:722
- **#6 maintenance | experimental | normal:** Current driver status
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

- **#92 bug | investigating | high:** Power controls disappear after CSV import and stale channels remain
  After a CSV library replacement, radio capabilities were discarded, hiding transmit power across every band. Full-image upload also relied on an incomplete cleared-location set, so removed channels could remain in the radio image.
  Source: `email` INBOX:746
- **#1 maintenance | experimental | normal:** Current driver status
  Transport: CHIRP Yaesu clone serial, 38400 8N1. Read: Stock CHIRP driver. Write: Corrected Low/Mid/High encoding. Settings: Not exposed by stock driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:25

### FTX-1

- **#3 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu CAT serial, 4800-115200 auto-baud. Read: 999 live memories. Write: Yes, offline-tested. Settings: Hidden. Ledger status: Experimental.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:27

### VX-6

- **#66 maintenance | experimental | normal:** Current driver status
  Transport: Yaesu clone serial, 19200 8N1. Read: Unprogrammable stored slots are treated as empty. Write: Stock CHIRP driver. Settings: Stock CHIRP driver. Ledger status: Experimental compatibility override.
  Source: `docs/DRIVER_STATUS.md` docs/DRIVER_STATUS.md:90
