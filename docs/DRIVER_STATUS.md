# NewChirp driver status

This is the authoritative local ledger for radios whose support is maintained
by NewChirp rather than upstream CHIRP. Update it whenever a driver is added,
changes transport, gains or loses write support, or completes hardware testing.
For bugs, commits, evidence, email follow-ups, and dated work history by
manufacturer/model, use the driver ledger (`database/driver_work/`, queried
through `scripts/driver_work.py`) as described in
`database/README.md`. The generated readable timeline is `docs/DRIVER_WORK.md`.

Last updated: 2026-11-20

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
| Yaesu FTM-7250D | `drivers/newchirp_ftm7250.py` | CHIRP Yaesu clone serial, 38400 8N1 | Stock CHIRP driver | Corrected Low/Mid/High encoding | Not exposed by stock driver | Experimental compatibility override |
| Yaesu FTM-150R/E/ASP | `drivers/newchirp_ftm150.py` | CHIRP clone serial, 38400 8N1 | Yes | Yes | Hidden | Experimental |
| Yaesu FTX-1 | `drivers/newchirp_yaesu_ftx1.py` | Yaesu CAT serial, 4800-115200 auto-baud | 999 live memories | Yes, offline-tested | Hidden | Experimental |
| Yaesu FT-991A | `drivers/newchirp_yaesu_ft991a.py` | Yaesu CAT serial, 4800-38400 auto-baud | 117 live memories | Known channel fields, offline-tested | Hidden | Experimental |
| Yaesu VX-170 / VX-177 | `drivers/newchirp_yaesu_vx170.py` | Stock CHIRP Yaesu clone serial (FT-7800 family) | Split-tone squelch modes decoded as Cross | Stock path; split modes encoded to raw 5-7, offline-tested | Not exposed by stock driver | Experimental compatibility override |
| Retevis RT22 | `drivers/newchirp_retevis_rt22.py` | Stock CHIRP clone serial, 9600 | Any complete 8-byte ID accepted for the plain RT22, as Retevis's software does | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Retevis RA87 | `drivers/newchirp_retevis_ra87.py` | Stock CHIRP clone serial, 9600, echoing cable | Download identifies by model byte 0x1F05 = A5 (OEM CPS rule) instead of two fixed 8-byte fingerprints | Stock CHIRP driver (already checks 0x1F05) | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-5R Mini | `drivers/newchirp_uv5r_mini.py`, `drivers/newchirp_uv5rm_plus.py` | Stock CHIRP UV-17Pro-family serial | CPS handshake (skip non-ACK bytes, resend up to five times); unanswered block requests resent up to five times (OEM CPS rules) | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-5R family (`uv5r.py` radios with the settings block: UV-5R, BF-F8HP, UV-82, UV-5RX3 and others) | `drivers/newchirp_uv5r_aux_first.py` | Stock CHIRP UV-5R serial | Download reads the settings block 0x1EC0-0x1FFF right after the firmware-version read, then channels 0x0000-0x17FF; same blocks, block sizes and image layout as stock (a radio on the 50 BB FF 20 12 07 25 handshake refused the jump back to 0x1EC0 after the channels, INBOX:985; the UV-5RX CPS never makes that jump) | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override; offline-tested, not hardware-confirmed |
| Baofeng UV-3R | `drivers/newchirp_uv3r_compat.py` | Stock CHIRP serial | Stock | Stock | Stock | Compatibility fix: after ten failed handshakes the real error is reported (stock raised a Python "cannot access local variable 'e'" error) |
| Baofeng 5RX, UV-S9X3, BF-A58S and other `BaofengCommonHT` radios | `drivers/newchirp_baofeng_common_power.py` | Stock CHIRP serial | 5RX/UV-S9X3: power read from byte 14 bit 0 (set = Low), as the official Baofeng UV-5RX CPS 20231124 does (ZIP SHA-256 `4848128a68dcb0d2ddfa54c65ad43591718d8e9e3b62112691ff6cd60926590a`); other radios: an unrecognised value shows as High instead of failing the read (stock crashed logging a nonexistent `_mem.power`); a corrupt tone word (CTCSS not in the standard list, or a DCS index past the table, e.g. 5RX rxtone `0xFF30`) shows as no tone instead of failing the read | 5RX/UV-S9X3 write Low as 1 and High as 0 like the CPS (stock wrote Low as 2, which the CPS reads as High); a channel whose power or tones are not edited keeps its raw power and tone words | Stock CHIRP driver | Experimental compatibility override; CPS-derived, not hardware-confirmed |
| AnyTone AT-D878UVII Plus | `drivers/newchirp_anytone_d878uvii.py` | AnyTone D578UV/D878UV serial protocol, 115200 8N1 | Conventional channels and zones, offline-tested | Disabled | Hidden | Experimental read-only |
| Quansheng UV-K5 (V1) with Robzyl RO-KO 512K firmware | `drivers/newchirp_uvk5_roko512k.py` | Stock UV-K5 serial (0x0514 hello, 0x051B read), 38400 8N1 | 999 channels from the firmware layout, offline-tested; refuses other firmware and 8 KB EEPROMs | Disabled | Hidden | Experimental read-only |
| Yaesu FT-1D/2D/3D/5D clone family | `drivers/newchirp_yaesu_clone.py` | CHIRP Yaesu clone serial, 38400 8N1 | Completion-safe timeout; multi-bank mappings | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Yaesu FT-50 | Pinned CHIRP `ft50.py` with `drivers/newchirp_ft50_compat.py` | Yaesu clone serial, 9600 8N2 | Odd-split channels decode; reporter image verified | Hardware-tested name write and restore; channel clear fixed in both flag tables; odd-split channel write (all hardware-confirmed 2026-11-19) | Stock FT-50 settings | Supported; read and write hardware-confirmed 2026-11-19 |
| Radtel RT-950 | `drivers/newchirp_rt950.py` | CHIRP-compatible serial, 115200 8N1 + RTS/XON | Yes, designed | Disabled | Hidden | Experimental |
| Radtel RT-950 Pro | `drivers/newchirp_rt950pro.py` | USB: RT-950 Pro CPS 1.3.3 clone serial, 115200 8N1 + RTS/DTR; Bluetooth: experimental raw FFE1 stream | 990 channels + full CPS map (272 blocks); USB old-map read hardware-confirmed; Bluetooth read unvalidated | USB: CPS write path, owner write confirmed; Bluetooth: refused | Hidden | Experimental; stock-firmware Bluetooth read pending hardware validation; Bluetooth write not implemented |
| Radtel RT-860 | `drivers/newchirp_rt860.py` | iRadio/Iradio clone serial, 115200 8N1 + DTR | 1,024 channels + 256 zones, offline-tested | Disabled | Hidden | Experimental |
| Radtel RT-950 Pro, Bajeton BJ-9000 with nicFW950 | `drivers/newchirp_nicfw950.py` | nicFW serial, 38400 → 460800 8N1 | Yes | Changed blocks | Global settings and group names | Hardware-tested on one 6.00.16c unit; other versions/aliases experimental |
| Radtel RT-950 Pro with Ferrite | `drivers/newchirp_ferrite.py` | Ferrite link protocol 1, COBS frames, 115200 8N1 | Yes (channels, zones) | Changed channels through the radio's own checks | Not exposed | Experimental; offline-tested only |
| Retevis RT97L | `drivers/newchirp_rt97l.py` | Stock USB serial, 9600 8N1 + DTR/RTS | Yes, hardware pending | Disabled | Hidden | Experimental |
| Kenwood TS-2000 | `drivers/newchirp_ts2000.py` | Kenwood live CAT serial, 9600 8N1 + RTS | Yes | Yes, longer write timeout | Standard | Hardware read verified; write retest pending |
| Kenwood TH-D75 | `drivers/newchirp_thd75.py` | Kenwood clone CAT serial, 9600-57,600 baud | Yes, echo-tolerant | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Kenwood TK-3401D | `drivers/newchirp_kenwood_tk3401d.py` | KPG-171D clone serial, 9600 then 19200 baud | Yes, provisional record scan | Disabled | Hidden | Experimental |
| Kenwood TK-350 | `drivers/newchirp_kenwood_kpg23.py` | KPG-23D clone serial, 4800 8N2, DTR/RTS off, 6-byte identity, 28 × 128-byte blocks from 0xF000, no exit command (KPG-23D 1.01 QEMU register trace 2026-11-26) | Yes, matches the OEM trace; not hardware-tested | Disabled | Hidden | Experimental read-only |
| Kenwood TK-359 | `drivers/newchirp_kenwood_kpg23.py` | KPG-32D clone serial, 9600 8N1, 0xF000 addressed blocks | Yes, offline-tested | Disabled | Hidden | Experimental read-only |
| Kenwood TK-863G | `drivers/newchirp_kenwood_tk863g.py` | KPG-76D clone serial, 9600 8N2 with OEM baud fallback | 128 channels + full 32 KiB image, offline-tested | Disabled | Hidden | Experimental read-only |
| Quansheng UV-K5 family | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | Yes, firmware-ID retry | Stock CHIRP policy | Stock CHIRP policy | Experimental |
| Quansheng UV-K1 / UV-K5 V3 (F4HWN 6.3) | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | 1,024 channels + 14 VFOs, offline-tested | Program/configuration region only, offline-tested | Hidden | Experimental |
| KSUN UV-K60 rebrand | `drivers/newchirp_uvk5.py` | UV-K5 framed serial, 38400 8N1 | Stock UV-K5-family profile | Stock UV-K5-family policy | Stock UV-K5-family policy | Experimental |
| KSUN UV-K60 Plus | `drivers/newchirp_uvk60plus.py` | MH-580 clone serial, 38400 8N1 | Sparse `0x2A00` image, offline-tested | Disabled | Hidden | Experimental read-only |
| Connect Systems CS750 | `drivers/newchirp_cs750.py` | NewChirp raw SCSI/RAP; CPS `.rdb` import | Yes, untested hardware; Windows opens read-only | Disabled | Hidden | Experimental |
| Baofeng GM-32 | `drivers/newchirp_gm32.py` | UV-32 clone serial, 115200 8N1 | Yes | Yes | Yes, including bank names | Experimental |
| Baofeng DM-32UV | `drivers/newchirp_dm32uv.py` | CHIRP DM-32UV serial protocol, 115200 8N1 + DTR/RTS | Stock CHIRP driver; receive-only airband accepted | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Baofeng BF-V12D | `drivers/newchirp_baofeng_bfv12d.py` | CPS-derived P3107 clone serial, 9600 8N1 | Original-firmware sequence traced; hardware pending | Stock image/upload path | Stock channel decoder | Experimental |
| Baofeng K67 Pro | `drivers/newchirp_baofeng_k67pro.py` | Shared K6/K63 CPS serial, 115200 8N1 + DTR/RTS | 1,000 channels + sparse full image, offline-tested | Disabled | Hidden | Experimental read-only |
| Baofeng 5RH Pro / UV-5RH Pro / UV-5RH Plus / UV-5RM Plus v2 | `drivers/newchirp_baofeng_5rh_pro.py` | UV-5RH v2 encrypted clone serial, 115200 then 19200 8N1 | 640 channels + 10 zones, offline-tested | Full image, offline-tested | Basic settings and zone names | Experimental |
| Baofeng UV-5RM Plus | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv5rm_plus.py` | UV-17-family serial, 115200 8N1 + DTR/RTS | OEM-style handshake retry; stock channel decode | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-5RH | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv5rm_plus.py` | UV-17-family serial, 115200 8N1 + DTR/RTS | OEM-style handshake retry; stock channel decode | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-17ProGPS | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv17progps_compat.py` | UV-17-family serial, 115200 8N1 | Malformed CTCSS values no longer abort channel decode | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng UV-29 Pro | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_baofeng_uv29pro.py` | UV-17-family serial through the UV-28 Plus profile, 115200 8N1 | UV-28 Plus profile, offline fixture round-trip | Stock UV-28 Plus policy | Stock UV-28 Plus policy | Experimental vendor alias; hardware validation pending |
| Baofeng UV-5G Mini | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_uv5g_mini.py` | UV-17-family serial, 115200 8N1 | Fixed GMRS frequencies; channels 15-22 retain stored duplex | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Baofeng GM-21 | Pinned CHIRP `baofeng_uv17Pro.py` with `drivers/newchirp_baofeng_gm21.py` | UV-17-family serial; GM-5RH and UV-17Pro GPS handshakes | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| AnyTone 5888UV | `drivers/newchirp_anytone.py` | Stock AnyTone clone serial | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| AnyTone AT-D578UVIII Plus | `drivers/newchirp_anytone_d578uviii.py` | D578UV CPS serial, 115200 8N1 | 4000 channels + zones | Yes, offline-tested | Hidden | Experimental |
| TYT MD-UV380 | `drivers/newchirp_tyt_mduv380.py` | ST DfuSe USB 0483:DF11 + libusb | 3000 channels + zones | Yes, offline-tested | Hidden | Experimental |
| Baofeng UV-9G | Pinned CHIRP `baofeng_wp970i.py` with `drivers/newchirp_uv9g.py` | CHIRP WP970I clone serial, 9600 8N1 | Stock CHIRP driver | Stock CHIRP driver | Invalid service calibration values are read-only and preserved | Experimental compatibility override |
| Baofeng UV-9R | `drivers/newchirp_uv9r.py` | CHIRP WP970I clone serial, 9600 8N1 | Stock CHIRP driver | Retry for missing write ACK | Stock CHIRP driver | Experimental |
| TIDRADIO TD-H3 family | `drivers/newchirp_tdh3.py` | OEM-verified TD-H3 clone serial, 38400 8N1 | Invalid brightness normalized; five-attempt identity probe | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| TIDRADIO TD-H8 fourth-generation | `drivers/newchirp_tdh8_serial.py` | ODMaster-verified TD-H8 G4 clone serial, 38,400 8N1 | Normal, HAM, and GMRS G4 identities; 151-channel physical read | Official 170-page map, offline-tested | Stock CHIRP driver | Experimental |
| TIDRADIO TD-H9 (Normal, HAM, GMRS) | `drivers/newchirp_tdh8_serial.py` | TD-H8 G4 clone serial, 38,400 8N1 (TIDRADIO templates identical apart from the identity) | Full `0x1FEF` image, G4 channel decode, offline-tested | Official 170-page G4 map, offline-tested | Stock CHIRP TD-H8 settings | Experimental |
| Radioddity GA-510 V2 | `drivers/newchirp_ga510_v2.py` | OEM CPS v1.00.36, 57,600 8N1, DTR/RTS | Dynamic five-block `0x5000` image, offline-tested | Mapped 64-byte blocks, offline-tested | Stock V2 decoder | Experimental |
| Radioddity DB25-G | `drivers/newchirp_db25g.py` | OEM DB25-G CPS clone serial, 9600 8N1, no DTR/RTS | CPS retry handshake; block framing | 16-byte blocks through 0x30FF; hardware pending | Stock decoder cross-check | Experimental |
| Radioddity DB35-G | `drivers/newchirp_db35g.py` | OEM clone serial, 115200 8N1 | 80 channels + settings | Disabled pending hardware validation | Basic radio settings | Experimental |
| Radioddity X1 Pro GMRS | `drivers/newchirp_x1pro.py` | OEM X1 Pro CPS serial, 115200 8N1, no DTR/RTS | Settings + 30 channel pages, offline-tested | Settings + all 30 channel pages, offline-tested | Full exposed settings page | Experimental |
| Radioddity GS-5B 1.XX | `drivers/newchirp_gs5b.py` | OEM GS-5B Pro CPS v1.1.3 serial, 115200 8N1, DTR/RTS on | 512 channels, offline-tested | All mapped pages, offline-tested | Preserved, hidden | Experimental |
| Midland MXT295 | `drivers/newchirp_mxt295.py` | CHIRP clone serial, 115200 8N1 | Yes, designed | Yes, hardware-tested | Radio & Modes | Hardware-tested |
| Wouxun KG-UVD1P / KG-UV2D | Pinned CHIRP `wouxun.py` with NewChirp bridge timing | CHIRP clone serial, 9600 8N1 | One-second block timeout | Stock CHIRP driver | Stock CHIRP driver | Experimental timing override |
| Wouxun KG-UV8D | Pinned CHIRP `kguv8d.py` with `drivers/newchirp_kg_uv8d_compat.py` | Wouxun clone serial, 19200 8N1, 64-byte blocks | Reserved DCS words no longer abort channel decode; raw bytes preserved | Stock CHIRP driver, offline round-trip | Stock CHIRP settings | Experimental compatibility override |
| Wouxun KG-689E / KG-699E | `drivers/newchirp_wouxun_kg689e.py` | Wouxun KG669V clone serial, 9600 8N1, DTR on (OEM CPS) | 128 channels + names, CPS block plan, replay-tested | CPS write spans with radio-limit check, replay-tested | Preserved, not decoded | Experimental; no hardware |
| Wouxun KG-905G Plus | `drivers/newchirp_kg905g.py` | Wouxun clone serial, 19200 8N1, DTR on, RTS on | Yes, offline-tested | Yes, offline-tested | Hidden | Experimental |
| Wouxun KG-Q10H | `drivers/newchirp_kgq10h.py` | Wouxun encrypted clone serial, 115200 8N1, DTR on, RTS on | Yes, offline-tested | Yes, offline-tested | Hidden | Experimental |
| Icom IC-F50V / IC-F60V | `drivers/newchirp_icom_f50v_capture.py` | Icom clone serial, 9600, model ID learned from the radio | Channel names and RX/TX from the image's section directory; tones and options not shown | Never | None | Experimental; read-only; one owner capture (Web Programmer) |
| Icom IC-F50V / IC-F60V (capture) | `drivers/newchirp_icom_f50v_capture.py` | Icom clone serial, 9600, model ID learned from the radio | Raw memory capture only, no channels decoded | Never | None | Experimental capture tool |
| Icom IC-9700 | `drivers/newchirp_icom9700.py` | Icom CI-V serial, auto-baud from 4800 to 115200 | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Icom CI-V live radios (IC-910 and others) | Pinned CHIRP `icomciv.py` with `drivers/newchirp_icomciv_tone_compat.py` | Icom CI-V serial | Unset CTCSS tones read as 88.5 Hz instead of stopping the read | Stock CHIRP driver | Stock CHIRP driver | Compatibility override; offline-tested |
| Icom IC-7200 | `drivers/newchirp_icom_ic7200.py` | Icom CI-V serial, 19200 8N1 | Corrected memory grammar | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Icom IC-7100 | `drivers/newchirp_icom_ic7100.py` | Icom CI-V serial, auto-baud | Opaque mode bytes decode read-only | Disabled for opaque channels | Stock IC-7100 settings | Experimental compatibility override |
| Icom IC-E90 / IC-T90A | `drivers/newchirp_icx90.py` | NewChirp ICF clone transport, 9600 8N1 | Four identity attempts; checksum-validated contiguous full image; invisible-slot guard | NewChirp clone-in boundary, 362 32-byte blocks, required `E6 00` | Stock ICX90 decoder | Experimental |
| Icom IC-746PRO | `drivers/newchirp_icom_ic746pro.py` | Icom CI-V serial, 9600 8N1 | Stock IC-746 family logic | Stock IC-746 family logic | Stock IC-746 family logic | Experimental model profile |
| Icom ID-50 | `drivers/newchirp_icom_id50_id52.py` | Icom `IcomCloneFormat3` serial, 9600 8N1 | Yes, physical image verified | Disabled | Hidden | Experimental |
| Icom ID-52 | `drivers/newchirp_icom_id50_id52.py` | Icom `IcomCloneFormat3` serial, 9600 8N1 | Yes, transport verified | Disabled | Hidden | Experimental |
| Icom IC-41S | `drivers/newchirp_ic41s.py` | Legacy Icom clone serial, 9600 8N1 | Yes, hardware pending | Yes, experimental | Hidden | Experimental |
| Kenwood TM-D710P / TM-D710GP | `drivers/newchirp_tmd710.py` | CHIRP TM-D710/TM-D710G clone serial | Hardware-read via rear PC port on one TM-D710A | Hardware write succeeded with 8-character names | Stock driver | Identity compatibility; read-back pending |
| Kenwood TM-V71A/E (clone mode) | `drivers/newchirp_tmv71.py` | MCP-2A clone serial, 8N1 RTS/CTS, probed baud, `0M PROGRAM` + 256-byte `R` blocks to 0x7EFF | Yes, replay-tested | Disabled | Body settings, Sky Command removed | Experimental read-only |
| Alinco DR-735 (T/E/R/J) | Pinned CHIRP `alinco_dr735t.py` with `drivers/newchirp_alinco_dr735.py` | DR-735 Memory Editor serial, 38400 8N1, echoed `AL~` lines on the rear LEFT speaker jack | 1000 common + 414 extended channels, VFO/settings/DTMF blocks kept; replay-tested | 1000 common channels with per-model band check; extended channels read-only | Not exposed yet | Experimental; hardware pending |
| Kenwood TM-D710/V71/TH-D72/TH-D74 (live mode) | `drivers/newchirp_kenwood_live_cache.py` | CHIRP Kenwood live CAT | Stock driver | Fresh-connection write and erase fixed | Stock driver | Write fix offline-tested |
| Kenwood TK-270G | `drivers/newchirp_kenwood_tk270g.py` (`NewChirpTK270G`) | Kenwood Series 60G clone serial, 9600 8E1 | NewChirp decode with raw-preserving invalid-index normalization | NewChirp write path with bank-state validation, bank-count block upload and transient checksum retry; offline-tested | Stock driver | Experimental |
| Motorola MOTOTRBO R7 | `lib/services/mototrbo_cps2_xml.dart` | CPS 2.0 Zone XML import | Conventional channels | Disabled | Import-only extras | Experimental |
| Retevis MA1 | Pinned CHIRP `th9800.py` | TYT clone serial, 38400 8N1 | Stock CHIRP driver | Stock CHIRP driver | Stock CHIRP driver | Experimental |
| Retevis MA1 model A9305B | `drivers/newchirp_retevis_ma1_a9305b.py` | TYT addressed blocks, 9600 then 57600 8N1 | 1,000 channels | Yes, offline-tested | Hidden | Experimental |
| Retevis RA89 | `drivers/newchirp_ra89.py` | OEM addressed blocks, 57,600 8N1, DTR/RTS on | 200 channels + core settings | Yes, offline-tested | Core settings and startup text | Experimental |
| TYT TH-9800 | Pinned CHIRP `th9800.py` with `drivers/newchirp_th9800_compat.py` | TYT clone serial, 38400 8N1 | Reserved tone values no longer abort the read | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Icom ID-4100 / ID-5100 | Pinned CHIRP `id5100.py` with `drivers/newchirp_icom_id5100_tone_compat.py` | Icom clone serial | DTCS(T), pocket-beep TSQL/DTCS and undefined tone values no longer abort the read | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Yaesu FT-70D | Pinned CHIRP `ft70.py` with `drivers/newchirp_ft70_compat.py` | Yaesu clone serial, 38400 8N1 | Read resyncs on the `AH51G` ID block; checksum failures explain recovery | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Yaesu VX-6 | Pinned CHIRP `vx6.py` with `drivers/newchirp_vx6_compat.py` | Yaesu clone serial, 19200 8N1 | Unprogrammable stored slots are treated as empty | Stock CHIRP driver | Stock CHIRP driver | Experimental compatibility override |
| Binqi BQ-889 analog | `drivers/newchirp_bq889_probe.py` | USB/AT probe, baud auto-detect | Read-only transport probe; no channel decoder | Disabled | Hidden | Experimental probe |

## Radio details

### Baofeng 5RH Pro v2 family

- Maintained driver: `drivers/newchirp_baofeng_5rh_pro.py`
- Protocol notes: `docs/BAOFENG_5RH_PRO_PROTOCOL.md`
- Official CPS: `Baofeng_UV-5RM_Plus_GPS_CPS_V1.17.zip`, SHA-256
  `12dbcbce64381d03e1922e481ddc7455da04755244efa5090bcdd372528318cb`
- Extracted CPS executable SHA-256:
  `0a455577b791204c42f538b04e23bfd83fef4d509f8826d753a5379d92981300`
- Driver SHA-256:
  `681e9c20e66ecde764321a3c04d1655b2721ac551877cca4526fe42584074f6d`
- Transport: 115200 then 19200 baud, 8N1, DTR and RTS asserted
- Implemented: `A` announce, seeded `PROGRAM` handshake,
  `INFORMATION` model stage, read/write direction, twelve encrypted
  4,100-byte image blocks, 640 channels, ten zones, basic settings, and
  the separate boot-image write path
- Read/write policy: full-image read and write; existing channels preserve
  firmware fields without established semantics
- Evidence: official CPS V1.17 CIL/PDB analysis plus public CHIRP PR 1625
  hardware testing on firmware `v2_0_09`
- NewChirp hardware validation: full read confirmed on a physical UV-5RM
  Plus v2 (Linux, NewChirp 1.0.61, 2026-11-19) after the radio was
  power-cycled; it first answered with a stray byte following failed
  attempts with the older UV-5RM Plus profile. Writes are not yet
  hardware-tested.
- Zones (2026-11-19 CPS V1.17 trace): zone channel IDs are big-endian
  `zone * 64 + slot` (`Frm_ZoneChn` line 583, `DataProtocol.ZoneConvert`),
  exactly what `_rebuild_zones()` writes. The device feature byte `0x73`
  bit 2 is `EnZone`; with it clear the CPS offers only zone 1, so the driver
  now exposes only zone 1 then. A reporter saw zone 2/3 edits appear in
  zone 1 after a write (mailbox INBOX:807); an offline bridge replay puts a
  zone 2 edit at channel 65 correctly, so the radio's image and what it
  shows are needed to find the cause. The desktop app still discards edits
  when switching zones before a write.
- Next milestone: the 2026-11-06 UV-5RH Pro reporter completes a read,
  compares channels with the radio, edits one unused channel, uploads it,
  reads it back, and verifies it on the radio.

### Baofeng UV-5RM Plus and UV-5RH

- Maintained compatibility: `drivers/newchirp_uv5rm_plus.py`
- 2026-11-23: the handshake retry also covers the UV-32. Baofeng "BF-UVs Pro"
  CPS v1.4.7 (UV-17/18/19/21/25/28/29/32 Pro, 5RH Pro, AR-152; ZIP SHA-256
  `d2635bde922a66a182efd00a9c6aae9e79c057648429d3f937fc28051f73fbb2`)
  discards a reply byte other than `06` and resends `PROGRAMCOLORPROU` on a
  1 s timer up to five times; a UV-32 answered `40` first (INBOX:915). The
  v2-firmware hint stays limited to models with a v2 profile.
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
- Additional evidence: the 2026-11-06 Windows 10 report from
  `[redacted-email]` selected `Baofeng_UV-5RH`, opened `COM5`, and received
  the single stray byte `0xE0` instead of `0x06` from
  `PROGRAMBFNORMALU`. Official CHIRP completed the same read, showing that
  the radio and cable support the protocol.
- Hardware validation: none for the retry override
- Next milestone: reporters retest the next normal build; the UV-5RH reporter
  should confirm that settings and channels download successfully, while the
  macOS reporter should confirm the edited channel library uploads and reads
  back correctly

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

### Baofeng UV-29 Pro

- Maintained compatibility alias: `drivers/newchirp_baofeng_uv29pro.py`
- Vendor mapping: Baofeng's official UV-29 Pro product page instructs CHIRP
  users to select the UV-28 Plus model
- Model mapping: `Baofeng_UV-29Pro` subclasses the pinned CHIRP `UV28Plus`
  class and intentionally does not redefine the transport, channel decoder,
  settings, or upload path
- Transport: pinned CHIRP UV-17-family serial at 115200 8N1
- Read/write policy: exactly the pinned UV-28 Plus profile
- Driver SHA-256:
  `3eec557a98efcdac6f25a2e15a68e047ac01fa8802a42a0db65b3982f25053fe`
- Website: `UV-29Pro (experimental)` catalog entry and matching UV-28 Plus
  Web Serial profile
- Evidence: official Baofeng product metadata and the 2026-11-14 Windows report
  in email UID 670 where `Baofeng_UV-21ProV2` received no response to the
  `PROGRAMBFNOR` identity probe
- Offline validation: the upstream `Baofeng_UV-28Plus.img` fixture decodes
  identically through both model identifiers, and an image saved as
  `Baofeng_UV-29Pro` reopens under the alias. Fixture SHA-256:
  `04c5de4c2fcb556190ddafbd9bab512326da1bf8895b8eae1d41a480c8514617`
- Hardware validation: none
- Next milestone: the reporter selects `Baofeng_UV-29Pro`, completes a read,
  saves the image, and compares the decoded channels with the radio before
  attempting any upload

### Yaesu FT-50 odd split

- Maintained compatibility: `drivers/newchirp_ft50_compat.py`
- Transport: pinned CHIRP Yaesu clone serial at 9600 8N2. ADMS-1E builds a
  Win16 DCB from the literal `9600,n,8,2` before opening communication.
- Decode policy: duplex code `3` represents an odd-split channel. Expose it as
  CHIRP's `split` duplex with the stored offset as the transmit frequency.
- Write policy: the stock FT-50 encoder now accepts `split`; channel fields
  continue to use the established 16-byte record layout
- Hardware (2026-11-19): the reporter programmed an odd-split channel,
  wrote it, and read it back correctly (mailbox INBOX:815).
- Evidence: email UID 672 from `[redacted-email]` supplied NewChirp image
  `newchirp-1tmrlsdr.img`, SHA-256
  `db87e5dd14f0333f1f7fe72e35cfb984054d96c30c543c33c7ef092cfbccca32`
- OEM evidence: ADMS-1E `Wft50.exe` SHA-256
  `06f0be506b59153059d130e4fb5948049f0a40dd44f6df051097b9272f17945b`;
  static call path at `1040:0a0d` uses `BuildCommDCB`, `SetCommState`,
  `READCOMM`, and `WRITECOMM`. See `docs/YAESU_FT-50_PROTOCOL.md`.
- Reporter image: 57 active channels, including ten odd-split channels
  (`6, 7, 60, 77, 81, 83, 85, 86, 87, 89`); channel 6 receives on
  155.700 MHz and transmits on 154.755 MHz
- Erase policy (2026-11-18): the FT-50 stores each channel's flag byte twice,
  at `0x001A` and `0x079C`. Both physical-radio images (the reporter image
  and CHIRP `tests/images/Yaesu_FT-50.img`) keep the tables identical, with
  empty slots at `0x00`. Stock `set_memory` cleared only the first table's
  `used` bit and returned before its copy to `flag_repeat`, so a cleared
  channel was uploaded as `0x02`/`0x03` and stayed on the radio (reporter
  confirmed: blanked channels survived a write). The override clears `used`,
  `mask`, and `skip` in both tables. Upstream CHIRP master has the same code.
  ADMS-1E references neither table by literal offset; its delete path is not
  yet traced (E1 pending). Evidence: E2 (`test/ft50_erase_test.py`).
  Hardware (2026-11-19): the reporter cleared the stale channels, wrote,
  read back, and confirmed they are gone (mailbox INBOX:805).
- Driver SHA-256:
  `68457dacb8d164c1eff28a51b605a4baeb3651fa894cfe4deacd3184a80db73a`
- Offline validation: all active channels decode, editing a split channel
  round-trips through the stock encoder, and the bridge opens the FT-50
  transport with two stop bits.
- Hardware validation: partial. On 2026-11-17, Mark reported that NewChirp
  1.0.56 changed one character in channel 1's name and committed that write.
  Every other channel remained identical to the original image. Changing the
  character back and writing again changed only channel 1's name. This
  verifies the 9600 8N2 upload transport, targeted channel write, radio
  commit, and preservation of unchanged channels.
- Next milestone: write one unused odd-split channel with RX frequency, split
  TX frequency, tone, name, and power; power-cycle the radio, read it back,
  and verify every field. Do not promote the entire driver to hardware-tested
  until that field-level round-trip succeeds.

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

### Yaesu FT-70D

- Maintained compatibility: `drivers/newchirp_ft70_compat.py`
- Transport (Yaesu ADMS-10 1.0.1.0, `adms10.exe`
  `SerialProtocol.backgroundWorker1_DoWork`, static .NET decompile): 38400
  8N1, no handshake. The radio sends a 10-byte ID starting `AH51G`; ADMS
  rejects any other ID, sends one ACK (0x06), then reads 65,216 data bytes
  in 64-byte pieces (5 s first-byte, 1 s inter-block timeout) and one
  checksum byte. Checksum is the low byte of the sum of the ID and data
  bytes, matching CHIRP's `YaesuChecksum(0x0000, 0xFEC9)` at 0xFECA. ADMS
  writes the same order with 64-byte blocks 15 ms apart after a 2 s pause.
  `default_en.dat` is 65,216 bytes, so the stock image size is unchanged.
- Read policy: clear stale serial input, discard bytes received ahead of
  `AH51G` (up to 64), reject a non-FT-70D stream, and turn a checksum
  failure into ADMS-from-cold recovery guidance. Layout, checksum and the
  stock write path are unchanged.
- Evidence: static ADMS-10 REA (package sha256 `ea61c942…499c`); 2026-11-23 report (INBOX:938) of
  `Checksum Failed [0000-FEC9 (@FECA)]` after an early-[BAND] attempt;
  offline tests in `test/ft70_id5100_compat_test.py`
- Hardware validation: pending
- Next milestone: reporter re-reads with the update; a clean read confirms
  the stray-byte cause

### Icom ID-4100 / ID-5100 tone modes

- Maintained compatibility: `drivers/newchirp_icom_id5100_tone_compat.py`
- Decode policy: tone-mode value 8 (`DTCS-T`, the radio's DTCS(T) encode-only
  setting) is CHIRP cross mode `DTCS->`; values 2 and 4 (TSQL/DTCS with
  pocket beep) show as TSQL/DTCS and keep the pocket-beep value when an
  unchanged channel is written; undefined values 12-15 read as no tone
  without changing image bytes; TSQL-R and DTCS-R are editable
- Evidence: CHIRP `id5100.py` TMODES table and the 2026-11-23 report
  (INBOX:940) of `` `DTCS-T' is not in valid list ``; no image attached;
  offline tests use the CHIRP ID-4100 and ID-5100 fixtures
- Hardware validation: pending
- Next milestone: reporter reads the radio with the update and confirms the
  DTCS(T) channel shows as Cross `DTCS->`

### Binqi BQ-889 analog probe

- Maintained probe: `drivers/newchirp_bq889_probe.py`
- Protocol notes: `docs/BQ889_PROTOCOL.md`
- Related OEM utility: KSUN `POC写号通用工具V6.2_BLT`, SHA-256
  `9e2d4a316225e1e5837d535b53c7fa1d9a34c625af96723a222b22304fab5577`
- Hardware evidence: FCC ID `2BNNE-BQ-889`, Beken `BK4819`, and
  `BQ-889_MAIN_V2.3`
- Transport: candidate USB/AT serial interface; baud rate and control lines
  are not yet confirmed
- Implemented: selectable read-only probe for `AT`, `AT*READVER`, `AT+CGMR`,
  `AT+HSQ=R`, `AT+HXTO=R`, and `AT+HCHDATA=R`, with a bounded transcript
- Read/write policy: no codeplug decode yet; all writes disabled
- Evidence: FCC teardown, manual, and static strings from the related KSUN
  utility only (E0)
- NewChirp hardware validation: none
- Next milestone: Frank Lopez Sr. selects `Binqi BQ-889 Analog Probe`, runs
  Download From Radio, and sends the generated read-only transcript

### Quansheng UV-K5 (V1) with Robzyl RO-KO 512K firmware

- Maintained driver: `drivers/newchirp_uvk5_roko512k.py`
  (`Quansheng_UV-K5_RO-KO_512K`), model "UV-K5 (RO-KO 512K)"
- Firmware oracle: K5Quan/Robzyl_512K_RO_KO commit
  `a4ab1a0b6ff56fbe33c1ea202d0e07d5241fc81a` (Apache-2.0). `misc.h` with
  `ENABLE_EEPROM_512K`: 999 channels, 16-byte records at `0x2000`,
  attributes at `0x5E80` (band low nibble, scan list high nibble), names in
  16-byte slots at `0x6280` (10 characters used), history at `0xA100`.
  `radio.c` `RADIO_ConfigureChannel` defines the field rules; `dcs.c` has 55
  CTCSS tones (standard 50 plus 55.0-65.0 Hz); `frequencies.c` the 21-step
  table. The author's own CHIRP module carries a stale 24-entry step list;
  the firmware table is used.
- Transport: stock UV-K5 hello and 0x80-byte 0x051B reads of `0x0000-0xA0FF`,
  38400 8N1. Accepted identity: firmware starting `RO-KO` (V6.11 reports
  "RO-KO V6.11"). The 8K and 512K builds report the same version, so the
  driver refuses an image whose `0x2000-0x7FFF` repeats the first 8 KB (a
  24C64 ignores the upper address bits).
- Implemented: frequency, offset/direction, FM/NFM/AM/NAM, SSB shown as USB,
  Low/Mid/High power, 10-character name, CTCSS (including the five low
  tones)/DCS with cross modes, step; read-only extras for bandwidth,
  modulation, scan list, scrambler, busy lockout and reverse
- Read/write policy: read-only (`NEWCHIRP_WRITE_DISABLED`); `sync_out` and
  `set_memory` refuse before any radio I/O. Web Programmer profile
  `quansheng-uv-k5-roko-512k` is read-only too.
- Driver SHA-256: `a2d05335e3abb873114ef73a43e36d86df84de6aa5593b7f19e151da9ed7f463`
- Field request: forum file drop `512k_CHIRP_UV-K5_V1_ROBZYL-KO.py`
  (2026-11-22, SHA-256
  `06df9e84441162d9e65e044f7cecb3b6308c69c3d6a1cef6c3d09de5fd2086ef`). That
  module split the attribute byte 5/3, used 16-character names and wrote
  0xA100 bytes without a firmware or EEPROM-size check; it was not used.
  Ledger `w-20261123-211e`.
- Hardware validation: none
- Next milestone: a physical read from an upgraded radio, then a controlled
  single-channel write and read-back before enabling writes

### AnyTone AT-D878UVII Plus

- Maintained driver: `drivers/newchirp_anytone_d878uvii.py` (`AnyTone_AT-D878UVII_Plus`),
  a read-only subclass of the AT-D578UVIII Plus driver
- Protocol notes: `docs/ANYTONE_D578UVIII_PROTOCOL.md` (shared AnyTone session)
- Transport: `PROGRAM` -> `QX 06`, `02` -> `I` + model + bands + version + `06`,
  16-byte `R`/`W` frames, `END`; 115200 8N1. Accepted identity: `D878UV2`.
- Official CPS evidence: BridgeCom "D878UVII PLUS V4.00 official release 250815"
  (ZIP SHA-256 `5ba14d88cebef105365e8977529a5817d1d163a9e9eccc5156ccd9575be500e6`),
  `D878UVII.exe` (SHA-256
  `4e7f8b4d6e119b8b9ef0a4ffd82aef2bd83d1887d11e5651596b86f371711005`): contains
  the `D878UV2` model string and the channel-bitmap `0x024C1500`, zone-bitmap
  `0x024C1300` and zone-name `0x02540000` addresses as constants (static string
  and constant evidence only, no disassembly).
- Implementation reference: QDMR commit `fb9c96af53f646c0706fa360209b2e0e6cd79a08`
  (`anytone_interface.cc` maps `D878UV2` to the D878UVII; `D878UV2Codeplug`
  inherits the D878UV/D868UV channel and zone layout; channel bytes
  `0x00-0x33` match the fields decoded by the D578 driver).
- Implemented: 4000 conventional channels (128 per bank), frequency/offset,
  FM/NFM/DMR, Low/Mid/High/Turbo power (1/2.5/5/7 W nominal), name, CTCSS/DCS,
  color code, time slot, TX contact index, RX group index, receive-only,
  talkaround, and 250 zones; VHF 136-174 and UHF 400-480 MHz
- Read/write policy: read-only (`NEWCHIRP_WRITE_DISABLED`); `sync_out` refuses
  before any radio I/O. Web Programmer profile `anytone-at-d878uvii-plus` is
  read-only too.
- Driver SHA-256:
  `f7c4a1f39d0dd931ec1015b4898bb0c22f761630bdbc9932f227053534f8aca8`
- Field request: forum topic "Can you configure a connection to Anytone
  AT-D878UVII PLUS" (2026-11-21); the owner's radio rebooted harmlessly when
  the D578 profile refused its identity and ended PC mode. Ledger
  `w-20261123-2772`.
- Hardware validation: none
- Next milestone: a physical read compared with the official CPS, then a
  controlled single-channel write and read-back before enabling writes

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
  `d760e08ed0866cce18ef575a13532656baa177d376a7ca74336373294d2eb7ea`
- 2026-11-23 channel-bank correction: QDMR computes `0x00800000 + (i / 128)
  * 0x40000 + (i % 128) * 0x40` for the D868UV/D878UV/D578UV codeplugs
  (`d868uv_codeplug.cc:1618`, `d578uv_codeplug.cc:3415`); the driver used
  1000 channels per bank, which put channel 129 at `0x00802000`, the
  channel-extension area. Reads of channels 129+ were wrong and a write
  could have overwritten other channels' extension records. Now 128 per
  bank (desktop and Web Programmer). No hardware reports were affected.
- Known limitation: High and Turbo have the same wattage in the power list,
  so a Turbo channel edited here is written as High.
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
  `273e6a444854e8fcc6cb6a07d0faed021aa2a0957421d98eddbaa8101666a176`
- Hardware validation: none
- 1.0.48 field correction: active-channel selection now reads with `MC0;`
  and sends `MC0nnnnn;` without waiting for a nonexistent response.
- Next milestone: physical empty-memory behavior, one controlled memory write,
  read-back, tone comparison, and repeater-shift verification

### Yaesu FT-991A

- Maintained driver: `drivers/newchirp_yaesu_ft991a.py`
- Protocol notes: `docs/YAESU_FT991A_PROTOCOL.md`
- Transport: Yaesu live CAT serial at 38400, 19200, 9600, or 4800 baud;
  identity `0670`
- Implemented: 117 live memory channels, 12-character tags, frequency,
  repeater shift, FM/NFM, AM, LSB/USB, CW sideband, RTTY sideband, DATA
  sideband/FM, C4FM, CTCSS, and DCS
- Write policy: read/modify/write only validated channel pairs through
  documented/field-traced SPR and SPW commands; unknown channel bytes remain
  unchanged
- Safety limits: unsupported nonstandard split frequencies, per-channel RF
  power, and radio-wide DCS polarity are not modified
- Evidence: Yaesu CAT reference SHA-256
  `52164f737e37a3ffc8276eccedf8ecb524607198c38d386ae4ff7b2fc1d60c95`,
  Gil Kloepfer memory map revision 0.7f SHA-256
  `dc72359ca2c5b983b5821a727c0b5f62a5d9b7b87461259765bcf4d450e26e5c`,
  SPR/SPW pseudocode SHA-256
  `ae87abeac11960fcd65a18ae0d1bb00e39cfd1649b0e6e651844d9610a8c5bee`,
  and CHIRP issue 2531 packet capture SHA-256
  `8ca3fe60db1ad2294c963ecc2db495d647fc32cda2ae6b801d1214935b9949c0`
- Driver SHA-256:
  `6c406c883c30a29d4ceed14c7058500c450a1b0f70bcc8bb03faa4316be7cfcb`
- Hardware validation: none
- Next milestone: physical read-only comparison against the radio and an
  existing programmer, followed by one inactive-channel write and read-back

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
- Identity: the 0xA2 identity upload asks for 64 bytes and accepts a shorter
  reply, as dmrconfig's identify() does; the model name is in the first 32
  bytes. A 2026-11-25 macOS report (INBOX:986) got 32 bytes and stock-strict
  handling stopped the read. Memory reads still require full blocks.

### Retevis RT22

- Maintained file: `drivers/newchirp_retevis_rt22.py`; replaces
  `retevis_rt22._rt22_enter_programming_mode` in place for the plain
  `Retevis_RT22` model only. KD-C1, RT22FRS, RT622, BF-T20 and the other
  RT22-family models keep CHIRP's ID list.
- Driver SHA-256:
  `77433ffc6919b2b81628af26f7adfb4f527407d745b5e84fad6d30eba495930c`
- Field issue (ledger `w-20261121-badb`, INBOX:871/875): 2025 RT22 units fail
  "Radio identification failed" in NewChirp and stock CHIRP while older units
  read; upstream CHIRP #6747 has been open since 2019.
- OEM evidence: Retevis "RT22-Programming-Software" (retevis.com, listed
  2025-10-31; ZIP SHA-256
  `acefd8d334c55ec34edd0b05de4dc74c115d5ab70073084c9bc2d52b2f08f68d`),
  installer `RT22-DSETUP-V1.05.EXE` (SHA-256
  `8fe80ec050b121a9cffdfd9a507a4020226b64bcab33bba9aa05d20cfbae58f1`), main
  MFC program (SHA-256
  `6c0c179ccf5da02d737374b10d54dc7efc4289ca86db2d890982d1df839a4ea4`).
  Disassembly at `0x4022CC`: `PROGRGS` with up to 10 tries for `06`, then `02`
  and an 8-byte read (500 ms); it fails only on no reply or fewer than 8
  bytes, sends `06`, and reads memory. The ID buffer is overwritten by the
  first `R` reply before any comparison. Writes are `W <addr> 10` up to
  `0x3F0`, the same `0x400` bytes CHIRP reads.
- Change: the plain RT22 accepts any complete 8-byte ID (unknown IDs are
  logged); a short reply reports its bytes. CHIRP's extra `07`/`4E` step,
  which the Retevis software does not send, is kept because older units
  answer it; if a newer unit refuses it, that step is the next suspect.
- Tone OFF (2026-11-23, INBOX:925): the Retevis software writes "no tone" as
  `FF FF` (`0x40DAAE`/`0x40DBA4`), as stock CHIRP's `tone_init=0xFFFF` does
  on the desktop. The Web Programmer wrote `00 00`, and a 2025 unit then
  stayed muted on those channels as if a tone were set. Web fix `b89bf7a`
  writes `FF FF` and repairs `00 00` on channels in use. The Retevis
  software also writes the identity block at `0x000` and checks a 6-byte
  password at `0x360` before writing; it never changes channel bytes 12, 14
  or 15.
- Hardware validation: none.

### Retevis RA87

- Maintained file: `drivers/newchirp_retevis_ra87.py`; it replaces
  `retevis_ra87._enter_programming_mode_download` in place, so the
  `Retevis_RA87` IDs and images are unchanged.
- Driver SHA-256:
  `c55ada0767c973f21c643f709c82ae0956dd8bf75913f4bc23871336d759c615`
- Field issue (ledger `w-20261122-8452`, INBOX:888): "Radio identification
  failed" after `PROGRAM` (echo + ACK) and `0x02` (echo + 8-byte ident). The
  ident bytes are not in the 1.0.66 trace.
- OEM evidence: Retevis RA87 CPS `RunApp.exe` (VB6) inside
  `ra87-programming-software_20251104150930_0234.zip` (SHA-256
  `54d14be98e42274419946de60ccf998f19114ae47d69b98f347bf02c7fdf8eb0`; an
  Advanced Installer bootstrapper whose payload's first 512 bytes per file
  are XOR 0xFF). Its command scripts give the read handshake as
  `TX PROGRAM RX 06 TX 02 RX VA*8 TX 06 RX 06` (any 8 bytes) and identify the
  model with `TX 52 1F 05 01 RX 57 1F 05 01 <5A|79|A5>`. The exit script
  `45 5A A5 32 23 45 F2` equals CHIRP's `CMD_EXIT`. The three model values sit
  next to the 134-176, 340-400 and 400-480 MHz range strings in that order;
  the A5/400-480 pairing is static string-table evidence, corroborated by the
  CHIRP sample image and the stock upload check, not by disassembly.
- Change: the 8-byte ident is the image's 0x1F00-0x1F07 block (CHIRP's sample
  holds `FF FF FF FF FF A5 2C FF` there), so the download accepts any ident
  whose byte 5 is A5. 5A/79 are refused by band name; anything else reports
  the bytes. Everything after identification is the stock sequence.
- Hardware validation: none. Next: the reporter's 1.0.68 trace or a read on
  the fixed build.

### Baofeng UV-5R Mini

- Maintained file: `drivers/newchirp_uv5r_mini.py`; sets
  `UV5RMini.download_function`. `UV-5G Mini` (a subclass) keeps the stock
  read.
- Driver SHA-256:
  `bc3014cf4509165cfe1dd4a10274ddc3bf2004cdebfc7260a5414b407785ba6c`
- Field issue (ledger `w-20261122-e807`, INBOX:885/886): about 75 blocks read
  normally, then one block request got no reply and the read failed. A first
  attempt on another port got `P` (the handshake echoed), so that port was
  not the programming cable.
- OEM evidence: Baofeng UV-5R Mini CPS v1.0.7
  (`Baofeng_UV_5R_Mini_CPS_V1.0.7.zip`, SHA-256
  `f96977b15bd9859fc53d0fe432ea48d4c4994074de73555ce8615d3d9e38f607`), .NET,
  decompiled `KDH.Communication.Read`: `52 hi lo 40`, wait for 68 bytes, a
  1 s timer resends the same request up to five more times
  (`timesOfRetry = 5`); address walk 0x0000-0x803F, 0x9000-0x903F,
  0xA000-0xA1BF, matching CHIRP.
- Change: each block is requested up to six times, the input is flushed
  between attempts, and a final failure names the block. Upload is stock.
- Handshake (2026-11-24, ledger `w-20261124-87c9`, INBOX:948/950): two more
  owners got `P` (0x50) as the first handshake byte; one read a UV-5RM on the
  same cable and port right after. CPS v1.0.7 `KDH.Communication.HandShake`
  (`STEP_HANDSHAKE_2`) reads one byte at a time and ignores anything that
  is not 0x06, so a stray byte or an echoed command is skipped and a later
  ACK is accepted; its 1 s timer resends the code up to five times. The
  UV-5R Mini now uses `drivers/newchirp_uv5rm_plus.py`'s handshake retry,
  which also reads up to 24 more bytes in that second looking for the ACK.
  If all five attempts hear only the echoed `PROGRAMCOLORPROU`, the error
  says the plug is not fully in (or the radio is off) instead of
  "Unexpected response". This applies to every model in that module's
  `RETRY_MODELS` (UV-5RM Plus, UV-5RH, UV-32, UV-5R Mini).
- Hardware validation: none.

### Yaesu VX-170 / VX-177

- Maintained file: `drivers/newchirp_yaesu_vx170.py`; `VX170Radio` and
  `VX177Radio` replace the stock registrations, keeping the `Yaesu_VX-170`
  and `Yaesu_VX-177` IDs.
- Driver SHA-256:
  `8bbc373d93ef8ee955646c509a4685487430666bff3e05fc8ac5841359b527f1`
- Transport: unchanged stock CHIRP Yaesu clone (FT-7800 family, 6057 bytes).
- Field issue (ledger `w-20261122-28ff`, INBOX:893): a 193-channel codeplug
  from another tool downloaded, then decoding failed with "list index out of
  range". The memory `tmode` field is 3 bits but stock `TMODES` lists five
  values, so `self.TMODES[_mem.tmode]` overflows on 5-7 (the same traceback
  is in upstream CHIRP #11624's debug log; upstream master is unchanged).
- Evidence for 5-7: the VX-170 manual's Set Mode Item 44 SQL.TYP lists OFF /
  TONE / TSQL / REV TN / DCS, then, with Item 43 SPLIT on, D (DCS encode
  only), T DCS and D TSQL; CHIRP's FT-60 driver (same generation, same
  `tmode:3` layout) maps 5-7 to `DTCS->`, `Tone->DTCS`, `DTCS->Tone`. No
  Yaesu CPS exists for this radio (only RT Systems ADMS-VX170), so there is
  no CPS or OEM-capture evidence. EPCS (ECS) is not mapped.
- Change: raw 5-7 decode as CHIRP Cross with those cross modes and encode
  back to the same raw value; 0-4 use the stock code unchanged. Offline tests
  use a synthetic image (CHIRP ships no VX-170 sample).
- Hardware validation: none. The reporter's image has been requested to
  confirm which values their channels hold.
- Next milestone: decode the reporter's image; then a physical read and an
  unchanged write/read-back.

### Yaesu FTM-7250D

- Maintained file: `drivers/newchirp_ftm7250.py`
- Driver SHA-256:
  `72c2af9f086edc882bd402f612d5ac66f19d897424f35866aa5b186c264d18a6`
- Transport: pinned CHIRP Yaesu clone serial at 38400 8N1
- Read policy: stock `ftm7250d.py` image layout and 199-memory decoder
- Field issue: the 2026-11-10 report from `[redacted-email]` showed
  that selecting Low power programmed High. The pinned driver's decode path
  treats stored codes 1/2/3 as Low/Mid/High, but its inherited write helper
  encoded them in reverse.
- Change: NewChirp overrides `_encode_power_level()` so Low/Mid/High write as
  1/2/3. The bundled FTM-7250D image test verifies all three values round-trip.
- Settings: the pinned CHIRP driver does not implement radio-wide settings;
  NewChirp reports that state rather than treating it as a failed read.
- Hardware validation: Radio-Club Cyrano reported real FTM-7250D programming
  before this correction. A physical Low/Mid/High write and radio-display check
  after the fix is pending.
- Follow-up: the 2026-11-18 report confirmed that removed channels still
  survived an upload and that transmit-power controls disappeared after a CSV
  replacement. The CSV path incorrectly discarded the selected radio's
  capability set, which hid power controls on every channel. Full-image
  uploads now also derive their clear set from every in-range location absent
  from the active library instead of relying only on tracked removals.
- Next milestone: the reporter verifies power labels on a harmless channel,
  then reuses the corrected image to confirm removed memory slots are erased.

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
  report from [redacted-email]. The FT5D completed its Send operation after
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
- 2026-11-23 tone decoding (INBOX:919): mirrors the CPS exactly
  (`GetQTInfo_HexToStr`): a zero high byte is a 1-based DCS index, otherwise
  CTCSS with a low byte of `00`/`FF` meaning OFF. Previously `0x0800`-style
  words decoded as tones, and a channel holding `0x5750` (shown as "2235.2"
  by the CPS too) stopped the whole read; out-of-list tones now read as none
  (driver is read-only). Web Programmer decoder updated to match.
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

### Radtel RT-950 Pro

- **Write pause 2026-11-20, lifted the same day.** An owner reported that
  the RT-950 Pro beeped on PTT and would not transmit after a NewChirp write
  (INBOX:849, ledger `w-20261120-9877`), so writes were suspended on desktop
  and in the Web Programmer. REA of the Pro CPS 1.3.3 (`BT-RT950PRO_CPS.exe`
  SHA-256 `1a20aa53...`) showed NewChirp's channel encoder matches
  `SetCHInfo_Parameter` byte for byte, the CPS accepts TX at 18-1000 MHz
  with no amateur-band limit, and no radio-wide setting blocks transmit; the
  only per-channel TX-off is a blank TX frequency (Duplex "off"). The owner
  then found his channels had transmit off; after turning it on and
  re-writing, the radio transmits on 156.800 MHz (INBOX:853). Cause: TX-off
  channels, not the write. The write confirmation now lists receive-only
  channels, the marine template explains its receive-only default, and the
  write prompt mentions TX off. An earlier amateur-band TX warning
  (8a815371) was reverted as unsupported by the CPS.
- Maintained driver: `drivers/newchirp_rt950pro.py`
- Protocol notes: `docs/RT950PRO_PROTOCOL.md`
- Separation: distinct `Radtel_RT-950_Pro` model; the base RT-950 stays
  read-only
- Evidence: Radtel RT-950PRO CPS V1.3.3 (2026-06-22) from radtels.com.
  Archive SHA-256
  `96bf4f13089dd401e74f91d7a7c32d56d98300c1fb03daf2798b40d43fd5191f`;
  `BT-RT950PRO_CPS.exe` SHA-256
  `1a20aa5390345f879f64cfe8d3a299671ca0fb975c38bb191958840e9fa6441d`;
  traced `KDH.RWDataOperation` (`HandShake`, `ReadRadioData`,
  `WriteRadioData`, `Set/GetCHInfo_Parameter`) and `ChannelData`
- Transport: shared RT-950/BT-9000 handshake at 115200 8N1 with a 3.0-second
  initial ACK window; writes require model code exactly `RT-950` (the base
  radio reports `BT-9000`)
- Map: 272 blocks in CPS order: `0x52/0x57` 0x0000-0x7FFF (990 channels),
  0x8000, 0x9000, 0xA000-0xA17F, 0xB000-0xB0FF, 0xC000-0xC0FF (zone names),
  0xD000-0xD2FF, then APRS `0x54/0x58` 0x0000. Image 0xD380 with APRS at
  0xD300; legacy 0xD300 images open read-only
- Implemented: 990-channel decode and CPS encoder (frequency, tones, power,
  scramble, encryption, BCL, scan, AM, bandwidth, FHSS code in CPS byte
  order, PTT ID BOT/EOT/BOTH, signalling group 1-15, GB2312 names);
  6.25/12.5 kHz steps accepted
- Read/write policy: writes enabled as experimental. Every block is written
  with one `0x06` ACK, up to three resends after 1 s, then `E`; blocks not
  edited are written back byte-for-byte. Refused for a non-`RT-950` model or
  a legacy image before any write byte is sent
- Evidence levels: E1 static CPS trace; E2 replay in
  `test/rt950pro_driver_test.py` (CPS block order, ACK retry/stop, encoder,
  app round trip of 580 random channels byte-identical); physical read on
  the old map confirmed by a reporter (INBOX:789, 1.0.58, stock firmware)
- Physical write validation: none
- Android Bluetooth (2026-11-20, ledger `w-20261120-36d6`): experimental
  read-only support for stock `Radtel_RT-950_Pro` over FFE0/FFE1. The setup
  tells the owner to enable BT Write; a zero-byte BLE handshake or first block
  explains BT Write and the stock-versus-nicFW950 profile choice. Bluetooth
  upload is refused in both the model/controller and the Python driver before
  a radio command is sent.
- Bluetooth evidence: Radtel's official product page advertises phone
  programming; Play package `com.uniapp.kdh.uniplugin_kdh` version 1.4.7
  statically shows `flutter_blue_plus`, `write_without_response`,
  `handleBluetoothData`, and KDH secret-key generation; the CPS stores the BT
  Write switch at function-settings part 1 byte 29. No OEM BLE capture or
  complete app call path has been recovered. Reusing the raw stock frame over
  BLE remains a hypothesis.
- Bluetooth write: not implemented. Uploading over BLE is blocked until a
  complete physical Bluetooth read is confirmed and a separate write design
  review covers dropped-link recovery.
- Next milestone: a stock-firmware owner enables BT Write, selects
  `Radtel RT-950 Pro`, completes a full Android Bluetooth read, and sends the
  Bluetooth diagnostics. A one-channel USB write/read-back remains separate.

### Radtel RT-860

- Maintained driver: `drivers/newchirp_rt860.py`
- Protocol notes: `docs/RT860_PROTOCOL.md`
- Evidence: official RT-860 CPS V1.06 (2025-06-20), .NET metadata and CIL
- CPS artifact SHA-256:
  `4a5a4b00a79fa4f6aae8ab77ae40cbaa954033b0089a3250e0a02448ae478a26`
- Extracted CPS executable SHA-256:
  `f9b3d9d3fadae96caa3a1a0480a0f8a8622957d2142a745e70c1b711393ada69`
- Transport: 115200 8N1, DTR asserted, RTS not asserted, no hardware or
  XON/XOFF flow control
- Handshake: `34 52 05 10 9B`, one-byte ACK `06`; exit is
  `34 52 05 EE 79`
- Read blocks: 1,028-byte binary frames with an echoed `52` page header,
  1,024-byte payload, and one-byte additive checksum over the first 1,027
  bytes
- Read strategy: the exact OEM sparse 184-page sequence for settings,
  1,024 channels, 256 zones, and 128 broadcast memories
- Implemented: receive/transmit frequency, duplex, CTCSS/DCS, FM/NFM/AM/USB,
  Low/High power, scan skip, 16-character GBK names, channel extras inherited
  from the shared RT-880G record layout, and GBK zone membership
- Read/write state: read implemented; every upload entry point is disabled.
  The CPS write opcodes are recorded but the password branch and complete
  acknowledgement flow are not yet validated.
- Offline validation: registration, serial policy, exact sparse-page order,
  fragmented 1,028-byte responses, malformed checksums, wrong page echoes,
  short responses, channel decoding, zone decoding, GBK names, and write
  rejection
- Hardware validation: a 2026-11-08 macOS NewChirp 1.0.48 report from
  `[redacted-email]` completed two RT-860 reads and decoded 311 channels
  through the same USB serial adapter that had just read a UV-5R Mini. No
  saved image, serial capture, or OEM-CPS comparison was attached, and
  uploads remain disabled.
- Unresolved: LSB/USB/CW selection, setting-block semantics, unknown channel
  bytes, and the complete upload state machine
- Next milestone: capture the OEM reading a physical RT-860, compare an
  unedited NewChirp read with the CPS export, then replay-test the write path

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
  `a3166f66517999e3db2cd015bce69faf3f423c5ccb9446d124b1f9a58356ce03`
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
- A9305B channel byte 12 is split into four two-bit fields. Bits 0-1 are
  transmit inhibit and reverse, bits 2-3 are busy-channel behavior, bits 4-5
  select Wide/Mid/Narrow, and bits 6-7 select High/Mid/Low. The official CPS
  reads and writes power with masks `0xC0`/shift 6 and bandwidth with
  `0x30`/shift 4. The first driver had those two fields reversed, so power
  appeared High and every wide channel appeared narrow.
- Zoran's 2026-11-10 OEM CPS screenshot and 2026-11-05 `.icf` independently
  show channels 6-14 as Low, channel 15 as Mid, channel 16 as High, channels
  17-21 as Mid, channel 22 as Low, and all 22 as Wide. Decoding the payloads
  from the `.icf` now matches that table exactly. An `.icf` row contains a
  four-character address, a two-character row checksum, and 64 data
  characters; the checksum is not part of the channel record stream.
- A9305B writable ranges mirror the CPS and exclude
  `0x1680-0x19BF`, `0x2B80-0x31FF`, `0x3284-0x3FFF`, and
  `0xBED0-0xCFFF`.
- A 2026-11-08 complete read from another A9305B-labelled unit omitted the
  expected `MA1-A9305B` marker at `0x19C0`. NewChirp now retains and decodes
  that image for evidence collection but forces it read-only until the variant
  is compared with its CPS.
- Offline validation: registration of both MA1 variants, channel decoding
  across both 200/800 sections, 16-character names, tone fields, active/skip
  bitmaps, model fingerprinting, complete binary and ASCII-hex read framing,
  short response packets, opaque read checksums, write-side block checksums,
  complete write framing, and the reported power/bandwidth table. The focused
  A9305B suite runs 14 tests.
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

### Retevis RA89

- Maintained driver: `drivers/newchirp_ra89.py`
- Protocol notes: `docs/RA89_PROTOCOL.md`
- Official CPS package: `RA89-Programming-Software.zip`, SHA-256
  `ba792a74a122f33c4b70405aae0ab35018efa3e75842b8efe4e94f360015a500`
- Inner installer: `RA89_20230909_V108.exe`, SHA-256
  `610cbca1ba74cde6fed09ea7ff8639a23f7bced111210569f4c86c14ab61194e`
- Main .NET application SHA-256:
  `d313f027c3310ca5166cdcfe98022e6f59d98716584487e5b47210825b0ea3c6`
- Driver SHA-256:
  `1df11114ceedcc3c12c1fff1dc088f57e051c61a97e4b12a8d2ca08fafee49cf`
- Transport: 57,600 baud, 8N1, DTR and RTS asserted, no hardware or software
  flow control. The OEM CPS waits 500 ms after opening the port and allows
  three seconds per response.
- Session: `UV99` identify, optional `E7` programming-code stage, 57,600-baud
  setup, `E2`/`E3` read/write mode, 32-byte addressed block commands, and
  `E5` exit. The receive path uses exact 36-byte identify, 7-byte ACK, and
  `payload length + 13` block response counts. The OEM callback requires
  `BytesToRead == ReceivedBytesThreshold`; NewChirp accumulates fragmented
  responses until the exact count arrives or the command deadline expires.
- Implemented: all 200 channels, 16-character names, RX/TX frequency,
  duplex/split/off, CTCSS/DCS with polarity and cross modes, FM/NFM/WFM, three
  power levels, scan skip, bus lock, optional signaling, PTT ID, tuning step,
  scramble, core settings, startup text, side keys, and work modes.
- Read/write policy: full 0x22A0 image read and ordered 32-byte writes, except
  the OEM protected range `0x1680-0x193F`. Read-side checksum differences are
  logged but not rejected because the OEM receive path discards that field.
  Unknown fields and the protected range are preserved byte-for-byte.
- Evidence: static CIL analysis of `serialPortResSetPro`, `SendComDatPro`,
  `SendBaudComDatPro`, `GetDataTxRxBytePro`, `SendReadDatAddComPro`,
  `GetChkSum_AddrPro`, `SendWriteDatAddComPro`, `SaveReadDataPro`,
  `DisplayText`, and `serialPort1_DataReceived`; vendor sample ICF SHA-256
  `cd5fb8f5ad492d6e28bc6db108547558176783ea965e32cfcbd5da30b01ed811`
  independently confirms the 21-byte channel records, 200-bit active/skip
  maps, 10-byte extended names, and sample frequencies. The pinned CHIRP
  `th_uv88.py` profile was used only as a field-semantic comparison.
- Hardware validation: none. The 2026-11-07 report from [redacted-email]
  stopped at the inherited CHIRP driver's 10-byte TYT handshake. The OEM CPS
  asserts DTR/RTS and emits the same `FEFEEEEFE055563939FD` identify frame
  after its 500 ms setup delay; this maintained driver now follows that path.
- Next milestone: the reporter reads the radio on the next build, saves an
  unedited image, and compares channels/settings with the CPS or radio display.
  Enable the first controlled write only after that read succeeds.

### Radtel RT-950 Pro with Ferrite

- Maintained driver: `drivers/newchirp_ferrite.py`; protocol notes in
  `docs/FERRITE_PROTOCOL.md`; tests `test/ferrite_driver_test.py`
- Catalog entry: `Radtel_RT-950_Pro_Ferrite` (separate from stock and
  nicFW950)
- Evidence: Ferrite's published specification only, FerriteFW/docs commit
  `7dcbe19` (2026-11-23), `manual/G-link-protocol.md` SHA-256
  `58373b6a417b930c46df3e8d562c4ead75dc42836c06ff1dee37974bff5e11c4`; record layouts cross-checked against
  the Ferrite Console and firmware sources for field order. No Ferrite code
  is copied (Ferrite is PolyForm Noncommercial; NewChirp's code is GPL).
- Driver SHA-256: `99e8ce328e720e7e1aaf149562cb5fc7183e30a6b3198e5e861a5d50082458cf`
- Transport: 115200 8N1; 0x03 then 0x00 takes the cable from Ferrite's
  terminal; COBS frames with CRC-16/CCITT-FALSE; `HELLO` must report
  protocol 1, may-go-on (no PIN lock) and chip layout 3. Compression is not
  requested. Bluetooth (FFE0/FFE1, 20-byte paced writes) is specified but
  not implemented.
- Implemented: 4,000 channels, 16-character names in Ferrite's character
  set, RX, shift/split/RX-only, FM/NFM/AM/NAM/WFM (USB/LSB/CW on HF
  channels), CTCSS 60.0-260.0 and DCS normal/inverted per direction,
  Low/Mid/High, skip/priority, and extras for zone, squelch, step, busy
  lockout, reverse, APRS and hidden. Zones are read and kept; settings,
  positions, APRS and other lists are untouched.
- Read/write policy: `READ_MANY` of channels and zones. Writes use
  `BEGIN`/`WRITE_MANY`/`END` for changed, new and deleted channels only,
  after checking each against the radio; the radio validates every record
  and a refusal stops the write naming the channel and reason. The image
  keeps an as-read baseline so a saved image or a second write is checked
  the same way; written channels are read back.
- Physical-radio validation: none yet. Next milestone: one owner's full
  read and a one-channel write that reads back after a power cycle.

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
  `f333be00bea3c731006f256fa21d5d4446415a20a7760f7eff9f5fbc47fb9a29`
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
- 2026-11-15: a read-only nicFW950 map on Ubuntu failed to decode because an
  unset 16-bit subtone field stored `0xFFFF`; the driver treated it as DCS
  octal `37777`, outside CHIRP's valid DCS list. The driver now treats
  `0xFFFF` as no tone, matching an unset `0x0000`. This fixes the same
  reported sentinel on the RT-950 Pro nicFW950 maps and does not change the
  guarded write policy.
- Next milestone: upstream review and additional firmware/alias coverage.

### Connect Systems CS750

- Maintained importer: `drivers/newchirp_cs750.py`
- Importer SHA-256:
  `dec316cfd0a5e4bf3992605e90f5097bbed32f88e2540031e1ccdc11f4e530f1`
- Raw transport SHA-256:
  `6f449f1034003a5e5a5584c1f96a5fc7759fb7f2fc5d19b2c82afb700f2f57cc`
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
  only the macOS IOKit helper has been compiled on this host. Windows opens
  `PHYSICALDRIVE` handles with read-only access because CS750 writes are
  disabled; access-denied errors now explain the Administrator requirement.
- Field evidence: the 2026-11-15 report from [redacted-email] reached
  `\\.\PHYSICALDRIVE2` but Windows rejected the previous read/write handle
  with error 5. The new path requests read access only and retains an
  explicit fail-closed diagnostic.
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

### Fixed-zone radios (StaticBankModel)

- Override: `drivers/newchirp_static_bank_compat.py` reports the fixed zones
  of 13 radios (BF-F8HP-PRO, UV-17ProGPS family, GM-32, RT-910 and others)
  as read-only "Zone N" blocks of channels.
- 2026-11-19 write fix (mailbox INBOX:812, BF-F8HP-PRO on 1.0.60): after
  channels were inserted or moved, the app shifted fixed-zone memberships
  with them and the write stopped with "Zones are fixed by this radio and
  cannot be changed." The app now leaves fixed zones alone
  (`remapRadioMappingLocations`, `_restoreMappingMembershipsAt`), never
  counts them as a mapping change (`radioMappingsSignature`), and the
  bridge ignores a fixed zone's membership list instead of refusing the
  write. Tests: `test_write_ignores_shifted_fixed_zone_memberships`,
  `test/radio_mapping_test.dart`.

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
  UV-32 programming link. On 2026-11-19 a reporter confirmed NewChirp
  1.0.61 reads the radio's fractional CTCSS tones (141.3, 103.5 Hz)
  correctly after the `uv17progps_compat` tone fix (mailbox INBOX:813).
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
  2026-10-30 NewChirp 1.0.25 report from [redacted-email]. The radio
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
- Protocol evidence: `docs/TIDRADIO_TD-H8_G4_PROTOCOL.md`
- Transport: pinned CHIRP TD-H8 clone serial at 38,400 8N1; ODMaster uses the
  same application frames over its Bluetooth programmer
- Identities: `TDH84GEH` Ham, `TDH84GEN` Normal, and `TDH84GEG` GMRS from
  ODMaster 2.6.4. The first two were also observed in NewChirp 1.0.30 and
  1.0.37 reports.
- Implemented: complete `0x1FEF` image download/offline editing and the
  ODMaster G4 write state machine
- Write map: exactly 170 32-byte pages across `0x0000-0x1380`,
  `0x1800-0x18E0`, `0x1900-0x1980`, `0x1C00-0x1C40`, and
  `0x1F20-0x1F40`; every other image byte is preserved
- Failure policy: validate image completeness and regional identity before
  the first write, then stop immediately on a missing or incorrect page ACK
- Evidence: ODMaster APK SHA-256
  `52e6d0516f49de17f2869c800ef8fc84f41933b768e1205a0d7876705e2afdf5`;
  identical 170-page maps from all three public G4 templates; E1 call-path
  analysis and E2 synthetic replay
- Driver SHA-256:
  `840a95135128bcd9ba7a2240f7ed3ae8c0530072ecf21212afc4584ce66f23b8`
- Hardware validation: E4 reads only. The 2026-11-08 NewChirp 1.0.46 report
  completed a 151-channel read with `TDH84GEN`.
- Next milestone: the reporter edits one unused channel, uploads, reads back,
  and verifies the edited channel on the radio. This is required before
  claiming E5 hardware validation.

### TIDRADIO TD-H9

- Maintained file: `drivers/newchirp_tdh8_serial.py` (`TIDRadioTDH9`,
  `TIDRadioTDH9HAM`, `TIDRadioTDH9GMRS`; IDs `TIDRADIO_TD-H9`,
  `TIDRADIO_TD-H9-HAM`, `TIDRADIO_TD-H9-GMRS`), reusing the G4 mixin.
- Field report: ledger `w-20261124-dfcb` (INBOX:949, macOS 1.0.70, TD-H8 G4
  selected): the entry magic was ACKed and `02` returned
  `54 44 48 39 FF FF FF 4E` (`TDH9...N`), then "Unsupported model".
- Identities: `TDH9\xff\xff\xffN` Normal, `...H` HAM, `...G` GMRS (from
  TIDRADIO's templates; the HID cable profiles in the website list the same
  three).
- OEM evidence (2026-11-24):
  - ODMaster 2.6.4 `IndexFragment` reads `TD-H9` with `H8ReadUtil`, the
    same path as TD-H8 and TD-H3.
  - TIDRADIO's public `protocol/readProtocol` templates for `TD-H9`,
    `TD-H9 Ham` and `TD-H9 GMRS` are identical to `TD-H8 4rd`, `TD-H8 4rd
    Ham` and `TD-H8 4rd GMRS` except for `initresult` (same entry codes, same
    225 block requests). SHA-256 of the saved responses: `1ca88ca709d0e67e16f368b459c4743182ae8b33babf1477af0a048cff559edf`,
    `3b64d3bddf67ad714bf14ee14206d1b1770fab6a40295610fe1cce228800f375`, `1874d8c765e573dafb3cc75bbe5f87e1f82c9284c8f339c4d98a537d8ea0cc1d`.
  - `protocol/wfDirect` for `TD-H9` (from its `protocol/defaultRecord`)
    returns exactly the 170 pages of `TDH8_G4_WRITE_RANGES`, every frame
    `57 addr 20 <32> <sum>` (`d1a5c02182da2e8379be7b3c2276c6f86721a30deb473eb704721bc152219fdf`).
  - `protocol/translateRead` decodes one synthetic image (CHIRP
    `TIDRADIO_TD-H8-HAM.img` packed into the template's 224 replies,
    `e06c142da96944d732179c5b6e8f435404b8a16ccf1df9bda41943f49b03d176`) identically for TD-H9 and TD-H8 4rd in all three
    regions: all 2,493 G4 fields match. The TD-H9 adds two settings, DTMF
    speed and backlight brightness, which NewChirp preserves but does not
    show yet.
- Read/write: read and write enabled as experimental, the same policy as the
  G4 profiles (validated image, identity check before writing, stop on the
  first missing page ACK). Hardware validation: none.
- Website: `TD-H9`, `TD-H9-GMRS`, `TD-H9-HAM` in the experimental catalog;
  Web Programmer USB-serial profiles with the same names in
  `lib/tdh8-web.ts` (reads like the G4, writes only the 170 pages with the
  ODMaster entry magic). The existing read-only HID cable profiles are now
  listed as `TD-H9-... (HID)`.
- Next milestone: a physical read, then one channel edit, write, power
  cycle and read-back.

### Radioddity GA-510 V2

- Maintainer: NewChirp transport recovered from official GA-510 CPS
  v1.00.36
- Maintained file: `drivers/newchirp_ga510_v2.py`
- Protocol evidence: `docs/GA510_V2_PROTOCOL.md`
- Transport: 57,600 8N1, DTR and RTS asserted, no flow control
- Implemented: the full OEM `PSEARCH`, `PASSSTA`, `SYSINFO`, `DMR1702`,
  memory-info, unlock, descriptor-map, 64-byte read/write, and ACK sequence
- Memory: five logical 4 KiB blocks (`2, 4, 6, 16, 24`) assembled into a
  `0x5000` image; physical page locations are read from the radio
- Read/write policy: read and write are enabled for experimental testing;
  the driver fails closed on a missing or malformed page map
- Selection policy: the explicit `Radioddity_GA-510_V2` entry uses this
  transport directly. The generic `Radioddity_GA-510` entry probes V2 first
  and falls back to the legacy 9,600-baud protocol.
- Evidence: official CPS ZIP SHA-256
  `e4e9638dd86e88a05299ed38886ccfc2b2d8a05942e565fc8d6392718b5067f5`;
  native CPS executable SHA-256
  `28e865070f5a46024b4f5e30458b9b044689dc99c6f1c5a68a6ba127ef6631b9`;
  upstream V2 fixture SHA-256
  `ab9848966a53ad26fd065d5d7101e77109120113ba467664b90a4c8c3d64ce4a`;
  static call-path analysis E1 and synthetic replay E2
- Driver SHA-256:
  `397dd55f847983c64cfdc91cb5200d00e20e85b49df62beb09d630aed836bc88`
- Hardware validation: none. This replaces the bundled CHIRP transport while
  retaining its pinned channel/settings decoder.
- Next milestone: Don Huey should test the generic and explicit V2 entries on
  the same COM4 cable, compare a full read with CPS, then perform one channel
  edit and read-back.

### Radioddity DB25-G

- Maintainer: NewChirp driver recovered from the official Radioddity DB25-G
  GMRS CPS 20250903
- Maintained file: `drivers/newchirp_db25g.py`
- Protocol evidence: `docs/DB25G_PROTOCOL.md`
- Transport: 9600 8N1 through the programming cable; InputMode is binary,
  InputLen is one byte, and the OEM CPS does not assert DTR or RTS
- Handshake: `55 20 16 08 01 FF DC 02`, then a 50-byte binary identity reply
  beginning with ACK `06` and containing fingerprint `VC7062` or `VC6182`
- Commands: read uses `06 53 <address:u16be> <length:u8>` and expects
  `ACK X <address:u16be> <length:u8> <payload>`; write uses the corresponding
  21-byte `X` frame with a 16-byte payload
- Implemented: OEM-style four-attempt handshake retry, fragment-safe exact
  reads, header validation, and the inherited DB25-G channel/settings decode
- Read/write policy: read enabled; write enabled only through the OEM
  `0x3100` upload range in 16-byte blocks. The driver does not write
  `0x3100` through `0x3FFF` or calibration pages
- Evidence: CPS archive SHA-256
  `97e18276039ea344297fc7be2f4d45ec7433015ee547b3c1a46803418666a258`;
  CPS executable SHA-256
  `f4e3affa512eca914888a888af156365a1b4f06df55da1a31d71a2b67a77ea87`;
  REA/Ghidra 12.1.4 static call-path analysis E1 and synthetic replay E2
- Driver SHA-256:
  `375174dffa76fec537ea3a17befffe0359102cbbcf0da5f2df31ebf19b1cde9e`
- Hardware validation: none
- Next milestone: reporter performs a physical read and one controlled write
  with the new profile, compares channels/settings against CPS, and returns
  the resulting diagnostic report and read-back image

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

### Radioddity X1 Pro GMRS

- Maintainer: NewChirp driver recovered from the official Radioddity X1 Pro
  firmware/CPS package dated 2026-07-15
- Maintained file: `drivers/newchirp_x1pro.py`
- Protocol notes: `docs/X1PRO_PROTOCOL.md`
- Transport: 115200 8N1, no flow control, no DTR/RTS; fixed `02PROGRAM` and
  `SMP558 FF FF` CPS handshake
- Commands: 16-byte settings and channel pages. Read is
  `52 <address:u16be> 10` and returns the four-byte echo plus 16 data bytes.
  Write is `57 <address:u16be> 10 <16 bytes>` and requires ACK `06`.
- Memory map: 30 channel records from `0x0000` through `0x01DF`, plus the
  settings record at `0xE000`. No channel-name field exists.
- Tone byte order: read replies return CTCSS/DCS words little-endian.
  `writeChannelAsync` accepts big-endian tone words, so NewChirp converts only
  channel payload bytes 8-11 at the transmission boundary. Download images
  remain in read order for lossless reloads and comparisons.
- Implemented: RX/TX frequency, simplex and +/-5 MHz repeater offsets,
  arbitrary split TX, CTCSS/DCS including independent TX/RX tones and DCS
  inversion, three power levels, narrow/wide, scan add/skip, busy lock,
  squelch, key tone, record, Roger beep, power save, scan mode, NRC, and VOX.
- Read/write policy: both are enabled for experimental testing. Upload writes
  the settings page followed by all 30 channel pages, matching the OEM state
  machine, and never writes the undocumented image gap.
- Evidence: official ZIP SHA-256
  `88715c06694994d58b4791deeaa6641d7b4303fb15c317f062591eff56bb9519`;
  executable SHA-256
  `64f90289b838adae6d01691649b08812e5783751a6bbcae157b39d5e2af87339`;
  `model.xml` SHA-256
  `51b0e546fe644a865fe46c021f1fccf655723d953fc326a0cdd9276f7dde0005`;
  CIL static call-path analysis E1 and synthetic replay E2. The CPS tone table
  stores `03 75` for 88.5 Hz; `writeChannelAsync` writes those bytes directly,
  while `readChannelAsync` reverses them when assembling the same table value.
  A 1.0.46 physical report from Dustin showed an unedited write causing the
  radio to reboot at channel 23, which is the first receive-tone exception.
  That report exposed the previous little-endian-on-write assumption.
- Driver SHA-256:
  `4e262b160e698b957b480cacc9df9ac9fa999a1cf429773b70f2e8b516090dd2`
- Hardware validation: none. Focused offline transport and field tests pass.
- Next milestone: ask Dustin to test the corrected CPS-matched write order on
  the next prerelease, then compare all 30 channels plus settings with a saved
  OEM image before promoting the driver.

### Radioddity GS-5B 1.XX

- Maintained driver: `drivers/newchirp_gs5b.py`
- Protocol notes: `docs/GS5B_PROTOCOL.md`
- Transport: `PROGRAMSHXPU`, 115200 8N1, DTR/RTS asserted, 64-byte pages
- Memory map: 512 inline 32-byte channel records plus VFO, settings, DTMF,
  zone-name, and FM ranges through `0xB03F`
- Implemented: RX/TX frequency, names, independent CTCSS/DCS, DCS polarity,
  cross tones, three power levels, wide/narrow, scan add/skip, and busy lock
- Read/write policy: both enabled for experimental testing. All documented
  pages are written; gaps are never touched. Settings and aux data are
  preserved but not yet exposed in the editor.
- Compatibility: the normal `Radioddity_GS-5B` entry remains the upstream
  0.XX driver. Select `Radioddity GS-5B (1.XX)` for the current CPS transport.
- Evidence: official CPS ZIP SHA-256
  `628ed2f64c644673a8a9a3c7aa6d45d1d42f2baaf32f860e3922c824e501396f`;
  extracted CPS SHA-256
  `7878a58b2e33a153e3e137ab803b90db43ac438a00851853641fe2bccba92d54`;
  CIL static call-path analysis E1 and synthetic replay E2
- Driver SHA-256:
  `b33acbb7e43ab83b46e1e7b16719d082f4366aca093cafbfd3ac2294370cd48a`
- Hardware validation: none. The 2026-11-08 report confirmed that the same
  cable and COM4 successfully read 52 channels when using `Baofeng_5RM`, while
  the upstream GS-5B selector failed at `PROGROMSHXU`.
- Next milestone: ask reporter `[redacted-email]` to select
  `Radioddity GS-5B (1.XX)`, save the full image, and compare it with the OEM
  CPS before any controlled write.

### Baofeng DM-32UV

- Maintainer: NewChirp override of the upstream CHIRP `DM32UV` driver
- Maintained file: `drivers/newchirp_dm32uv.py`
- Transport: 115200 8N1 with DTR and RTS asserted; no hardware flow control
- Implemented: all 4,000 channels, editable named zones with multi-zone channel
  membership, analog and DMR channel fields, contacts, RX groups, scan lists,
  privacy-key references, and settings provided by the pinned upstream CHIRP
  implementation
- Receive coverage: 108-136 MHz airband channels are accepted when duplex is
  `off`; transmit validation rejects the same channels because the radio only
  supports airband reception.
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
- Unreadable tones (2026-11-23, INBOX:907): firmware `DM32.00.01.048` stored a
  tone of `0x3E08`, which the stock BCD decoder read as "3e08" = 3e8 Hz and
  the whole read failed. DM-32UV CPS v1.60 (SHA-256
  `8541dc78b2fb5b4a09de9954519b0c8a96baa3ca5717bd4caf04893e095ef895`) offers
  exactly CHIRP's 50 CTCSS tones, and an OEM save file from another radio
  stores BCD; so a tone value that is not valid BCD CTCSS/DCS now reads as
  no tone and its raw bytes are written back unless the user sets a tone.
  The meaning of `0x3E08` on that firmware is unconfirmed (image requested).
- Write-stall watchdog (2026-11-23, INBOX:902): the owner reports the app
  can sit at 17-19% indefinitely while the radio times out and reboots. The
  bridge now ends any radio write after 150 s without serial activity, with
  the trace and a stack dump of where it stopped.
- Upload progress (2026-11-22, ledger `w-20261121-ab4d`): stock reports once
  per memory tag and kept the "Scanning flash pages" label until the first
  page was erased and written, so a ~50-60 s write sat near 18%; the
  reporter cancelled two working writes. The label now switches to
  "Writing to radio - this takes about a minute" when scanning ends and
  reports each page written. The app asks before cancelling any radio
  write. Protocol and written bytes are unchanged.
- Evidence: upstream CHIRP commit
  `832d349e050fbdcde50185f77cdb34fbe5bab57a`, vendor CPS v1.60 protocol
  work recorded by the upstream driver author, and CHIRP issue 12652
  documenting intermittent DM-32UV failures with some FTDI adapters. The
  2026-10-28 report from [redacted-email] returned only the first byte of
  the `V00000007` information reply after the previous 0.5-second window.
  A second report from [redacted-email] reached a slow, retried PSEARCH
  sequence and received a non-ACK SYSINFO reply.
- Driver SHA-256:
  `59aca2e9624b57a173cd0b6964b5b922818684a26defe2311fee32d3a1036b9c`
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

### Baofeng BF-V12D

- Maintainer: NewChirp transport recovered from the official Baofeng
  BF_Series CPS 1.5.1
- Maintained file: `drivers/newchirp_baofeng_bfv12d.py`
- Protocol evidence: `docs/BAOFENG_BF_V12D_PROTOCOL.md`
- Transport: 9,600 8N1 through a standard Baofeng K-type programming cable.
  FTDI adapters are explicitly not recommended based on public field reports.
- Unlock: fixed CPS sequence `02ucbfpwd`, `10c5ea35`, encoded model token
  `Q041OTUwMA==` plus four NUL bytes, then `02prOGRAM`; every password stage
  requires ACK `06` and the radio ID must report P3107 model byte `0x0A`
- Clone protocol: model A with magic `80 82`, eight-byte read/write blocks,
  `52` reads, `57` writes, ACK after each block, and exit `45`/reply `46`
- Memory: legal `0x03E0` image with sparse read windows
  `0x0000-0x010F`, `0x02B0-0x02BF`, `0x0330-0x033F`, and
  `0x0380-0x03DF`; channel rows are `0x0010-0x010F`
- Implemented: NewChirp-owned unlock transport with fragment-safe fixed-length
  reads, exact CPS frame bytes, five one-second retries, and detailed
  fail-closed diagnostics
- Read/write policy: retained from the pinned CHIRP image/upload implementation
  after the NewChirp unlock succeeds. The image and channel decoder remain
  experimental until a physical read/write/read-back is reported.
- Evidence: official CPS ZIP SHA-256
  `c07f3664c7bf87721376042c53a06b29055fec0c2ccc3d6192c8d005b4582f72`;
  installer SHA-256
  `6bf5c0feda83007e7d5bce468c059af499bd2fd89335422b28771d787e655a2a`;
  ASAR renderer/main hashes and E1 call-path analysis, plus public E3 read and
  write captures from an original-firmware unit
- Driver SHA-256:
  `2adc7e1e35ccb597e5b8ad0580393c3dd9915eebc60794c4953b5ef381bcb93d`
- Unsupported firmware: public V1.19 and V2.02 units reject the fixed password
  stage. Baofeng CPS 1.5.1 also reports password failures on those units, and
  its renderer contains no alternate version-dependent handshake. NewChirp
  does not guess credentials or attempt writes on those variants.
- Hardware validation: none by NewChirp. Upstream support was validated by its
  author on earlier firmware, and public OEM captures prove the same sequence.
- Official CPS retained at
  `/Users/rlopez/Downloads/Baofeng_BF_Series_CPS_1.5.1.zip`.
- Next milestone: read an original-firmware radio with a standard K-type cable,
  compare its image with CPS, then perform one controlled write/read-back.
  Supporting V1.19/V2.02 requires a working OEM capture or documented newer
  password challenge.

### Baofeng K67 Pro

- Maintainer: NewChirp driver recovered from the official shared K6/K63 CPS
- Maintained driver: `drivers/newchirp_baofeng_k67pro.py`
- Protocol notes: `docs/BAOFENG_K67PRO_PROTOCOL.md`
- Official CPS: `BAOFENG_K6_CPS_1.1.2_20240913.zip`, SHA-256
  `3f9c52ece3a8b6726fba4135b5a0f458b5d81f47d2e83af75045e82d8931b917`
- Installer SHA-256:
  `62b3cd09bedc8c5d789e293743363efe7434fec2fe631959954e3ca80d91162e`
- Extracted `BF-K6 CPS.exe` SHA-256:
  `a9017b8b840c4e00e9d575077dc2d44f465ccab2f30fba6dbb4c18e58f08e271`
- Driver SHA-256:
  `5d1498c497bb7f598dd82046838680ecc679bc3eb6492afed4fdd7481591d0b8`
- Transport: 115200 8N1 with DTR and RTS asserted; entry
  `PROGRAMBF-K6PROU`, ACK `06`, identity request `F`, 31-byte identity response
  containing `K6PROU`, 64-byte addressed reads, and exit `E`
- Image: `0xd040` bytes with sparse program ranges. The first 1,000
  32-byte records map CHIRP memories 1-1000 to CPS indexes 0-999.
- Implemented: receive/transmit frequencies, split and transmit-disabled
  channels, independent CTCSS/DCS and polarity, GB2312 names, wide/narrow FM,
  airband AM presentation, High/Low power, and scan skip. All unknown bytes
  remain in the saved image.
- Read/write policy: complete sparse read; uploads disabled pending physical
  validation. The CPS write request and ACK are documented but not implemented.
- Evidence: static IL analysis of the artifact-hashed CPS, covering serial
  setup, handshake, read framing, sparse ranges, channel serialization,
  frequency packing, tone tables, and flags. No CPS executable was run.
- Model provenance caution: Baofeng's official page names the CPS K6/K63 and
  has no official K67 Pro product entry. The K67 Pro association currently
  relies on a third-party CPS tutorial, so exact model/firmware variants remain
  unverified.
- Offline validation: raw frequency vectors, 68-byte block framing, all sparse
  ranges, channels 1 and 1000, CTCSS/DCS, airband AM, sparse image assembly,
  registration, and read-only policy.
- Hardware validation: none. No physical read, OEM capture, or reporter image
  has been received.
- Website catalog: listed as `K67 Pro (experimental)`; the browser Web
  Programmer exposes a matching read-only K67 Pro profile.
- Next milestone: obtain a physical read and compare the identity, multiple
  channels, and saved CPS image before reviewing any separate write
  implementation.

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
  from [redacted-email] showing a complete 16-byte hello reply while the
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
- Read/write policy: require `F4HWN v6.3.x` or `v7.0.x`; write only
  `0x0000-0xA177`; preserve calibration at `0xB000-0xB18F`. An image is
  written only to a radio of the series it was read from (6.3 images
  without firmware metadata are still accepted by 6.3 radios).
- F4HWN 7.0 (2026-11-22, ledger `w-20261119-7381`): the official
  `f4hwn.chirp.v7.0.0.py` (SHA-256
  `8eb622ec4a4eeaa26cf77ef878022e066b3d674d9fa214bf99c889571b9f4f41`)
  differs from the 6.3 module only by naming two formerly unused bytes,
  `set_rxg` (RX noise gate) and `set_fnt` (display font). Layout, size and
  every channel structure are unchanged. Settings stay hidden; the bytes
  round-trip unchanged within one series.
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

### KSUN UV-K60 Plus

- Maintained driver: `drivers/newchirp_uvk60plus.py`
- Protocol evidence: `docs/KSUN_UVK60PLUS_PROTOCOL.md`
- OEM programmer: KSUN `MH-580` version 0.2, dated 2025-10-24
- OEM ZIP SHA-256:
  `790507b60b875259a1a2ba665ca39f5be31793870722706494123ddd7e8b2ac9`
- OEM executable SHA-256:
  `b241af593ba2b327a0b155bd287813df37becaa275294bae5ca77b5c3a19e79f`
- Radio evidence: `X-TFSI V5: UV60dplus`, serial `26UV60DPLUS00798`
- Transport: 38,400 8N1, `P{OJI}E` entry, eight-byte `P311` family
  identity, 32-byte `R <address:u16be> 20` reads, and `E` exit
- Image: `0x2A00` bytes across `0x0000-0x1F40` and `0x2000-0x2A00`;
  the `0x1F40-0x2000` gap is preserved without a read
- Implemented: complete raw-image retention, 128 channel records, BCD
  RX/TX frequency decoding, offset direction, CTCSS, and the apparent
  `0x2000` name table
- Read/write policy: read-only. Uploads and channel mutation fail closed
  because the option bytes, write fields, and checksum acceptance policy
  remain unvalidated
- Evidence: E1 static MH-580 call-path analysis and E2 synthetic replay.
  The supplied OEM dump decodes correctly for its 17 active records, but it
  does not match the separate 97-channel CSV snapshot
- Driver SHA-256:
  `e7a317a59d25f786453fb25dc108a18a3ecbdfaf62ec815518c6dee52e2647a8`
- Website: experimental catalog entry and read-only Web Serial profile
- Hardware validation: none
- 2026-11-22: the first same-state NewChirp read and MH-580 file agree on
  every byte both read, except that MH-580 blanks records 84-97, whose bits
  are clear in the channel maps at `0x1A00`/`0x1A20`. NewChirp now treats
  unmapped records as deleted (83 channels, as MH-580); the Web Programmer
  does the same. Which map is the scan list is unproven.
- Next milestone: a controlled single-channel write and read-back compared
  with MH-580 before enabling writes

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
  1.0.24 report from [redacted-email]. The second radio completed a 92-channel
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
  to two seconds for read commands and five seconds for `MW`/`MC` write
  commands. A 2026-11-11 TS-2000 report showed `ID` replying after 1.20 seconds,
  which exceeded the former one-second read window.
- Settings: the TS-2000 does not expose radio-wide settings through CHIRP.
  NewChirp now reports that state without first downloading all 290 channels.
- Diagnostics: serial errors include a bounded CAT trace with the failed
  operation and memory location, elapsed time, refusal/no-response result,
  and detected radio ID. Channel contents are not recorded.
- Write status: protocol-level tests pass; upload/read-back retest on physical
  hardware is required before calling the timeout fix hardware-verified
- Next milestone: the affected owner retests the identification/read with 2.0
  seconds, then validates both a small loadset and the full 258-channel
  loadset with a read-back comparison. Submit the generated communication
  trace if either operation still fails.

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
  from [redacted-email] showing ID-like replies at every baud without a
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

### Kenwood TK-350 and TK-359

- Maintained driver: `drivers/newchirp_kenwood_kpg23.py`
- Protocol notes: `docs/KPG23_PROTOCOL.md`
- OEM programmers: KPG-23D 1.01 and KPG-32D 1.00
- CPS archive SHA-256 values:
  - `kpg23d.zip`:
    `2407d17f2f8890db3b21bdfe69beb7154444c3ecd5d44dd743c4e9d45d0279af`
  - `kpg32d.zip`:
    `91b828a2d1e032b807ae3bed107426b844833483015a73c7b801f89446c8f37e`
- Representative channel-data hashes:
  - KPG-23D `SAMPLE.V1B`:
    `6b61db4739fc1e19d18f47171620bdbb3ced2decb63c4aca9aaa87abb970b981`
  - KPG-32D `SAMPLE.FDT`:
    `0107e63b70d156acabb2873b6ab8ddcbb0e291e94b15b0cff95889ae00ba5189`
- Driver SHA-256:
  `4b0f2a04c8055c3b4aa7a7af1f5109f2e1e08a52e7aaad26d2a916fe22459f4d`
- Transport, TK-350 (KPG-23D 1.01 QEMU register trace with a simulated
  radio, 2026-11-26): 4,800 baud 8N2, DTR and RTS off (KPG-23D never writes
  the modem-control register), `0x02` answered by a 6-byte identity that is
  not checked, `06`/`06`, 28 `R <hi> <lo> 80` requests from 0xF000 answered
  `W <hi> <lo> 80` + 128 bytes with `06`/`06` after each, no exit command;
  a `Z` reply fails the read. The 2026-11-13 notes (9,600 8N1, 8-byte
  identity, `Z`, `E`) came from the BIOS's boot-time COM1 set-up and were
  wrong; no TK-350 owner's radio ever answered them.
- Transport, TK-359: still the 2026-11-13 assumptions (9,600 baud 8N1,
  8-byte identity, `Z` fill, `E` exit) until KPG-32D is traced the same way
- Implemented: full raw-image retention, the 16-byte channel record
  layout, RX/TX frequency decoding for the 450-470 MHz band, and
  four-character channel names. The `0x02` identity request is retried up
  to three times when the radio enters PC mode late or the first reply is
  fragmented.
- Read/write policy: read-only. Uploads remain disabled because the
  channel option fields, settings map, model-specific write protection,
  and final partial-block behavior have not been validated on hardware
- Evidence: official CPS static traces plus the supplied KPG-23D/KPG-32D
  sample data. The identity/read request sequence was also observed in a
  controlled DOS VM. The response header after `W` remains classified as
  a family-derived replay rule, not hardware capture. On 2026-11-17,
  [redacted-email] reported zero identity bytes on both COM3 and COM4
  with NewChirp 1.0.56 and TK-350 selected; the bounded retry covers a
  late-ready radio without retrying memory writes.
- NewChirp hardware validation: none
- Next milestone: the requester performs complete reads on a TK-350 and
  TK-359, saves both images, and compares frequencies, names, power, and
  tone fields with the OEM CPS

### Kenwood TK-863G

- Maintained driver: `drivers/newchirp_kenwood_tk863g.py`
- Protocol notes: `docs/KPG76D_PROTOCOL.md`
- OEM programmer: Kenwood KPG-76D 1.00 for TK-373G/TK-863G
- CPS archive SHA-256:
  `94cfae17605565e92cf14135c7a391a450395e697f2a8d7053090b73df63cbee`
- CPS executable SHA-256:
  `2041afe2b14883ea1411d139227bb6c19ff4292c909c89599a812c475bafcfde`
- Uploader DAT SHA-256:
  `5afb8f37a3a28a0882b98eb8d340e6caec64f1b8b53b742426cac52ca3b89434`
- Transport: KPG-76D `PROGRAM` session at 9600 8N2 with the OEM
  9600/19200/4800/2400/1200 fallback order, `M0863` identity, `NRK`
  tuning record, `0x7C` memory-session request, 256-byte `R` blocks,
  additive checksums, fill responses, three-attempt recovery, and `E` exit
- 0x7C memory session: 3 s read timeout per try (KPG-76D 0x403110) and up to
  three tries in the same session, as KPG-76D's Retry button does
  (0x4037b0 -> 0x402ff0, MessageBoxA 0x15). 2026-11-25 Linux 1.0.75 report
  (INBOX:1000) got 1 of the 2 bytes; the error now shows the bytes received.
- Implemented: complete 32 KiB image read, OEM DAT unwrapping, model
  validation, 128 channel records, RX/TX frequency, offset, name,
  wide/narrow, CTCSS, DTCS, and cross-tone decode. All unknown channel bytes
  remain unchanged in the image.
- Read/write policy: read-only. The CPS write framing is understood, but the
  complete ownership map and physical write/read-back behavior are not yet
  validated.
- Offline validation: five focused tests pass, including three-byte
  fragmentation across all 128 blocks, checksum recovery, DAT unwrapping,
  supplied record encoding, wrong-model rejection, and blocked writes. The
  complete Python suite passes 404 tests with two fixture-dependent skips;
  all 215 Flutter tests pass and `flutter analyze` is clean.
- Hardware validation: none.
- Next milestone: the uploader performs a NewChirp read, compares all decoded
  channels with KPG-76D, and reports any missing option fields before the
  write map is considered.
- 2026-11-24 correction (INBOX:943, Linux 1.0.72 read stopped with "0 of
  2 bytes while starting the memory session" after a valid `NRK` record):
  KPG-76D's `0x403110` calls its SetCommTimeouts helper with 3,000 ms, not a
  sleep. The CPS sends `0x7C` right after `NRK` and waits up to 3 s for the
  two-byte reply, then 500 ms for the ACK. The driver used to idle 3 s and
  then wait only 1 s; it now matches the CPS. Framing is `9600,N,8,2` (the
  only mode string; the baud probe rewrites just the speed), so the driver
  and Web Programmer now use no parity instead of even. Offline-tested; no
  physical read yet.
- Website catalog: live as `TK-863G (experimental)` in the Kenwood catalog
  and **New Experimental Radio Support** from website source `be979f0`
  (`index-CbTrONP8.js`). The read-only `kenwood-tk863g` Web Programmer
  profile is included.

### Kenwood TK-270G

- Maintained driver: `drivers/newchirp_kenwood_tk270g.py`; the
  `NewChirpTK270G` class supersedes CHIRP's `Kenwood_TK-270G` registration.
- Driver SHA-256:
  `8b430cfbb4a40650878733770961c9c1b4f159b2925cfbb81866596301825b7b`
- Transport: pinned CHIRP Kenwood Series 60G clone serial at 9600 with even
  parity and one stop bit. KPG-56D statically configures `9600,N,8,2`; the
  live serial setting remains unchanged pending an OEM capture or physical
  comparison.
- OEM evidence: KPG-56D v4.22 package SHA-256
  `7168c25603ab592cb5f3061ac56f71f80c6a83dccede4fbd54165bda5ea023e4`;
  main executable SHA-256
  `51530de3587c72c7cd4a7d6808b7a202614affbcc63a9f66917b90b61d380b28`.
  Full artifact and protocol evidence is in `docs/KPG56D_PROTOCOL.md`.
- Issue: the pinned `tk760g.py` extra-setting loop tests
  `setting != "bank" or setting != "bnumb"`, which is always true. It converts
  `bank` and `bnumb` to inverted booleans during every channel write. The
  NewChirp bridge writes active channels one at a time, so each upload can
  clear another channel from its bank and eventually generate zero programmed
  channels and zero banks.
- Correction: NewChirp now owns the channel decode and write methods. Decoded
  bank metadata no longer mutates raw image bytes. `set_memory()` writes
  `bank` and `bnumb` directly and never sends those two fields through the
  broken upstream boolean loop. Existing inversion handling for beat shift,
  compander, and busy-channel lockout is unchanged. A post-write bank-state
  check stops the upload before radio I/O if generated counts disagree with
  the active channel records. Before rebuilding those tables, upload now
  replaces erased bank and bank-index sentinels with safe defaults: bank 1
  and the channel's zero-based memory position.
- 2026-11-19 correction: `set_memory()` validated every channel's bank
  metadata but normalized only during `sync_out()`, so editing channel 1 on
  a radio whose channel 24 held index 128 stopped with "invalid bank
  metadata" before radio I/O (1.0.60 report, mailbox INBOX:808). Each
  channel write now normalizes all erased sentinels before rebuilding the
  bank tables, matching what `get_memory()` already shows. Regression test:
  `test_editing_one_channel_tolerates_erased_index_elsewhere`.
- Write recovery: if the radio rejects a data block with checksum status
  `0x15`, NewChirp resends the identical block up to three times. A persistent
  rejection closes programming mode and reports the block and attempt count.
  Other write acknowledgements are not retried.
- Offline validation: the shared `Kenwood_TK-272G.img` fixture is
  re-identified as a TK-270G. Its 36 active channels are round-tripped through
  the same decode/write path used by the bridge; all active bank assignments
  and bank indexes are retained and the generated channel/bank counts remain
  nonzero. A regression injects one block-51 checksum rejection and verifies
  that the identical frame is retried before the session exits. Another
  regression changes an active channel's bank index to the erased sentinel
  128 and verifies that an unchanged upload normalizes it before preparing
  the bank tables.
- Field evidence: the 2026-11-15 report from [redacted-email] failed
  with `Bad checksum in block 51 write`.
- Field evidence: the 2026-11-16 report from [redacted-email] downloaded
  channel 24 with bank index 128. NewChirp 1.0.56 then rejected the unchanged
  upload before radio I/O because validation ran against the unnormalized
  image.
- 2026-11-20 correction (ledger `w-20261120-8af9`, INBOX:855): 1.0.63 wrote
  without error but the last channel in the list was unusable on the radio.
  CHIRP's OEM-style `Kenwood_TK-760G.img` sample stores each record's
  `bnumb` as the 1-based position within its bank, matching the 0x300 table
  `(bank, position, bank-1, slot)`. Stock CHIRP, and so NewChirp, gave new
  channels and the 0x80 sentinel `slot - 1` (0-based), duplicating a KPG
  position and leaving the last one empty; `_prep_data` rebuilt 0x300 by
  slot order without touching record positions. NewChirp's `_prep_data`
  now renumbers every bank 1..n in the order of the current 0x300 table
  (new or moved channels after, by slot), writes the same positions to the
  records and the table, clears stale table entries through 0x4FF, and
  validation requires positions 1..n per bank. The TK-760G sample's table,
  bank counts and record positions rebuild byte for byte. The 0x7000
  per-channel ID area is still filled by count as in stock CHIRP; whether
  the radio indexes it by slot is unconfirmed.
- 2026-11-22 correction (ledger `w-20261120-8af9`, INBOX:877/884/887): 1.0.66
  still stopped at channel 24. The owner's read-back after the 1.0.66 write
  (SHA-256 `2fe8044a22fa40a0fbb2fb29eeb9383284f0c051dd118ffe98c10efba22788a4`)
  holds the corrected record positions 1..25, a 25-entry 0x300 table and a
  header count of 25, but the 0x1000 per-bank count is still `01 18` (bank 1,
  24 channels) from KPG-56D. NewChirp's `sync_out` override skipped every
  `RO_BLOCKS` entry, including 0x10-0x1E, which stock CHIRP writes when not
  empty, so the rebuilt counts never reached the radio. The override now
  matches stock: 0x10-0x1E are written unless empty, and 0x59-0x5E are never
  sent. A dry run of the owner's image against a fake serial port sends block
  0x10 as `01 19`. Regression:
  `test_upload_writes_rebuilt_bank_counts_block`.
- Hardware validation: none. No controlled NewChirp write/read-back has been
  performed on a TK-270G, and the OEM serial setting has not been compared on
  the wire.
- Next milestone: with a saved radio image and physical TK-270G, compare
  KPG-56D and NewChirp reads, perform an unchanged NewChirp write, then compare
  both read-backs for all channel and group metadata.

### Alinco DR-735T/E/R/J

- Maintained file: `drivers/newchirp_alinco_dr735.py`. It replaces the stock
  `AlincoDR735T` methods in place, so the `Alinco_DR735T` ID and existing
  64,000-byte images keep working. Protocol: `docs/ALINCO_DR735_PROTOCOL.md`
- Source: Alinco DR-735 Memory Editor 0.06. Download SHA-256
  `3931cfc1cab4b977d4f433582850995ed323cd7dc3c1f62e247281c0c7992924`,
  assembly SHA-256
  `a7e5ce73a821bb2469b546edfe943c8c7cac6cea39314b4a2599c7aa71f80eaa`
- Transport: 38400 8N1. Every command is CRLF-terminated, and its echo from
  the single-wire ERW-7 is validated; cables that don't echo are accepted.
  Read: `AL~` → `OK`, `AL~WHO` (9 OEM identities), `AL~EEPEL` for common
  channels and `AL~EEPDL` for extended channels and trailer blocks, with
  500 ms per block. Write: `AL~DR735J` → `OK`, 1000 `AL~EEPEL W` → `OK`,
  `AL~RESET` → `OK`.
- Implemented:
  - Channel fields: OEM tone semantics (TSQL encodes and decodes the same
    tone; Cross Tone->Tone for split tones), both DCS bytes, and the
    48-character name set.
  - Records: delete writes 0xFF (`can_delete` on), 10 banks, and the pch
    link, fav, bell, BCL, heterodyne, dcsOff and colors as extras.
  - Bands: per-model ranges (EN and RN narrow, no airband).
  - Extended channels: rows 1000–1413 use the OEM numbering (L, R, P, APL,
    APH, CAV, CAU, d00–d99 L/R) and are read-only.
  - Reads: if the extended part of a read fails, the 1000 common channels
    are still kept.
- Read/write policy: the read covers everything the OEM reads. The write
  sends only the 1000 common channels, the same EEPEL path stock CHIRP
  uses. Before entering write mode, it rejects any channel outside the
  connected model's bands, and an image read from a different model ID.
  Extended channels, VFOs, colors, settings and DTMF are never written.
- Evidence:
  - E1: static trace of `sio`, `btRead_Click`, `btWrite_Click`, `ExpandMem`
    and `Memory.btnOK_Click`.
  - E2: replay in `test/alinco_dr735_driver_test.py` (identities, OEM
    addresses, echo/no-echo, missing-echo and missing-reply diagnostics,
    short block, stock image decode and round trip, tone/DCS/name encode,
    delete, banks, upload sequence, band and model refusals, extended
    channels not written).
  - Web mirror: `lib/alinco-dr735t-web.ts` in the web repo, covered by
    `scripts/test-experimental-web-programmer.mjs`.
- Physical-radio validation: none
- Next milestone: a physical DR-735T read (common and extended) compared
  with the OEM editor, then one controlled common-channel write and
  read-back. After that, decode settings and enable extended-channel writes
  through `EEPDL` with the OEM's settings read-modify-write.

### Kenwood TM-V71A/E clone mode

- Maintained file: `drivers/newchirp_tmv71.py` (`Kenwood_TM-V71_CloneMode`).
  Protocol: `docs/KENWOOD_TMV71_PROTOCOL.md`
- Source: Kenwood MCP-2A 3.22. Archive SHA-256
  `901596b9b52d398131408d257c54dfb0548e79f269dfe830792a6e9ebce0e678`,
  `MCP-2A.exe` SHA-256
  `e7a71f0e58b32ec02f41f6da5f1b6b927177c0ba5a3b7a497c19cff23421bf48`
- Transport: 8N1, RTS/CTS, DTR+RTS asserted. Pinned CHIRP Kenwood `ID` baud
  probe, then `0M PROGRAM\r` → `0M\r`. Blocks `R hi lo 00` →
  `W hi lo 00` + 256 bytes, with the echo validated; host `06` → radio `06`;
  `E` → `06`. Reads `0x0000–0x7EFF` only; `0x7F00`+ (factory adjustment)
  and `0x8000`+ (RC-D710 head) are never requested.
- Implemented: the 1000 memories plus scan, WX and call specials, and body
  settings from the pinned CHIRP TM-D710 layout, which matches MCP-2A's
  shared map. Uppercase 8-character names. A TM-D710/RC-D710 identity is
  rejected with a pointer to the TM-D710 driver.
- Read/write policy: read-only. `sync_out` raises before sending any bytes.
- Evidence: E1 static trace of `Communication` (ctor, `Seq_ID/TY/0M/E`,
  `b(int,int)`, `Sequense_MemRead/MemWrite`) and E2 replay in
  `test/kenwood_tmv71_driver_test.py` (full, fragmented, wrong echo, short
  block, NAK, refused `0M`, TM-D710 identity, upload disabled, channel and
  settings decode)
- Physical-radio validation: none
- Next milestone: a physical TM-V71A/E read compared with MCP-2A. Then port
  the MCP-2A pre-write password and repeater rules and write from `0x0004`
  with a controlled edit and read-back.

### Kenwood live-mode write cache (TM-D710, TM-D710G, TM-V71, TH-D72, TH-D74, TM-V7)

- Maintained file: `drivers/newchirp_kenwood_live_cache.py`
- Transport: unchanged pinned CHIRP `kenwood_live` CAT commands (`ME`/`MN`
  for the TM-D710 family), 1 s per-command timeout, hardware flow
- Defect: stock `KenwoodLiveRadio.set_memory` runs
  `del self._memcache[number]`. NewChirp writes through a newly opened radio
  instance with an empty cache, so the first channel raised `KeyError(0)`,
  which was reported as "Reported error: 0", and nothing was written. Stock
  `erase_memory` also returned early for uncached slots, so channels deleted
  in NewChirp were silently left on the radio.
- Fix: `set_memory` no longer requires a cache entry, and no placeholder is
  left behind if spec construction fails. `erase_memory` reads an uncached
  slot first and erases it only when the radio holds a memory there.
- Evidence: 2026-11-18 NewChirp 1.0.57 Windows report (TM-D710, COM8). The
  read returned 51 channels. The write ended with five baud-probe `ID`
  timeouts, a successful `ID TM-D710` at the sixth attempt, `AI`, and then
  error `0`. Offline reproduction against the pinned CHIRP source raises
  `KeyError('0')` without the override.
- Offline validation: `test/kenwood_live_write_cache_test.py` covers a
  fresh-connection write, a failed spec that leaves no placeholder, erasing an
  occupied uncached slot, and skipping an empty uncached slot.
- Not covered: TH-G71, TS-590 and TS-480 override these methods themselves
  and keep their stock behaviour. Erase verification is not added to
  `verify_live_write` (it still receives `cleared=[]`).
- Hardware validation: none. Next milestone: the reporter writes one edited
  and one deleted channel on a TM-D710, then reads both back.

### Kenwood TM-D710P / TM-D710GP identity compatibility

- Maintained file: `drivers/newchirp_tmd710.py`
- Driver SHA-256:
  `63f9199a5d3ceca790228af78a3f782ac07e3133bed6c239e1531c40233f70a9`
- Transport and layout: unchanged pinned CHIRP clone protocols
- Implemented: accepts `D710GP` for the TM-D710G profile and `D710P` for the
  TM-D710 profile. The P suffix is treated as a compatible identity response,
  not as proof of a regional hardware model.
- Evidence: 2026-11-01 NewChirp 1.0.30 report from [redacted-email]; the
  complete command handshake reached `ID TM-D710GP` instead of `TM-D710G`
- Additional evidence: 2026-11-15 NewChirp 1.0.54 reports from
  [redacted-email] reached `ID TM-D710P` while the non-G TM-D710 profile was
  selected
- Name policy: the TM-D710 accepts eight-character channel names. NewChirp
  blocks an upload before radio I/O when an imported name is longer, instead
  of silently truncating it.
- Hardware validation: partial. On 2026-11-17, Robby reported that the control
  head COM port could not read, while the rear PC port read successfully on
  a TM-D710A. A RepeaterBook HMK file with names within the eight-character
  limit wrote successfully. A file containing longer names did not write.
- Next milestone: read the radio back after a short-name write, power-cycle,
  and compare every channel. Confirm the accepted `D710P` suffix on another
  firmware/unit before treating it as universal.

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
  [redacted-email] showed CI-V address `0x56` selected for a radio reported as
  an IC-746PRO.
- Offline validation: exact model registration, CI-V destination address,
  frame construction, and separation from the original IC-746 profile.
- Hardware validation: none.
- Next milestone: read the IC-746PRO with CI-V address `66h` and
  CI-V Transceive off, then perform one controlled memory edit and read-back.

### Icom IC-7100

- Maintained driver: `drivers/newchirp_icom_ic7100.py`
- Driver SHA-256:
  `5a1d39629cb1736c709d513b964672ab5dd44b90c6e4210f97a7f7556e2c011c`
- Transport and layout: unchanged pinned CHIRP live CI-V driver
- Issue: some stored memories contain reserved or undocumented mode indexes,
  including `11` and `0x85`. The stock driver assigns `None` to
  `Memory.mode`, which raises before its intended unknown-mode guard.
- Correction: unknown mode indexes are displayed as FM with an explicit
  comment, the mode field is immutable, and an upload to that channel stops
  before radio I/O. Known modes and all other channel fields retain the stock
  IC-7100 behavior.
- Evidence: the 2026-11-16 report from [redacted-email] reached the channel
  records and failed on mode `0x85` in bank 1 location 0, then exposed the
  stock `None` valid-list exception.
- Offline validation: fallback indexes, immutable-mode annotation, branch
  registration, and pre-I/O upload blocking.
- Hardware validation: pending. The reporter must retry a read and verify the
  affected channels against the radio before editing.
- Next milestone: identify the OEM meaning of the unknown mode byte from a
  reviewed CPS export or the reporter's saved channel details.

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
  and the 2026-10-29 NewChirp 1.0.23 report from [redacted-email] showing incomplete
  responses on COM13
- Driver SHA-256:
  `ab65a5b0699585d042257b727dc18003d0d5c41f649ed83dfdff659973d5a4d0`
- Band switching (2026-11-20, mailbox INBOX:825): a live radio keeps no
  clone image, so its saved snapshot holds only the band that was read.
  Choosing the 430 band from the Radio section list fed that snapshot to the
  image reader, which stopped with `Unknown file format`. `model-info` now
  reports `liveRadio`, and the app reads the chosen band from the radio.
  Tests: `test/chirp_bridge_catalog_test.py` (`ModelInfoTest`).
- Hardware validation: 2026-11-19 NewChirp 1.0.61 read 28 channels from a
  physical IC-9700 on COM7 (mailbox INBOX:825). Read only; no write and no
  second-band read confirmed yet.
- Next milestone: the 430 band read after the band-switch fix, then a channel
  write that reads back after a power cycle. Earlier: luc retests after confirming CI-V address `A2h`, USB baud
  rate 115200, `Unlink from [REMOTE]`, and `CI-V Transceive off`; then record
  a successful multi-band read and separate read/write validation

### Icom IC-E90 / IC-T90A clone transport

- Maintainer: NewChirp-owned transport with the upstream ICX90 memory schema
- Maintained file: `drivers/newchirp_icx90.py`
- Protocol notes: `docs/ICX90_PROTOCOL.md`
- Models: Icom IC-E90 and IC-T90A
- Transport: legacy Icom ICF clone serial at 9600 8N1
- Image: model bytes `25 07 00 01`, fixed size `0x2D40`
- Implemented: NewChirp ICF frame construction/parsing, four identity attempts,
  echo handling, checksum validation, fixed 32-byte block writes, clone-in
  turnaround, required clone completion, completion-safe readout, and the
  upstream channel, bank, settings, and special-memory schema. Memories marked
  `invisible_channel` are treated as empty before stale fields are decoded.
- Read policy: a download is successful when decoded frames cover the entire
  `0x2D40` image contiguously. This handles IC-E90 revisions that omit or
  malform the generic final end frame after sending the complete image. A
  normal end frame is still accepted. Every data frame's address, returned
  length, and checksum are validated.
- Write policy: wait for clone-in after `E3` before streaming 362 32-byte
  blocks. Each block uses the CPS checksum. The driver requires a final `E6`
  status byte `00` and reports a radio that does not complete the clone rather
  than claiming success.
- Upload procedure: power-cycle the radio and enter cloning mode as a fresh
  operation before writing. The radio must display `CL IN`; a radio left on
  `CL OUT` from the preceding download will not accept the write.
- Evidence: CS-T90A CPS archive SHA-256
  `c520827dd586f4bcd4304c999699b01c723ee0d4cbc0fbb0f07b6d04892d0fae`;
  executable SHA-256
  `aae6ea1353a3b0f85379bf30eb66a69fc7814a5a370a555acee2579d64ff7adf`;
  VB6 inventory identifies `clsCmcIcf3Drv`, `clsCmcIcf3Sequence`, and
  `clsCmcRadio`, with retry, answer, echo, and packet-size state.
- Field image 2026-11-02: Klas supplied a 11,769-byte CHIRP image,
  SHA-256
  `356041292a5b3edb9204c023359798981c19e406ccd02b5f87993ff3d770cc26`.
  NewChirp failed on stale data in memories 83 and 89; both carry
  `invisible_channel=1`, but upstream attempted to decode tone mode `4`.
  With the visibility guard, the image loads 82 visible channels and no
  parser exception.
- Driver SHA-256:
  `a846c3a353f4c302cd89ae5110e853dc1f896957027bee13269b95ac4061c73a`
- Hardware validation: NewChirp 1.0.45 completed a read and repeated writes on
  Tony G4WIF's IC-E90 once the radio had been reset to a clean codeplug. The
  new retry transport has not yet been physically retested.
- Offline tests cover identity retries, echoed and non-echoed cables, normal
  and missing download end frames, malformed checksums, truncated images,
  clone-in ordering, all 362 write blocks, exact image round trips, and
  missing completion status. The public 500-channel image also loads.
- Next milestone: Tony retests the next build from an unrepaired radio state,
  confirms the display changes to `CL IN`, and verifies the edited channel by
  read-back.

### Icom IC-F50V / IC-F60V capture

- Profile: `drivers/newchirp_icom_f50v_capture.py` (2026-11-19, request
  mailbox INBOX:816). Web Programmer: `icom-ic-f50v-f60v-capture`.
- Why: no public memory map, protocol notes or shared files exist, CHIRP
  has no driver, and Icom's CS-F50V is dealer software that NewChirp has
  not obtained.
- Basis: CHIRP's `icf520.py` (IC-F621-2, same land-mobile line) uses
  Icom's standard clone protocol: CLONE_ID `E0` → 4-byte model ID,
  CLONE_OUT `E2` with that ID → 16-byte legacy hex data frames → `Icom Inc.`
  end frame. The profile learns the model ID from the radio, clones out up
  to 64 KiB with 2-byte addresses, truncates to what the radio sends, and
  stores the model ID in the image metadata.
- Policy: read-only (`NEWCHIRP_WRITE_DISABLED`, `sync_out` refuses). Shows
  no channels. Decodes nothing.
- Driver SHA-256: `a00c14061e82ad8e578891466ff7f581a952ecf3809361660080a73e42d28465`
- Evidence: `test/icom_f50v_capture_test.py` (CHIRP's Icom clone simulator
  with an unknown model ID and size). Hardware: none.
- Next milestone: two or three owner captures with known channels, or
  CS-F50V `.icf` files, to map channel records; then a write-limited driver.

### Icom IC-F50V / IC-F60V (read-only channels)

- Driver: class `IcomF60V` in `drivers/newchirp_icom_f50v_capture.py`
  (2026-11-20), CHIRP ID `Icom_IC-F50V_F60V`. Same transport as the
  capture profile.
- Evidence: one owner's IC-F60V capture read in the Web Programmer
  (INBOX:842, image SHA-256
  `f94c00f3a034df39836a2eeb12066a27090e975e5ff337acd3db4c27d18eff3b`, kept
  out of Git) and the owner's list of eight channels (INBOX:843). This is
  a physical read through the browser transport, not through the desktop.
- Layout: 3538-byte image. `ICOM Inc` at `0x100`; the big-endian u16 at
  `0x110` is the data length minus 8. A section directory of 10-byte
  big-endian entries (id, record size, count, offset, 0) sits at the end
  and its 18 sections tile `0x180` up to the directory with no gaps. The
  driver locates the directory by that contiguity, not by a fixed offset.
  Section 2 is the channels: 16 records of `0x22` bytes. Record: name
  (8 ASCII, space padded), RX Hz u32 BE, TX Hz u32 BE (RX 0 = empty), two
  tone words at `0x10` (`0x8000` = none; values 0-50 seen, encoding
  unconfirmed), then flags/options.
- Check: 7 of 8 listed channels match name and frequency. DECK 2 decodes
  460.500 MHz; the owner listed 460.550. Asked the owner to confirm.
- Policy: read-only (`NEWCHIRP_WRITE_DISABLED`, `set_memory` and
  `sync_out` refuse). Every field is immutable. Images without a valid
  directory are refused with a pointer to the capture profile.
- Known limitations: tones, power, bandwidth, scan and zones are not shown.
- Driver SHA-256: `2178d6c8219b156808b8b4ba268729528343f630061515454b50ab9a3b75768b`
- Tests: `test/icom_f60v_driver_test.py` (5, synthetic image only).
- Next milestone: owner confirms DECK 2 and sends tone settings for two
  or three channels to decode the tone words; a desktop read on hardware.

### Icom CI-V unset tone compatibility

- Override: `drivers/newchirp_icomciv_tone_compat.py` (2026-11-19, IC-910H
  report on 1.0.60, mailbox INBOX:810).
- Issue: `icomciv` decodes `mem.rtone = value / 10`. A channel that never had
  a tone set reports 0, which raises `'0.0' is not a valid value for
  'rtone'`. CHIRP's GUI marks only that channel bad; NewChirp's single-pass
  live read stopped after about four seconds.
- Correction: every CI-V memory frame's parsed object (including NewChirp's
  IC-7200 and IC-9700 frames) reads a non-standard `rtone`, `ctone`,
  `rtone_tx` or `ctone_tx` as 88.5 Hz, CHIRP's default. The tone is unused on
  such a channel. A later write stores 88.5 Hz in that unused field.
- Driver SHA-256: `fa9fb3d71c02bb70b27290e6e281cf4448e96fe31ae62a3929b94d7df1f146a5`
- Evidence: `test/icomciv_tone_compat_test.py` reproduces the reported error
  without the override and passes with it. Hardware validation: none.

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
- Evidence: 2026-11-02 NewChirp 1.0.34 report from [redacted-email] on
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
  `[redacted-email]` completed the clone download and exposed the invalid
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
- Read guidance: download and check channels before an upload, and keep a backup of your radio from the Midland program. Steps: 12 volt power, Bluetooth mic off, MXPG15 on the radio base.
- Write guidance: make a backup before using NewChirp to change the radio.
- Next milestone: none for first read/write support. Several physical uploads have succeeded.
- Website catalog: listed in the normal Midland catalog with desktop and Web Programmer support, and not included in New Experimental Radio Support.

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
  2026-10-30 NewChirp 1.0.23 report from [redacted-email]. The radio
  completed identification, then returned 67 bytes for the first 68-byte
  block response.
- Hardware validation: none for the timeout override.
- Next milestone: the KG-UV2D owner power-cycles the radio and retests a full
  read. If the block is still short, capture whether Wouxun CPS can read it and
  provide the first response header bytes so the protocol variant can be
  separated from a cable timing issue.

### Wouxun KG-UV8D reserved DCS code

- Maintained compatibility: `drivers/newchirp_kg_uv8d_compat.py`
- Protocol notes: `docs/WOUXUN_KG_UV8D_PROTOCOL.md`
- Driver SHA-256:
  `79d8ee3e8fe9b59caf5363f7b1e00b4c37e80eac93d2ce3e80142f6613a5e495`
- Official CPS: `UV8D_SEN.rar`, SHA-256
  `86a9fbe354682ba9cdc658dc9ea1e17835b6425ad979af01f910affb35302eb2`
- Extracted CPS executable: KG-UV8D Commander B2.1.03 (140808), SHA-256
  `534e0e82248b4ce8391e215fe56679ce6c1a2f2a235fde4c1986d6c34c280d57`
- Transport: pinned CHIRP Wouxun clone serial, 19200 8N1, `0x7D` record
  framing, `0x80` through `0x83` commands, additive checksum, and 64-byte
  program blocks. The OEM application's DCB and serial call paths confirm
  19200, eight data bits, no parity, and one stop bit.
- Decode policy: a reserved DCS word whose recovered octal code is outside
  CHIRP's `000`-`777` code set is exposed as no tone on that side. The raw tone
  word remains unchanged in the image. Report error `3777` corresponds to the
  stock decoder's reserved `0x2FFF` word and used to abort the entire map.
- Write policy: stock CHIRP channel, settings, and upload logic. If an affected
  channel is edited without changing its decoded tone state, both original
  reserved tone words are restored after encoding. Deliberately selecting a
  new tone writes the stock valid CHIRP encoding.
- Evidence: official CPS static trace of serial setup at `0x0040A650`, read at
  `0x0040A910`, write at `0x0040AA50`, tone formatting at `0x00420060`, and
  the main read/write maps at `0x004243C0` and `0x00424790`; plus the
  2026-11-04 and 2026-11-15 reports from `[redacted-email]`. The reporter's
  macOS download completed and saved a 32 KiB image, then channel decoding
  failed on code `3777`.
- Reporter image: unavailable. The reports did not include an attachment, so
  the regression uses the pinned upstream image SHA-256
  `ab44d24d89e95e01e717d1de9eb5b5f83e6e1e8a43153c5abc5867b005a346a7`
  with the reported reserved word inserted into channel 1.
- Offline validation: all 999 slots decode with the reserved word present,
  editing another field preserves the original tone bytes, valid DCS `023`
  still decodes and round-trips, and `0xFFFF` remains no tone. All 433 Python
  tests pass.
- Hardware validation: pending. The reporter must read the radio with the next
  NewChirp build and compare the formerly failing channel with the radio.
- Next milestone: reporter confirms the complete channel map opens, sends the
  saved image, and verifies the affected channel's tone and frequency before
  any upload.

### Wouxun KG-689E / KG-699E

- Maintained driver: `drivers/newchirp_wouxun_kg689e.py` (new 2026-11-19,
  forum topic 93). Protocol and evidence: `docs/WOUXUN_KG689E_PROTOCOL.md`.
- Source: static analysis of Wouxun's `KG-699E 689E.exe` (MFC), unpacked
  from the official Setup Factory 6 installer. Package SHA-256
  `9a7b56650b30b9eac691f7b638cf0d87b84051d63c1d51add239ae4fb3876c4b`;
  programmer SHA-256
  `21620918dc196e04631bc88e761fd7ff17add76156f3c57ca0bd2a55bd77f554`.
- Transport: 9600 8N1, DTR on. `HiWOUXUN\x02` → `06`; `02` →
  `06 KG669V F8`; `06` → `06`. Reads `R hi lo 40` → `W hi lo 40` + 64 bytes
  then `06`/`06`; writes `W hi lo 10` + 16 bytes → `06`.
- Read: 67 blocks (channels `0x0010-0x080F`, names `0x1010-0x180F`,
  settings `0x0810`, `0x0E20`, `0x1810`) plus the radio-limits block
  `0x0970`, which the CPS reads before every write.
- Write: exactly the CPS spans (full channel and name pages, 32 bytes of
  `0x0810`, 64 of `0x0E20`, 32 of `0x1810`). It first re-reads `0x0970` and
  refuses any channel outside the radio's own RX/TX limits (+0.995 MHz on
  the upper edge, as the CPS does), or a radio that reports no limits.
- Fields: RX/TX, CTCSS/DCS both directions, wide/narrow, high/low, scan add,
  6-character name; extras for busy lock, DTMF optional signal and mute
  mode. Unknown bits and bytes 14-15 are preserved.
- Cable echo (2026-11-20, INBOX:840): the first owner read got `48` ('H',
  the first wake byte) back on every wake because his cable echoes host
  bytes. The driver now detects an echoed wake, strips the echo from every
  later exchange (and refuses on an echo mismatch), and when only the echo
  comes back says the cable is the wrong type instead of "answered 48".
- Driver SHA-256: `d5f639986326fedb3c5d9852268d3a484372f3ed7e05ee5f028e053183cfd826`
- Hardware validation: none. Replay evidence:
  `test/wouxun_kg689e_driver_test.py` (12 tests, including echo cables).
- Website: the Web Programmer profiles (Nov 18) read the DTMF bit as
  bandwidth and the bandwidth bit as scan skip, invented a bit-0 split
  flag, wrote the second halves of `0x0810`/`0x1810`, and had no limit
  check. They were corrected on 2026-11-19 to match this driver.
- Next milestone: a reporter reads the radio, saves the image, writes one
  channel name change, power-cycles and reads back.

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
- Identity failures report the decoded display name, internal model, and
  software string so Q10G-family variants can be diagnosed without exposing
  the raw identity-region image.
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

### Baofeng UV-5R family: settings block read first

- Driver: `drivers/newchirp_uv5r_aux_first.py` (2026-11-25, report on
  1.0.73 macOS, mailbox INBOX:985).
- Issue: the radio answered the `50 BB FF 20 12 07 25` handshake (ident
  `AA 30 76 04 00 05 20 DD`), the firmware-version reads at 0x1E80, 0x1EC0
  and 0x1FC0, and every channel block 0x0000-0x17C0, then sent nothing for
  0x1EC0. Stock fails with "Radio refused to send second block 0x1ec0". Same
  result five times as UV-5R, BF-F8HP and UV-5RX3.
- OEM evidence: Baofeng UV-5RX CPS 20231124 (ZIP SHA-256
  `4848128a68dcb0d2ddfa54c65ad43591718d8e9e3b62112691ff6cd60926590a`, same
  handshake in `WriFreq.hSTable1`). `ReadCHData` reads 0x0000-0x17C0 and stops.
  `ReadConfigData` reads 0x1FC0 then 0x1EC0, at the start of its own session.
  The CPS never asks for the settings block after the channels.
- Correction: the settings block is read straight after the firmware-version
  read, then the channels. The blocks, block sizes, the dropped-byte 0x10 tail
  reads and the image layout are unchanged. BJ-UV55 and radios without the
  settings block keep the stock download. Uploads are unchanged. An upload
  still writes the settings ranges after the channels; whether this radio
  accepts that is not known yet.
- Evidence: `test/uv5r_aux_first_test.py` (a fake radio that refuses the
  jump; stock fails on it, the override reads a byte-identical image).
  Hardware validation: none.

### Settings the driver cannot load (all clone radios)

- Bridge: `preserve_unloadable_settings` in `scripts/chirp_bridge.py`
  (2026-11-20, UV-5R report on 1.0.61, mailbox INBOX:833).
- Issue: a radio can store a value outside a driver's range, for example a
  UV-5R factory squelch calibration of 124 against `uv5r.py`'s 0-123. CHIRP
  logs `Failed to load ...` and leaves the value unset. The driver's
  `set_settings` then raised `int() argument must be ... not 'NoneType'`, so no
  setting could be written.
- Correction: before `set_settings`, each unloaded value gets the radio's own
  stored value back, without validation, and is marked read-only. The app
  already shows these values as unsupported, and the radio's bytes are
  written back unchanged. Clamping into range was rejected because it would
  overwrite factory calibration.
- Evidence: `UnloadableSettingTest` in `test/chirp_bridge_upload_test.py`
  (uv5r.py image with the service block). Hardware validation: none.

### Blank CSV cross mode

- Bridge `apply_json` and `lib/services/chirp_csv.dart` (2026-11-20, UV-32
  report on 1.0.54, mailbox INBOX:828).
- A CSV with an empty `CrossMode` cell gave every channel the cross mode
  `''`. CHIRP rejects that value, so the write stopped on the first such
  channel, even one that was not a Cross channel. Blank now imports as
  `Tone->Tone`, and the bridge ignores an invalid cross mode on channels that
  are not Cross. Tests: `chirp_csv_test.dart`, `chirp_bridge_upload_test.py`.

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
