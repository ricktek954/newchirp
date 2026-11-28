# NewChirp Project State

Last updated: 2026-11-28

This is the short operational handoff for restarting work with no conversation
history. `README.md` and `AGENTS.md` remain authoritative for build rules and
release requirements.

## Resume here

- CHIRP pin moved 2026-11-28 from `21e42e45` to upstream master
  `f28d9202f98118af16706b3f1a8d89458da1fa1c` (99 commits, archive SHA-256
  `0c291cad...a8c7`) after the first upstream review
  (`docs/upstream_reviews/2026-11-28-f28d9202f.md`, ledger
  `w-20261128-d1f0`). Every platform's next build ships it: run
  `bash scripts/update_chirp.sh` first. New radios include BTECH UV-PRO,
  Kenwood TH-K20 / TM-D750, Yaesu FTM-150E (NewChirp driver) and Zastone
  ZT-D9000. NewChirp drivers keep precedence (FTX-1, FTM-150E;
  `test/newchirp_precedence_test.py`). Verified on macOS: all 87 Python
  test files and all 258 Flutter tests pass on the new pin. The website
  catalog is built from the pin (`catalog/chirp-pinned-models.json`).
  Next review due around 2026-12-12.

- Linux `1.0.79` is live from source commit `d1665f13`. It adds the
  Quansheng TK11 OEM login/session flow before uploads, decodes and writes
  TK-350 5 kHz channels by their step bits and writes CTCSS tones, and makes
  UV-5RM Pro/5RH Pro announce at 19200 first while skipping stray bytes
  before the sync acknowledgement like the v1.12 CPS. Verification: analyzer
  clean; all 257 Flutter tests with the bundled Python 3.13 runtime; 701
  bundled Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI
  maximum GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version
  `1.0.79`; DEB and AppImage Xvfb smoke tests; AppImage host launches under
  Wayland and X11; package payloads include the TK11, TK-350, and UV-5RM Pro
  changes and omit GLVND/EGL/GLES loaders; all public downloads returned
  HTTP 200; and the Linux platform manifest reports `1.0.79`.

### macOS session handoff, 2026-11-27 (before a reboot)

Released: macOS `1.0.77` (2026-11-27), Windows `1.0.76`, Linux `1.0.79`. The website matches
`022980f`; the bundle `index-UeTE45j-.js` went live at
`03:39`. Desktop and web are committed and pushed. All support mail has been
answered except one forum notification (UID 1048).

Fixed since 1.0.76. These are in `main`, the Web Programmer, macOS 1.0.77, and
Linux 1.0.79 (Windows needs its next build):

- TK-350 5 kHz channels, item `w-20261127-edf2`, commit `a029606e7`.
  - The step size is set by record byte 13: bit 5 for RX and bit 6 for TX.
    Set means 6.25 kHz; clear means 5 kHz, with anchors `8C5E` (RX) and
    `AF90` (TX). This was confirmed by loading records into KPG-23D in QEMU.
  - Owner Paul's channel 114 was a 5 kHz channel. NewChirp 1.0.76 wrote
    6.25 kHz words into it, so the radio sits on 353.020 / 344.010 and will
    not transmit.
  - He has been sent the steps to repair it in the Web Programmer.
  - His other writes worked: about 12 writes on 1.0.76, and the radio
    receives and transmits.
  - Graduate the TK-350 when he confirms channel 114 reads back and
    transmits after a power cycle (`docs/DRIVER_STATUS.md` row).
- UV-5RM Pro handshake, item `w-20261125-2905`, commit `3287cf9d4`.
  - CPS v1.12 skips bytes that are not seed^'A' after the sync. The radio
    answered "N" (0x4E) to both sync forms.
  - NewChirp now waits up to 1 s for the acknowledgement and skips stray
    bytes. This is still a hypothesis; Kaloyan has been asked to retest in
    the Web Programmer.
- Quansheng TK11 upload opens its own session (`e1d4ce671`). Earlier fixes in
  `main` after 1.0.76 include the per-channel decode and the image-attach
  work; check `git log` since `026cd8fc7`.

Waiting on owners:

- Paul (TK-350): repair and read-back of channel 114.
- Paul (TK-359): his image is in the ledger (`w-20261126-95c9`, image SHA
  `2c3bb88f...`). Writing stays off. The image has 22 site channels whose
  names look byte-reversed (NEPO = OPEN). Next step: compare these records
  with the decoder.
- Kaloyan: UV-5RM Pro retest.
- TK11 owner (`w-20261126-0461`) and Ferrite owner (`w-20261126-8d5d`).
- Mike: Abbree AR8118 label and cable when the radio arrives
  (`w-20261126-044a`). The OEM CPS is on abbree.com/pages/abbree and has not
  been fetched yet.
- Bill: KPG-49 software is coming by another mail account; not received yet
  (`w-20261126-565d`).
- Milan: Windows SmartScreen download (#91). FAQ `#windows-smartscreen` was
  added.
- Del: Android app cannot see his Tidradio Bluetooth adapter after pairing
  it in Android settings (`w-20261127-31d2`). He was told to forget the
  adapter in Android settings and connect from the app.
  - Proposed mobile fix, not started: also list devices the system already
  has connected (`UniversalBle.getSystemDevices`) in
  `lib/services/ble_radio_service.dart`.

Open tasks:

- Forum topic 56, post 218 (emmett, Yaesu FT-2900 "header" error,
  `w-20261127-b76c`): the reply is drafted but not posted, because there is
  no posting tool and production `data/` must not be written. Rick posts it.
  Draft text: ask whether the label says FT-2900R or FT-2900E and whether the
  radio is TX-modified (try "FT-2900R/1900R(TXMod)"), then ask for the
  report from the error's "Submit Bug Report" button.
  - Stock `ft2900` accepts only one 10-byte ID. CHIRP leaves the FT-2900E
    class (`...41 02...`) unregistered. A possible NewChirp overlay would
    accept the R, E and Mod IDs and reuse the received ID on upload.
- TK-350: adding channels to empty slots is still refused. Trace the
  KPG-23D defaults for a new channel; the scan bitmap is near `0x0D40`.
  - Byte 12 options are known: power bits 7-6, shift bit 5, busy bit 4.
  - Typing into an empty row in KPG-23D under QEMU kept going to the
    Transmit column. Crafting `.U1F` files and loading them works better
    (the VM must be restarted to see new files).
- Next macOS release is `1.0.77` (platform versions are independent). Build
  it when Rick asks, to ship the fixes above to desktop users.

Session tools:

- Mail scripts are in the session scratchpad and in web `ops/support/`.
  Reply drafts used this session are in the scratchpad `replies/` folder,
  which a reboot may clear.
- KPG-23D test files are in the scratchpad `k3/`. The QEMU harness is in
  `tools/rea/qemu_dos/` (local only).

- Linux `1.0.78` is live from source commit `3d16733f`. It decodes channels
  one at a time and reports undecodable slots instead of failing the entire
  list, lets bug reports attach the radio image, enables the experimental
  TK-350 desktop write path and decodes/preserves its CTCSS tones, adds the
  UV-5RM Pro plain-`PROGRAM` synchronization fallback, and gives the Find
  Repeaters results list its own scroll bar. Verification: analyzer clean;
  all 257 Flutter tests with the bundled Python 3.13 runtime; 693 bundled
  Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI maximum
  GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version `1.0.78`;
  DEB and AppImage Xvfb smoke tests; AppImage host launches under Wayland and
  X11; package payloads include the per-channel decode, image-report,
  TK-350, UV-5RM Pro, and Repeater UI changes and omit GLVND/EGL/GLES
  loaders; all public downloads returned HTTP 200; and the Linux platform
  manifest reports `1.0.78`.
- Linux `1.0.77` is live from source commit `8a24cd2f`. It decodes TK-350
  channels across all UHF bands, handles the TK-359 uniform `Z` plus fill-byte
  block and KPG-32D 32-byte channel records with flag-byte frequencies, and
  bounds IC-E90 tone, DTCS, mode, tone-mode, and step lookups so one
  out-of-table value cannot stop the channel list. Verification: analyzer
  clean; all 254 Flutter tests with the bundled Python 3.13 runtime; 677
  bundled Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI
  maximum GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version
  `1.0.77`; DEB and AppImage Xvfb smoke tests; AppImage host launches under
  Wayland and X11; package payloads include the TK-350, TK-359, and IC-E90
  decoder changes and omit GLVND/EGL/GLES loaders; all public downloads
  returned HTTP 200; and the Linux platform manifest reports `1.0.77`.
- Linux `1.0.76` is live from source commit `ab66c0d7`. It adds the
  KPG-23D TK-350 and KPG-32D TK-359 sessions with OEM DTR/RTS behavior,
  reads UV-5R settings before the channels for radios that refuse the jump
  back, reports the real UV-3R handshake error, accepts a short MD-UV380 DFU
  identity while keeping memory reads strict, and retries the TK-863G `0x7C`
  memory session like KPG-76D. It also explains the safe CSV route when a
  full image belongs to a different UV-5R radio. Verification: analyzer
  clean; all 254 Flutter tests with the bundled Python 3.13 runtime; 672
  bundled Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI
  maximum GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version
  `1.0.76`; DEB and AppImage Xvfb smoke tests; AppImage host launches under
  Wayland and X11; package payloads include the new KPG, UV-5R, UV-3R, DFU,
  bridge, and TK-863G changes and omit GLVND/EGL/GLES loaders; all public
  downloads returned HTTP 200; and the Linux platform manifest reports
  `1.0.76`.
- Linux `1.0.75` is live from source commit `79b693a5`. It fixes RT-950 Pro
  Ferrite zone reads by ending `READ_MANY` cleanly when the radio returns an
  empty non-advancing answer, and preserves undecodable Baofeng 5RX S-CODE
  values for the repair step instead of stopping the write. Verification:
  analyzer clean; all 254 Flutter tests with the bundled Python 3.13 runtime;
  654 bundled Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI
  maximum GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version
  `1.0.75`; DEB and AppImage Xvfb smoke tests; AppImage host launches under
  Wayland and X11; package payloads include both fixes and omit
  GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the
  Linux platform manifest reports `1.0.75`.
- **Linux Wayland freeze follow-up (2026-11-24):** the simulated write test
  in `docs/LINUX_WAYLAND_FREEZE_TEST.md` did not reproduce the freeze on the
  available Hyprland 0.56.2 Wayland host. Foreground, switch-away,
  hidden-workspace, XWayland, and 120-second native runs all completed with
  continuous frame heartbeats, steady RSS, and no stale progress. Exact KDE
  Plasma Wayland/X11 controls and multi-monitor scaling remain untested
  because Plasma is not installed and this host has one display. Evidence is
  on ledger item `w-20261121-ab4d`. The owner's 1.0.72 logs still show the
  write finishing while the window stops redrawing at 18%.
- RepeaterBook approved NewChirp's centralized-server API application on
  2026-11-20 for `api.export` and `api.export_row`. The shared `app_` token is
  configured only on `newchirp.net`; desktop and browser searches use the
  server relay at `/api/repeaters/repeaterbook/search`. The old CHIRP bulk
  dataset path and the pending-approval notice are removed. Credential
  custody, request routing, mapping, and verification are documented in
  `docs/REPEATERBOOK_API.md`. Verification: 12 focused website relay tests,
  the production web build, all 550 Python tests with two fixture-dependent
  skips, all 239 Flutter tests, and `flutter analyze lib test` pass. The live
  relay returned 9 filtered Buffalo matches and an Ontario-only Canadian
  result set; the desktop bridge converted the Buffalo results into CHIRP
  channels. macOS `1.0.63` and later contain this integration.
- The manufacturer/model driver work ledger lives in `database/driver_work/`
  (one JSON file per record since 2026-11-19; `database/driver_work.sqlite3`
  is a git-ignored cache). Use `scripts/driver_work.py` to list/search
  work, add bugs or enhancements, append commit/email/evidence/hardware-test
  events, and export `docs/DRIVER_WORK.md`. The initial database contains all
  67 current driver inventory rows plus recent CPS-derived drivers and email
  bug-fix history. `database/README.md` documents statuses and commands.
- Linux `1.0.74` is live from source commit `76519b2d`. It adds the
  experimental Ferrite RT-950 Pro link-protocol driver and web profile,
  renders corrupt Baofeng tone words as no tone, names refused channels and
  write progress for live-radio refusals, adds FT-60 clone/cable guidance,
  sibling-model selection, AnyTone USB guidance, XWayland preference, and the
  PMR446 frequency reference. It also carries TH-D7G, UV-5R Mini,
  AT-D878UVII Plus, 5RX, and Wayland follow-up fixes. Verification: analyzer
  clean; all 254 Flutter tests; 653 bundled Python tests with two
  fixture-dependent skips; Ubuntu 20.04 ABI maximum GLIBC `2.18`; DEB, RPM,
  and Pacman metadata plus embedded version `1.0.74`; DEB and AppImage Xvfb
  smoke tests; AppImage host launches under Wayland and X11; package payloads
  include Ferrite, Baofeng tone handling, PMR446, and bridge updates and omit
  GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the
  Linux platform manifest reports `1.0.74`.
- Linux `1.0.73` is live from source commit `b8dd8004`. It adds Spanish and
  French beta translations, offers channel-name shortening for radio limits,
  resynchronizes FT-70D clone reads on the AH51G identifier, decodes Icom
  ID-5100 DTCS-T and pocket-beep tones, adds the TIDRADIO TD-H9
  Normal/HAM/GMRS driver on the TD-H8 G4 transport, matches OEM memory-session
  timing for TK-863G, updates UV-5R Mini handshakes, and reuses loaded bridge
  drivers across reloads. Verification: analyzer clean; all 253 Flutter tests;
  636 bundled Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI
  maximum GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version
  `1.0.73`; DEB and AppImage Xvfb smoke tests; AppImage host launches under
  Wayland and X11; package payloads include the TD-H9, UV-5RM Plus, TK-863G,
  and bridge updates and omit GLVND/EGL/GLES loaders; all public downloads
  returned HTTP 200; and the Linux platform manifest reports `1.0.73`.
- Linux `1.0.72` is live from source commit `6704d9bb`. It preserves the
  selected radio zone when replacing the channel list and allows repeat radio
  settings writes. It also carries the RT22 tone and deployment updates plus
  the UV-5RM Plus zone, UV-82, KG-689, and settings-button report and reply
  records. Verification: analyzer clean; all 249 Flutter tests; 618 bundled
  Python tests with two fixture-dependent skips; Ubuntu 20.04 ABI maximum
  GLIBC `2.18`; DEB, RPM, and Pacman metadata plus embedded version `1.0.72`;
  DEB and AppImage Xvfb smoke tests; AppImage host launches under Wayland and
  X11; package payloads omit GLVND/EGL/GLES loaders; all public downloads
  returned HTTP 200; and the Linux platform manifest reports `1.0.72`.
- Linux `1.0.71` is live from source commit `98309c23`. It adds the read-only
  AnyTone AT-D878UVII Plus driver, fixes AnyTone D578 channel-bank sizing,
  adds the read-only Quansheng UV-K5 Robzyl RO-KO 512K profile, encodes
  Baofeng 5RX/UV-S9X3 channel power as the CPS does, and keeps unknown
  Baofeng power values readable without rewriting them. Verification:
  analyzer clean; all 249 Flutter tests; 618 bundled Python tests with two
  fixture-dependent skips; Ubuntu 20.04 ABI maximum GLIBC `2.18`; DEB, RPM,
  and Pacman metadata plus embedded version `1.0.71`; DEB and AppImage Xvfb
  smoke tests; AppImage host launches under Wayland and X11; new drivers and
  power handling present in package payloads with no GLVND/EGL/GLES loaders;
  all public downloads returned HTTP 200; and the Linux platform manifest
  reports `1.0.71`.
- Linux `1.0.70` is live from source commit `76de9782`. It adds a write
  watchdog that ends stalled radio operations, safely treats malformed or
  out-of-range tone fields as no tone without rewriting them on DM-32UV,
  RT-950, and UV-17ProGPS images, and retries the UV-32/UV-5RM Plus handshake.
  It also carries the latest Android USB and proxy broken-pipe work plus all
  intervening driver-work records. Verification: analyzer clean; all 249
  Flutter tests; 605 bundled Python tests with two fixture-dependent skips;
  Ubuntu 20.04 ABI maximum GLIBC `2.18`; DEB, RPM, and Pacman metadata plus
  embedded version `1.0.70`; DEB and AppImage Xvfb smoke tests; AppImage host
  launches under Wayland and X11; changed drivers and bridge code present in
  package payloads with no GLVND/EGL/GLES loaders; all public downloads
  returned HTTP 200; and the Linux platform manifest reports `1.0.70`.
- Linux `1.0.69` is live from source commit `5dd9aa67`. It adds the
  experimental Retevis RA87 driver, fixes Retevis RT22 identification and Web
  Programmer mapping, adds the UV-5R Mini driver with OEM-style block retries,
  decodes Yaesu VX-170/VX-177 split tones, adds channel-list PDF printing,
  hardens radio-key clone readiness and stale-input flushing, fixes TK-270G
  bank counts, and updates UV-K60 Plus and F4HWN 7.0 behavior. Verification:
  all 249 Flutter tests passed; 597 Python tests passed with two
  fixture-dependent skips; the Ubuntu 20.04 ABI check passed with maximum
  GLIBC `2.18`; DEB and AppImage Xvfb smoke tests passed; the final AppImage
  launched under host Wayland and XWayland; package payloads include the four
  release drivers and omit GLVND/EGL/GLES loaders; the embedded version is
  `1.0.69`; all public downloads returned HTTP 200; and the Linux platform
  manifest reports `1.0.69`.
- Linux `1.0.68` is live from source commit `360773be`. It ends DM-32UV
  channel and zone names at the first NUL so stale padding no longer leaks
  into edited names. Verification: analyzer clean; 242 Flutter tests; 559
  Python tests with two fixture-dependent skips; max glibc `2.18`; DEB, RPM,
  and Pacman metadata plus embedded version `1.0.68` / `68`; DEB and AppImage
  Xvfb launch tests passed on Ubuntu 20.04; the final AppImage launched under
  host Wayland and XWayland; package payloads include the DM-32UV fix and omit
  GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the
  Linux platform manifest reports `1.0.68`.
- Linux `1.0.67` is live from source commit `99175783`. It preserves moved
  channel extras when an insertion shifts channels onto a different slot,
  numbers TK-270G bank positions from 1 like KPG-56D, and adds RT-950 Pro
  Bluetooth read diagnostics. Verification: analyzer clean; 242 Flutter
  tests; 557 Python tests with two fixture-dependent skips; max glibc `2.18`;
  DEB, RPM, and Pacman metadata plus embedded version `1.0.67` / `67`; DEB
  and AppImage Xvfb launch tests passed on Ubuntu 20.04; the final AppImage
  launched under host Wayland and XWayland; package payloads include the
  TK-270G and RT-950 Pro fixes and omit GLVND/EGL/GLES loaders; all public
  downloads returned HTTP 200; and the Linux platform manifest reports
  `1.0.67`.
- Linux `1.0.66` is live from source commit `268f70cd`. It re-enables
  Radtel RT-950 Pro writes after physical read/write validation and adds
  receive-only channel handling and UI safeguards for marine and protected
  channels. Verification: analyzer clean; 242 Flutter tests; 550 Python tests
  with two fixture-dependent skips; max glibc `2.18`; DEB, RPM, and Pacman
  metadata plus embedded version `1.0.66` / `66`; DEB and AppImage Xvfb launch
  tests passed on Ubuntu 20.04; the final AppImage launched under host Wayland
  and XWayland; package payloads include the rebuilt RT-950 Pro driver and
  omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and
  the Linux platform manifest reports `1.0.66`.
- Linux `1.0.65` is live from source commit `014df59b`. It integrates the
  approved RepeaterBook API relay, expands the read-only Icom IC-F50V/F60V
  channel support, handles echoing programming cables on the Wouxun KG-689E,
  and carries the related UI and error-reporting fixes. Verification:
  analyzer clean; 239 Flutter tests; 550 Python tests with two
  fixture-dependent skips; max glibc `2.18`; DEB, RPM, and Pacman metadata
  plus embedded version `1.0.65` / `65`; DEB and AppImage Xvfb launch tests
  passed on Ubuntu 20.04; the final AppImage launched under host Wayland and
  XWayland; package payloads include the IC-F50V/F60V and KG-689E drivers and
  omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and
  the Linux platform manifest reports `1.0.65`.
- macOS `1.0.77` is live from source commit `0e9a4242b` as a universal,
  signed, and notarized DMG. Since 1.0.76: TK-350 5 kHz step bits, CTCSS
  tone writes and frequency edits no longer refused by the tone check;
  UV-5RM Pro handshake follows CPS v1.12 (19200 first, stray bytes skipped);
  TK11 upload opens its own session. Verification: analyzer clean; 257
  Flutter tests; 701 Python tests (2 fixture skips); embedded `1.0.77` /
  `77`; arm64 and x86_64; 278 driver modules; bundled drivers and bridge
  match source; Gatekeeper accepted DMG and mounted app; local, server and
  public SHA-256 `1feead82…cad7d879c`. Notarization:
  `8e4766d8-b1ba-48ba-b9db-81f3fdab5206`. The commit sits on top of Linux
  `1.0.79` (`d1665f133`); platform versions are independent.
- macOS `1.0.76` is live from source commit `026cd8fc7` as a universal,
  signed, and notarized DMG. Since 1.0.75: UV-5RM Pro plain-sync fallback;
  TK-350 experimental write and CTCSS tone decode; TK-359 read baseline (write
  still off); per-channel decode with an undecodable-channel notice; bug
  reports can attach the radio image; a working scroll bar for Find Repeaters
  results. Verification: analyzer clean; 257 Flutter tests; full Python suite;
  embedded version `1.0.76` / `76`; arm64 and x86_64; 277 driver modules;
  bundled driver and bridge hashes match source; strict codesigning and
  Gatekeeper accepted; matching local, server, and public SHA-256
  `a5f4841b…7869bf`. Notarization submission:
  `a4f926ae-93ba-4438-ad7c-1e034f1c2c2c`.
- macOS `1.0.75` is live from source commit `0407d809` as a universal,
  signed, and notarized DMG. It adds the TK-350 all-UHF-band channel decode,
  TK-359 `Z` fill-block handling and KPG-32D channel records, and the IC-E90
  bounded decode. Verification: analyzer clean; 254 Flutter tests; 677
  Python tests; embedded version `1.0.75` / `75`; arm64 and x86_64; 277
  driver modules; bundled driver and bridge hashes match source; strict
  codesigning and Gatekeeper accepted; matching local, server, and public
  SHA-256 `45c4bb35…34337`. Notarization submission:
  `83493bc5-6950-4b58-8f57-0fb76d591fd8`. Platform versions are
  independent: macOS 1.0.75 follows macOS 1.0.74 regardless of Linux.
- macOS `1.0.74` is live from source commit `e7a0fc5e` as a universal,
  signed, and notarized DMG. It adds the OEM-traced KPG-23D TK-350 and
  KPG-32D TK-359 sessions with BIOS DTR/RTS behavior, the UV-5R/UV-3R
  aux-first download and UV-3R error reporting, the MD-UV380 short DFU
  identity read, the TK-863G memory-session retry, and image-mismatch CSV
  guidance. Verification: analyzer clean; 254 Flutter tests; 672 Python
  tests; embedded version `1.0.74` / `74`; arm64 and x86_64 Python
  `3.13.15`; CHIRP `21e42e4518c167548af90ed7f9edf75e516c491a`; 277 driver
  modules; catalog `list-models` returned 608 models across 62 vendors;
  strict codesigning and Gatekeeper accepted; and matching local, server,
  and public SHA-256 `631e5867…41aa7d`. Notarization submission:
  `e999d8f9-3def-43fc-8596-cec6e8e91115`. Run `notarytool` outside the
  Claude Code sandbox; inside it the `newchirp` keychain profile is not found.
- macOS `1.0.73` is live from source commit `5e734229` as a universal,
  signed, and notarized DMG. It adds the experimental Ferrite RT-950 Pro
  link-protocol driver and web profile, completes Ferrite empty-read and zone
  ranges, preserves driver extras it cannot decode for safe repair, and
  carries the corrupt Baofeng tone, 5RX S-CODE, refused-channel progress,
  FT-60, sibling-model, AnyTone USB, XWayland, PMR446, TH-D7G, and UV-5R Mini
  work. Verification: analyzer clean; 254 Flutter tests; 654 Python tests
  with two fixture-dependent skips; embedded version `1.0.73` / `73`; arm64
  and x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 274 driver modules; catalog
  `list-models` returned 608 models across 62 vendors; strict codesigning
  and Gatekeeper accepted; mounted-app launch smoke test passed; and matching
  local, server, and public SHA-256. Notarization submission:
  `83014a33-40e8-4065-abba-40cf4b8585f6`.
- macOS `1.0.72` is live from source commit `d502504e` as a universal,
  signed, and notarized DMG. It adds the experimental Ferrite protocol driver
  for the RT-950 Pro, a PMR446 frequency reference, FT-60 clone-entry
  guidance, sibling-model selection guidance, safe reading of corrupt
  Baofeng tone words, 5RX tone handling, AnyTone USB-port guidance, and
  refused-channel plus live-write progress diagnostics. Verification:
  analyzer clean; 254 Flutter tests; 653 Python tests with two
  fixture-dependent skips; embedded version `1.0.72` / `72`; arm64 and
  x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 274 driver modules; catalog
  `list-models` returned 608 models across 62 vendors; strict codesigning
  and Gatekeeper accepted; mounted-app launch smoke test passed; and matching
  local, server, and public SHA-256. Notarization submission:
  `1fd6915b-24e2-40c2-927e-104e67879ff8`.
- macOS `1.0.71` is live from source commit `876c765b` as a universal,
  signed, and notarized DMG. It adds TIDRADIO TD-H9 Normal, HAM, and GMRS
  profiles on the TD-H8 G4 transport, matches TK-863G OEM memory-session
  timing, improves UV-5R Mini echo and handshake recovery, preserves the
  selected zone during list replacement, and includes the cumulative 1.0.70
  UI, driver, bridge, Android USB, trace, printing, and write-progress
  changes. The bridge now reuses loaded NewChirp driver modules for the same
  file path instead of re-registering duplicate classes. Verification:
  analyzer clean; 253 Flutter tests; 636 Python tests with two
  fixture-dependent skips; embedded version `1.0.71` / `71`; arm64 and
  x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 274 driver modules; catalog
  `list-models` returned 607 models including all three TD-H9 profiles;
  Apple notarization accepted and the ticket validates; mounted-app launch
  smoke test passed; and matching local, server, and public SHA-256. This
  host's code-signing assessment service reports the same internal error seen
  with prior releases, so that local check is not treated as an artifact
  failure. Notarization submission:
  `11a7e4f4-f0b4-4bec-bffa-e89561f2a606`.
- macOS `1.0.70` is live from source commit `b6fbc544` as a universal,
  signed, and notarized DMG. It preserves the active radio zone when replacing
  the channel list, allows repeated radio-settings writes, adds RT22 tone and
  UV-5RM Plus zone fixes, applies UV-82 and KG-689 settings-button
  corrections, and carries the cumulative 1.0.69 drivers, watchdog, tone
  handling, Android USB, UI, bridge, trace, printing, and write-progress
  changes. Verification: analyzer clean; 249 Flutter tests; 618 Python tests
  with two fixture-dependent skips; embedded version `1.0.70` / `70`; arm64
  and x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 272 driver modules; catalog
  `list-models` returned 604 models; Apple notarization accepted and the
  ticket validates; mounted-app launch smoke test passed; and matching local,
  server, and public SHA-256. This host's code-signing assessment service
  reports the same internal error seen with prior releases, so that local
  check is not treated as an artifact failure. Notarization submission:
  `c763ad92-b1db-4a94-9110-757a471ab3f0`.
- macOS `1.0.69` is live from source commit `0f7f9048` as a universal,
  signed, and notarized DMG. It adds a read-only UV-K5 Robzyl RO-KO 512K
  profile, AT-D878UVII Plus support with the D578 second-bank mapping fix,
  Baofeng 5RX OEM power encoding, safe handling of unknown Baofeng power
  values, and the cumulative 1.0.68 watchdog, tone, UV-32, Android USB,
  driver, trace, printing, and write-progress changes. Verification: analyzer
  clean; 249 Flutter tests; 618 Python tests with two fixture-dependent skips;
  embedded version `1.0.69` / `69`; arm64 and x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 272 driver modules; catalog
  `list-models` returned 604 models; Apple notarization accepted and the
  ticket validates; mounted-app launch smoke test passed; and matching local,
  server, and public SHA-256. This host's code-signing assessment service
  reports the same internal error seen with prior releases, so that local
  check is not treated as an artifact failure. Notarization submission:
  `baa15c49-30d7-4b03-986b-a30fc5dbe577`.
- macOS `1.0.68` is live from source commit `48f56627` as a universal,
  signed, and notarized DMG. It ends stalled writes with a diagnostic
  watchdog, reads unreadable DM-32UV and RT-950 tone values without aborting
  the channel, retries the UV-32 handshake like the OEM CPS, handles Android
  USB broken-pipe failures, and includes the cumulative 1.0.67 driver, UI,
  bridge, trace, printing, and write-progress changes. Verification: analyzer
  clean; 249 Flutter tests; 605 Python tests with two fixture-dependent skips;
  embedded version `1.0.68` / `68`; arm64 and x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 269 driver modules; catalog
  `list-models` returned 602 models; Apple notarization accepted and the
  ticket validates; mounted-app launch smoke test passed; and matching local,
  server, and public SHA-256. This host's code-signing assessment service
  reports the same internal error seen with prior releases, so that local
  check is not treated as an artifact failure. Notarization submission:
  `ad8c3d81-e2f2-493a-a972-cb34f65952ea`.
- macOS `1.0.67` is live from source commit `8e03e24b` as a universal,
  signed, and notarized DMG. It includes the cumulative driver, UI, bridge,
  trace, printing, and write-progress fixes after 1.0.66, including FTM-300DR
  and F4HWN 7.0, RT22, DM-32UV progress/cancel, UV-K60 Plus, RA87, UV-5R Mini,
  VX-170, TH-350, and no-step tuning work. Verification: analyzer clean; 249
  Flutter tests; 597 Python tests with two fixture-dependent skips; embedded
  version `1.0.67` / `67`; arm64 and x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 269 driver modules; catalog
  `list-models` returned 602 models; Apple notarization accepted and the
  ticket validates; mounted-app launch smoke test passed; and matching local,
  server, and public SHA-256. This host's code-signing assessment service
  reported an internal error for both the new DMG and the already-published
  1.0.66 control, so that local check is not treated as an artifact failure.
  Notarization submission: `653b46a8-5cd8-43e5-bea0-da202daa2832`.
- macOS `1.0.66` is live from source commit `ee72c09e` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It includes the
  DM-32UV channel and zone name NUL-termination fix, current RT-950 Pro
  behavior, approved RepeaterBook API search, and cumulative driver, UI,
  and bridge compatibility changes. Verification: analyzer clean; 242
  Flutter tests; 559 Python tests with two fixture-dependent skips; embedded
  version `1.0.66` / `66`; arm64 and x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 265 driver modules; catalog
  `list-models` returned 602 models including `Icom_IC-F50V_F60V_Capture`,
  `Radtel_RT-950_Pro`, and `Wouxun_KG-689E`; strict app/DMG signatures;
  Apple notarization and stapling; Gatekeeper acceptance of the DMG and
  mounted app; mounted-app launch smoke test; and matching local, server,
  and public SHA-256. Notarization submission:
  `a48065c5-5e65-488c-aa7a-0c19fe5c3755`.
- macOS `1.0.65` is live from source commit `8f56c3da` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It includes the
  DM-32UV shifted-insert extras fix, TK-270G one-based bank positions,
  current RT-950 Pro work, the approved RepeaterBook API relay, and
  cumulative driver, UI, and bridge compatibility changes. Verification:
  analyzer clean; 242 Flutter tests; 557 Python tests with two
  fixture-dependent skips; embedded version `1.0.65` / `65`; arm64 and
  x86_64 Python `3.13.15`; CHIRP
  `21e42e4518c167548af90ed7f9edf75e516c491a`; 265 driver modules; catalog
  `list-models` returned 602 models including `Icom_IC-F50V_F60V_Capture`,
  `Radtel_RT-950_Pro`, and `Wouxun_KG-689E`; strict app/DMG signatures;
  Apple notarization and stapling; Gatekeeper acceptance of the DMG and
  mounted app; mounted-app launch smoke test; and matching local, server,
  and public SHA-256. Notarization submission:
  `b9931c3b-064a-4b8b-b22d-8508e72bdf2f`.
- macOS `1.0.64` is live from source commit `2fc54348` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It carries the
  RT-950 Pro transmit/write correction, the approved RepeaterBook API relay,
  Icom IC-F50V/F60V capture support, KG-689E/699E fixes, and cumulative
  driver, UI, CSV, and bridge compatibility changes. Verification: analyzer
  clean; 242 Flutter tests; 550 Python tests with two fixture-dependent
  skips; embedded version `1.0.64` / `64`; arm64 and x86_64 Python `3.13.15`;
  CHIRP `21e42e4518c167548af90ed7f9edf75e516c491a`; 265 driver modules;
  catalog `list-models` returned 602 models including
  `Icom_IC-F50V_F60V_Capture`, `Radtel_RT-950_Pro`, and
  `Wouxun_KG-689E`; strict app/DMG signatures; Apple notarization and
  stapling; Gatekeeper acceptance of the DMG and mounted app; mounted-app
  launch smoke test; and matching local, server, and public SHA-256.
  Notarization submission:
  `dbd06c9d-66de-4d3f-a19b-5e2c1117dca5`.
- macOS `1.0.63` is live from source commit `847db298` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds RepeaterBook
  API search through the server relay, the read-only Icom IC-F50V/F60V
  capture profile, KG-689E/699E fixes, and the cumulative mapping,
  cross-mode, live-band, CSV, and bridge compatibility fixes. Verification:
  analyzer clean; 239 Flutter tests; 550 Python tests with two
  fixture-dependent skips; embedded version `1.0.63` / `63`; arm64 and
  x86_64 Python `3.13.15`; CHIRP `21e42e4518c167548af90ed7f9edf75e516c491a`;
  265 driver modules; catalog `list-models` returned 602 models including
  `Icom_IC-F50V_F60V_Capture`, `Wouxun_KG-689E`, and
  `Radtel_RT-950_Pro`; strict app/DMG signatures; Apple notarization and
  stapling; Gatekeeper acceptance of the DMG and mounted app; mounted-app
  launch smoke test; and matching local, server, and public SHA-256.
  Notarization submission:
  `baac68f6-92f7-4154-b680-3b3a6c57adc1`.
- Linux `1.0.64` is live from source commit `12c4633d`. It fixes blank cross
  modes, preserves radio settings that the current CHIRP build cannot load,
  restores live band switching, adds collapsible channel-summary metrics, and
  carries the latest CSV and bridge compatibility fixes. Verification:
  analyzer clean; 239 Flutter tests; 543 Python tests with two
  fixture-dependent skips; max glibc `2.18`; DEB, RPM, and Pacman metadata
  plus embedded version `1.0.64` / `64`; DEB and AppImage Xvfb launch tests
  passed on Ubuntu 20.04; the final AppImage launched under host Wayland and
  XWayland; package payloads omit GLVND/EGL/GLES loaders; all public downloads
  returned HTTP 200; and the Linux platform manifest reports `1.0.64`.
- Linux `1.0.63` is live from source commit `5c2c607f`. It adds the read-only
  Icom IC-F50V/F60V memory-capture profile, prevents fixed-zone metadata from
  blocking writes after channels move, and preserves radio-mapping
  memberships when channel locations are remapped. Verification: analyzer
  clean; 237 Flutter tests; 540 Python tests with two fixture-dependent skips;
  max glibc `2.18`; DEB, RPM, and Pacman metadata plus embedded version
  `1.0.63` / `63`; DEB and AppImage Xvfb launch tests passed on Ubuntu 20.04;
  the final AppImage launched under host Wayland and XWayland; all package
  payloads include the IC-F50V/F60V capture driver and omit GLVND/EGL/GLES
  loaders; all public downloads returned HTTP 200; and the Linux platform
  manifest reports `1.0.63`.
- Linux `1.0.62` is live from source commit `0d09b292`. It adds the
  CPS-derived Wouxun KG-689E/KG-699E driver, keeps Icom CI-V reads working
  when a channel has no tone set, fixes TK-270G editing and the 5RH Pro zone
  flag, handles UV-5RM Plus v2 replies, imports F4HWN module images, and
  carries the JSON-backed driver-work ledger. Verification: analyzer clean;
  235 Flutter tests; 536 Python tests with two fixture-dependent skips; max
  glibc `2.18`; DEB, RPM, and Pacman metadata plus embedded version `1.0.62`
  / `62`; DEB and AppImage Xvfb launch tests passed on Ubuntu 20.04; the final
  AppImage launched under host Wayland and XWayland; all package payloads
  include the KG-689E and Icom tone compatibility drivers and omit
  GLVND/EGL/GLES loaders; all public downloads returned HTTP 200; and the
  Linux platform manifest reports `1.0.62`.
- macOS `1.0.62` is live from source commit `89b4876e` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. Its application payload
  is runtime-identical to the final 1.0.62 release boundary `0d09b292`; that
  later commit changes only an Ubuntu ledger test. It carries the
  CPS-derived Wouxun KG-689E/KG-699E driver, Icom CI-V unset-tone handling,
  promoted FT-50 support, and the latest TK-270G and 5RH Pro fixes.
  Verification: analyzer clean; 235 Flutter tests; 536 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.62` / `62`;
  arm64 and x86_64 Python `3.13.15`; 264 CHIRP driver modules; catalog
  `list-models` returned 600 models including `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`; strict app/DMG
  signatures; Apple notarization and stapling; Gatekeeper acceptance; launch
  smoke test; and matching local, server, and public SHA-256. Notarization
  submission: `8fed5c04-70ea-4d77-b69c-b36b9340ea38`.
- Linux `1.0.61` is live from source commit `50f17c3c`. It restores the
  read-only zone display for fixed-zone radios such as the BF-F8HP-PRO,
  UV-17ProGPS family, GM-32, GM-30 Plus/Pro, RT-910, and BJ7800. Verification:
  analyzer clean; 235 Flutter tests; 508 Python tests with two
  fixture-dependent skips; max glibc `2.18`; DEB, RPM, and Pacman metadata
  plus embedded version `1.0.61` / `61`; DEB and AppImage Xvfb launch tests
  passed on Ubuntu 20.04; the final AppImage launched under host Wayland and
  XWayland; all package payloads include the fixed-zone compatibility driver
  and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200;
  and the Linux platform manifest reports `1.0.61`.
- macOS `1.0.61` is live from source commit `0e701b16` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the
  CPS-derived Wouxun KG-689E/KG-699E driver, tolerates unset Icom CI-V tones,
  promotes FT-50 to supported status after hardware confirmation, and includes
  the latest TK-270G, 5RH Pro zone-flag, reporter, and documentation updates.
  Verification: analyzer clean; 235 Flutter tests; 536 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.61` / `61`;
  arm64 and x86_64 Python `3.13.15`; 264 CHIRP driver modules; catalog
  `list-models` returned 600 models including `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`; strict app/DMG
  signatures; Apple notarization and stapling; Gatekeeper acceptance; launch
  smoke test; and matching local, server, and public SHA-256. Notarization
  submission: `6c290229-c679-465a-9d0b-0ab077ba1799`.
- Linux `1.0.60` is live from source commit `66383721`. It adds the
  OEM CPS-derived Alinco DR-735 driver, official manufacturer model names in
  radio lists, CSV encoding detection and channel select-all, UV-17ProGPS
  fractional CTCSS preservation, RT-950 decode/upload error fixes, the rebuilt
  RT-950 Pro driver with enabled writes, and the latest read-only safety and
  reporter-triage updates. Verification: analyzer clean; 235 Flutter tests;
  506 Python tests with two fixture-dependent skips; max glibc `2.18`; DEB,
  RPM, and Pacman metadata plus embedded version `1.0.60` / `60`; DEB and
  AppImage Xvfb launch tests passed on Ubuntu 20.04; the final AppImage
  launched under host Wayland and XWayland; all package payloads include the
  Alinco DR-735 and rebuilt RT-950 Pro drivers and omit GLVND/EGL/GLES
  loaders; all public downloads returned HTTP 200; and the Linux platform
  manifest reports `1.0.60`.
- macOS `1.0.60` is live from source commit `488564b4` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the rebuilt
  Alinco DR-735 driver, RT-950 Pro CPS 1.3.3 read/write support, fixed-zone
  display for radios such as the BF-F8HP-PRO, the RT-950 Pro web flow-control
  fix, official manufacturer model names, encoding-tolerant CSV import and
  channel select-all, fractional UV-17ProGPS CTCSS preservation, and the
  latest read-only safety and bug-report fixes.
  Verification: analyzer clean; 235 Flutter tests; 508 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.60` / `60`;
  arm64 and x86_64 Python `3.13.15`; 262 CHIRP driver modules; catalog
  `list-models` returned 598 models including `Baofeng_BF-F8HP-PRO`,
  `Alinco_DR735T`, and `Radtel_RT-950_Pro`; strict app/DMG signatures; Apple
  notarization and stapling; Gatekeeper acceptance; launch smoke test; and
  matching local, server, and public SHA-256. Notarization submission:
  `87136c3e-df9d-43bf-8a77-07a1246e1f66`.
- Linux `1.0.59` is live from source commit `0614c316`. It adds the
  experimental Kenwood TM-V71 clone driver, Kenwood live-write cache fixes,
  FT-50 channel clearing in both flag tables, FTM-7250 capability retention
  and stale-channel clearing fixes, and the latest installer/mobile package
  ignore rules. Verification: analyzer clean; 227 Flutter tests; 478 Python
  tests with two fixture-dependent skips; max glibc `2.18`; DEB, RPM, and
  Pacman metadata plus embedded version `1.0.59` / `59`; DEB and AppImage
  Xvfb launch tests passed on Ubuntu 20.04; the final AppImage launched under
  host Wayland and XWayland; all package payloads include the TM-V71 driver
  and omit GLVND/EGL/GLES loaders; all public downloads returned HTTP 200;
  and the Linux platform manifest reports `1.0.59`.
- macOS `1.0.59` is live from source commit `170c63f3` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the rebuilt
  Alinco DR-735 driver, Radtel RT-950 Pro CPS 1.3.3 read/write support,
  clearer read-only-driver messaging, official manufacturer model names,
  encoding-tolerant CSV import and channel select-all, fractional UV-17ProGPS
  CTCSS preservation, and the latest upload and bug-report fixes.
  Verification: analyzer clean; 235 Flutter tests; 506 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.59` / `59`;
  arm64 and x86_64 Python `3.13.15`; 261 CHIRP driver modules; catalog
  `list-models` returned 598 models including `Alinco_DR735T`,
  `Radtel_RT-950_Pro`, `Kenwood_TM-V71_CloneMode`, and `Yaesu_FT-50`; the
  website catalog and picker expose DR-735, TM-V71, and the rebuilt RT-950 Pro
  profile; strict app/DMG signatures; Apple notarization and stapling;
  Gatekeeper acceptance; launch smoke test; and matching local, server, and
  public SHA-256. Notarization submission:
  `31e8f183-0412-4c69-aab4-4d7cfbc39b77`.
- Linux `1.0.58` is live from source commit `dcccfd9b`. It adds the
  experimental Baofeng K67 Pro driver, TK-270G bank-sentinel normalization,
  late TK-350 identity retries, corrected Australian CB frequency references,
  the latest reported-driver fixes, and the private-reporter-data guard.
  Verification: analyzer clean; 226 Flutter tests; 456 Python tests with two
  fixture-dependent skips; max glibc `2.18`; package metadata and embedded
  version `1.0.58` / `58`; DEB and AppImage Xvfb launch tests passed on Ubuntu
  20.04; the final AppImage launched under host Wayland and XWayland; the
  package payloads omit GLVND/EGL/GLES loaders; all public downloads returned
  HTTP 200; and the Linux platform manifest reports `1.0.58`.
- macOS `1.0.58` is live from source commit `0ccff82c` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the read-only
  Kenwood TM-V71A/E clone driver, fixes Kenwood live-mode writes, clears
  FT-50 channels in both flag tables, preserves FTM7250 capabilities while
  clearing removed channels, and carries the current driver diagnostics.
  Verification: analyzer clean; 227 Flutter tests; 478 Python tests with two
  fixture-dependent skips; 66 bridge tests; embedded version `1.0.58` / `58`;
  arm64 and x86_64 Python `3.13.15`; 260 CHIRP driver modules; catalog
  `list-models` returned 598 models including `Kenwood_TM-V71_CloneMode` and
  `Yaesu_FT-50`; the website catalog and picker expose the read-only TM-V71
  profile; strict app/DMG signatures; Apple notarization and stapling;
  Gatekeeper acceptance; launch smoke test; and matching local, server, and
  public SHA-256. Notarization submission:
  `678ebc18-dd9a-442f-a351-a78e8507e2a1`.
- macOS `1.0.57` is live from source commit `1d94b15f` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It carries the
  TK-270G erased-bank-index upload normalization and the sanitized driver
  work ledger. Verification: analyzer clean; 226 Flutter tests; 456 Python
  tests with two fixture-dependent skips; embedded version `1.0.57` / `57`;
  arm64 and x86_64 Python `3.13.15`; 258 CHIRP driver modules; catalog
  `list-models` returned 597 radios; strict app/DMG signatures; Apple
  notarization and stapling; Gatekeeper acceptance; launch smoke test; and
  matching local, server, and public SHA-256. Notarization submission:
  `143a2885-b3ab-478b-a263-e5e02a0f5cea`.
- Linux `1.0.57` is live from current `origin/main`. It adds the
  OEM-verified Yaesu FT-50 serial framing override at 9600 8N2 and includes
  the latest macOS release-build ownership documentation. Verification:
  analyzer clean; 226 Flutter tests; 433 Python tests with two
  fixture-dependent skips; max glibc `2.18`; package metadata and embedded
  version `1.0.57` / `57`; DEB and AppImage Xvfb launch tests passed on Ubuntu
  20.04; the final AppImage launched under host Wayland and XWayland; all
  public downloads returned HTTP 200; and the Linux platform manifest reports
  `1.0.57`.
- macOS `1.0.56` is live from source commit `b037f65a`. It adds the
  OEM-verified Yaesu FT-50 serial framing override at 9600 8N2 and carries
  the KG-UV8D reserved-DCS compatibility work. Verification: embedded version
  `1.0.56` / `56`; bundled FT-50 override sets `SERIAL_STOPBITS = 2`; bundled
  bridge honors driver-level stop-bit overrides; focused FT-50 tests pass;
  strict app and DMG signatures verify inside the mounted image; live manifest
  reports macOS `1.0.56`; and local/server DMG SHA-256 both match
  `b2cae937143218eddcaea1896a7bec7e5a2d87a3429982eccde894326c3e08fe`.
  Physical FT-50 upload/read-back validation is still pending.
- Windows `1.0.70` is live from source commit `4fde327b`. It preserves the
  active radio zone when replacing the channel list from CSV, the library, or
  a repeater search, and allows repeated radio-settings writes so several
  identical radios can be programmed in a row. It also carries the cumulative
  1.0.69 drivers: the read-only AnyTone AT-D878UVII Plus, the AnyTone D578
  channel-bank sizing fix, the read-only Quansheng UV-K5 Robzyl RO-KO 512K
  profile, Baofeng 5RX/UV-S9X3 OEM power encoding, safe unknown Baofeng power
  values, the watchdog, tone handling, UV-5RM Plus handshake, and Android
  broken-pipe work. Verification: installer metadata `1.0.70.0` / `1.0.70`;
  release app `1.0.70+70` with an in-app version string of `1.0.70`; bundled
  Python `3.13.15`; no `__pycache__`/`.pyc` files; 272 CHIRP driver modules
  pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`; bridge `list-models`
  exit 0 with empty stderr and 604 models across 62 vendors; all four
  frequency-reference PDFs; matching local/server/public SHA-256
  `f6b86ac40af732f9e27a4fb6b8ce10e706e82d979e48eae5b525426626e89c5a`,
  size `51,073,329` bytes; public HTTP 200; and live manifest Windows
  `1.0.70`. `flutter analyze lib test` is clean. The full Flutter suite ran
  244 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 618 tests: 613 passed, 2 fixture-dependent
  tests skipped, and 3 known Windows temporary-file-lock helper errors. The
  installer remains unsigned. At verification time, macOS was `1.0.70` and
  Linux was `1.0.72`.
- Windows `1.0.69` is live from source commit `5db67c3b`. It adds the
  read-only AnyTone AT-D878UVII Plus driver, fixes AnyTone D578 channel-bank
  sizing, adds the read-only Quansheng UV-K5 Robzyl RO-KO 512K profile,
  encodes Baofeng 5RX/UV-S9X3 channel power as the CPS does, keeps unknown
  Baofeng power values readable without rewriting them, and carries the
  cumulative 1.0.68 watchdog, tone, UV-5RM Plus handshake, and Android
  broken-pipe work. Verification: installer metadata `1.0.69.0` / `1.0.69`;
  release app `1.0.69+69` with an in-app version string of `1.0.69`;
  bundled Python `3.13.15`; a clean runtime with no `__pycache__`/`.pyc`
  files and no `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 272
  CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`; bridge `list-models` exit 0
  with empty stderr and 604 models across 62 vendors including
  `AnyTone_AT-D878UVII_Plus`, `Baofeng_5RX`, and
  `Quansheng_UV-K5_RO-KO_512K`; all four frequency-reference PDFs; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.69`. `flutter analyze lib test` is clean. The full Flutter suite ran
  244 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 618 tests: 613 passed, 2 fixture-dependent
  tests skipped, and 3 known Windows temporary-file-lock helper errors. The
  installer remains unsigned. At verification time, macOS was `1.0.69` and
  Linux was `1.0.71`.
- Windows `1.0.68` is live from source commit `dcc91434`. It adds the
  stalled-write diagnostic watchdog, safe reads of unreadable DM-32UV and
  RT-950 tone values, the OEM-style UV-5RM Plus handshake retry, Android
  USB broken-pipe handling, and the cumulative 1.0.67 driver, UI, bridge,
  trace, printing, and write-progress work. Verification: installer
  metadata `1.0.68.0` / `1.0.68`; release app `1.0.68+68` with an in-app
  version string of `1.0.68`; bundled Python `3.13.15`; a clean runtime
  with no `__pycache__`/`.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 269 CHIRP driver
  modules pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`; bridge
  `list-models` exit 0 with empty stderr and 602 models across 62 vendors
  including `Baofeng_DM-32UV`, `Radtel_RT-950_Pro`,
  `Baofeng_UV-5RM_Plus`, `Baofeng_BF-F8HP`, and
  `Wouxun_KG-UV9D_Plus`; all four frequency-reference PDFs; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.68`. `flutter analyze lib test` is clean. The full Flutter suite ran
  244 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 605 tests: 600 passed, 2 fixture-dependent
  tests skipped, and 3 known Windows temporary-file-lock helper errors. The
  installer remains unsigned. At verification time, macOS was `1.0.68` and
  Linux was `1.0.70`.
- Windows `1.0.67` is live from source commit `8e03e24b`. It includes the
  cumulative driver, UI, bridge, trace, printing, and write-progress fixes
  after 1.0.66, including FTM-300DR and F4HWN 7.0, RT22, DM-32UV
  progress/cancel, UV-K60 Plus, RA87, UV-5R Mini, VX-170, TH-350, and
  no-step tuning work. Verification: installer metadata `1.0.67.0` /
  `1.0.67`; release app `1.0.67+67` with an in-app version string of
  `1.0.67`; bundled Python `3.13.15`; a clean runtime with no
  `__pycache__`/`.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 269 CHIRP driver
  modules pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`; bridge
  `list-models` exit 0 with empty stderr and 602 models across 62 vendors
  including `Retevis_RA87`, `Retevis_RT22`, `Baofeng_UV-5R_Mini`,
  `Yaesu_VX-170`, `Baofeng_DM-32UV`, `Radtel_RT-950_Pro`,
  `Wouxun_KG-689E`, and `Yaesu_FTM-300DR`; all four frequency-reference
  PDFs; bundled application launch smoke test succeeded; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.67`. `flutter analyze lib test` is clean. The full Flutter suite ran
  244 passing tests in the parallel run with the five known Windows-only
  sandbox/Help failures. The complete Python suite ran 597 tests: 592
  passed, 2 fixture-dependent tests skipped, and 3 known Windows
  temporary-file-lock helper errors. The installer remains unsigned. An
  initial build from the pre-version-bump `5dd9aa67` tree was replaced
  before recording because its in-app string read `1.0.69`; the superseded
  artifact is quarantined on the server. At verification time, macOS was
  `1.0.67` and Linux was `1.0.69`.
- Windows `1.0.66` is live from source commit `cd9ced58`. It integrates the
  DM-32UV channel and zone name NUL-termination fix, moved-channel extras
  preservation, TK-270G one-based bank positions, RT-950 Pro transmit-band
  warnings and Bluetooth read diagnostics with writes re-enabled after the
  receive-only guard, and Windows-checkout-safe driver ledger paths. It also
  carries the 1.0.65 IC-F50V/F60V, KG-689E, RepeaterBook, UI, and
  error-reporting work. Verification: installer metadata `1.0.66.0` /
  `1.0.66`; release app `1.0.66+66`; bundled Python `3.13.15`; a clean
  runtime with no `__pycache__`/`.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 265 CHIRP driver
  modules pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`; bridge
  `list-models` exit 0 with empty stderr and 602 models across 62 vendors
  including `Icom_IC-F50V_F60V`, `Icom_IC-F50V_F60V_Capture`,
  `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`, `Yaesu_FT-50`,
  `Radtel_RT-950_Pro`, and `Baofeng_DM-32UV`; all four
  frequency-reference PDFs; extracted payload launch succeeded; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.66`. `flutter analyze lib test` is clean. The full Flutter suite ran
  236 passing tests in the parallel run with the five known Windows-only
  sandbox/Help failures plus one diagnostic-log temp-lock failure that
  passed in isolation. The complete Python suite ran 560 tests: 555 passed,
  2 fixture-dependent tests skipped, and 3 known Windows temporary-file-lock
  helper errors. The installer remains unsigned. At verification time, macOS
  was `1.0.66` and Linux was `1.0.68`.
- Windows `1.0.65` is live from source commit `014df59b`. It integrates the
  approved RepeaterBook API relay, expands read-only Icom IC-F50V/F60V
  channel support alongside the capture profile, handles echoing programming
  cables on the Wouxun KG-689E, and carries the related UI and error-reporting
  fixes. Verification: installer metadata `1.0.65.0` / `1.0.65`; release app
  `1.0.65+65`; bundled Python `3.13.15`; a clean runtime with no
  `__pycache__`/`.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 265 CHIRP driver
  modules pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`; bridge
  `list-models` exit 0 with empty stderr and 602 models including
  `Icom_IC-F50V_F60V`, `Icom_IC-F50V_F60V_Capture`, `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`; all four
  frequency-reference PDFs; extracted payload launch succeeded; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.65`. `flutter analyze lib test` is clean. The full Flutter suite ran
  233 passing tests in the parallel run with the five known Windows-only
  sandbox/Help failures plus one diagnostic-log temp-lock failure that passed
  in isolation. The complete Python suite ran 550 tests: 544 passed, 2
  fixture-dependent tests skipped, 3 known Windows temporary-file-lock helper
  errors, and 1 Windows-only path-separator assertion in
  `driver_work_test.py`. The installer remains unsigned. At verification
  time, macOS was `1.0.65` and Linux was `1.0.67`.
- Windows `1.0.64` is live from source commit `83a592ae`. It integrates the
  approved RepeaterBook API relay, adds read-only Icom IC-F50V/F60V channel
  support alongside the capture profile, handles echoing programming cables
  on the Wouxun KG-689E, and removes the channel-library compatibility
  subtitle. It also carries the cumulative blank-cross-mode, unloadable-
  settings, live-band-switching, fixed-zone-write, and mapping-preservation
  fixes. Verification: installer metadata `1.0.64.0` / `1.0.64`; release app
  `1.0.64+64`; bundled Python `3.13.15`; a clean runtime with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 265 CHIRP driver
  modules; bridge `list-models` exit 0 with empty stderr and 602 models
  including `Icom_IC-F50V_F60V`, `Icom_IC-F50V_F60V_Capture`,
  `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`; all
  four frequency-reference PDFs; extracted payload launch succeeded;
  matching local/server/public SHA-256; public HTTP 200; and live manifest
  Windows `1.0.64`. `flutter analyze lib test` is clean. The full Flutter
  suite ran 234 passing tests with the five known Windows-only sandbox/Help
  failures. The complete Python suite ran 550 tests: 544 passed, 2
  fixture-dependent tests skipped, 3 known Windows temporary-file-lock helper
  errors, and 1 Windows-only path-separator assertion in
  `driver_work_test.py`. The installer remains unsigned. At verification
  time, macOS was `1.0.64` and Linux was `1.0.65`.
- Windows `1.0.63` is live from source commit `f550ae84`. It adds the
  read-only Icom IC-F50V/F60V memory-capture profile, keeps fixed-zone
  metadata from blocking writes after channels move, preserves radio-mapping
  memberships when locations are remapped, fixes blank cross modes, preserves
  radio settings the current CHIRP build cannot load, and restores live band
  switching. It also carries the KG-689E/KG-699E, Icom CI-V unset-tone,
  TK-270G, 5RH Pro, UV-5RM Plus v2, F4HWN module-image, and JSON ledger work
  from the 1.0.62 line. Verification: installer metadata `1.0.63.0` /
  `1.0.63`; release app `1.0.63+63`; bundled Python `3.13.15`; a clean
  runtime with no `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 265
  CHIRP driver modules; bridge `list-models` exit 0 with empty stderr and 601
  models including `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`,
  `Icom_IC-F50V_F60V_Capture`, and `Yaesu_FT-50`; all four
  frequency-reference PDFs; extracted payload launch succeeded; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.63`. `flutter analyze lib test` is clean. The full Flutter suite ran
  234 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 543 tests: 537 passed, 2 fixture-dependent
  tests skipped, 3 known Windows temporary-file-lock helper errors, and 1
  Windows-only path-separator assertion in `driver_work_test.py`. The
  installer remains unsigned. At verification time, macOS was `1.0.62` and
  Linux was `1.0.64`.
- Windows `1.0.62` is live from source commit `d9b31864`. It adds the
  CPS-derived Wouxun KG-689E/KG-699E driver, keeps Icom CI-V reads working
  when a channel has no tone set, fixes TK-270G editing and the 5RH Pro zone
  flag, handles UV-5RM Plus v2 replies, imports F4HWN module images, and
  carries the JSON-backed driver-work ledger. It also adds the read-only
  Icom IC-F50V/F60V memory-capture profile and prevents fixed-zone metadata
  from blocking writes after channels move. Verification: installer metadata
  `1.0.62.0` / `1.0.62`; release app `1.0.62+62`; bundled Python `3.13.15`;
  a clean runtime with no `okf`/`tree_sitter`/`tqdm`/`colorama`
  contamination; 265 CHIRP driver modules; bridge `list-models` exit 0 with
  empty stderr and 601 models including `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, `Icom_IC-F50V_F60V_Capture`, and
  `Yaesu_FT-50`; all four frequency-reference PDFs; extracted payload launch
  succeeded; matching local/server/public SHA-256; public HTTP 200; and live
  manifest Windows `1.0.62`. `flutter analyze lib test` is clean. The full
  Flutter suite ran 232 passing tests with the five known Windows-only
  sandbox/Help failures. The complete Python suite ran 540 tests: 534 passed,
  2 fixture-dependent tests skipped, 3 known Windows temporary-file-lock
  helper errors, and 1 Windows-only path-separator assertion in
  `driver_work_test.py`. The installer remains unsigned. At verification
  time, macOS was `1.0.62` and Linux was `1.0.64`.
- Windows `1.0.61` is live from source commit `0e701b16`. It adds the
  CPS-derived Wouxun KG-689E/KG-699E driver, tolerates unset Icom CI-V tones,
  promotes FT-50 to supported status after hardware confirmation, and includes
  the latest TK-270G, 5RH Pro zone-flag, reporter, and documentation updates.
  Verification: installer metadata `1.0.61.0` / `1.0.61`; release app
  `1.0.61+61`; bundled Python `3.13.15`; a clean runtime with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 264 CHIRP driver
  modules; bridge `list-models` exit 0 with empty stderr and 600 models
  including `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`, and
  `Yaesu_FT-50`; all four frequency-reference PDFs; extracted payload launch
  succeeded; matching local/server/public SHA-256; public HTTP 200; and live
  manifest Windows `1.0.61`. `flutter analyze lib test` is clean. The full
  Flutter suite ran 230 passing tests with the five known Windows-only
  sandbox/Help failures. The complete Python suite ran 536 tests: 530 passed,
  2 fixture-dependent tests skipped, 3 known Windows temporary-file-lock
  helper errors, and 1 Windows-only path-separator assertion in
  `driver_work_test.py` (expects `/events/`, receives a backslash path). The
  installer remains unsigned. At verification time, macOS was `1.0.61` and
  Linux was `1.0.62`.
- Windows `1.0.60` is live from source commit `488564b4`. It adds read-only
  zone display for fixed-zone radios including the BF-F8HP-PRO and carries
  the RT-950 Pro web flow-control fix plus the Alinco DR-735 rebuild, RT-950
  Pro CPS 1.3.3 read/write support, official manufacturer model names,
  encoding-tolerant CSV import, channel select-all, fractional UV-17ProGPS
  CTCSS preservation, read-only warnings, and bug-report fixes. Verification:
  installer metadata `1.0.60.0` / `1.0.60`; release app `1.0.60+60`; bundled
  Python `3.13.15`; a clean runtime with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 262 CHIRP driver
  modules; bridge `list-models` exit 0 with 598 models including
  `Baofeng_BF-F8HP-PRO`, `Alinco_DR735T`, and `Radtel_RT-950_Pro`; the
  BF-F8HP-PRO image reports ten read-only zones spanning channels 1-100,
  101-200, and onward; all four frequency-reference PDFs; extracted payload
  launch succeeded; matching local/server/public SHA-256; public HTTP 200;
  and live manifest Windows `1.0.60`. `flutter analyze lib test` is clean.
  The full Flutter suite ran 230 passing tests with the five known
  Windows-only sandbox/Help failures. The complete Python suite ran 508
  tests: 503 passed, 2 fixture-dependent tests skipped, and 3 Windows
  temporary-file-lock helper errors. The installer remains unsigned. At
  verification time, macOS was `1.0.60` and Linux was `1.0.60`.
- Windows `1.0.59` is live from source commit `170c63f3`. It adds the
  OEM-rebuilt Alinco DR-735 driver, RT-950 Pro writes from Radtel Pro CPS
  1.3.3, read-only warnings before writes, official manufacturer model names,
  common-encoding CSV imports with channel select-all, fractional CTCSS for
  the UV-17ProGPS family, RT97L analysis/fixes, and bug-report upload/decode
  fixes. Verification: installer metadata `1.0.59.0` / `1.0.59`; release app
  `1.0.59+59`; bundled Python `3.13.15`; a clean runtime with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 261 CHIRP driver
  modules; bridge `list-models` exit 0 with 598 models including
  `Alinco_DR735T`, `Radtel_RT-950_Pro`, `Wouxun_KG-UV8D`, `Yaesu_FT-50`,
  `Baofeng_K67_Pro_CPS_V1.1.2`, and `Kenwood_TM-V71`; all four
  frequency-reference PDFs; extracted payload launch succeeded; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.59`. `flutter analyze lib test` is clean. The full Flutter suite ran
  230 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 506 tests: 501 passed, 2 fixture-dependent
  tests skipped, and 3 Windows temporary-file-lock helper errors. The
  installer remains unsigned. At verification time, macOS was `1.0.59` and
  Linux was `1.0.60`.
- Windows `1.0.58` is live from source commit `0ccff82c`. It adds the
  Kenwood TM-V71 clone-mode driver, Kenwood live-write cache fixes, FT-50
  channel clearing in both flag tables, refreshed OKF bundles, and repository
  ignore rules for installer/mobile package files, while retaining the
  Baofeng K67 Pro, TK-270G, TK-350, FT-50, KG-UV8D, nicFW950, and GMRS work.
  Verification: installer metadata `1.0.58.0` / `1.0.58`; release app
  `1.0.58+58`; bundled Python `3.13.15`; a clean runtime with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 260 CHIRP driver
  modules; bridge `list-models` exit 0 with 598 models including
  `Wouxun_KG-UV8D`, `Yaesu_FT-50`, `Baofeng_K67_Pro_CPS_V1.1.2`,
  `Kenwood_TM-V71`, and `Kenwood_TM-V71_CloneMode`; the bundled FT-50
  override sets `SERIAL_STOPBITS = 2` and clears both flag tables; all four
  frequency-reference PDFs; matching local/server/public SHA-256; public HTTP
  200; and live manifest Windows `1.0.58`. Installer payload extraction
  confirmed the embedded runtime and files; the installer remains unsigned.
  `flutter analyze lib test` is clean. The full Flutter suite ran 222 passing
  tests with the five known Windows-only sandbox/Help failures. The full
  Python suite ran 478 tests: 473 passed, 2 fixture-dependent tests skipped,
  and 3 Windows temporary-file-lock helper errors.
- Windows `1.0.57` is live from source commit `1d94b15f`, the same 1.0.57
  source used by macOS. It adds the experimental Baofeng K67 Pro driver,
  TK-270G erased-bank-index upload normalization, late TK-350 identity
  retries, corrected Australian CB frequency references, the reported-driver
  fixes, and the private-reporter-data guard, while retaining the FT-50,
  KG-UV8D, nicFW950, and GMRS starter work. Verification: installer metadata
  `1.0.57.0` / `1.0.57`; release app `1.0.57+57`; bundled Python `3.13.15`;
  a clean runtime with no `okf`/`tree_sitter`/`tqdm`/`colorama`
  contamination; 258 CHIRP driver modules; bridge `list-models` exit 0 with
  597 models including `Wouxun_KG-UV8D`, `Yaesu_FT-50`, and
  `Baofeng_K67_Pro_CPS_V1.1.2`; the bundled FT-50 override sets
  `SERIAL_STOPBITS = 2`; all four frequency-reference PDFs; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.57`. Installer payload extraction confirmed the embedded runtime and
  files; the installer remains unsigned. `flutter analyze lib test` is clean.
  The full Flutter suite ran 221 passing tests with the five known
  Windows-only sandbox/Help failures. The full Python suite ran 456 tests:
  451 passed, 2 fixture-dependent tests skipped, and 3 Windows
  temporary-file-lock helper errors.
- Windows `1.0.56` is live from source commit `361da9e9`. It adds the
  OEM-verified Yaesu FT-50 serial framing override at 9600 8N2 and carries
  the KG-UV8D reserved-DCS, nicFW950 no-tone, and GMRS starter-bandwidth work.
  Verification: installer metadata `1.0.56.0` / `1.0.56`; release app
  `1.0.56+56`; bundled Python `3.13.15`; a clean runtime with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination; 256 CHIRP driver
  modules; bridge `list-models` exit 0 with 596 models including
  `Wouxun_KG-UV8D` and `Yaesu_FT-50`; the bundled FT-50 override sets
  `SERIAL_STOPBITS = 2`; all four frequency-reference PDFs; matching
  local/server/public SHA-256; public HTTP 200; and live manifest Windows
  `1.0.56`. A silent install to a temporary directory launched the bundled
  runtime, exited cleanly, and was removed. The installer remains unsigned.
  `flutter analyze lib test` is clean. The full Flutter suite ran 221 passing
  tests with the five known Windows-only sandbox/Help failures. The full
  Python suite ran 433 tests: 428 passed, 2 fixture-dependent tests skipped,
  and 3 Windows temporary-file-lock helper errors. At Windows release time,
  macOS and Linux were also at `1.0.56`.
- Linux `1.0.56` is live from current `origin/main`. It adds the
  KG-UV8D reserved-DCS compatibility override, treats nicFW950 all-ones
  subtones as no tone, corrects GMRS starter-channel bandwidths, and recovers
  from macOS CSV save permission errors. Verification: analyzer clean; 226
  Flutter tests; 432 Python tests with two fixture-dependent skips; max glibc
  `2.18`; package metadata and embedded version `1.0.56` / `56`; DEB and
  AppImage Xvfb launch tests passed on Ubuntu 20.04; the final AppImage
  launched under host Wayland and XWayland; all public downloads returned HTTP
  200; and the Linux platform manifest reports `1.0.56`.
- Linux `1.0.55` is live from the current `origin/main` plus the
  Ubuntu 20.04 release hardening. It fixes blank AppImages caused by mixing an
  old bundled GLVND loader with newer NVIDIA/Mesa drivers, clears vacated
  channel locations when removing empty slots, makes occupied channel moves
  use an explicit swap/overwrite decision, adds exact decimal and per-column
  filters, shows bank boundaries, supports searchable regions and coordinate
  searches independent of the selected region, expands frequency references,
  and explains the pending RepeaterBook API application. Build and release
  details are recorded below. Verification: analyzer clean; 226 Flutter tests;
  426 Python tests with two fixture-dependent skips; max glibc `2.18`;
  package metadata and embedded version `1.0.55` / `55`; DEB and AppImage Xvfb
  launch tests passed on Ubuntu 20.04; and the final AppImage launched under
  host Wayland and XWayland. All four public downloads returned HTTP 200 and
  the Linux platform manifest reports `1.0.55`. Craig received the 1.0.55
  AppImage and Pacman retest links in Sent UID 443.
- Windows `1.0.54` is live from source commit `c55530b9`. It adds the
  read-only experimental KSUN UV-K60 Plus driver, the Baofeng UV-29 Pro
  compatibility profile, Yaesu FT-50 odd-split decoding, and upload
  hardening. Verification: installer metadata `1.0.54.0` / `1.0.54`; release
  app `1.0.54+54`; bundled Python `3.13.15`; a clean cached runtime with no
  `okf`/`tree_sitter` contamination; 255 CHIRP driver modules; bridge
  `list-models` exit 0 with 596 models including `KSUN_UV-K60-Plus`,
  `Baofeng_UV-29Pro`, and `Yaesu_FT-50`; matching local/server/public
  SHA-256; public HTTP 200; and live manifest Windows `1.0.54`. The installer
  remains unsigned. `flutter analyze lib test` is clean. The full Flutter
  suite ran 213 passing tests with the five known Windows-only
  sandbox/Help failures. The full Python suite ran 423 tests: 418 passed,
  2 fixture-dependent tests skipped, and 3 Windows temporary-file-lock
  helper errors.
- macOS `1.0.54` is live from source commit `c55530b9` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the Baofeng
  UV-29 Pro alias, Yaesu FT-50 odd-split decoding, the read-only KSUN
  UV-K60 Plus driver, TD-H8 upload safeguards, and the latest 596-model
  bundled CHIRP catalog. Verification: 423 Python tests with two
  fixture-dependent skips, 218 Flutter tests, a clean analyzer, strict app
  codesigning, Apple notarization and stapling, mounted-DMG inspection,
  Gatekeeper, launch smoke test, and matching local/server/public SHA-256 all
  passed.
- Update checks now request only their own platform manifest with
  `/api/releases/latest?platform=<windows|macos|linux>`. The server returns
  one `{platform, version, download_url, release_url}` object, and there is no
  shared top-level desktop version. The website endpoint is deployed; the
  platform-query client change awaits the next desktop builds.
- The Kenwood TK-350/KPG-23D and TK-359/KPG-32D submissions from forum
  topic 39 were analyzed on 2026-11-13. NewChirp now has read-only
  experimental entries using the supplied OEM CPS files and sample data.
  The drivers retain the complete image and decode 16-byte channel
  records with RX/TX frequency and four-character names. Transport evidence
  is documented in `docs/KPG23_PROTOCOL.md`; uploads remain disabled.
  Verification: the focused driver suite passes, all 408 Python tests pass
  with two fixture-dependent skips, all 84 standard Web Programmer tests,
  16 experimental Web Programmer tests, and 9 RepeaterBook tests pass, and
  the production website build is clean. The site is live as
  `index-fwCJsaXw.js` with 654 selectable profiles. Replies are archived in
  Sent UIDs 414 and 415. Physical reads on both models are the next
  milestone.
- The About & licenses screen now explains that NewChirp develops drivers
  for radios with missing or broken upstream CHIRP support, releases those
  drivers under GPLv3-or-later, and makes them available for incorporation
  into upstream CHIRP subject to maintainer review and acceptance.
  Verification: the focused About test passes, all 215 Flutter tests pass,
  and `flutter analyze` is clean.
- Kenwood KPG-76D 1.00 was statically reverse engineered for the TK-863G
  upload from file-drop IDs 3 and 4 (`w8one`, account 586). The supplied
  CPS-read DAT maps to a 0x8000-byte image after a 0x70-byte DAT wrapper and
  contains 128 32-byte channel records at image offset 0x02F0. The new
  `drivers/newchirp_kenwood_tk863g.py` implements the OEM 9600 8N2
  `PROGRAM`/`M0863`/`NRK`/`0x7C`/256-byte-`R` read transport, fragmented
  reads, fill blocks, checksums, retries, model checks, and read-only decode
  for frequency, offset, name, bandwidth, CTCSS, DTCS, and cross tones.
  Protocol evidence is in `docs/KPG76D_PROTOCOL.md`. Uploads remain disabled
  pending a physical read and controlled write/read-back. Verification: five
  focused TK-863G tests pass, including all 128 blocks fragmented into
  three-byte reads and checksum recovery; all 404 Python tests pass with two
  fixture-dependent skips; all 215 Flutter tests pass; and `flutter analyze`
  is clean. The uploader received the driver status and physical-read test
  request at `[redacted-email]`; the verified copy is in `Sent` UID 401.
  The website now lists `TK-863G (experimental)` in both the Kenwood catalog
  and **New Experimental Radio Support**, and exposes a read-only
  `kenwood-tk863g` Web Programmer profile. Website source `be979f0` is live
  as `index-CbTrONP8.js`; the source inventory now has 652 selectable
  profiles.
- The 2026-11-13 mailbox triage handled eleven actionable messages. Replies
  were sent and verified in `Sent` UIDs 402-412, and all source messages were
  marked
  `\Seen`. RepeaterBook fixed its form; the Centralized backend
  application for NewChirp was submitted under account `WQWR692` as request
  `#295`, and Garrett received the request-ID follow-up in Sent UID 404.
  Evidence now requested from reporters: the FT-50 `.img` (UID 605),
  controlled pre/post DM-32UV images and settings screenshots (610), exact
  GM-32 label/OEM-CPS result (611), UV-5R model/cable/read result (607), and
  GS-5B 1.XX label/CPS version/OEM read result (603). Additional connection
  failures were answered with port/model/cable checks: UV-5R UID 613 and
  DM-32UV UID 614. UV-5RM Plus UID 616 was directed to use a USB-C data cable
  and select the matching v1/v2 entry after confirming firmware. The UID 613
  recipient did not exist; Gmail's non-delivery notice was handled as UID
  615. Mark received the TK-270G follow-up: Channel
  24 is NOAA 162.550 MHz in bank 1; the current source normalizes that
  unprogrammed bank-index sentinel and needs a next-build physical
  write/read-back. Mike was directed to reinstall the full Windows package
  because the bundled Python runtime was missing (609). The Inbox returned to
  zero unread.
- The latest 2026-11-12 mailbox triage handled 20 unread threads. Eighteen
  tailored report replies were sent and verified in `Sent` as UIDs 383-400,
  and every source report was marked `\Seen`. Two account notices and three
  Microsoft delivery bounces were also marked read; the inbox returned to
  zero unread. Three replies did not reach recipients because Outlook blocks
  the NewChirp server IP: `[redacted-email]`, `[redacted-email]`,
  and `[redacted-email]`.
- New radio or firmware evidence requested from reporters: Radioddity DB40-G
  (UID 540), Retevis RT86S (544), Baofeng DM-32UV firmware `DM32.NRF.01.049`
  (546), Baofeng 5RM firmware 05 (547), and Wouxun KG-UV980P (578). The next
  step for each is the exact label, OEM CPS version/archive, and proof that
  the OEM CPS can read the same radio/cable before deriving or extending a
  driver.
- High-priority follow-ups from the same triage are the TK-270G bank-index
  sentinel on channel 24 (UID 592) and the GS-5B 1.XX CPS handshake variant
  (583). Reporters were told not to write until those images and OEM
  comparisons are available. The nicFW950 RT-950 Pro invalid channel-map
  value 37777 (UIDs 585 and 684) was traced to the `0xFFFF` no-tone sentinel
  and corrected in source on 2026-11-15; focused tests cover the decode.
- The A9305B power report was traced through the official CPS instead of
  waiting for another read. Channel byte 12 stores power in bits 6-7 and
  wide/narrow in bits 4-5; the driver had those fields reversed. Zoran's CPS
  UI and `.icf` agree on every reported row from channels 6-22, and the
  corrected driver decodes that table exactly. The focused A9305B suite now
  covers the OEM table and the write-side masks. Writes remain restricted by
  the existing model-marker policy. Verification: 14 focused A9305B tests,
  399 Python tests with two fixture-dependent skips, 213 Flutter tests, and a
  clean `flutter analyze`.
- A direct FTM-7250D/VX-7R report exposed a reversed Low/Mid/High power write
  mapping in the pinned CHIRP driver. `drivers/newchirp_ftm7250.py` now writes
  the stored codes in the same order the driver decodes them, with an image
  round-trip test. The same pass explicitly clears radio locations removed by
  a replacement channel library, hides transmit power for TX-off channels,
  and opens Save As in the imported CSV directory. Physical power-level
  validation on the reporter's radio remains pending.
- The next FTM-7250D report showed that power controls still disappeared after
  opening a CSV and that removed channels still survived programming. The CSV
  replacement path now retains the selected radio capabilities, and full-image
  uploads clear every in-range location missing from the active library rather
  than depending on an incomplete removal history.
- The Help menu now offers **Report a problem…** at any time. It opens the
  existing diagnostic report form even when the current page has no error;
  the form was relabeled from error report to bug report.
- Windows window restoration now detects mixed display scale factors and
  centers the saved window on the primary work area instead of reapplying
  coordinates saved under another monitor's DPI basis. Matching-scale layouts
  retain their saved position; off-screen and oversized bounds are centered
  and clamped. Focused tests cover mixed 4K/1080p-style scaling, valid
  secondary-display restoration, and off-screen recovery.
- TSQL channels now expose their shared CTCSS tone consistently. The channel
  table shows the same effective tone in both TX and RX columns, and the editor
  uses one **CTCSS tone** field because CHIRP applies the receive-tone value in
  both directions for TSQL. Cross modes still show independent TX/RX fields.
- A 2026-11-08 RT-860 report completed two physical reads and decoded 311
  channels on macOS through a cable that had just read a UV-5R Mini. The report
  included no saved image, trace, or OEM-CPS comparison, and RT-860 writes
  remain disabled.
- A 2026-11-09 UV-17ProGPS follow-up reported that an upload erased all tones.
  This remains unresolved and safety-sensitive. Ask for the NewChirp
  version/build, pre-write image, source of the channel data, post-write image,
  and affected channel/tone expectations before any further write.
- Radtel RT-950 and RT-950 Pro now have separate NewChirp models. The base
  RT-950 driver is unchanged. Christophe Marcant supplied a MIT-licensed
  community RT-950 Pro CHIRP driver that confirms the Pro's larger CPS map
  and 259-block read: channels, VFO, function, DTMF, modulation, and
  `0x54/0x55` APRS data. `drivers/newchirp_rt950pro.py` uses the shared
  `PROGRAMBT9000U` transport, a three-second initial ACK window, and all Pro
  blocks. It remains read-only until Christophe completes a physical read.
  Evidence is in `docs/RT950PRO_PROTOCOL.md`. Verification: 5 focused Pro
  transport tests pass.
- NewChirp now has a built-in Marine VHF frequency template under **New →
  Marine VHF template**. It offers a nationwide US plan based on FCC 47 CFR
  80.371(c) and 80.373(f) plus NOAA weather channels, and an ITU Appendix 18
  international plan. Templates are selected by regulatory plan rather than
  ZIP code. Receive-only is the default; ship transmit requires explicit
  opt-in, while DSC, AIS, weather, and government-only channels remain
  transmit-disabled. CHIRP's marine stock CSVs are not used. Evidence and
  safety rules are in `docs/MARINE_VHF_PLANS.md`. Verification: all 205
  Flutter tests pass and `flutter analyze` is clean.
- Desktop bug reports now include a dedicated radio-firmware field when
  available. NewChirp reads firmware from CHIRP image/driver metadata for
  supported models and decodes the UV-K5 hello frame directly, so failed
  handshakes can still report identities such as `2.01.39` before a radio
  image exists. The website bug-report API accepts, sanitizes, and displays
  the field in report email. Verification: all 381 Python tests pass with 2
  fixture-dependent skips; all 197 Flutter tests pass; `flutter analyze` is
  clean; the website production build and complete Web Programmer/RepeaterBook
  suites pass. Website commit `cb74792` is deployed; the live bundle
  `index-qGNixYAS.js` contains the optional firmware field. The pre-deploy
  source backup is
  `/root/newchirp-firmware-report-before-cb74792/site-sources.tgz`.
- The FT-991A forum request led to a NewChirp-owned experimental live CAT
  driver in `drivers/newchirp_yaesu_ft991a.py`. Yaesu's CAT reference,
  Gil Kloepfer's public FT-991A NVRAM map and SPR/SPW pseudocode, and a public
  RT Systems exchange capture establish the `0670` identity, 117-channel
  bitmap, 96-byte records, and read/modify/write transport. NewChirp exposes
  frequency, name, shift, mode, CTCSS, and DCS while preserving unknown channel
  bytes. RT Systems ADMS-991A itself is a paid serial-gated download and was
  not obtained. Protocol evidence is in
  `docs/YAESU_FT991A_PROTOCOL.md`; physical validation remains pending.
  Verification: 7 focused FT-991A tests pass, all 388 Python tests pass with
  2 fixture-dependent skips, all 197 Flutter tests pass, `flutter analyze` is
  clean, and the website build plus Web Programmer/RepeaterBook suites pass.
- The 2026-11-08 RT-950 DTCS report was a shared-versus-split tone
  presentation bug, not a memory decode failure. For ordinary `DTCS` mode,
  CHIRP uses one code for transmit and receive; the separate receive code is
  meaningful only for `DTCS -> DTCS` cross mode. The channel table and detail
  editor now show one `DTCS code` field for ordinary DTCS and retain separate
  transmit/receive fields for cross tone. The RT-950 remains read-only.
  Verification: all 197 Flutter tests pass and `flutter analyze` is clean.
- A Windows 1.0.48 DM-32UV report completed the radio read but lost the
  bundled `scripts/chirp_bridge.py` asset when loading write instructions
  three minutes later. `RadioBridge` now caches bundled helper bytes after the
  first successful load and reports an actionable reinstall message if the
  asset is genuinely absent. Verification: 2 focused asset tests pass and the
  complete Flutter suite now passes 199 tests with a clean analyzer.
- macOS `1.0.50` is live from source commit `23931970` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It includes the current
  TS-2000 timing, FTM-7250D power, mixed-DPI restoration, TSQL presentation,
  A9305B power/bandwidth, and Linux module diagnostics updates.
- macOS `1.0.49` is live from source commit `d4b20d0a` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the built-in
  US/International Marine VHF templates, independent RT-950 model selection,
  the separate read-only RT-950 Pro driver, and the channel validation and
  radio-helper reliability fixes.
- macOS `1.0.48` is live from source commit `11053cfd` as a universal, signed,
  notarized, stapled, Gatekeeper-accepted DMG. It adds firmware identities to
  desktop bug reports, including direct decoding of UV-K5 hello frames.
- Windows `1.0.49` and Linux `1.0.50` are live from their native release
  sessions.
- The 2026-11-08 BF-V12D password failure led to a full REA of Baofeng
  BF_Series CPS 1.5.1. The CPS is an Electron application; its renderer and
  main process prove the exact fixed unlock sequence,
  `02ucbfpwd`/`10c5ea35`/encoded model token, P3107 magic, eight-byte clone
  commands, retries, and sparse memory map. The official ZIP is retained at
  `/Users/rlopez/Downloads/Baofeng_BF_Series_CPS_1.5.1.zip`, SHA-256
  `c07f3664c7bf87721376042c53a06b29055fec0c2ccc3d6192c8d005b4582f72`.
  `drivers/newchirp_baofeng_bfv12d.py` now owns that read-only unlock
  transport and fails closed on the newer V1.19/V2.02 password variants,
  which the official CPS also cannot read. Evidence is in
  `docs/BAOFENG_BF_V12D_PROTOCOL.md`. Verification: 6 focused BF-V12D tests,
  all 379 Python tests, `flutter analyze`, and all 196 Flutter tests pass.
  Desktop commit `0da89ffb` is pushed. Website commits `cb44b2f` and
  `e007427` add and deploy `BF-V12D (experimental)`; live asset
  `index-1anbK7Q1.js` was verified. Neil received the CPS findings, K-type
  cable requirement, and newer-firmware limitation in a threaded follow-up;
  the reply is verified in `Sent`.
- The 2026-11-08 TD-H8 G4 write blocker led to the official ODMaster Android
  `2.6.4` package and its public protocol service. ODMaster exposes distinct
  Normal, Ham, and GMRS G4 profiles (`TDH84GEN`, `TDH84GEH`, and
  `TDH84GEG`) with a common 170-page write map. NewChirp now enables
  experimental writes only for those verified 32-byte pages, validates the
  image and regional identity before transmitting, checks every ACK, and
  preserves all unlisted bytes. Protocol evidence is in
  `docs/TIDRADIO_TD-H8_G4_PROTOCOL.md`. The reporter's 1.0.46 trace proves a
  complete 151-channel read but not a write; controlled write/read-back
  validation remains the next milestone. Verification: 6 focused G4 tests
  pass, all 373 discovered Python tests pass with 2 fixture-dependent skips,
  `flutter analyze` is clean, and all 196 Flutter tests pass. Desktop commit
  `c433bd1e` is pushed. The reporter received the controlled-test procedure
  in `Sent`, and source email UID 502 is verified `\Seen`. Website commits
  `301dc7e` and `d754956` add and deploy the three TD-H8 experimental catalog
  entries; live asset `index-DFclwBXd.js` was verified. A second threaded
  follow-up with the live radio-list link and next-test instructions is
  verified in `Sent`.
- The 2026-11-07 GA-510 follow-up (email UID 497) showed stock CHIRP
  succeeded on the same COM4 radio and cable while both NewChirp GA-510
  entries failed at the first five-byte serial exchange. The official
  newer-hardware `GA-510 CPS v1.00.36` and original 2020 CPS were downloaded.
  Static REA of the native v1.00.36 CPS recovered `PSEARCH`, `PASSSTA`,
  `SYSINFO`, `DMR1702`, the second identity handshake, explicit memory unlock,
  three memory-info queries, descriptor-mapped 4 KiB pages, and 64-byte
  addressed reads/writes. `drivers/newchirp_ga510_v2.py` now owns that
  transport, replaces the bundled V2 entry, and makes the generic GA-510
  selector probe V2 before falling back to the legacy 9,600-baud protocol.
  Desktop commit `87587bd7` is pushed. Website commit `6a60abb` adds
  `GA-510 V2 (experimental)` to the catalog and the New Experimental Radio
  Support section; live asset `index-CPA29zpe.js` was verified.
  Protocol evidence is in `docs/GA510_V2_PROTOCOL.md`. The official CPS ZIPs
  and manual are retained in `/Users/rlopez/Downloads/`. Physical validation
  is still pending; the next reporter test must begin with an OEM CPS backup
  and a read-only image comparison. Don Huey received the threaded diagnosis
  and test plan in `Sent` UID 322; source email UID 497 is verified `\Seen`.
- Verification for the GA-510 V2 transport: focused CPS replay tests pass
  5/5; the complete Python suite passes 357 tests with 2 fixture-dependent
  skips; `flutter analyze` is clean; and all 195 Flutter tests pass.
- The 2026-11-07 Radioddity X1 Pro GMRS request led to download and static
  REA of the official 2026-07-15 firmware/CPS package. The managed CPS shows
  a `02PROGRAM` / `SMP558` handshake, settings read at `0xE000`, 30 fixed
  16-byte channel pages beginning at `0x0000`, and 16-byte addressed writes.
  The new experimental driver in `drivers/newchirp_x1pro.py` implements the
  recovered read/write state machine and field map. The matching browser
  profile is in `/Volumes/RICKEXT/web/newchirpweb/lib/radioddity-x1pro-web.ts`;
  it supports experimental read/write and independent TX/RX CTCSS/DCS editing.
  Website commit `068f655` adds the experimental catalog entry and raises the
  browser inventory to 651 selectable profiles. The live site now serves
  `index-D0eCIYT3.js`, which contains both `X1 Pro (experimental)` and the
  `radioddity-x1-pro` Web Programmer profile; website deployment record
  `cdfc6b6` includes the rollback paths.
  The ZIP is retained at
  `/Users/rlopez/Downloads/2026-07-15_Radioddity_X1_PRO_Firmware_Update_with_CPS.zip`;
  full evidence is in `docs/X1PRO_PROTOCOL.md`. Physical read/write/read-back
  validation is still pending. Verification: 10 focused X1 Pro tests pass;
  all 352 Python tests pass with 2 fixture-dependent skips;
  `flutter analyze` is clean; all 195 Flutter tests pass; the website build
  and complete Web Programmer suite pass. Dustin Souers received the threaded
  test instructions in `Sent` UID 321; source email UID 492 is verified
  `\Seen`.
- Session saved on 2026-11-07 after all `1.0.45` platform release records
  landed. After this handoff commit is pushed, repository `main` should be
  clean and synced. Immediate follow-ups are normal unread-email triage and
  any physical RA89/TK-270G read/write validation from reporters.
- Repeater search now persists the directory, country, region, service, sort
  order, text query, latitude, longitude, radius, open/FM filters, and map
  mode. Changes are saved after a short debounce and again before searching,
  and the stored defaults remain backward compatible with version-1 files.
  Commit `a4533d11`. Verification: the complete Flutter suite passed 189
  tests, the focused persistence/dialog tests passed, and `flutter analyze`
  is clean.
- The 2026-11-07 Radioddity DB25-G report led to the official
  `Radioddity_DB25_G_GMRS_CPS_20250903.zip` download and static REA of
  `DB25_G_GMRS_CPS.exe`. The OEM CPS shows 9600 8N1 binary MSComm framing,
  the eight-byte `55 20 16 08 01 FF DC 02` programming request, OEM handshake
  retries, 69-byte block replies, and 16-byte `X` writes. The new
  `drivers/newchirp_db25g.py` uses the traced retry/framing behavior, writes
  the OEM `0x3100` upload range, and inherits the pinned DB25-G memory decode.
  The CPS archive is retained at
  `/Users/rlopez/Downloads/Radioddity_DB25_G_GMRS_CPS_20250903.zip`;
  protocol evidence is in `docs/DB25G_PROTOCOL.md`. Website commit `a70df5c`
  marks DB25-G as experimental and is live. The reporter reply is in `Sent`
  as UID 319; source UID 489 is verified `\Seen`. Desktop commit `d8191436`.
- Tony G4WIF's follow-up on the 2026-11-07 IC-E90 report shows the radio
  stayed on `CLONE` during the first failed writes, then accepted writes and
  displayed `CL IN` after a full reset and a successful CHIRP Next write.
  NewChirp 1.0.45 subsequently read and wrote the cleaned radio successfully.
  This rules out the previous assumption that the CS-T90A stream should be
  inherited unchanged. `drivers/newchirp_icx90.py` now owns the transport,
  retries identity four times, handles cable echo, waits after clone-in,
  checksums every block, writes all 362 blocks explicitly, and requires
  completion status `E6 00`. The CS-T90A CPS archive is retained at
  `/Users/rlopez/Downloads/CS-T90A-251201-001044.ZIP`; protocol evidence is in
  `docs/ICX90_PROTOCOL.md`.
- The cross-platform `1.0.45` release is live. Windows and Linux artifacts are
  from source commit `4ca2a6f9` and include the Retevis RA89 driver plus the
  safe TK-270G driver. macOS is from source commit `4ca2a6f9` and is fully
  recorded below. All three platform release records are verified by their
  native builders.
- The 2026-11-07 Retevis RA89 report UID 485 failed at the inherited CHIRP
  driver's 10-byte TYT handshake. The official RA89 CPS V1.08 was downloaded,
  statically reverse engineered, and documented in
  `docs/RA89_PROTOCOL.md`. The new `NewChirpRA89Radio` driver is committed as
  `ba9adab1`: it asserts 57,600-baud DTR/RTS, waits 500 ms, uses the OEM UV99
  session and optional programming-code stage, accumulates fragmented exact
  reads, reads/writes 32-byte addressed blocks, and skips
  `0x1680-0x193F` on writes. It implements 200 channels, names, tones, power,
  bandwidth, skip, startup text, core settings, side keys, and work modes.
  Physical read/write validation is still pending. The reply is in `Sent` as
  UID 311; source UID 485 is verified `\Seen`.
- RA89 verification: focused driver tests passed 8/8; the complete Python
  suite passed 321 tests with 2 fixture-dependent skips; `flutter analyze` is
  clean; and all 188 Flutter tests passed.
- Website commit `58c6d81` adds RA89 to New Experimental Radio Support. The
  prebuilt site was deployed from that commit after comparing the live source
  hashes with the prior source; the live bundle contains
  `RA89 (experimental)`. The pre-deploy source/dist backup is
  `/root/newchirp-before-ra89-20261107053812`.
- The 2026-11-06 UV-5RH Pro report on 1.0.43 still used the legacy
  `Baofeng_UV-5RH` entry. Official 5RH PRO CPS V1.17 uses an `A` announce,
  a seeded `PROGRAM` handshake, password and `INFORMATION` stages, then
  encrypted 4,100-byte clone blocks. The experimental
  `Baofeng_UV-5RH_Pro`, `Baofeng_5RH_Pro`, `Baofeng_UV-5RH_Plus`, and
  `Baofeng_UV-5RM_Plus_v2` entries now use that protocol. The public CHIRP
  contributor reports hardware validation on firmware v2_0_09; NewChirp
  physical validation is still pending.
- The 2026-11-06 Kenwood TK-7160K report downloaded the complete radio image
  but failed while decoding its dynamic zone subdevice because
  `TKx160Zone` has no external metadata owner. NewChirp now skips metadata
  augmentation when neither the subdevice nor its parent owns a metadata
  store. The upstream `Kenwood_TK-7160K.img` fixture covers the decode path.
  This radio uses upstream CHIRP `tk8160.py`; no NewChirp CPS reverse
  engineering is recorded.
- The 2026-11-06 BF-F8HP Pro timeout guidance now names the selected COM port
  and asks the reporter to compare against Baofeng CPS instead of repeatedly
  directing the user to the stale COM4 example.
- UID 464 reported that `Quansheng_UV-K1` rejected an `F4HWN v6.3.0`
  handshake on Linux. The current UV-K1 profile supports only stock 7.03.x and
  the official Quansheng CPS is also stock-only. NewChirp now routes a
  manually selected UV-K1 to an experimental F4HWN 6.3 profile with the
  firmware's 1,024-channel `0xB190` memory map, 128-byte transfers, and a
  write ceiling of `0xA178` so calibration is preserved. Offline protocol
  coverage uses the reporter's exact hello frame. Physical read/write and
  read-back validation are still pending. The reply to [redacted-email] is
  in `Sent` as UID 296, and the original UID 464 is verified `\Seen`.
- Verification for the F4HWN 6.3 profile: the complete Python suite ran 278
  tests with 2 fixture-dependent skips, `flutter analyze` is clean, and all
  186 Flutter tests pass.
- After UID 464, 11 matching reports remain unread because they require
  Windows or Linux diagnosis: UIDs 446, 447, 450, 451, 452, 455, 456, 457,
  461, 462, and 463.
- The 2026-11-06 email triage found 16 unread bug-report messages. UID 448
  (macOS DM-32UV zone capacity) received an explanation of the radio's
  64-members-per-zone limit. UIDs 459 and 460 (Quansheng TK11) exposed a
  shared bridge bug in which JSON string values were applied directly to
  numeric `RadioSettingValueList` extras; commit `d5a6f1b5` restores the
  driver's native option value before upload. The fix will be in the next
  build. Replies for UIDs 448 and 460 were verified in `Sent`, and source
  UIDs 448, 459 (duplicate report), and 460 were verified `\Seen`.
- Verification for `d5a6f1b5`: the complete Python suite ran 268 tests with
  2 fixture-dependent skips, `flutter analyze` is clean, and all 186 Flutter
  tests pass from a native-path worktree. The standalone formatter still
  reports the same two pre-existing files it would rewrite:
  `lib/models/repeater_counties.dart` and
  `lib/services/window_state_store.dart`.
- Follow-up UX fix `da1a744c` replaces the raw DM-32UV full-zone exception
  with the radio's actual capacity and recovery steps, and stops zone display
  names at an embedded NUL terminator. Regression tests cover a 65th zone
  membership and the malformed stored name. The complete Python suite now
  runs 270 tests with 2 fixture-dependent skips; all 186 Flutter tests and
  `flutter analyze` pass.
- Scott's 2026-11-05 GM-21 1.0.40 report showed the GM-5RH identification
  string succeeding but the UV-17Pro GPS follow-up magic being sent next, so
  the first clone read returned eight bytes instead of 68. The compatibility
  path now pairs each identification string with its own `F`/`M`/`SEND`
  sequence. Physical retest through the GM-21 catalog entry is pending.
- The 2026-11-05 A9305B follow-up showed NewChirp 1.0.38 rejecting a complete
  494-byte read response because its `F3` trailing checksum did not match the
  driver's write-side `A2` calculation. The official CPS read path strips that
  field without validating it; source now mirrors that policy while retaining
  marker, address, length, payload, and terminator checks. A physical read and
  comparison with the CPS export are still required.
- Verification for the A9305B correction: the focused driver suite ran 11
  tests, all 254 discovered Python tests passed with 2 fixture-dependent
  skips, `flutter analyze` is clean, and all 186 Flutter tests pass. The
  installed formatter still reports two pre-existing files it would rewrite:
  `lib/models/repeater_counties.dart` and
  `lib/services/window_state_store.dart`.
- The 2026-11-05 email triage handled 24 unread messages. Nineteen replies
  were sent and verified in `Sent`; five already-handled/no-action messages
  were marked `\Seen`. Three immediate delivery bounces were marked `\Seen`:
  two Microsoft-family recipients rejected the server IP as blocklisted, and
  one Gmail recipient address did not exist. The inbox returned to zero unread.
- Triage added and pushed `f66e6ecc`, accepting the TIDRADIO TD-H8 Gen 4
  generic identity `TDH84GEN` as read-only. Writes remain disabled pending
  physical write/read-back validation.
- The cross-platform `1.0.44` release is superseded. macOS is from source commit
  `9929f997`; the Linux artifacts are from `ec059527`. They add the
  CPS-derived Baofeng 5RH Pro / UV-5RH Pro v2 driver, fix TK-7160K
  dynamic-zone metadata decoding, and correct BF-F8HP Pro port guidance.
- myGMRS approved the confidential server-side client and callback on
  2026-11-05. The desktop myGMRS directory is enabled again.
- Added myGMRS.com repeater search with OAuth 2.0 Authorization Code plus PKCE
  in commit `8476c0c3`. The repeater dialog can switch between RepeaterBook and
  myGMRS, signs in through the system browser, imports GMRS frequencies and
  mapped tones, and honors the API's license and Premium data restrictions.
  Integration details are in `docs/MYGMRS_API.md`.
- The desktop calls `/api/mygmrs/oauth/start`, opens myGMRS in the system
  browser, polls with a short-lived handoff token, and receives only an opaque
  NewChirp session token. Website commit `4f57d20` performs the confidential
  client exchange, keeps myGMRS access/refresh tokens server-side, refreshes
  them, proxies authenticated and ZIP-radius repeater searches, and revokes
  them on sign-out.
- myGMRS text searches use literal listing text and do not resolve county
  names. NewChirp now treats a 5-digit search entry as a myGMRS ZIP-radius
  search and explains the limitation instead of returning a misleading empty
  result.
- The Linux `1.0.45` DEB, RPM, AppImage, and Pacman artifacts are live from
  source commit `4ca2a6f9`. They add the Retevis RA89 driver and safe TK-270G
  driver, keep the CPS-derived Baofeng 5RH Pro /
  UV-5RH Pro v2 driver, include the latest GitHub bridge fixes, and keep the
  UV-5RH handshake retry, experimental KSUN UV-K60 profile, KG-Q10H and
  RT-860 support, malformed-tone handling, cancellable myGMRS sign-in, F4HWN
  support, and GM-21/TD-H3 updates.
- Linux `1.0.45` verification: quick safety review of the incoming RA89 and
  TK-270G driver changes found no unexpected process execution, credential
  access, arbitrary filesystem behavior, or obfuscation; `flutter analyze`
  was clean; focused Python regression tests ran 74 tests successfully;
  embedded `version.json`, DEB/RPM/Pacman metadata, package payloads,
  extracted AppImage payload, bundled Python/CHIRP runtime, bundled
  `libusb-1.0.so.0`, absence of GLib 2.80 once-init pointer symbols, server
  checksums, public HTTP 200 checks, and the live platform manifest were
  verified.
- The `1.0.45` artifacts include the experimental `KSUN UV-K60` model profile
  using the pinned Quansheng UV-K5 transport and memory layout. Physical
  read/write comparison is still required.
- The client secret is stored only in `/opt/newchirp/.env.mygmrs` with mode
  `0600`. It is not present in either repository or in desktop builds.
- Verification for the confidential relay and desktop session path:
  `flutter analyze` is clean, all 183 Flutter tests pass, all 248 Python tests
  pass with 2 fixture-dependent skips, the website build and forum tests pass,
  and the website OAuth test covers token refresh, opaque sessions, ZIP search
  proxying, logout revocation, and invalid state.
- Verification for `8476c0c3`: `flutter analyze` is clean, all 183 Flutter
  tests pass, and all 248 discovered Python tests pass with 2 fixture-dependent
  skips. A read-only anonymous request to `GET /repeaters?state=NY` confirmed
  the documented response shape and confirms that anonymous frequencies are
  omitted.
- The third 2026-11-03 triage found 11 unread bug reports. Replies were
  verified in `Sent`, and source UIDs 384, 390, 392, 394, 396, 397, 398, and
  400 were verified `\Seen`. UIDs 385 and 399 are reporter acknowledgements;
  401 and 402 are the Yaesu VX-5 hardware/protocol thread. All four remain
  unread pending hardware validation or no action.
- The Windows serial-diagnostic fix is committed and pushed as `ccb389d1`.
  Error 31 / "cannot configure port" failures now identify the USB-serial
  device and recovery steps, and localized `PermissionError(13, ...)` text no
  longer bypasses the port-ownership explanation.
- Verification for `ccb389d1`: the focused bridge suite ran 53 tests with one
  pre-existing Windows `NamedTemporaryFile` `PermissionError`; Flutter ran 173
  passing tests with four intentional Windows module-sandbox failures and one
  pre-existing Help-menu expectation failure; `flutter analyze` reported only
  three pre-existing `avoid_print` infos. This note predates the later
  Windows `1.0.38` publication.
- The second 2026-11-03 triage found 14 unread bug reports and handled UIDs
  383, 386, 387, 388, 391, 393, and 395. Every reply was verified in `Sent`,
  and every original source UID was verified `\Seen`. UIDs 384, 385, 389, 390,
  392, 394, and 396 remain unread: five require Windows/COM-port or handshake
  diagnosis, and two are reporter acknowledgements.
- Scoped fixes are committed and pushed as `4d2c385c`: unprogrammed UV-5RM
  Plus PTT-ID bytes load as Off, out-of-range UV-9G service squelch calibration
  values are read-only and preserved during settings upload, and invalid
  TK-270G bank metadata is normalized before channel decode.
- Verification for `4d2c385c`: `flutter analyze` is clean, all 178 Flutter
  tests pass, and all 245 discovered Python tests pass with 2 fixture-dependent
  skips. The installed formatter still reports 13 pre-existing Dart files it
  would rewrite; no Dart source was changed for this triage.
- The 2026-11-03 triage handled all 23 unread bug-report messages (UIDs
  347, 348, 349, 351, 352, 354, 356, 357, 359, 360, 361, 362, 363, 364,
  366, 367, 372, 374, 375, 376, 377, 379, and 380). Every reply was verified
  in `Sent`, every source message was marked `\Seen`, and the inbox returned
  to zero unread bug reports. Scoped fixes are committed as `d6df462a`:
  correct A9305B mixed-frame handling, little-endian RT-950 frequency decoding,
  TD-H3 family auto-detection, the field-confirmed GM-21 alternate handshake,
  and a Linux Python compatibility patch for CHIRP's error annotation.
- The Windows `1.0.37` installer is live. It applies the CPS-verified RT-950
  transport correction: hardware and XON/XOFF flow control are disabled,
  the randomized 25-byte `SEND` authentication exchange is performed with
  session-symbol payload decryption, and the Web Programmer's 3.5-second
  block response window is allowed. It keeps the `1.0.27`-`1.0.36` fixes.
- The macOS `1.0.44` release is live from source commit `9929f997`. It adds
  the CPS-derived Baofeng 5RH Pro / UV-5RH Pro v2 driver, fixes TK-7160K
  dynamic-zone metadata decoding, and corrects BF-F8HP Pro port guidance.
- The 2026-11-01 macOS triage handled RT-950 report UID 309 and FT-5D report
  UID 313. The fixes are committed as `9ab7e522`; both replies were verified
  in `Sent`, and both source messages were marked `\Seen`.
- The 2026-11-02 triage handled UIDs 319, 320, 323, 325, 337, and 338 with
  verified replies and `Sent` copies. The A9305B protocol correction is
  `dd5beb22`; the IC-E90 invisible-slot and IC-7200 grammar fixes are
  `27851d1d`.
- The second 2026-11-02 pass handled UIDs 305, 306, 308, 311, 314, 316, 322,
  326, 327, 328, 329, 330, 332, 333, 334, and 335 with verified replies and
  `Sent` copies. The inbox is at zero unread bug reports.
- Commit `12d35fd7` keeps TH-9800 channels readable when a reserved CTCSS
  field appears in an unused tone slot, keeps VX-6 reads usable when a stored
  frequency has no programmable step, removes file-only models from the
  connected-radio catalog, and reports `wx`-dependent CHIRP modules as
  unsupported by the headless runtime. Offline fixtures and the full Python
  suite verify the changes; physical retests and saved images are still
  pending for TH-9800 and VX-6.
- Triage guidance now distinguishes diagnosis from communication: a known,
  confirmed fix is sent to a reporter regardless of their operating system.
  Platform ownership only determines where native retesting is required.
- Added `docs/REA_PLAYBOOK.md` after the A9305B protocol miss. Future
  CPS-derived driver work must trace both serial directions, document wire
  encoding and response-length rules, build replay fixtures, and record
  static/OEM-capture/physical evidence separately.
- The Linux `1.0.37` DEB, RPM, AppImage, and Pacman artifacts are superseded
  by Linux `1.0.43`. The `1.0.37` release was built from `5a5e79a9` and
  included the RT-950 transport correction while keeping the GLib 2.74 API cap
  so Debian 12/MX Linux systems do not fail at startup with missing
  `g_once_init_enter_pointer` / `g_once_init_leave_pointer` symbols.
- The live downloads page shows separate Linux rows for DEB, RPM, AppImage,
  and Pacman. Keep Pacman labeled for Arch/Omarchy/Manjaro and keep the
  copyable `sudo pacman -U ~/Downloads/NewChirp-linux-x64-<version>.pkg.tar.zst`
  helper under that row.
- The macOS `1.0.44` release is built, signed, notarized, stapled, uploaded,
  and live. The universal DMG contains both Python architectures and universal
  libusb.
- The RT97L serial protocol is implemented and offline-tested, but its
  provisional channel map still requires validation on physical hardware.
- The experimental GM-32 has physical read/write evidence from 2026-10-25.
  The TS-2000 write-timeout fix still needs a physical upload/read-back retest.
  TS-2000 settings reads now report unsupported cleanly, and failed serial
  operations include a sanitized command trace for support reports.
- The Midland MXT295 has completed physical read and write testing. It is
  normal supported hardware on desktop and in the Web Programmer, not
  experimental.
- `tshirt - i chirp often.png` is an untracked user asset and must not be
  committed or deleted.
- `pubspec.lock` may be locally modified by the installed Flutter SDK. Do not
  include it unless the next task intentionally changes dependencies.
- After rebooting, run `git fetch origin` and inspect new commits before
  choosing the next task.
- Build release artifacts only on their native platform.

## Repository state

- Local path: `/home/rlopez/newchirp.net`
- Branch: `main`
- Windows `1.0.70` artifact source commit: `4fde327b`
- Windows `1.0.69` artifact source commit: `5db67c3b`
- Windows `1.0.68` artifact source commit: `dcc91434`
- Windows `1.0.67` artifact source commit: `8e03e24b`
- Windows `1.0.66` artifact source commit: `cd9ced58`
- Windows `1.0.65` artifact source commit: `014df59b`
- Windows `1.0.64` artifact source commit: `83a592ae`
- Windows `1.0.63` artifact source commit: `f550ae84`
- Windows `1.0.62` artifact source commit: `d9b31864`
- Windows `1.0.61` artifact source commit: `0e701b16`
- Windows `1.0.60` artifact source commit: `488564b4`
- macOS `1.0.73` artifact source commit: `5e734229`
- macOS `1.0.72` artifact source commit: `d502504e`
- macOS `1.0.71` artifact source commit: `876c765b`
- macOS `1.0.70` artifact source commit: `b6fbc544`
- macOS `1.0.69` artifact source commit: `0f7f9048`
- macOS `1.0.68` artifact source commit: `48f56627`
- macOS `1.0.67` artifact source commit: `8e03e24b`
- macOS `1.0.66` artifact source commit: `ee72c09e`
- macOS `1.0.65` artifact source commit: `8f56c3da`
- macOS `1.0.64` artifact source commit: `2fc54348`
- macOS `1.0.63` artifact source commit: `847db298`
- macOS `1.0.62` artifact source commit: `89b4876e`
- macOS `1.0.61` artifact source commit: `0e701b16`
- macOS `1.0.60` artifact source commit: `488564b4`
- macOS `1.0.59` artifact source commit: `170c63f3`
- macOS `1.0.58` artifact source commit: `0ccff82c`
- macOS `1.0.57` artifact source commit: `1d94b15f`
- Linux `1.0.79` artifact source commit: `d1665f13`
- Linux `1.0.78` artifact source commit: `3d16733f`
- Linux `1.0.77` artifact source commit: `8a24cd2f`
- Linux `1.0.76` artifact source commit: `ab66c0d7`
- Linux `1.0.75` artifact source commit: `79b693a5`
- Linux `1.0.74` artifact source commit: `76519b2d`
- Linux `1.0.73` artifact source commit: `b8dd8004`
- Linux `1.0.72` artifact source commit: `6704d9bb`
- Linux `1.0.71` artifact source commit: `98309c23`
- Linux `1.0.70` artifact source commit: `76de9782`
- Linux `1.0.69` artifact source commit: `5dd9aa67`
- Linux `1.0.68` artifact source commit: `360773be`
- Open pull requests: none
- Checked-out source version: `1.0.77+77` (macOS `1.0.77`; Linux artifact is `1.0.79`)
- macOS builds are pinned to CocoaPods with
  `flutter.config.enable-swift-package-manager: false`.
- Intended untracked file: `tshirt - i chirp often.png`
  - This is a user asset, not application source.
  - Do not commit or delete it unless explicitly requested.

## Live releases

Latest public artifacts reported by
`https://newchirp.net/api/releases/latest`:

| Platform | Version |
|---|---:|
| macOS | 1.0.77 |
| Windows | 1.0.76 |
| Linux | 1.0.79 |

Linux `1.0.79` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.79.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.79.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.79.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.79.pkg.tar.zst`
- DEB: `48,942,988` bytes, SHA-256
  `a6864bd263e2b32b15cc66dd76f164c86ee2bb7426a62fb069e65f8290a6f64f`
- RPM: `49,027,853` bytes, SHA-256
  `3e349d34dbcf5ccf185e6ac6baf201bdfde4f3f96e9da87cef4299c3bfd7e50f`
- AppImage: `49,218,752` bytes, SHA-256
  `306aecb74cff4af8c3d4b3df2170a3928b9689fa8eeb68e35de0eecb729353a6`
- Pacman: `47,876,783` bytes, SHA-256
  `6190fa6a17e928b68b4de5b15f00fe44c30c24c782cf1bcbc46c64c8d9bd0804`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.79`

Linux `1.0.78` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.78.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.78.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.78.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.78.pkg.tar.zst`
- DEB: `48,938,920` bytes, SHA-256
  `25bdf0a5781d8d773cc9404e84e2a890d8c11a543bf3b9557137224ffe13c60a`
- RPM: `49,022,187` bytes, SHA-256
  `b6faf0562f8d81e9190868fae5d92ef1f7d231b3dc37ecac28ac1fae3e1ce569`
- AppImage: `49,218,752` bytes, SHA-256
  `2ceb67a0294f180f582495d2c7c6db5d3c5529495a0aff47b81098159954756a`
- Pacman: `47,871,603` bytes, SHA-256
  `6d4f7c15b3e23b48f19033e354baa0c3c5c2e9c2e5d7cc1549af3f6fb3d6c013`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.78`

Linux `1.0.77` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.77.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.77.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.77.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.77.pkg.tar.zst`
- DEB: `48,926,594` bytes, SHA-256
  `aefe1289b33eeb5a9b998daa62dcfbef05c804855d1e908b1802e7a5b75cef5e`
- RPM: `49,008,576` bytes, SHA-256
  `5225239ab8b6a64065bafa629426dae4cee1b104d8cabe77143e20aac9c939d8`
- AppImage: `49,206,464` bytes, SHA-256
  `1e5b76ee86a5582ecff4f9d49e0ce54830ff2b2bff35b23596a87cabffb3de7d`
- Pacman: `47,886,940` bytes, SHA-256
  `919db7e723e3f47231f7758483b5014a48154c727f9382bd3d834faa4a46f485`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.77`

Linux `1.0.76` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.76.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.76.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.76.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.76.pkg.tar.zst`
- DEB: `48,923,388` bytes, SHA-256
  `3170f5a782647293747f5a93a64b2a297deb5b03a8d17be0b1edd2ca73cf6f49`
- RPM: `49,005,117` bytes, SHA-256
  `1aca797940d07b5949a188fde408b89fc22791f888c91cc2314c55230b83f73c`
- AppImage: `49,202,368` bytes, SHA-256
  `467a9aa3a7032934dbcf982269fc73733e39088abe136a8bde5e13afa5a6a059`
- Pacman: `47,885,354` bytes, SHA-256
  `275d66593a360bc2702856a17e4a7f4ddf3744c1182b89a2241e418f7369f957`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.76`

Linux `1.0.75` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.75.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.75.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.75.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.75.pkg.tar.zst`
- DEB: `48,921,708` bytes, SHA-256
  `05fb23dda2e7de0bee2c1166b2bea1c61590d0439ea714a9bf6628ac06d2b8b9`
- RPM: `48,997,928` bytes, SHA-256
  `7fa461d62bd8d4676a712abcf9ddb7a5933ba67258947c035bd8b96bbe66ee46`
- AppImage: `49,198,272` bytes, SHA-256
  `31ea654a6247256626d95140cbdc22ddf5c9428a10fe5aeed7e7c08085b9029d`
- Pacman: `47,870,070` bytes, SHA-256
  `49b6a837b90cf2b33899d0db2ab866e9a6a672cfee3ea807d039eb6599c72495`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.75`

Linux `1.0.74` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.74.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.74.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.74.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.74.pkg.tar.zst`
- DEB: `48,920,586` bytes, SHA-256
  `c07aade70cc9efb115336f5a09e78a4ed3b64bfa90feec8f2b5c07d986ddbe87`
- RPM: `48,997,835` bytes, SHA-256
  `06e3fa3c80c5ce7eb2fcde11dd5645cdfa53c1ebae087c85e3917597448008d5`
- AppImage: `49,198,272` bytes, SHA-256
  `02658d6459f53b684bbe42f9b102980884e8cc1b99d64e4071c5a072f7c67978`
- Pacman: `47,866,435` bytes, SHA-256
  `294483a0c8f92ca825332cec669b6c21db239294b7f60e56ffadef931e2163a6`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.74`

Linux `1.0.73` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.73.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.73.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.73.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.73.pkg.tar.zst`
- DEB: `48,906,462` bytes, SHA-256
  `3f0b742e9fe3e0b188d1a574d3c9d9743d60c2855fcfb735930c6c6762f0a914`
- RPM: `48,987,301` bytes, SHA-256
  `bea404982c8bec2ec63f107888f129dcf8eaa63997d06cf942ad3967402b5189`
- AppImage: `49,185,984` bytes, SHA-256
  `49739a2e85308e9a6ea3273c72100d958753cb0c4f7fecf832505d122f7eaade`
- Pacman: `47,843,544` bytes, SHA-256
  `93b0f1e1225f6033e6d532561454473602872f87e48317ec71a37fa379b6b56e`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.73`

Linux `1.0.72` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.72.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.72.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.72.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.72.pkg.tar.zst`
- DEB: `48,598,242` bytes, SHA-256
  `6903bbc19dc4a0d8ebf826287451e96696220a4df08540ba2ee271f4373c6605`
- RPM: `48,686,588` bytes, SHA-256
  `60a74750fb66bacf1b2cc2d02c6ea9c27cca40d5fcea53fcdde216f4f86d5c89`
- AppImage: `48,886,976` bytes, SHA-256
  `eaf12f5fe21c997b87f29aca8c979e0db680d1cac73402fc4add9117a01b5049`
- Pacman: `47,562,354` bytes, SHA-256
  `e34cc9ce28b344bf3f82fb7351631947eff5c1c14a0f7f708737b2f6a5fe7396`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.72`

Linux `1.0.71` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.71.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.71.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.71.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.71.pkg.tar.zst`
- DEB: `48,598,690` bytes, SHA-256
  `61d3e9b6f5f2d9a013bfd7e963ce2ea808d1c104fd2c865bbe58cb58cfaaa6dc`
- RPM: `48,686,205` bytes, SHA-256
  `67059796d48aa5c4daef76db0fa69d178a65564d78ca8dc2893ccca8771c45a4`
- AppImage: `48,886,976` bytes, SHA-256
  `9796efebdab17374cb56d99f0e41598a5ac5fd4859caaf7f0e852dd620e7f019`
- Pacman: `47,561,213` bytes, SHA-256
  `dcd91cc86a283a4ca415007d033048954755c3bb7d5f3f54c1fd650274f1aeea`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.71`

Linux `1.0.70` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.70.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.70.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.70.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.70.pkg.tar.zst`
- DEB: `48,590,972` bytes, SHA-256
  `2bdae61e142ec25efc3199a71ec3a95e782b9342253c7c7c638186f23d12d66a`
- RPM: `48,678,830` bytes, SHA-256
  `d2cd41886d279e467f7aefba08d03cea6f0ea09b4cd2e3b77f33bc80d2c15f7c`
- AppImage: `48,878,784` bytes, SHA-256
  `d7faf36fcabe83dd02b1d0df1c4cb0b5077b21f31bd26dc52d2c2ef62ea0fcbe`
- Pacman: `47,540,072` bytes, SHA-256
  `895ec1bb9cc2b7706c35c7b918ac5ae1eb8b1372c2390a69f6c39e5ed2e4a68f`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.70`

Linux `1.0.69` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.69.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.69.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.69.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.69.pkg.tar.zst`
- DEB: `48,590,228` bytes, SHA-256
  `18890608dadda95a0b4601cb376acd983958dc0947a075b7daa823d77c4060e0`
- RPM: `48,678,376` bytes, SHA-256
  `f47c61949b62b60b276e6462d433ffb7a172f81c27dc9ca1e97cc98feae6ada8`
- AppImage: `48,878,784` bytes, SHA-256
  `15be796f559b3f184308e8dd74899f79b5e9a6c2cc527dc6dd9bf178792f20d8`
- Pacman: `47,543,913` bytes, SHA-256
  `fd7164a91f42a7d0a45871512e826b28de5f4cb503757be9cac6facbba7e9abe`
- Public HTTP checks returned `200 OK`
- Server checksums and sizes matched the local artifacts
- Linux platform manifest reports `1.0.69`

Linux `1.0.68` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.68.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.68.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.68.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.68.pkg.tar.zst`
- DEB: `48,567,146` bytes, SHA-256
  `a60af27ff15691a98a88057f2f9b6213ed026dc0c65fc410e4d2add9c18ee3e8`
- RPM: `48,650,673` bytes, SHA-256
  `0ea65c3d2163d403923df814d4276c96407275f24b589298abf824677a3c7419`
- AppImage: `48,854,208` bytes, SHA-256
  `4e5c027498b788f4c1747a0fa5f06482d1e04bcac51ea9c1ddd9d8ed0a798d0f`
- Pacman: `47,533,925` bytes, SHA-256
  `b56ba89d36e0f513f73b2014809e4ecff49a8e8e58d0bd809b9bad76497c625d`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.68`

Linux `1.0.67` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.67.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.67.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.67.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.67.pkg.tar.zst`
- DEB: `48,567,574` bytes, SHA-256
  `d8e8be645be49740dd6cec9ff6e7c14f989c542683235495b0ec9573e3116f79`
- RPM: `48,651,169` bytes, SHA-256
  `c8bbf9c8ef4d3acede49c3fcd636fe0c7c6b498d2be49f3bd88ab0f19a9a2ed8`
- AppImage: `48,854,208` bytes, SHA-256
  `85ef5b9c0ca708ee8590b926737328097cea642316f863525ecf724bfcf84a8b`
- Pacman: `47,529,844` bytes, SHA-256
  `4906d358a09bfbe57d3177bcc58a49686e63a8e6bc549dbfa4e7f6eb22d0780b`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.67`

Linux `1.0.66` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.66.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.66.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.66.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.66.pkg.tar.zst`
- DEB: `48,558,974` bytes, SHA-256
  `d7135ce5062bff886b418a42b8e8c6fe5f06ce00f85bea4fd1acd7235ef9948f`
- RPM: `48,651,431` bytes, SHA-256
  `8c409604d642e68a1c764062699008d936990c523f7e3ea53f10f3998419b200`
- AppImage: `48,850,112` bytes, SHA-256
  `1d8a92db199f83e240203ce9f6dbbd14e1b0e730474961b0ddefc0d9c0f0b8d9`
- Pacman: `47,525,864` bytes, SHA-256
  `3a6c8d357568ccc7873efe7974cd6ed335a10d3edfad066a910eb13f8a7feb47`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.66`

Linux `1.0.65` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.65.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.65.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.65.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.65.pkg.tar.zst`
- DEB: `48,563,176` bytes, SHA-256
  `f3cf598266edcd1c75944703cbb3e4699afb82cf6282c8054e797922d3e1df9e`
- RPM: `48,652,761` bytes, SHA-256
  `fd1af91bc3a84bbcb267fb0a3e19ec35c8d3a7b92b5407e1fb6415c14102210e`
- AppImage: `48,850,112` bytes, SHA-256
  `c0849973a05f21de913201ff4c3de253b9020e52af0f55a8dc162253a9349f20`
- Pacman: `47,524,945` bytes, SHA-256
  `f1aca0d1b313ce5db5145407ff811cfb3f4979dadb611d9382e1cec3f4ae9958`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.65`

macOS `1.0.73` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.73.dmg`
- Version/build: `1.0.73` / `73`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `cca9e2081060d0c389ed40e0c400a696bb7f76b13037929422d733321aa1659f`
- Size: `87,684,759` bytes
- Built from `5e734229`
- Notarization submission:
  `83014a33-40e8-4065-abba-40cf4b8585f6`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains the Ferrite RT-950 Pro driver, Ferrite range and repair
  fixes, corrupt Baofeng tone handling, 5RX S-CODE handling, refused-channel
  progress, FT-60 and sibling-model guidance, AnyTone USB guidance, XWayland,
  PMR446, TH-D7G, and UV-5R Mini changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.72` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.72.dmg`
- Version/build: `1.0.72` / `72`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `e3fb1bff88d84731222a4e54506bcf470bf1da48bd5324e6f06e1e246cbe812e`
- Size: `87,695,433` bytes
- Built from `d502504e`
- Notarization submission:
  `1fd6915b-24e2-40c2-927e-104e67879ff8`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains the Ferrite RT-950 Pro driver, PMR446 reference, FT-60 and
  sibling-model guidance, corrupt/5RX tone handling, AnyTone USB guidance,
  and refused-channel/live-write progress diagnostics
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.71` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.71.dmg`
- Version/build: `1.0.71` / `71`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `cb0bc91f4c1268cd13859170ca329e08c8ba65c606840d68c6541538e8b2ae8b`
- Size: `87,642,244` bytes
- Built from `876c765b`
- Notarization submission:
  `11a7e4f4-f0b4-4bec-bffa-e89561f2a606`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains all TD-H9 profiles, TK-863G timing, UV-5R Mini handshake,
  zone preservation, and cumulative 1.0.70 changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.70` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.70.dmg`
- Version/build: `1.0.70` / `70`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `93c57aea40bf5d03f6fa65007a7d0a4af14f41b1b9a11f1b5423cc801a9d2202`
- Size: `86,989,022` bytes
- Built from `b6fbc544`
- Notarization submission:
  `c763ad92-b1db-4a94-9110-757a471ab3f0`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains zone preservation, repeated settings writes, RT22 tone,
  UV-5RM Plus zone, UV-82/KG-689 settings-button, and cumulative 1.0.69
  changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.69` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.69.dmg`
- Version/build: `1.0.69` / `69`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `38aae79413d8775d704a5b9197f828f11f982ebc354f9ec702560f71cdf298ab`
- Size: `86,986,597` bytes
- Built from `0f7f9048`
- Notarization submission:
  `baa15c49-30d7-4b03-986b-a30fc5dbe577`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains the UV-K5 RO-KO 512K, AT-D878UVII Plus/D578, Baofeng 5RX,
  and cumulative 1.0.68 release changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.68` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.68.dmg`
- Version/build: `1.0.68` / `68`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `3fd6068c5750adcb1d3a53928e41cddaab789394989d60ee9b76f321e334c47d`
- Size: `86,939,830` bytes
- Built from `48f56627`
- Notarization submission:
  `ad8c3d81-e2f2-493a-a972-cb34f65952ea`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains stalled-write watchdog handling, safe odd-tone decoding,
  UV-32 handshake retries, Android USB broken-pipe handling, and cumulative
  1.0.67 release changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.67` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.67.dmg`
- Version/build: `1.0.67` / `67`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `250f68ae8fe5d2be54e0e73956277e5ba114c5f6dd4258eb35763e41722b7f22`
- Size: `86,928,648` bytes
- Built from `8e03e24b`
- Notarization submission:
  `653b46a8-5cd8-43e5-bea0-da202daa2832`
- Apple notarization accepted and the stapled ticket validates
- Mounted-app launch smoke test passed
- Bundle contains the cumulative post-1.0.66 FTM-300DR/F4HWN 7.0, RT22,
  DM-32UV progress/cancel, UV-K60 Plus, RA87, UV-5R Mini, VX-170, TH-350,
  no-step tuning, trace, printing, and write-progress changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.66` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.66.dmg`
- Version/build: `1.0.66` / `66`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `0087cb989e126669d63be4f5eaa94ca80dbc41ecd03b2d81b1091359723893b9`
- Size: `74,696,389` bytes
- Built from `ee72c09e`
- Notarization submission:
  `a48065c5-5e65-488c-aa7a-0c19fe5c3755`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the DM-32UV name-termination fix, current RT-950 Pro
  behavior, RepeaterBook relay integration, and cumulative compatibility
  changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.65` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.65.dmg`
- Version/build: `1.0.65` / `65`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `6dedceb731cc6bebfa76de76aaaea62cc8e4e4729fc9d5fe4064afce27404bd5`
- Size: `74,696,389` bytes
- Built from `8f56c3da`
- Notarization submission:
  `b9931c3b-064a-4b8b-b22d-8508e72bdf2f`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the DM-32UV shifted-insert extras fix, TK-270G one-based
  bank positions, current RT-950 Pro work, RepeaterBook relay integration,
  and cumulative compatibility changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.64` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.64.dmg`
- Version/build: `1.0.64` / `64`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `05ccb46548ff27de481610d6b41c0a5cc0515504eb9617c5c9763e1bf2c0a8cb`
- Size: `74,694,851` bytes
- Built from `2fc54348`
- Notarization submission:
  `dbd06c9d-66de-4d3f-a19b-5e2c1117dca5`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the RT-950 Pro write/transmit correction, approved
  RepeaterBook relay integration, Icom IC-F50V/F60V capture profile,
  KG-689E/699E compatibility fixes, and cumulative compatibility changes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.63` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.63.dmg`
- Version/build: `1.0.63` / `63`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `0496ad47204d606a09555d4c27fcc5fc88f1bd6a101b14d6865cbe00f692477a`
- Size: `74,692,293` bytes
- Built from `847db298`
- Notarization submission:
  `baac68f6-92f7-4154-b680-3b3a6c57adc1`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the approved RepeaterBook relay integration, Icom
  IC-F50V/F60V read-only capture profile, KG-689E/699E compatibility fixes,
  and cumulative 1.0.63 through 1.0.65 fixes
- Local, server, and public-download checksums matched the final stapled DMG

Linux `1.0.64` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.64.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.64.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.64.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.64.pkg.tar.zst`
- DEB: `48,566,694` bytes, SHA-256
  `c58f4ef279e260f131eb700d651d4063e289999cf4bc7083cfde2a6529bcd0be`
- RPM: `48,653,747` bytes, SHA-256
  `d4e13e4a0cacf24cc90cd428cd4633544588a7d8b4e69be75888d493211720c4`
- AppImage: `48,846,016` bytes, SHA-256
  `26048b9b36e63eefe3016811d5232f6b6acf399f0a39a603e93ea5092127132e`
- Pacman: `47,544,695` bytes, SHA-256
  `05e0c9c23db86200c80924bdbdf86804126365d817e5f655dfa27f3e1073cf9f`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.64`

Linux `1.0.63` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.63.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.63.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.63.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.63.pkg.tar.zst`
- DEB: `48,564,024` bytes, SHA-256
  `01b9ab23a869829a58024cb1c086e753f1a39cf870b546a1cc4f6c309aa78898`
- RPM: `48,651,203` bytes, SHA-256
  `70a5f484b2ac85112e50c1468b3bd3d10cbd063e79300868ddf9de117909dc0b`
- AppImage: `48,846,016` bytes, SHA-256
  `99b578e21654e28859f5cdd15f270d1be5f3c9e46e5a9463c694f3f8507dc15b`
- Pacman: `47,531,477` bytes, SHA-256
  `8ed7d2c954dfd349affa9f8aae3a22cc27c32573e05eb17da35904dc58c7779a`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.63`

Linux `1.0.62` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.62.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.62.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.62.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.62.pkg.tar.zst`
- DEB: `48,560,022` bytes, SHA-256
  `34dfca976a39e621ae7797bdb4148f1e1ae2c753df18feb2046320d72206e7aa`
- RPM: `48,649,543` bytes, SHA-256
  `9e8a8be6dc45c6342d7a9c9cfd89b3d88193acbd736edd7d7885bffa0aebd240`
- AppImage: `48,846,016` bytes, SHA-256
  `8d313037c55f62f07455d2a996fae07fb06fbcdf45399895465b6177fd87502e`
- Pacman: `47,524,746` bytes, SHA-256
  `44c1585e5113f0300681dd19c1e564dbbe09bc0a7a912cb323a46d1a609a273f`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.62`

Linux `1.0.61` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.61.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.61.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.61.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.61.pkg.tar.zst`
- DEB: `48,551,858` bytes, SHA-256
  `b32b6dc5ea2edcf1a7f6f29e0cae249357dd0ebe462b76cfbcd16757eee8ac27`
- RPM: `48,637,203` bytes, SHA-256
  `74ba479102c025ff4b3f65d7337f57467428c3bbe7b3c9cc8d0d828c1e084e41`
- AppImage: `48,837,824` bytes, SHA-256
  `c4306b569fc9f551b4b74f217663f16ec664f481ddf59b81ba3b1678470bac61`
- Pacman: `47,497,916` bytes, SHA-256
  `e839269b1d6421b31ebc445dc21da7cb6638019dbf0d4b97315bf02edfaa10e1`
- Public HTTP checks returned `200 OK`
- Server checksums, sizes, and permissions matched the local artifacts
- Linux platform manifest reports `1.0.61`

Linux `1.0.60` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.60.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.60.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.60.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.60.pkg.tar.zst`
- DEB: `48,546,800` bytes, SHA-256
  `b9477b552f5036bf28bc7f9a41eb3408913cb5a152528b19c6846c36fe4cbe01`
- RPM: `48,635,951` bytes, SHA-256
  `4bedd1db0d82994079d50d58fe098da337d386ec39d2bb43ad92371e0cd3b642`
- AppImage: `48,837,824` bytes, SHA-256
  `7eff0a199ad059a45ba52c1809f1d0d7f8cb48fa59ab1689a4ce72544827e855`
- Pacman: `47,499,778` bytes, SHA-256
  `775a415bfbbd088dbb6e9c4e1d82735b7d0ed2bcb486e56a6dce5f15051fd13d`
- Public HTTP checks returned `200 OK`
- Server checksums and sizes matched the local artifacts
- Linux platform manifest reports `1.0.60`

macOS `1.0.62` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.62.dmg`
- Version/build: `1.0.62` / `62`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `76221b2015baf52d7b50e912ef40261c5a101a89b2f3fd99ab75d074fc711a90`
- Size: `86,852,737` bytes
- Built from `89b4876e`
- Notarization submission: `8fed5c04-70ea-4d77-b69c-b36b9340ea38`
- Gatekeeper result: accepted as Notarized Developer ID
- Application payload is runtime-identical to the final 1.0.62 release
  boundary `0d09b292`, which only changes an Ubuntu ledger test
- Bundle contains Wouxun KG-689E/KG-699E support, the Icom CI-V unset-tone
  compatibility fix, promoted FT-50 support, and the latest TK-270G and 5RH
  Pro zone-flag fixes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.61` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.61.dmg`
- Version/build: `1.0.61` / `61`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `7ae5be6ac211dd4bc221032e2a8b0fa10c05eb969280f45a9f10624a411b941a`
- Size: `86,853,247` bytes
- Built from `0e701b16`
- Notarization submission: `6c290229-c679-465a-9d0b-0ab077ba1799`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains Wouxun KG-689E/KG-699E support, the Icom CI-V unset-tone
  compatibility fix, promoted FT-50 support, and the latest TK-270G and 5RH
  Pro zone-flag fixes
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.60` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.60.dmg`
- Version/build: `1.0.60` / `60`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `2f85468d79a6b359ed7e77ed9b3c63a15f5e6a215fbfddc51b2a1719eeac39d7`
- Size: `86,823,835` bytes
- Built from `488564b4`
- Notarization submission: `87136c3e-df9d-43bf-8a77-07a1246e1f66`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains BF-F8HP-PRO fixed-zone support, the Alinco DR-735 rebuild,
  RT-950 Pro CPS 1.3.3 read/write transport, official model display names,
  CSV encoding detection, and channel select-all
- Local, server, and public-download checksums matched the final stapled DMG

Linux `1.0.59` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.59.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.59.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.59.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.59.pkg.tar.zst`
- DEB: `48,529,134` bytes, SHA-256
  `866e5efa60f4bf1e49e3c854bc871a27e9054403430b8f1afafe049e730b03df`
- RPM: `48,622,908` bytes, SHA-256
  `22da4352375bb49800d65c0b2d18c15ccb7a4e223aacef69f9f3264b5e9c8a7c`
- AppImage: `48,817,344` bytes, SHA-256
  `bf0144b2d517f405b79d2005be0e488075f9583c1aa127426649d1148ca369ff`
- Pacman: `47,499,651` bytes, SHA-256
  `c1db4b456333036052a95ccf2d44db2683ffb70d261a9983bc75884a8adc507c`
- Public HTTP checks returned `200 OK`
- Server checksums and sizes matched the local artifacts
- Linux platform manifest reports `1.0.59`

macOS `1.0.59` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.59.dmg`
- Version/build: `1.0.59` / `59`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `cee32d26bbf1910e981698f666d4111364c9c4cf50350c83420b736d7499dbe7`
- Size: `86,820,651` bytes
- Built from `170c63f3`
- Notarization submission: `31e8f183-0412-4c69-aab4-4d7cfbc39b77`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the Alinco DR-735 rebuild, RT-950 Pro CPS 1.3.3
  read/write transport, official model display names, CSV encoding support,
  channel select-all, and fractional UV-17ProGPS CTCSS preservation
- Local, server, and public-download checksums matched the final stapled DMG

Linux `1.0.58` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.58.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.58.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.58.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.58.pkg.tar.zst`
- DEB: `48,524,540` bytes, SHA-256
  `2869589c016a788a3fa17d334953812a61b1d317a5b103c2175435172e6d14ac`
- RPM: `48,610,864` bytes, SHA-256
  `808d58d030094d6b90befa54f3ee6d7b64b7a7d595942feebb9b467ad6ad6a17`
- AppImage: `48,813,248` bytes, SHA-256
  `858d3ec0ffc9395d7dc56e0abf78217c78ee4cee76d99e0f9facecfd2702cad3`
- Pacman: `47,507,454` bytes, SHA-256
  `30fbcdc60e84ded5f00aab6c3b68b03b6f77ce698fdb02a3ed35889fea67d19c`
- Public HTTP checks returned `200 OK`
- Server checksums matched the local artifacts
- Linux platform manifest reports `1.0.58`

macOS `1.0.58` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.58.dmg`
- Version/build: `1.0.58` / `58`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `c0f18c21936d6c7de14df75c6cac9cf1ee56bb33f6e0117c9d75e4367b2ea742`
- Size: `86,787,933` bytes
- Built from `0ccff82c`
- Notarization submission: `678ebc18-dd9a-442f-a351-a78e8507e2a1`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains TM-V71 clone-mode read support, the Kenwood live-write
  cache fix, FT-50 clearing in both channel flag tables, and the FTM7250
  stale-channel cleanup
- Local, server, and public-download checksums matched the final stapled DMG

macOS `1.0.57` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.57.dmg`
- Version/build: `1.0.57` / `57`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `6368e8216fb37764f30c5cacf82204364167d344834b7b51a461c40f12cc174b`
- Size: `82,656,870` bytes
- Built from `1d94b15f`
- Notarization submission: `143a2885-b3ab-478b-a263-e5e02a0f5cea`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the TK-270G erased-bank-index upload fix
- Local, server, and public-download checksums matched the final stapled DMG

Linux `1.0.57` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.57.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.57.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.57.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.57.pkg.tar.zst`
- DEB: `48,522,980` bytes, SHA-256
  `fa28f01a9609ef3e9d2ffa74a96c759e812499f26dea69f5e5b767e1320774c8`
- RPM: `48,605,433` bytes, SHA-256
  `8cee77ab108eaf963d42b1ebbe6a14d6195f8fcaff6fbbc5ef5dccdbb957ba44`
- AppImage: `48,805,056` bytes, SHA-256
  `e0d53ad143d63e06ccff566b655af1a99df79efad001dff6d559321c1d1bca5c`
- Pacman: `47,470,886` bytes, SHA-256
  `7c3a8240f301e75eeba413879e2a751b5cffbd73e6ad1314363d63f5e0eb8323`
- Public HTTP checks returned `200 OK`
- Server checksums matched the local artifacts
- Linux platform manifest reports `1.0.57`

Linux `1.0.56` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.56.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.56.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.56.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.56.pkg.tar.zst`
- DEB: `48,522,850` bytes, SHA-256
  `6b9a8ed78f606b59a19ea360ebb7a77d6e27e950d0bfc167dae75b0b86f095f5`
- RPM: `48,605,228` bytes, SHA-256
  `f718fc174b386b36e7b55675fba3d1bafbd5c050ab33603b40e057353526132c`
- AppImage: `48,805,056` bytes, SHA-256
  `b33ee9fda1fbeb85d44e7f4ad3bb4896e25b4a171e3d1b27fbfa5b11f1a93e82`
- Pacman: `47,470,313` bytes, SHA-256
  `9afbd59a68c62532b56e517ff530ef1f80903ce6f94a8a8217dd67857d81fa81`
- Public HTTP checks returned `200 OK`
- Server checksums matched the local artifacts
- Linux platform manifest reports `1.0.56`

Linux `1.0.55` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.55.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.55.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.55.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.55.pkg.tar.zst`
- Local DEB:
  `build/NewChirp-linux-x64-1.0.55.deb`, `48,518,340` bytes, SHA-256
  `8df63389b10c60208190c7e160113184da24ee96e887f7bf54eb497a2b08b294`
- Local RPM:
  `build/NewChirp-linux-x64-1.0.55.rpm`, `48,603,131` bytes, SHA-256
  `898b127d0cd58a01d30dbd5a5898128bc15be545561d0dce0e581a0010d54a5b`
- Local AppImage:
  `build/NewChirp-linux-x64-1.0.55.AppImage`, `48,805,056` bytes, SHA-256
  `2aa60dd242c15b071e35214ecb761dd09ef2fc7a988f614b80fd4397ccef3c89`
- Local Pacman:
  `build/NewChirp-linux-x64-1.0.55.pkg.tar.zst`, `47,467,554` bytes, SHA-256
  `292fece7e7f1d06ff64a17f9f34f8b9316594f22954780444017c93879da7736`
- Public HTTP checks returned `200 OK`
- Server checksums matched the local artifacts
- Linux platform manifest reports `1.0.55`

Windows `1.0.70` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.70.exe`
- Version/build: `1.0.70` / `70`
- SHA-256:
  `f6b86ac40af732f9e27a4fb6b8ce10e706e82d979e48eae5b525426626e89c5a`
- Size: `51,073,329` bytes
- Built from `4fde327b`
- Installer metadata `1.0.70.0` / `1.0.70`; release app `1.0.70+70`;
  in-app version string `1.0.70`
- Bundled Python `3.13.15`, 272 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, and a bridge `list-models`
  run with exit 0, empty stderr, and 604 models across 62 vendors
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains no `__pycache__` or `.pyc` files
- The bundle's `data/app.so` contains `1.0.70`
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.70`
- Authenticode: not signed

Windows `1.0.69` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.69.exe`
- Version/build: `1.0.69` / `69`
- SHA-256:
  `c3be7a1fefda0c883111ec730c1eaf3100771e880791a6d60a4acae2d7a2b774`
- Size: `51,070,106` bytes
- Built from `5db67c3b`
- Installer metadata `1.0.69.0` / `1.0.69`; release app `1.0.69+69`;
  in-app version string `1.0.69`
- Bundled Python `3.13.15`, 272 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, and a bridge `list-models`
  run with exit 0, empty stderr, and 604 models across 62 vendors including
  `AnyTone_AT-D878UVII_Plus`, `Baofeng_5RX`, and
  `Quansheng_UV-K5_RO-KO_512K`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains no `__pycache__` or `.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- The bundle's `data/app.so` contains `1.0.69`; the installer was compiled
  from the clean runtime bundle after purging host bytecode caches
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.69`
- Authenticode: not signed

Windows `1.0.68` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.68.exe`
- Version/build: `1.0.68` / `68`
- SHA-256:
  `1d9cb4b6dac537c7ac69f93c41bca3da3a4c12f935bf747870e9f232674837b8`
- Size: `51,068,933` bytes
- Built from `dcc91434`
- Installer metadata `1.0.68.0` / `1.0.68`; release app `1.0.68+68`;
  in-app version string `1.0.68`
- Bundled Python `3.13.15`, 269 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, and a bridge `list-models`
  run with exit 0, empty stderr, and 602 models across 62 vendors including
  `Baofeng_DM-32UV`, `Radtel_RT-950_Pro`, `Baofeng_UV-5RM_Plus`,
  `Baofeng_BF-F8HP`, and `Wouxun_KG-UV9D_Plus`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains no `__pycache__` or `.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- The extracted `data/app.so` contains `1.0.68`; the installer was
  compiled from the clean runtime bundle after purging host bytecode caches
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.68`
- Authenticode: not signed

Windows `1.0.67` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.67.exe`
- Version/build: `1.0.67` / `67`
- SHA-256:
  `3786af74ed71fc00205bed0ca10cd31923fcc6609304bcab84fd70cd52c740b6`
- Size: `51,066,621` bytes
- Built from `8e03e24b`
- Installer metadata `1.0.67.0` / `1.0.67`; release app `1.0.67+67`;
  in-app version string `1.0.67`
- Bundled Python `3.13.15`, 269 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, and a bridge `list-models`
  run with exit 0, empty stderr, and 602 models across 62 vendors including
  `Retevis_RA87`, `Retevis_RT22`, `Baofeng_UV-5R_Mini`, `Yaesu_VX-170`,
  `Baofeng_DM-32UV`, `Radtel_RT-950_Pro`, `Wouxun_KG-689E`, and
  `Yaesu_FTM-300DR`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains no `__pycache__` or `.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Bundled application launch smoke test succeeded; the installer was
  compiled from the verified bundle
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.67`
- Authenticode: not signed
- The superseded initial upload, which embedded in-app version `1.0.69`,
  is quarantined on the server and was never recorded as a release

Windows `1.0.66` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.66.exe`
- Version/build: `1.0.66` / `66`
- SHA-256:
  `ededeeb1f240cf4e647dda8d3adb0146bb39f668a7f451b02004fe47417cee4e`
- Size: `53,529,691` bytes
- Built from `cd9ced58`
- Installer metadata `1.0.66.0` / `1.0.66`; release app `1.0.66+66`
- Bundled Python `3.13.15`, 265 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, and a bridge `list-models`
  run with exit 0, empty stderr, and 602 models across 62 vendors including
  `Icom_IC-F50V_F60V`, `Icom_IC-F50V_F60V_Capture`, `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, `Yaesu_FT-50`, `Radtel_RT-950_Pro`, and
  `Baofeng_DM-32UV`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains no `__pycache__` or `.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.66`
- Authenticode: not signed

Windows `1.0.65` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.65.exe`
- Version/build: `1.0.65` / `65`
- SHA-256:
  `6aa267b209a53877b8ef82eb9b3fecaa9d08761ec5e10b2cbd5f2fd901362151`
- Size: `53,527,982` bytes
- Built from `014df59b`
- Installer metadata `1.0.65.0` / `1.0.65`; release app `1.0.65+65`
- Bundled Python `3.13.15`, 265 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, and a bridge `list-models`
  run with exit 0, empty stderr, and 602 models including
  `Icom_IC-F50V_F60V`, `Icom_IC-F50V_F60V_Capture`, `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains no `__pycache__` or `.pyc` files and no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.65`
- Authenticode: not signed

Windows `1.0.64` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.64.exe`
- Version/build: `1.0.64` / `64`
- SHA-256:
  `3296e513dec117df8e71be19c3799df57c802da021c4df02813f810ef353daca`
- Size: `55,417,809` bytes
- Built from `83a592ae`
- Installer metadata `1.0.64.0` / `1.0.64`; release app `1.0.64+64`
- Bundled Python `3.13.15`, 265 CHIRP driver modules, and a bridge
  `list-models` run with exit 0, empty stderr, and 602 models including
  `Icom_IC-F50V_F60V`, `Icom_IC-F50V_F60V_Capture`, `Wouxun_KG-689E`,
  `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.64`
- Authenticode: not signed

Windows `1.0.63` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.63.exe`
- Version/build: `1.0.63` / `63`
- SHA-256:
  `798d4a1f219f8e1b3561c5ff8f48be5d7152a2cbf8b1bf9b9a1543d988849d03`
- Size: `55,414,252` bytes
- Built from `f550ae84`
- Installer metadata `1.0.63.0` / `1.0.63`; release app `1.0.63+63`
- Bundled Python `3.13.15`, 265 CHIRP driver modules, and a bridge
  `list-models` run with exit 0, empty stderr, and 601 models including
  `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`,
  `Icom_IC-F50V_F60V_Capture`, and `Yaesu_FT-50`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.63`
- Authenticode: not signed

Windows `1.0.62` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.62.exe`
- Version/build: `1.0.62` / `62`
- SHA-256:
  `a8c430b555d4e3b5de139eda955360ffdaef7ea9171c87443600985b92b84c1b`
- Size: `55,410,889` bytes
- Built from `d9b31864`
- Installer metadata `1.0.62.0` / `1.0.62`; release app `1.0.62+62`
- Bundled Python `3.13.15`, 265 CHIRP driver modules, and a bridge
  `list-models` run with exit 0, empty stderr, and 601 models including
  `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`,
  `Icom_IC-F50V_F60V_Capture`, and `Yaesu_FT-50`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.62`
- Authenticode: not signed

Windows `1.0.61` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.61.exe`
- Version/build: `1.0.61` / `61`
- SHA-256:
  `55036c23d5f813ad0710a60d45fa62b6499d56c919eac4ffb8dadc559afbe19f`
- Size: `55,410,271` bytes
- Built from `0e701b16`
- Installer metadata `1.0.61.0` / `1.0.61`; release app `1.0.61+61`
- Bundled Python `3.13.15`, 264 CHIRP driver modules, and a bridge
  `list-models` run with exit 0, empty stderr, and 600 models including
  `Wouxun_KG-689E`, `Wouxun_KG-699E`, `Icom_IC-910`, and `Yaesu_FT-50`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.61`
- Authenticode: not signed

Windows `1.0.60` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.60.exe`
- Version/build: `1.0.60` / `60`
- SHA-256:
  `27f75d3a76c78048029fd6d431751c5a569eedc78205742ab30ff52cbb0af421`
- Size: `55,397,644` bytes
- Built from `488564b4`
- Installer metadata `1.0.60.0` / `1.0.60`; release app `1.0.60+60`
- Bundled Python `3.13.15`, 262 CHIRP driver modules, and a successful bridge
  `list-models` run with 598 models including `Baofeng_BF-F8HP-PRO`,
  `Alinco_DR735T`, `Radtel_RT-950_Pro`, `Wouxun_KG-UV8D`, `Yaesu_FT-50`,
  `Baofeng_K67_Pro_CPS_V1.1.2`, and `Kenwood_TM-V71`
- The extracted BF-F8HP-PRO bridge payload reports ten read-only zones,
  including channels 1-100 and 101-200
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, fixed-zone compatibility driver, and PDFs; the extracted runtime
  reported Python `3.13.15`, and the extracted application launched
  successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.60`
- Authenticode: not signed

Windows `1.0.59` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.59.exe`
- Version/build: `1.0.59` / `59`
- SHA-256:
  `d5fff0f5d912332e46eb57a5e629c445ec5bdfc18ec846cb6c26c750728a6930`
- Size: `55,391,434` bytes
- Built from `170c63f3`
- Installer metadata `1.0.59.0` / `1.0.59`; release app `1.0.59+59`
- Bundled Python `3.13.15`, 261 CHIRP driver modules, and a successful bridge
  `list-models` run with 598 models including `Alinco_DR735T`,
  `Radtel_RT-950_Pro`, `Wouxun_KG-UV8D`, `Yaesu_FT-50`,
  `Baofeng_K67_Pro_CPS_V1.1.2`, `Kenwood_TM-V71`, and
  `Kenwood_TM-V71_CloneMode`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`, and the
  extracted application launched successfully
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.59`
- Authenticode: not signed

Windows `1.0.58` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.58.exe`
- Version/build: `1.0.58` / `58`
- SHA-256:
  `7f394d1f4bdb811c141a7795f229ec76ed704ce9e2ae1f758618c3bdf4d589ae`
- Size: `55,361,101` bytes
- Built from `0ccff82c`
- Installer metadata `1.0.58.0` / `1.0.58`; release app `1.0.58+58`
- Bundled Python `3.13.15`, 260 CHIRP driver modules, and a successful bridge
  `list-models` run with 598 models including `Wouxun_KG-UV8D`,
  `Yaesu_FT-50`, `Baofeng_K67_Pro_CPS_V1.1.2`, `Kenwood_TM-V71`, and
  `Kenwood_TM-V71_CloneMode`
- Bundled FT-50 override sets `SERIAL_STOPBITS = 2` and clears both channel
  flag tables; the bridge applies driver-level serial framing overrides
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.58`
- Authenticode: not signed

Windows `1.0.57` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.57.exe`
- Version/build: `1.0.57` / `57`
- SHA-256:
  `51626a0f30e588f2d7d49f265108a9537a3a9d75b7a4e111ccb8f44b1e5c70e8`
- Size: `55,349,277` bytes
- Built from `1d94b15f`, the same 1.0.57 source used by macOS
- Installer metadata `1.0.57.0` / `1.0.57`; release app `1.0.57+57`
- Bundled Python `3.13.15`, 258 CHIRP driver modules, and a successful bridge
  `list-models` run with 597 models including `Wouxun_KG-UV8D`,
  `Yaesu_FT-50`, and `Baofeng_K67_Pro_CPS_V1.1.2`
- Bundled FT-50 override sets `SERIAL_STOPBITS = 2`; the bridge applies
  driver-level serial framing overrides
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- Installer payload extraction confirmed the bundled runtime, driver tree,
  bridge, and PDFs; the extracted runtime reported Python `3.13.15`
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.57`
- Authenticode: not signed

Windows `1.0.56` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.56.exe`
- Version/build: `1.0.56` / `56`
- SHA-256:
  `dca65cbe04297c2adae79cf0ac2d3e5d5505aca2fa002243178399bb4399d3be`
- Size: `55,334,600` bytes
- Built from `361da9e9`
- Installer metadata `1.0.56.0` / `1.0.56`; release app `1.0.56+56`
- Bundled Python `3.13.15`, 256 CHIRP driver modules, and a successful bridge
  `list-models` run with 596 models including `Wouxun_KG-UV8D` and
  `Yaesu_FT-50`
- Bundled FT-50 override sets `SERIAL_STOPBITS = 2`; the bridge applies
  driver-level serial framing overrides
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter`/`tqdm`/`colorama` contamination
- A silent install to a temporary directory launched the bundled runtime and
  exited cleanly; the test installation was removed afterward
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.56`
- Authenticode: not signed

Windows `1.0.55` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.55.exe`
- Version/build: `1.0.55` / `55`
- SHA-256:
  `c38b7f98c3527e727d6997f62f5f16b31db0ad9241ed402cc21aa8a2098be13a`
- Size: `55,333,952` bytes
- Built from `26589b92`
- Installer metadata `1.0.55.0` / `1.0.55`; release app `1.0.55+55`
- Bundled Python `3.13.15`, 256 CHIRP driver modules, and a successful bridge
  `list-models` run with 596 models including `Wouxun_KG-UV8D`
- Bundled marine VHF, 27 MHz CB, Australian UHF CB, and GMRS/FRS
  frequency-reference PDFs
- The runtime contains only the normal pip files, with no
  `okf`/`tree_sitter` cache contamination
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.55`
- Authenticode: not signed

Windows `1.0.54` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.54.exe`
- Version/build: `1.0.54` / `54`
- SHA-256:
  `29f703b75c699ecc72499c7e6f323ef0a571438ab1dfba1b128dd87946f26422`
- Size: `55,303,832` bytes
- Built from `c55530b9`
- Installer metadata `1.0.54.0` / `1.0.54`; release app `1.0.54+54`
- Bundled Python `3.13.15`, 255 CHIRP driver modules, and a successful bridge
  `list-models` run with 596 models including `KSUN_UV-K60-Plus`,
  `Baofeng_UV-29Pro`, and `Yaesu_FT-50`
- The runtime was re-extracted from the pinned CPython archive with SHA-256
  `44bf9ae71f4b45e3ba3104ae331c6eff3f7002593c26fd12453eb9310c4f259a`;
  `python\Lib\site-packages` contains only the normal pip files, not the
  `okf`/`tree_sitter` cache contamination
- Server and public-download checksums matched the local artifact; public
  HTTP 200 and the live platform manifest reports Windows `1.0.54`
- Authenticode: not signed

macOS `1.0.54` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.54.dmg`
- Version/build: `1.0.54` / `54`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `211c9c6c93e20aee232e6f931caf92750eb667288cf5ecfd8214f008feed190e`
- Size: `86,642,668` bytes
- Built from `c55530b9`
- Notarization submission: `e19d0d70-9ace-4f97-bf70-aeb83c001174`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains Baofeng UV-29 Pro, Yaesu FT-50 odd-split, and KSUN
  UV-K60 Plus support
- Server and public-download checksums matched the final stapled DMG

macOS `1.0.53` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.53.dmg`
- Version/build: `1.0.53` / `53`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `17c3b3d3cea0611a43236470e0882919016f104a19adb997a296925beca6d233`
- Size: `82,536,313` bytes
- Built from `76fcaf93`
- Notarization submission: `a0a24eaf-72d6-4307-b14b-465817df267a`
- Gatekeeper result: accepted as Notarized Developer ID
- Bundle contains the TK-350/TK-359 KPG-23D/KPG-32D driver
- Server and public-download checksums matched the final stapled DMG

macOS `1.0.50` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.50.dmg`
- Version/build: `1.0.50` / `50`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `04c259cff3433aec572fc3313b40834530db540d74fab90eb2118945279972da`
- Size: `82,541,125` bytes
- Notarization submission: `9baa7cba-e835-447f-ae73-ea47b3943948`
- Gatekeeper result: accepted as Notarized Developer ID
- Server and public-download checksums matched the final stapled DMG

macOS `1.0.49` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.49.dmg`
- Version/build: `1.0.49` / `49`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `b94b57f1f2577fa4d032dd979d6c4e33e6487017007608d19023c54502fd0d79`
- Size: `81,438,614` bytes
- Notarization submission: `45ef102a-4597-47e5-8458-4c4605ec9dab`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum matched the final stapled DMG

macOS `1.0.48` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-1.0.48.dmg`
- Version/build: `1.0.48` / `48`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `4ef865249f0f72d7c53b8747071b05ca9463dcd0406a2e854edf0be56af279bd`
- Size: `82,507,658` bytes
- Notarization submission: `03759f9e-520c-492e-8eb6-b2677dea1c6c`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum matched the final stapled DMG

macOS `1.0.47` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-1.0.47.dmg`
- Version/build: `1.0.47` / `47`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `4a8d8f6f35533ba6824a00ccb9b0f711c5dc1b56f2d77ff4f82efc0cfbc9940a`
- Size: `82,488,386` bytes
- Notarization submission: `62383717-2440-4ac7-aea9-38fd1ef017b9`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum matched the final stapled DMG

macOS `1.0.46` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.46.dmg`
- Version/build: `1.0.46` / `46`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `572dc95bc348674533d71ffb2ef878d312a1b34b7e8ea69ce171c6912228c9ed`
- Size: `82,479,689` bytes
- Notarization submission: `07c91153-ab4d-4e3b-bdb2-153f17acf283`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum matched the final stapled DMG

macOS `1.0.45` artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.45.dmg`
- Version/build: `1.0.45` / `45`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `be6deab704e7df5383562f7dd26da45fdcf9fb9c0251489bdfd57c6ff1ba2c5c`
- Size: `82,456,304` bytes
- Notarization submission: `b22c8d76-7069-4ed1-9043-35711adfd0d3`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum recorded from the live artifact

macOS `1.0.44` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-1.0.44.dmg`
- Version/build: `1.0.44` / `44`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `367d86265534e4a6b279861e2161c9ba84ce09198dba133ce4f25e0dbb983ff8`
- Size: `82,435,001` bytes
- Notarization submission: `5492c9f7-182f-47b3-a395-9e1c6b178abf`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum recorded from the live artifact

Windows `1.0.53` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.53.exe`
- Version/build: `1.0.53` / `53`
- SHA-256:
  `cb64db20fa2a93a95d26bafaff6dd4261c9dae1e3caad5241c6176cda91baa83`
- Size: `61,530,894` bytes
- Built from `76fcaf93`
- Installer metadata `1.0.53.0` / `1.0.53`; release app `1.0.53+53`
- Bundled Python `3.13.15`, 252 CHIRP driver modules, and a successful bridge
  `list-models` run with 594 models including `Kenwood_TK-350`,
  `Kenwood_TK-359`, and `Wouxun_KG-Q10H`
- Server and public-download checksums matched the local artifact
- Authenticode: not signed

Windows `1.0.52` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.52.exe`
- Version/build: `1.0.52` / `52`
- SHA-256:
  `fa70d9830e19722bf965de87dc96df9b7e5b63e6ccf1580973583ad85a432779`
- Size: `61,514,994` bytes
- Built from `c6219ae7`
- Extracted installer verified with embedded `1.0.52` metadata, app version
  `1.0.52+52`, bundled Python `3.13.15`, 251 CHIRP driver modules, a successful
  bridge `list-models` run, and the new missing-runtime guidance
- Server and public-download checksums matched the local artifact
- Authenticode: not signed

Windows `1.0.51` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.51.exe`
- Version/build: `1.0.51` / `51`
- SHA-256:
  `de0a55ce434de48523c19cd3163f435650e412ce5c504ec03717c6216b2286c8`
- Size: `61,269,470` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.50` artifact (historical, superseded):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.50.exe`
- Version/build: `1.0.50` / `50`
- SHA-256:
  `3950843c54d40c64f7d2d1f4cbb9aa3a5fbfd7be60c2fadae546d48c015cf89e`
- Size: `61,267,947` bytes
- Built from `e7b96c44`; superseded the same day by `1.0.51` after the
  TS-2000, FTM-7250D, TSQL, mixed-DPI, and A9305B fixes landed upstream
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.49` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.49.exe`
- Version/build: `1.0.49` / `49`
- SHA-256:
  `59dae47deef1129ec096fb94c48c756a31392a48a6d48ca0ce1d8b826eb25278`
- Size: `61,269,593` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.48` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.48.exe`
- Version/build: `1.0.48` / `48`
- SHA-256:
  `5614055bf4b5efa72e65ac2fb36884690bdfa8c606a0b875d0faa718b1473939`
- Size: `61,246,193` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.47` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.47.exe`
- Version/build: `1.0.47` / `47`
- SHA-256:
  `b385cd811419b7b9998d858d3b2a4d05e01b5f3051cc52b0dee5f1c2bc0fa37b`
- Size: `61,236,623` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.46` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.46.exe`
- Version/build: `1.0.46` / `46`
- SHA-256:
  `6e9a6f649a147634d9aef033cdbc33fdd7c99219d334e29c858051a61f1a31e9`
- Size: `61,221,115` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.45` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.45.exe`
- Version/build: `1.0.45` / `45`
- SHA-256:
  `f6fdaaf75d82380d3ee86de9d6e333167de2cef1a98c2aa1f3766252cdc82b31`
- Size: `61,189,999` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.44` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.44.exe`
- Version/build: `1.0.44` / `44`
- SHA-256:
  `a90addfb67fed26ff27a846a9820884a37a4f2874f6183642003958c5df868c1`
- Size: `61,169,590` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.43` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.43.exe`
- Version/build: `1.0.43` / `43`
- SHA-256:
  `80c969b4e3a4af78d0d027cb7b6d9894474dc0b3503dec63dae9f41b693f07f5`
- Size: `61,152,977` bytes
- Server checksum matched the local artifact
- Authenticode: not signed

Windows `1.0.42` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.42.exe`
- Version/build: `1.0.42` / `42`
- SHA-256:
  `c1aaf8310f361f03fe097b0d4bef380dda830bf1454bc590c76df5b82a0e79fc`
- Size: `61,156,255` bytes
- Server checksum matched the local artifact

Windows `1.0.41` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.41.exe`
- Version/build: `1.0.41` / `41`
- SHA-256:
  `1b74852f3201216c8e5e5c8739575516fc39821742400282c4cedf8bbafc5518`
- Size: `61,150,266` bytes
- Server checksum matched the local artifact

Windows `1.0.40` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.40.exe`
- Version/build: `1.0.40` / `40`
- SHA-256:
  `16c99f969b05b742497eaf23f943a12c2384e756bf931987fed881b0544ddf90`
- Size: `61,124,631` bytes
- Server checksum matched the local artifact

Windows `1.0.39` artifact (historical):

- URL: `https://newchirp.net/downloads/NewChirp-Installer-1.0.39.exe`
- Version/build: `1.0.39` / `39`
- SHA-256:
  `b460f2e2f07ab8bd1b580e6d8c12a44e6c5d43f8c3554f855846247971d5594b`
- Size: `61,115,880` bytes
- Server checksum matched the local artifact

Linux `1.0.50` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.50.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.50.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.50.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.50.pkg.tar.zst`
- Embedded `version.json`: `1.0.50` / `50`
- Artifact source commit: `e7b96c44`
- Public HTTP checks returned `200 OK`
- `/api/releases/latest` reports Linux `1.0.50`
- Server checksums matched the local artifacts

Linux 1.0.50 SHA-256:

- DEB:
  `0cb91f5c8793575388e838d53af4fd0069c24bfafda6c368e16780cef8242d47`
- RPM:
  `ad7aff10d5158bd8922cef1129c372745ce6520d0017af9688e62e1b663dcd79`
- AppImage:
  `d81ab972a3e421fe15afd1e00ab58da77a5b081db55436398d89c3dffe8e8fc2`
- Pacman:
  `e2e24531ef12a0f8b9dbb19a47910a71192509feae90c1534b2bb868439edf5b`

Linux 1.0.50 sizes:

- DEB: `48,498,338` bytes
- RPM: `38,939,412` bytes
- AppImage: `145,183,936` bytes
- Pacman: `47,013,369` bytes

Linux `1.0.49` artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.49.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.49.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.49.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.49.pkg.tar.zst`

Linux 1.0.49 SHA-256:

- DEB:
  `535f6b06680265b90f60c35e48dd279dc1b2f0851e00900085189bcc84620878`
- RPM:
  `b9fdeb1fdf3f928a9493446951bd75de3ae8ce1e5703286f397dcb9843d55a5e`
- AppImage:
  `39b40d3705ec9e0bfd9711d86f720d57a3584ad0af37b22cc4d06e7e39bdf74f`
- Pacman:
  `7a2f43aca9a42c29e93c38acd5f8d69fc329c2eaa327b7a6e25f3a7d3a20778e`

Linux 1.0.49 sizes:

- DEB: `48,489,136` bytes
- RPM: `38,938,920` bytes
- AppImage: `145,183,936` bytes
- Pacman: `47,014,491` bytes

Linux `1.0.48` artifacts (historical):

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.48.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.48.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.48.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.48.pkg.tar.zst`
- Embedded `version.json`: `1.0.48` / `48`

Linux 1.0.48 SHA-256:

- DEB:
  `c22f56551b906675856d12391b8a04c9a870867f791ce8dbc78db7d35c69066a`
- RPM:
  `42144e1464f2a295cb99754f55cec7ed56848b1199d9b064d719bd93320e1aaa`
- AppImage:
  `aab0a4f67fc872c2cd30fc95ff31617cdf3991cd0451c9e6fa498347348d0e8f`
- Pacman:
  `8517df7914d95906fe7fc2394521828a3a255b4972469b4736cd4ed1e26845ff`

Linux 1.0.48 sizes:

- DEB: `48,478,818` bytes
- RPM: `38,919,942` bytes
- AppImage: `145,171,648` bytes
- Pacman: `46,983,837` bytes

Linux 1.0.46 and 1.0.47 artifact details were recorded by the Linux release
sessions and are not duplicated here.

Linux `1.0.45` artifacts (historical):

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.45.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.45.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.45.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.45.pkg.tar.zst`

Linux 1.0.45 SHA-256:

- DEB:
  `1695f2c890ca589943b8ecfe3efe2f7d8ab54c7352ba7642ed26b1ccab1780ee`
- RPM:
  `a3a9bb35b0abaf9a9ad93c9413c333528864bbc8b16d3455623428135b93f57e`
- AppImage:
  `ae545cb84e405230f69f97d7e3db3c26fcd74adcad323a1fa8aace6bc7d88efc`
- Pacman:
  `b65e1d82f6721a43bffcf2c31a2264fb7e8283aa488414bf14dd8aed272f5a46`

Linux 1.0.45 sizes:

- DEB: `48,453,562` bytes
- RPM: `38,895,452` bytes
- AppImage: `144,438,464` bytes
- Pacman: `46,942,112` bytes

Linux `1.0.44` artifacts (historical):

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.44.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.44.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.44.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.44.pkg.tar.zst`

Linux 1.0.44 SHA-256:

- DEB:
  `e214cbbe5c451a4d75b1f8ceedcf95d82081f522270739b8dd5b23eb70e3a17c`
- RPM:
  `9eb26a4c90e42daefee28f4821da06490dab8a7656a485b9d88f3410a9f5b8d5`
- AppImage:
  `125f26772d5e2370fb16f8b79e9fe0acd71251d06bb65ffcb4bd174d6ce10916`
- Pacman:
  `8e56e26e9fc25b648e662c1e0cab76d522274e172accff395b6ca53bdf3e2d5f`

Linux 1.0.44 sizes:

- DEB: `48,433,842` bytes
- RPM: `38,900,664` bytes
- AppImage: `144,426,176` bytes
- Pacman: `46,928,936` bytes

Linux `1.0.43` artifacts (historical):

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.43.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.43.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.43.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.43.pkg.tar.zst`

Linux 1.0.43 SHA-256:

- DEB:
  `8af61e703076544ef4f88fc40f2a605287bf66cb72669adf55df889499ac5d6c`
- RPM:
  `744f46ffe8ae202051e8ca39ab67ceee0f3b85b094cbd619c8522188cc4a4294`
- AppImage:
  `76d503c6b7a8cd316b78571cf0e3ce414bc614958f1a9b3ac5b3c8c14649ea6b`
- Pacman:
  `8377f0deb736e6948f5778edb797746bfb5b7e58b79f5e8c8f47ff4aadb9367f`

Linux 1.0.43 sizes:

- DEB: `48,429,464` bytes
- RPM: `38,897,774` bytes
- AppImage: `144,417,984` bytes
- Pacman: `46,922,621` bytes

Linux `1.0.42` artifacts (historical):

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.42.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.42.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.42.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.42.pkg.tar.zst`

Linux 1.0.42 SHA-256:

- DEB:
  `012d0c716e22eaa0c726668ddeebf2d348779764440ee870ed41874547bc5356`
- RPM:
  `0c0487b8f0ef6d6a51b1b94a44786309a070d5c3549997a80b3b33a0efc08c86`
- AppImage:
  `b62094f5f5df7833ae8b7043d37af2a8b38ffe038372f8aa2a55016ccc0a60ac`
- Pacman:
  `90bf7df07cec69f5fac33fe2438f366a9cb2730b40638dfe5ce203d12d071900`

Linux 1.0.42 sizes:

- DEB: `48,428,642` bytes
- RPM: `38,900,093` bytes
- AppImage: `144,417,984` bytes
- Pacman: `46,918,355` bytes

Linux `1.0.41` artifacts (historical):

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.41.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.41.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.41.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.41.pkg.tar.zst`

Linux 1.0.41 SHA-256:

- DEB:
  `4180a1b1a7960133b4e7cb5e83f49da0dc0f3bed2e4cef17183378f7ab7327c3`
- RPM:
  `71a4cc10351414213cf95e30be15245729500ad4b5e879d54471ab7895c7b0c9`
- AppImage:
  `3e839e0ec46938a38b224091adc8b7886833424cec5e6bc82988fa7b5ff42da5`
- Pacman:
  `260777c04470b0e022d4a606c3fe847dbc05f0096115754e90826f2968a7512c`

Linux 1.0.41 sizes:

- DEB: `48,431,176` bytes
- RPM: `38,899,633` bytes
- AppImage: `144,417,984` bytes
- Pacman: `46,918,623` bytes

## Recently completed

- Published Windows `1.0.70` from source commit `4fde327b`. The release
  preserves the active radio zone when replacing the channel list from CSV,
  the library, or a repeater search, and allows repeated radio-settings
  writes so several identical radios can be programmed in a row. It carries
  the cumulative 1.0.69 drivers, watchdog, tone, UV-5RM Plus handshake, and
  Android broken-pipe work. Verification: installer metadata `1.0.70.0` /
  `1.0.70`, release app `1.0.70+70`, in-app version string `1.0.70`,
  bundled Python `3.13.15`, zero bytecode caches, 272 CHIRP driver modules
  pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`, bridge `list-models`
  exit 0 with empty stderr, 604 models across 62 vendors, all four
  frequency-reference PDFs, matching local/server/public SHA-256
  `f6b86ac40af732f9e27a4fb6b8ce10e706e82d979e48eae5b525426626e89c5a`,
  size `51,073,329` bytes, public HTTP 200, and live manifest Windows
  `1.0.70`. `flutter analyze lib test` is clean. The full Flutter suite ran
  244 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 618 tests: 613 passed, 2 fixture-dependent
  tests skipped, and 3 known Windows temporary-file-lock helper errors. The
  installer remains unsigned.
- Published Windows `1.0.69` from source commit `5db67c3b`. The release
  adds the read-only AnyTone AT-D878UVII Plus driver, fixes AnyTone D578
  channel-bank sizing, adds the read-only Quansheng UV-K5 Robzyl RO-KO 512K
  profile, encodes Baofeng 5RX/UV-S9X3 channel power like the CPS, keeps
  unknown Baofeng power values readable, and carries the cumulative 1.0.68
  watchdog, tone, UV-5RM Plus handshake, and Android broken-pipe work.
  Verification: installer metadata `1.0.69.0` / `1.0.69`, release app
  `1.0.69+69`, in-app version string `1.0.69`, bundled Python `3.13.15`,
  zero bytecode caches, 272 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, bridge `list-models` exit 0
  with empty stderr, 604 models across 62 vendors, all four
  frequency-reference PDFs, matching local/server/public SHA-256
  `c3be7a1fefda0c883111ec730c1eaf3100771e880791a6d60a4acae2d7a2b774`,
  size `51,070,106` bytes, public HTTP 200, and live manifest Windows
  `1.0.69`. `flutter analyze lib test` is clean. The full Flutter suite ran
  244 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 618 tests: 613 passed, 2 fixture-dependent
  tests skipped, and 3 known Windows temporary-file-lock helper errors. The
  installer remains unsigned.
- Published Windows `1.0.68` from source commit `dcc91434`. The release
  adds the stalled-write diagnostic watchdog, safe reads of unreadable
  DM-32UV and RT-950 tone values, the OEM-style UV-5RM Plus handshake
  retry, Android USB broken-pipe handling, and the cumulative 1.0.67
  driver, UI, bridge, trace, printing, and write-progress work.
  Verification: installer metadata `1.0.68.0` / `1.0.68`, release app
  `1.0.68+68`, in-app version string `1.0.68`, bundled Python `3.13.15`,
  zero bytecode caches, 269 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, bridge `list-models` exit
  0 with empty stderr, 602 models across 62 vendors, all four
  frequency-reference PDFs, matching local/server/public SHA-256
  `1d9cb4b6dac537c7ac69f93c41bca3da3a4c12f935bf747870e9f232674837b8`,
  size `51,068,933` bytes, public HTTP 200, and live manifest Windows
  `1.0.68`. `flutter analyze lib test` is clean. The full Flutter suite
  ran 244 passing tests with the five known Windows-only sandbox/Help
  failures. The complete Python suite ran 605 tests: 600 passed, 2
  fixture-dependent tests skipped, and 3 known Windows
  temporary-file-lock helper errors. The installer remains unsigned.
- Published Windows `1.0.67` from source commit `8e03e24b`. The release
  carries the cumulative post-1.0.66 driver, UI, bridge, trace, printing,
  and write-progress fixes, including FTM-300DR and F4HWN 7.0, RT22,
  DM-32UV progress/cancel, UV-K60 Plus, RA87, UV-5R Mini, VX-170, TH-350,
  and no-step tuning. Verification: installer metadata `1.0.67.0` /
  `1.0.67`, release app `1.0.67+67`, in-app version string `1.0.67`,
  bundled Python `3.13.15`, zero bytecode caches, 269 CHIRP driver modules
  pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`, bridge
  `list-models` exit 0 with empty stderr, 602 models across 62 vendors,
  all four frequency-reference PDFs, matching local/server/public SHA-256
  `3786af74ed71fc00205bed0ca10cd31923fcc6609304bcab84fd70cd52c740b6`,
  size `51,066,621` bytes, public HTTP 200, and live manifest Windows
  `1.0.67`. The bundled application launch smoke test succeeded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 244
  passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 597 tests: 592 passed, 2 skipped, and 3
  known Windows temporary-file-lock helper errors. The installer remains
  unsigned. An initial build from `5dd9aa67` was replaced before recording
  because its in-app string read `1.0.69`; that artifact is quarantined on
  the server.
- Published Windows `1.0.66` from source commit `cd9ced58`. The release
  integrates the DM-32UV NUL-termination name fix, moved-channel extras
  preservation, TK-270G one-based bank positions, RT-950 Pro transmit-band
  warnings and Bluetooth reads with writes re-enabled, Windows-checkout-safe
  driver ledger paths, and the cumulative 1.0.65 RepeaterBook, IC-F50V/F60V,
  KG-689E, UI, and error-reporting work. Verification: installer metadata
  `1.0.66.0` / `1.0.66`, release app `1.0.66+66`, bundled Python `3.13.15`,
  zero bytecode caches, 265 CHIRP driver modules pinned to
  `21e42e4518c167548af90ed7f9edf75e516c491a`, bridge `list-models` exit 0
  with empty stderr, 602 models across 62 vendors including
  IC-F50V/F60V, KG-689E/KG-699E, IC-910, FT-50, RT-950 Pro, and DM-32UV,
  all four frequency-reference PDFs, matching local/server/public SHA-256
  `ededeeb1f240cf4e647dda8d3adb0146bb39f668a7f451b02004fe47417cee4e`,
  size `53,529,691` bytes, public HTTP 200, and live manifest Windows
  `1.0.66`. Installer payload extraction and runtime launch succeeded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 236 passing
  tests in the parallel run with the five known Windows-only sandbox/Help
  failures plus one diagnostic-log temp-lock failure that passed in
  isolation. The complete Python suite ran 560 tests: 555 passed, 2 skipped,
  and 3 known Windows temporary-file-lock helper errors. The installer
  remains unsigned.
- Published Windows `1.0.65` from source commit `014df59b`. The release
  integrates the approved RepeaterBook API relay, expands read-only Icom
  IC-F50V/F60V channel support, handles echoing programming cables on the
  Wouxun KG-689E, and carries the related UI and error-reporting fixes.
  Verification: installer metadata `1.0.65.0` / `1.0.65`, release app
  `1.0.65+65`, bundled Python `3.13.15`, zero bytecode caches, 265 CHIRP
  driver modules pinned to `21e42e4518c167548af90ed7f9edf75e516c491a`,
  bridge `list-models` exit 0 with 602 models including IC-F50V/F60V,
  KG-689E/KG-699E, IC-910, and FT-50, all four frequency-reference PDFs,
  matching local/server/public SHA-256
  `6aa267b209a53877b8ef82eb9b3fecaa9d08761ec5e10b2cbd5f2fd901362151`,
  size `53,527,982` bytes, public HTTP 200, and live manifest Windows
  `1.0.65`. Installer payload extraction and runtime launch succeeded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 233 passing
  tests in the parallel run with the five known Windows-only sandbox/Help
  failures plus one diagnostic-log temp-lock failure that passed in
  isolation. The complete Python suite ran 550 tests: 544 passed, 2 skipped,
  3 known Windows temporary-file-lock helper errors, and 1 Windows-only
  path-separator assertion. The installer remains unsigned.
- Published Windows `1.0.64` from source commit `83a592ae`. The release
  integrates the approved RepeaterBook API relay, adds read-only Icom
  IC-F50V/F60V channel support, handles echoing programming cables on the
  Wouxun KG-689E, and carries the cumulative cross-mode, unloadable-settings,
  live-band, fixed-zone-write, and mapping-preservation fixes.
  Verification: installer metadata `1.0.64.0` / `1.0.64`, release app
  `1.0.64+64`, bundled Python `3.13.15`, clean runtime, 265 CHIRP driver
  modules, bridge `list-models` exit 0 with 602 models including
  IC-F50V/F60V, KG-689E/KG-699E, IC-910, and FT-50, all four
  frequency-reference PDFs, matching local/server/public SHA-256, public HTTP
  200, and live manifest Windows `1.0.64`. Installer payload extraction and
  runtime launch succeeded. `flutter analyze lib test` is clean. The full
  Flutter suite ran 234 passing tests with the five known Windows-only
  sandbox/Help failures. The complete Python suite ran 550 tests: 544 passed,
  2 skipped, 3 known Windows temporary-file-lock helper errors, and 1
  Windows-only path-separator assertion. The installer remains unsigned.
- Published Windows `1.0.63` from source commit `f550ae84`. The release adds
  the read-only Icom IC-F50V/F60V capture profile, fixed-zone write handling
  after channel moves, radio-mapping preservation during remaps, blank
  cross-mode fixes, preservation of settings the current CHIRP build cannot
  load, and live band switching.
  Verification: installer metadata `1.0.63.0` / `1.0.63`, release app
  `1.0.63+63`, bundled Python `3.13.15`, clean runtime, 265 CHIRP driver
  modules, bridge `list-models` exit 0 with 601 models including KG-689E,
  KG-699E, IC-910, IC-F50V/F60V, and FT-50, all four frequency-reference
  PDFs, matching local/server/public SHA-256, public HTTP 200, and live
  manifest Windows `1.0.63`. Installer payload extraction and runtime launch
  succeeded. `flutter analyze lib test` is clean. The full Flutter suite ran
  234 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 543 tests: 537 passed, 2 skipped, 3 known
  Windows temporary-file-lock helper errors, and 1 Windows-only
  path-separator assertion. The installer remains unsigned.
- Published Windows `1.0.62` from source commit `d9b31864`. The release adds
  the OEM-CPS-derived Wouxun KG-689E/KG-699E driver, the Icom CI-V unset-tone
  compatibility fix, TK-270G and 5RH Pro fixes, UV-5RM Plus v2 and F4HWN
  image handling, the read-only Icom IC-F50V/F60V capture profile, and
  fixed-zone write handling after channel moves.
  Verification: installer metadata `1.0.62.0` / `1.0.62`, release app
  `1.0.62+62`, bundled Python `3.13.15`, clean runtime, 265 CHIRP driver
  modules, bridge `list-models` exit 0 with 601 models including KG-689E,
  KG-699E, IC-910, IC-F50V/F60V, and FT-50, all four frequency-reference
  PDFs, matching local/server/public SHA-256, public HTTP 200, and live
  manifest Windows `1.0.62`. Installer payload extraction and runtime launch
  succeeded. `flutter analyze lib test` is clean. The full Flutter suite ran
  232 passing tests with the five known Windows-only sandbox/Help failures.
  The complete Python suite ran 540 tests: 534 passed, 2 skipped, 3 known
  Windows temporary-file-lock helper errors, and 1 Windows-only
  path-separator assertion. The installer remains unsigned.
- Published macOS `1.0.62` from source commit `89b4876e` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. Its application payload
  is runtime-identical to the final 1.0.62 boundary `0d09b292`, whose only
  later change is an Ubuntu ledger-test adjustment. It carries the
  KG-689E/KG-699E driver, Icom CI-V unset-tone handling, promoted FT-50
  support, and current TK-270G and 5RH Pro fixes.
  Verification: analyzer clean; 235 Flutter tests; 536 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.62` / `62`;
  both Python architectures at `3.13.15`; 264 CHIRP driver modules; 600
  catalog models including KG-689E, KG-699E, IC-910, and FT-50; strict app
  and DMG signatures; Apple notarization ID
  `8fed5c04-70ea-4d77-b69c-b36b9340ea38`; staple, Gatekeeper, mounted-DMG,
  launch-smoke, server/public-download, and checksum checks passed. The live
  macOS manifest reports `1.0.62`.
- Published Windows `1.0.61` from source commit `0e701b16`. The release adds
  the OEM-CPS-derived Wouxun KG-689E/KG-699E driver, the Icom CI-V unset-tone
  compatibility fix, promoted FT-50 support after hardware confirmation, and
  the latest TK-270G and 5RH Pro zone-flag fixes.
  Verification: installer metadata `1.0.61.0` / `1.0.61`, release app
  `1.0.61+61`, bundled Python `3.13.15`, clean runtime, 264 CHIRP driver
  modules, bridge `list-models` exit 0 with 600 models including KG-689E,
  KG-699E, IC-910, and FT-50, all four frequency-reference PDFs, matching
  local/server/public SHA-256, public HTTP 200, and live manifest Windows
  `1.0.61`. Installer payload extraction and runtime launch succeeded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 230 passing
  tests with the five known Windows-only sandbox/Help failures. The complete
  Python suite ran 536 tests: 530 passed, 2 skipped, 3 known Windows
  temporary-file-lock helper errors, and 1 Windows-only path-separator
  assertion. The installer remains unsigned.
- Published macOS `1.0.61` from source commit `0e701b16` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the
  OEM-CPS-derived Wouxun KG-689E/KG-699E driver, the Icom CI-V unset-tone
  compatibility fix, promoted FT-50 support after hardware confirmation, and
  the latest TK-270G and 5RH Pro zone-flag fixes.
  Verification: analyzer clean; 235 Flutter tests; 536 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.61` / `61`;
  both Python architectures at `3.13.15`; 264 CHIRP driver modules; 600
  catalog models including KG-689E, KG-699E, IC-910, and FT-50; strict app
  and DMG signatures; Apple notarization ID
  `6c290229-c679-465a-9d0b-0ab077ba1799`; staple, Gatekeeper, mounted-DMG,
  launch-smoke, server/public-download, and checksum checks passed. The live
  macOS manifest reports `1.0.61`.
- Published Windows `1.0.60` from source commit `488564b4`. The release adds
  read-only zone display for fixed-zone radios including the BF-F8HP-PRO and
  carries the RT-950 Pro web flow-control fix plus the current DR-735,
  RT-950 Pro, official-name, CSV import, select-all, CTCSS, safety, and
  bug-report work. Verification: installer metadata `1.0.60.0` / `1.0.60`,
  release app `1.0.60+60`, bundled Python `3.13.15`, clean runtime, 262 CHIRP
  driver modules, bridge `list-models` exit 0 with 598 models including
  `Baofeng_BF-F8HP-PRO`, `Alinco_DR735T`, and `Radtel_RT-950_Pro`, ten
  read-only BF-F8HP-PRO zones spanning channels 1-100 and onward, all four
  frequency-reference PDFs, matching local/server/public SHA-256, public HTTP
  200, and live manifest Windows `1.0.60`. Installer payload extraction and
  runtime launch succeeded. `flutter analyze lib test` is clean. The full
  Flutter suite ran 230 passing tests with the five known Windows-only
  sandbox/Help failures. The complete Python suite ran 508 tests: 503 passed,
  2 fixture-dependent tests skipped, and 3 Windows temporary-file-lock helper
  errors. The installer remains unsigned. macOS was at `1.0.60`; Linux was at
  `1.0.60`.
- Published macOS `1.0.60` from source commit `488564b4` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds fixed-zone
  display for radios such as the BF-F8HP-PRO, the Alinco DR-735 rebuild,
  RT-950 Pro CPS 1.3.3 support, and the current official-name, CSV import,
  select-all, CTCSS, safety, and bug-report fixes.
  Verification: analyzer clean; 235 Flutter tests; 508 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.60` / `60`;
  both Python architectures at `3.13.15`; 262 CHIRP driver modules; 598
  catalog models including BF-F8HP-PRO, RT-950 Pro, and DR-735; strict app
  and DMG signatures; Apple notarization ID
  `87136c3e-df9d-43bf-8a77-07a1246e1f66`; staple, Gatekeeper, mounted-DMG,
  launch-smoke, server/public-download, and checksum checks passed. The live
  macOS manifest reports `1.0.60`.
- Published Windows `1.0.59` from source commit `170c63f3`. The release adds
  the OEM-rebuilt Alinco DR-735 driver, RT-950 Pro writes from Radtel Pro CPS
  1.3.3, read-only warnings before writes, official manufacturer model names,
  common-encoding CSV imports with channel select-all, and fractional CTCSS
  handling for the UV-17ProGPS family. It also carries the RT97L analysis and
  bug-report upload/decode fixes. Verification: installer metadata
  `1.0.59.0` / `1.0.59`, release app `1.0.59+59`, bundled Python `3.13.15`,
  clean runtime, 261 CHIRP driver modules, bridge `list-models` exit 0 with
  598 models including `Alinco_DR735T`, `Radtel_RT-950_Pro`,
  `Wouxun_KG-UV8D`, `Yaesu_FT-50`, `Baofeng_K67_Pro_CPS_V1.1.2`, and
  `Kenwood_TM-V71`, all four frequency-reference PDFs, matching
  local/server/public SHA-256, public HTTP 200, and live manifest Windows
  `1.0.59`. Installer payload extraction and runtime launch succeeded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 230 passing
  tests with the five known Windows-only sandbox/Help failures. The complete
  Python suite ran 506 tests: 501 passed, 2 fixture-dependent tests skipped,
  and 3 Windows temporary-file-lock helper errors. The installer remains
  unsigned. macOS was at `1.0.59`; Linux was at `1.0.60`.
- Published macOS `1.0.59` from source commit `170c63f3` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the rebuilt
  Alinco DR-735 driver, RT-950 Pro CPS 1.3.3 read/write support, clearer
  read-only-driver messaging, official model names, encoding-tolerant CSV
  import, channel select-all, and fractional UV-17ProGPS CTCSS preservation.
  Verification: analyzer clean; 235 Flutter tests; 506 Python tests with two
  fixture-dependent skips; 68 bridge tests; embedded version `1.0.59` / `59`;
  both Python architectures at `3.13.15`; 261 CHIRP driver modules; 598
  catalog models including DR-735, RT-950 Pro, TM-V71, and FT-50; strict app
  and DMG signatures; Apple notarization ID
  `31e8f183-0412-4c69-aab4-4d7cfbc39b77`; staple, Gatekeeper, mounted-DMG,
  launch-smoke, server/public-download, and checksum checks passed. The live
  macOS manifest reports `1.0.59`.
- Published Windows `1.0.58` from source commit `0ccff82c`. The release adds
  the Kenwood TM-V71 clone-mode driver, Kenwood live-write cache fixes, FT-50
  channel clearing in both flag tables, refreshed OKF bundles, and ignore
  rules for installer/mobile package files. Verification: installer metadata
  `1.0.58.0` / `1.0.58`, release app `1.0.58+58`, bundled Python `3.13.15`,
  clean runtime, 260 CHIRP driver modules, bridge `list-models` exit 0 with
  598 models including `Wouxun_KG-UV8D`, `Yaesu_FT-50`,
  `Baofeng_K67_Pro_CPS_V1.1.2`, `Kenwood_TM-V71`, and
  `Kenwood_TM-V71_CloneMode`, FT-50 stop-bit override and dual flag-table
  clearing present, all four frequency-reference PDFs, matching
  local/server/public SHA-256, public HTTP 200, and live platform manifest
  Windows `1.0.58`. Installer payload extraction and runtime launch succeeded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 222 passing
  tests with the five known Windows-only sandbox/Help failures. The complete
  Python suite ran 478 tests: 473 passed, 2 fixture-dependent tests skipped,
  and 3 Windows temporary-file-lock helper errors. The installer remains
  unsigned. macOS was at `1.0.57`; Linux was at `1.0.58`.
- Published macOS `1.0.58` from source commit `0ccff82c` as a universal,
  signed, notarized, stapled, Gatekeeper-accepted DMG. It adds the
  read-only Kenwood TM-V71A/E clone driver and Kenwood live-write fix,
  clears FT-50 channels in both flag tables, preserves FTM7250 capabilities
  while clearing removed channels, and carries the latest driver diagnostics.
  Verification: analyzer clean; 227 Flutter tests; 478 Python tests with two
  fixture-dependent skips; 66 bridge tests; embedded version `1.0.58` / `58`;
  both Python architectures at `3.13.15`; 260 CHIRP driver modules; 598
  catalog models including TM-V71 clone mode and FT-50; strict app and DMG
  signatures; Apple notarization ID
  `678ebc18-dd9a-442f-a351-a78e8507e2a1`; staple, Gatekeeper, mounted-DMG,
  launch-smoke, public-download, and checksum checks passed. The live macOS
  manifest reports `1.0.58`.
- Published Windows `1.0.57` from source commit `1d94b15f`, the same source
  used by the macOS 1.0.57 release. It adds the experimental Baofeng K67 Pro
  driver, TK-270G bank-sentinel normalization, late TK-350 identity retries,
  corrected Australian CB references, reported-driver fixes, and the
  private-reporter-data guard. Verification: installer metadata `1.0.57.0` /
  `1.0.57`, release app `1.0.57+57`, bundled Python `3.13.15`, clean runtime,
  258 CHIRP driver modules, bridge `list-models` exit 0 with 597 models
  including `Wouxun_KG-UV8D`, `Yaesu_FT-50`, and
  `Baofeng_K67_Pro_CPS_V1.1.2`, FT-50 stop-bit override present, all four
  frequency-reference PDFs, matching local/server/public SHA-256, public HTTP
  200, and live platform manifest Windows `1.0.57`. Installer payload
  extraction and runtime launch succeeded. `flutter analyze lib test` is
  clean. The full Flutter suite ran 221 passing tests with the five known
  Windows-only sandbox/Help failures. The complete Python suite ran 456
  tests: 451 passed, 2 fixture-dependent tests skipped, and 3 Windows
  temporary-file-lock helper errors. The installer remains unsigned. macOS
  was also at `1.0.57`; Linux was at `1.0.58`.
- Published Windows `1.0.56` from source commit `361da9e9`. The release adds
  the OEM-verified Yaesu FT-50 serial framing override at 9600 8N2 and carries
  the KG-UV8D reserved-DCS, nicFW950 no-tone, and GMRS starter-bandwidth work.
  Verification: installer metadata `1.0.56.0` / `1.0.56`, release app
  `1.0.56+56`, bundled Python `3.13.15`, clean runtime, 256 CHIRP driver
  modules, bridge `list-models` exit 0 with 596 models including
  `Wouxun_KG-UV8D` and `Yaesu_FT-50`, FT-50 stop-bit override present, all
  four frequency-reference PDFs, matching local/server/public SHA-256, public
  HTTP 200, and live platform manifest Windows `1.0.56`. A silent temporary
  install launched the bundled runtime and was removed. `flutter analyze lib
  test` is clean. The full Flutter suite ran 221 passing tests with the five
  known Windows-only sandbox/Help failures. The complete Python suite ran 433
  tests: 428 passed, 2 fixture-dependent tests skipped, and 3 Windows
  temporary-file-lock helper errors. The installer remains unsigned. At
  Windows release time, macOS and Linux were also at `1.0.56`.
- Published Windows `1.0.55` from source commit `26589b92`. The release adds
  per-column filters, bank boundaries, safer channel-location handling,
  expanded frequency references and PDFs, KG-UV8D reserved-DCS compatibility,
  nicFW950 no-tone decoding, and GMRS starter bandwidth corrections.
  Verification: installer metadata `1.0.55.0` / `1.0.55`, release app
  `1.0.55+55`, bundled Python `3.13.15`, clean runtime, 256 CHIRP driver
  modules, bridge `list-models` exit 0 with 596 models including
  `Wouxun_KG-UV8D`, matching local/server/public SHA-256, public HTTP 200,
  and live platform manifest Windows `1.0.55`. `flutter analyze lib test` is
  clean. The full Flutter suite ran 221 passing tests with the five known
  Windows-only sandbox/Help failures. The complete Python suite ran 432
  tests: 427 passed, 2 fixture-dependent tests skipped, and 3 Windows
  temporary-file-lock helper errors. The installer remains unsigned. At
  Windows release time, macOS remained at `1.0.54` and Linux was at `1.0.55`.
- Completed the remaining radio usability requests except the external
  RepeaterBook API blocker. Channel search now supports per-column filters and
  exact frequency matching, radio bank membership is visible in the channel
  grid with bank-scoped empty-slot insertion, and the frequency reference adds
  International Marine VHF, 27 MHz CB, and Australian UHF CB plans with matching
  printable PDFs and documented regulatory sources.
- Published Windows `1.0.54` from source commit `c55530b9`. The release adds
  the read-only experimental KSUN UV-K60 Plus driver derived from the MH-580
  OEM programmer, the Baofeng UV-29 Pro compatibility profile, Yaesu FT-50
  odd-split decoding, platform-specific update-manifest checks, and upload
  validation hardening. Verification: installer metadata `1.0.54.0` /
  `1.0.54`, release app `1.0.54+54`, bundled Python `3.13.15`, 255 bundled
  CHIRP driver modules, bridge `list-models` exit 0 with 596 models, matching
  local/server/public SHA-256, public HTTP 200, and live platform manifest
  Windows `1.0.54`. The clean runtime was re-extracted from the pinned
  CPython archive after a contaminated build cache was discarded.
  `flutter analyze lib test` is clean. The full Flutter suite ran 213 passing
  tests with the five known Windows-only sandbox/Help failures. The complete
  Python suite ran 423 tests: 418 passed, 2 fixture-dependent tests skipped,
  and 3 Windows temporary-file-lock helper errors. The installer remains
  unsigned. At Windows release time, macOS had also advanced to `1.0.54` and
  Linux remained at `1.0.51`.
- Published macOS `1.0.54` from source commit `c55530b9` as a universal,
  signed, notarized, stapled DMG. The release includes the Baofeng UV-29 Pro
  UV-28 Plus compatibility alias, Yaesu FT-50 odd-split decoding, read-only
  KSUN UV-K60 Plus support, TD-H8 upload safeguards, and the latest radio
  catalog. Verification: app/build version `1.0.54` / `54`; universal
  `arm64` and `x86_64`; Python 3.13.15 arm64 and x86_64 runtimes; pinned
  CHIRP commit `21e42e45`; 255 bundled driver modules; 596 selectable models;
  423 Python tests with two fixture-dependent skips; 218 Flutter tests;
  `flutter analyze` clean; notarization accepted; staple and DMG integrity
  checks passed; mounted-DMG signature, Gatekeeper, driver inspection, and
  launch smoke test passed; local, server, and public SHA-256 matched.
- Published macOS `1.0.53` from source commit `76fcaf93` as a universal,
  signed, notarized, stapled DMG. This is the first macOS desktop release with
  the read-only experimental Kenwood TK-350 and TK-359 drivers. It also carries
  the Baofeng 5 Mini profile-selection guidance and the detailed KG-Q10H
  family identity mismatch output. Verification: app/build version
  `1.0.53` / `53`; universal `arm64` and `x86_64`; both Python 3.13.15
  runtimes; pinned CHIRP tree; bundled TK-350/TK-359 driver; 409 Python tests
  with two fixture-dependent skips; 62 bridge tests; 219 Flutter tests;
  `flutter analyze` clean; strict codesigning; notarization accepted; staple
  and DMG integrity checks passed; mounted-DMG version, signature, Gatekeeper,
  and driver inspection passed; launch smoke test passed; local, server, and
  public SHA-256 matched.
- Published Windows `1.0.53` from source commit `76fcaf93`. The release adds
  read-only experimental Kenwood TK-350/KPG-23D and TK-359/KPG-32D support,
  clarifies the Baofeng Mini radio profiles, and reports Wouxun identity
  mismatches with more useful detail. Verification: installer metadata
  `1.0.53.0` / `1.0.53`, release app `1.0.53+53`, bundled Python `3.13.15`,
  252 CHIRP driver modules, bridge `list-models` exit 0 with 594 models,
  matching local/server/public SHA-256, public HTTP 200, and live platform
  manifest Windows `1.0.53`. `flutter analyze lib test` is clean. The full
  Flutter suite ran 214 passing tests with the five known Windows-only
  sandbox/Help failures. The complete Python suite ran 409 tests: 406 passed,
  2 fixture-dependent tests skipped, and 3 Windows temporary-file-lock helper
  errors. The installer remains unsigned. At Windows release time, macOS and
  Linux remained at `1.0.50`.
- Published Windows `1.0.52` from source commit `c6219ae7`. The release makes a
  missing, damaged, or blocked bundled Python runtime fail with an explicit
  reinstall message instead of silently falling back to the Microsoft Store
  `python` aliases referenced by UID 609. Verification: extracted installer
  metadata `1.0.52` / `1.0.52+52`, bundled Python `3.13.15`, 251 bundled CHIRP
  driver modules, bridge `list-models` exit 0, release binary contains the new
  Store-alias guidance, matching local/server/public SHA-256, public HTTP 200,
  and live platform manifest Windows `1.0.52`. `flutter analyze lib test` is
  clean. The full Flutter suite ran 213 passing tests with the five known
  Windows-only sandbox/Help failures; the Python bridge suite ran 61 passing
  tests with one Windows temporary-file-lock helper error. The installer
  remains unsigned. macOS and Linux remain at `1.0.50`.
- Published Windows `1.0.51` from source commit `6c02787e`. Verified installer
  file/product metadata `1.0.51.0` / `1.0.51`, app version `1.0.51+51`,
  bundled Python `3.13.15`, the bundled `scripts/chirp_bridge.py` asset and
  driver set including the updated TS-2000, FTM-7250D, and MA1-A9305B
  drivers, matching local/server/public SHA-256, and the live platform
  manifest. The release carries the TS-2000 slow-read allowance, FTM-7250D
  power fix with problem reporting, corrected A9305B power and bandwidth
  decoding, shared CTCSS tone display for TSQL, mixed-DPI window restoration
  guard, and the Linux module-sandbox diagnostics. TS-2000, FTM-7250D, and
  MA1-A9305B suites passed 24 tests; the full Flutter suite ran 210 passing
  tests with the five known Windows sandbox/Help failures; `flutter analyze`
  reported only three pre-existing `avoid_print` infos in `build_support`.
  The installer remains unsigned. Windows `1.0.50` was published earlier the
  same day from `e7b96c44` and superseded by `1.0.51` once those fixes landed
  upstream; Linux and macOS remain at `1.0.50`.
- Published macOS `1.0.50` from source commit `23931970` as a universal,
  signed, notarized, stapled DMG. The release includes the TS-2000 delayed
  read fix, FTM-7250D power correction, mixed-DPI window recovery, consistent
  TSQL presentation, corrected A9305B power and bandwidth decoding, and the
  Linux module-sandbox diagnostic update. App/build version `1.0.50` / `50`,
  both Python 3.13.15 runtimes, universal libusb, the pinned CHIRP tree, and
  the updated bundled drivers were verified. `flutter analyze`, all 215
  Flutter tests, and all 62 bridge upload tests passed. Strict codesigning,
  Apple notarization, stapling, mounted-DMG inspection, Gatekeeper, launch
  smoke test, local/server/public SHA-256, public HTTP, and the live macOS
  manifest entry all passed.
- Published Windows `1.0.49` from source commit `d4b20d0a`. Verified installer
  file/product metadata `1.0.49.0` / `1.0.49`, app version `1.0.49+49`,
  bundled Python `3.13.15`, the bundled RT-950 Pro, FT-991A, FTX-1,
  MA1-A9305B, GS-5B, BF-V12D, and TD-H8 G4 drivers plus the bundled
  `scripts/chirp_bridge.py` asset, matching local/server/public SHA-256, and
  the live platform manifest. The release carries the marine VHF template
  plans, the RT-950 Pro read driver, FT-991A CAT support, the FTX-1 selection
  fix, and the cached bundled-helper loader that keeps radio writes working if
  the installed helper file disappears mid-session. RT-950 Pro, FT-991A,
  FTX-1, and MA1-A9305B suites passed 28 tests; the new marine, model-picker,
  dialog, and asset-cache Flutter tests passed 15; the full Flutter suite ran
  201 passing tests with the five known Windows sandbox/Help failures;
  `flutter analyze` reported only three pre-existing `avoid_print` infos in
  `build_support`. The installer remains unsigned. Linux `1.0.49` artifacts
  are live.
- Published macOS `1.0.49` from source commit `d4b20d0a` as a universal,
  signed, notarized, stapled DMG. The release adds Marine VHF templates,
  separate RT-950 and RT-950 Pro models, the Pro read-only CPS transport,
  channel validation/clearing improvements, and radio-helper asset recovery.
  App/build version `1.0.49` / `49`, both Python 3.13.15 runtimes, universal
  libusb, and the pinned CHIRP tree were verified. Strict codesigning, Apple
  notarization, stapling, mounted-DMG inspection, Gatekeeper, launch smoke
  test, local/server SHA-256, public HTTP, and the live macOS manifest entry
  all passed.
- Published macOS `1.0.48` from source commit `11053cfd` as a universal,
  signed, notarized, stapled DMG. The release adds firmware identities to
  desktop bug reports and decodes UV-K5 hello frames before a radio image is
  available. App/build version `1.0.48` / `48`, both Python 3.13.15 runtimes,
  universal libusb, and the pinned CHIRP tree were verified. Strict
  codesigning, Apple notarization, stapling, mounted-DMG inspection,
  Gatekeeper, launch smoke test, local/server SHA-256, public HTTP, and the
  live macOS manifest entry all passed.
- Published Windows `1.0.48` from source commit `11053cfd`. Verified installer
  file/product metadata `1.0.48.0` / `1.0.48`, app version `1.0.48+48`,
  bundled Python `3.13.15`, the bundled GS-5B 1.XX, BF-V12D, and TD-H8 G4
  drivers, matching local/server SHA-256, public HTTP 200, and the live
  platform manifest. GS-5B, BF-V12D, experimental serial, and UVK5 suites
  passed 28 tests; Flutter ran 192 passing tests with the five known Windows
  sandbox/Help failures; `flutter analyze` reported only three pre-existing
  `avoid_print` infos in `build_support`. The installer remains unsigned.
  macOS, Linux, and the legacy shared manifest also report `1.0.48`; those
  artifacts were published by their native release sessions.
- Published Windows `1.0.47` from source commit `19dcd4c1`. Verified installer
  file/product metadata `1.0.47.0` / `1.0.47`, app version `1.0.47+47`,
  bundled Python `3.13.15`, the bundled BQ-889 probe and corrected X1 Pro
  driver, matching local/server SHA-256, public HTTP 200, and the live
  platform manifest. BQ-889, X1 Pro, and bridge suites passed 77 tests with
  one known Windows temporary-file `PermissionError`; Flutter ran 190 passing
  tests with the five known Windows sandbox/Help failures; `flutter analyze`
  reported only three pre-existing `avoid_print` infos in `build_support`.
  The installer remains unsigned.
- Published macOS `1.0.47` from source commit `19dcd4c1` as a universal,
  signed, notarized, stapled DMG. The release carries the CPS-aligned X1 Pro
  tone write order, the BQ-889 read-only probe, channel name validation and
  bulk clearing, write-review guidance, and ZIP-code RepeaterBook searches.
  App/build version `1.0.47` / `47`, both Python 3.13.15 runtimes, universal
  libusb, and the pinned CHIRP tree were verified. Strict codesigning, Apple
  notarization, stapling, mounted-DMG inspection, Gatekeeper, launch smoke
  test, local/server SHA-256, public HTTP, and the live macOS manifest entry
  all passed.
- Published macOS `1.0.46` from source commit `e4d4db35` as a universal,
  signed, notarized, stapled DMG. The release carries the CPS-derived
  DB25-G, X1 Pro, GA-510 V2, and retry-safe IC-E90 drivers plus
  hardware-tested MXT295 support. App/build version `1.0.46` / `46`, both
  Python 3.13.15 runtimes, universal libusb, and the pinned CHIRP tree were
  verified. Strict codesigning, Apple notarization, stapling, mounted-DMG
  inspection, Gatekeeper, local/server/public SHA-256, launch smoke test,
  and the live macOS manifest entry all passed.
- Published Windows `1.0.46` from source commit `e4d4db35`. Verified installer
  file/product metadata `1.0.46.0` / `1.0.46`, app version `1.0.46+46`,
  bundled Python `3.13.15`, the bundled DB25-G, X1 Pro, GA-510 V2,
  retry-safe IC-E90, and hardware-tested MXT295 drivers, matching
  local/server SHA-256, public HTTP 200, and the Windows platform manifest
  entry. DB25-G, X1 Pro, GA-510 V2, IC-E90, and MXT295 focused suites passed
  54 tests with one fixture-dependent skip; Flutter ran 184 passing tests
  with the five known Windows sandbox/Help failures; `flutter analyze`
  reported only three pre-existing `avoid_print` infos in `build_support`.
  The installer remains unsigned.
- Published macOS `1.0.45` from source commit `4ca2a6f9` as a universal
  signed, notarized, stapled DMG. The release carries the CPS-derived Retevis
  RA89 driver, app/build version `1.0.45` / `45`, both Python 3.13.15 runtime
  trees, universal libusb, and the pinned CHIRP tree. Strict codesigning,
  Apple notarization, stapling, mounted-DMG inspection, Gatekeeper, local and
  server SHA-256, public HTTP, and the live macOS manifest entry all verified.
- Published Windows `1.0.45` from source commit `4ca2a6f9`. Verified installer
  file/product metadata `1.0.45.0` / `1.0.45`, app version `1.0.45+45`,
  bundled Python `3.13.15`, the bundled RA89 and safe TK-270G drivers,
  matching local/server SHA-256, public HTTP 200, and the live platform
  manifest. RA89 and TK-270G focused suites passed 12 tests; Flutter ran 183
  passing tests with the five known Windows sandbox/Help failures;
  `flutter analyze` reported only three pre-existing `avoid_print` infos in
  `build_support`. The installer remains unsigned.
- Published Linux `1.0.45` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `4ca2a6f9`. Verified the
  incoming RA89 and TK-270G driver safety surface, `flutter analyze`,
  74 focused Python RA89/TK-270G/5RH Pro/bridge tests, embedded
  `version.json`, DEB/RPM/Pacman metadata, package payloads, extracted
  AppImage payload including the RA89 and TK-270G drivers, bundled
  Python/CHIRP runtime and `libusb-1.0.so.0`, absence of GLib 2.80
  once-init pointer symbols, matching server checksums, public HTTP 200
  checks, and the live platform manifest.
- Published Linux `1.0.44` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `ec059527`. Verified the
  incoming Baofeng 5RH Pro v2 driver safety surface, `flutter analyze`,
  62 focused Python bridge/5RH Pro tests, embedded `version.json`,
  DEB/RPM/Pacman metadata, package payloads, extracted AppImage payload
  including the Baofeng 5RH Pro v2 driver, bundled Python/CHIRP runtime and
  `libusb-1.0.so.0`, absence of GLib 2.80 once-init pointer symbols,
  matching server checksums, public HTTP 200 checks, and the live platform
  manifest.
- Published Windows `1.0.44` from source commit `9929f997`. Verified installer
  file/product metadata `1.0.44.0` / `1.0.44`, app version `1.0.44+44`,
  bundled Python `3.13.15`, the bundled CPS-derived Baofeng 5RH Pro v2
  driver, matching local/server SHA-256, public HTTP 200, and the Windows
  platform manifest entry. The new 5RH Pro driver suite passed 5 tests; the
  bridge suite ran 57 tests with one known Windows temporary-file
  `PermissionError`; Flutter ran 183 passing tests with the five known
  Windows sandbox/Help failures; `flutter analyze` reported only three
  pre-existing `avoid_print` infos in `build_support`. The installer remains
  unsigned.
- Published macOS `1.0.44` from source commit `9929f997` as a universal
  signed, notarized, stapled DMG. Verified the CPS-derived Baofeng 5RH Pro
  v2 driver and legacy-model recovery guidance, app/build version, both
  Python runtimes, universal libusb, strict signatures, Gatekeeper
  acceptance, the notarization ticket, matching local/server checksums,
  public HTTP availability, and the live platform manifest.
- Published Windows `1.0.43` from source commit `f37f138b`. Verified installer
  file/product metadata `1.0.43.0` / `1.0.43`, app version `1.0.43+43`,
  bundled Python `3.13.15`, matching local/server SHA-256, public HTTP 200,
  and the live platform manifest. The focused bridge suite ran 56 tests with
  one known Windows temporary-file `PermissionError`; Flutter ran 183 passing
  tests with the five known Windows sandbox/Help failures; `flutter analyze`
  reported only three pre-existing `avoid_print` infos in `build_support`.
  The installer remains unsigned.
- Published macOS `1.0.43` from source commit `f37f138b` as a universal
  signed, notarized, stapled DMG. Verified the TK-7160K subdevice metadata fix,
  BF-F8HP Pro selected-port guidance, app/build version, both Python runtimes,
  universal libusb, strict signatures, Gatekeeper acceptance, the
  notarization ticket, matching local/server checksums, public HTTP
  availability, and the live platform manifest.
- Published Linux `1.0.43` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `747afb48`. Verified
  `flutter analyze`, 60 focused Python bridge/UV handshake tests, embedded
  `version.json`, DEB/RPM/Pacman metadata, package payloads, extracted
  AppImage payload including the UV-5RH retry override, bundled Python/CHIRP
  runtime and `libusb-1.0.so.0`, matching server checksums, public HTTP 200
  checks, and the live platform manifest.
- Published Windows `1.0.42` from source commit `d98b660b`. Verified installer
  file/product metadata `1.0.42.0` / `1.0.42`, app version `1.0.42+42`, the
  four focused UV-5RH handshake tests, bundled Python `3.13.15`, matching
  server SHA-256, public HTTP 200, and the live platform manifest. Flutter ran
  183 passing tests with five known Windows sandbox/Help failures; the Python
  suite ran 303 tests with three Windows temporary-file permission errors and
  two fixture-dependent skips. The installer remains unsigned.
- Published macOS `1.0.42` from source commit `d98b660b` as a universal
  signed, notarized, stapled DMG. Verified the UV-5RH startup-handshake retry,
  app/build version, both Python runtimes, universal libusb, strict
  signatures, Gatekeeper acceptance, the notarization ticket, matching
  local/server checksums, public HTTP availability, and the per-platform live
  manifest.
- Published Linux `1.0.42` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `ccc98fd5`. This supersedes the
  same-day Linux `1.0.41` files without overwriting them because the first
  Linux `1.0.41` build had correct package metadata but was built before the
  app's in-code version constant was updated. Verified embedded
  `version.json`, DEB/RPM/Pacman metadata, package payloads, extracted
  AppImage payload, bundled Python/CHIRP runtime and `libusb-1.0.so.0`,
  absence of GLib 2.80 once-init pointer symbols, server checksums, public
  HTTP 200 checks, and the live platform manifest.
- Published Windows `1.0.41` from source commit `4fc6177f`. Verified installer
  file/product metadata `1.0.41.0` / `1.0.41`, app version `1.0.41+41`,
  focused Python driver suites (47 tests), myGMRS Flutter tests, the bundled
  KG-Q10H and RT-860 payloads, matching local/server SHA-256, public HTTP 200,
  and the live platform manifest.
- Published Linux `1.0.41` from source commit `4fc6177f` with DEB, RPM,
  AppImage, and Pacman `.pkg.tar.zst` artifacts. Verified package metadata,
  embedded `version.json`, driver payloads, live checksums and sizes, public
  downloads, and the platform manifest.
- Published macOS `1.0.41` from source commit `4fc6177f` as a universal
  signed, notarized, stapled DMG. Verified app/build version, the KSUN
  UV-K60 and read-only RT-860 driver payloads, both Python runtimes, universal
  libusb, strict signatures, Gatekeeper acceptance, the notarization ticket,
  matching local/server checksums, public HTTP availability, and the live
  platform manifest.
- Published macOS `1.0.40` from source commit `8fdcef21` as a universal
  signed, notarized, stapled DMG. Verified the official-CPS-derived Wouxun
  KG-905G Plus driver, app/build version, both Python runtimes, universal
  libusb, strict signatures, Gatekeeper acceptance, notarization ticket,
  public checksum, HTTP availability, and the per-platform live manifest.
- Published Linux `1.0.40` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `8fdcef21`. Verified
  `flutter analyze`, 186 Flutter tests, 265 Python tests with 2
  fixture-dependent skips, embedded `version.json`, DEB/RPM/Pacman metadata,
  package payloads, extracted AppImage payload, bundled Python/CHIRP runtime
  and `libusb-1.0.so.0`, absence of GLib 2.80 once-init pointer symbols,
  server checksums, public HTTP 200 checks, and live platform manifest.
- Published macOS `1.0.39` from source commit `91ac1711` as a universal
  signed, notarized, stapled DMG. Verified the A9305B CPS-aligned
  read-checksum correction, app/build version, arm64 and x86_64 Python
  runtimes, universal libusb, strict signatures, Gatekeeper acceptance,
  notarization ticket, public checksum, HTTP availability, and the
  per-platform live manifest.
- Published Linux `1.0.39` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `e515bc4b`. Verified
  `flutter analyze`, 184 Flutter tests, 248 Python tests with 2
  fixture-dependent skips, embedded `version.json`, DEB/RPM/Pacman metadata,
  package payloads, extracted AppImage payload, bundled Python/CHIRP runtime
  and `libusb-1.0.so.0`, absence of GLib 2.80 once-init pointer symbols,
  server checksums, public HTTP 200 checks, and live platform manifest.
- Published macOS `1.0.38` from source commit `10bafaeb` as a universal
  signed, notarized, stapled DMG. Verified myGMRS OAuth and ZIP-radius search
  tests, app/build version, arm64 and x86_64 Python runtimes, universal libusb,
  strict signatures, Gatekeeper acceptance, notarization ticket, server
  checksum, public download, and the per-platform live manifest.
- Published macOS `1.0.37` as a universal signed, notarized, stapled DMG.
  Verified the CPS-backed RT-950 authentication, flow-control, decryption,
  and block-timeout correction; app/build version; arm64 and x86_64 Python
  runtimes; universal libusb; strict signatures; Gatekeeper acceptance;
  notarization ticket; server checksum; public download; and live manifest.
- Published Linux `1.0.37` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `5a5e79a9`. Verified
  `flutter analyze`, the full Flutter test suite, RT-950 driver tests,
  bridge upload tests, embedded `version.json`, package metadata, bundled
  Python/CHIRP runtime and `libusb-1.0.so.0`, absence of GLib 2.80
  once-init pointer symbols, server checksums, public HTTP 200 checks, and
  live platform manifest.
- Published macOS `1.0.36` as a universal signed, notarized, stapled DMG.
  Verified the UV-5RM Plus handshake retry and diagnostic trace, app/build
  version, arm64 and x86_64 Python runtimes, universal libusb, strict code
  signatures, Gatekeeper acceptance, notarization ticket, server checksum,
  public download, and live platform manifest.
- Published macOS `1.0.35` as a universal signed, notarized, stapled DMG.
  Verified the app/build version, TH-9800 and VX-6 compatibility drivers,
  headless-module error handling, live-radio catalog filtering, arm64 and
  x86_64 Python runtimes, universal libusb, strict code signatures,
  Gatekeeper acceptance, notarization ticket, server checksum, public
  download, and live platform manifest.
- Published Linux `1.0.36` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `32fbc464`. Verified
  `flutter analyze`, the full Flutter test suite, UV-5RM Plus handshake
  retry tests, bridge upload tests, embedded `version.json`, package
  metadata, bundled Python/CHIRP runtime and `libusb-1.0.so.0`, absence of
  GLib 2.80 once-init pointer symbols, server checksums, public HTTP 200
  checks, and live platform manifest.
- Published macOS `1.0.33` as a universal signed, notarized, stapled DMG.
  Verified the app/build version, Icom ID-50 channel-field decoder, arm64 and
  x86_64 Python runtimes, universal libusb loading under both architectures,
  strict code signatures, Gatekeeper acceptance, notarization ticket, server
  checksum, public download, and live platform manifest.
- Published Linux `1.0.35` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `b39df094`. Verified
  `flutter analyze`, the full Flutter test suite, embedded `version.json`,
  package metadata, bundled Python/CHIRP runtime and `libusb-1.0.so.0`,
  absence of GLib 2.80 once-init pointer symbols, server checksums, public
  HTTP 200 checks, and live platform manifest.
- Published Linux `1.0.32` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts. Fixed the Debian 12/MX Linux startup failure
  reported as `undefined symbol: g_once_init_enter_pointer` by compiling
  the Linux runner and plugin targets with `GLIB_VERSION_MAX_ALLOWED` and
  `GLIB_VERSION_MIN_REQUIRED` capped at GLib 2.74. Verified the embedded
  `version.json`, package metadata, bundled `libusb-1.0.so.0` and USB DFU
  helper, absence of GLib 2.80 once-init pointer symbols, server checksums,
  public HTTP 200 checks, and live platform manifest.
- Published Linux `1.0.31` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts from source commit `604dbbf2`. Verified the
  embedded `version.json`, package metadata, bundled `libusb-1.0.so.0` and
  USB DFU helper, server checksums, public HTTP 200 checks, and live platform
  manifest.
- Published Linux `1.0.30` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts. Verified the embedded `version.json`,
  package metadata, bundled `libusb-1.0.so.0` and USB DFU helper, server
  checksums, public HTTP 200 checks, and live platform manifest.
- Fixed Linux runtime bundling so the packaged desktop bundle includes the
  system `libusb-1.0.so.0` shared library needed by USB DFU radios.
- Published macOS `1.0.30` as a universal signed, notarized, stapled DMG.
  Verified the app/build version, new experimental drivers, arm64 and x86_64
  Python runtimes, universal libusb loading under both architectures, strict
  code signatures, Gatekeeper acceptance, notarization ticket, server
  checksum, public download, and live platform manifest.
- Added experimental offline-tested read/write drivers for Yaesu FTX-1,
  TYT MD-UV380, and AnyTone AT-D578UVIII Plus. FTX-1 uses documented live CAT
  memory commands; AnyTone uses its CPS 1.21 serial codeplug protocol; and
  MD-UV380 uses a new libusb DfuSe transport. Complete images and zone records
  are preserved, while contacts, scan lists, optional signalling, and
  radio-wide settings remain untouched. All three require physical-radio
  validation before release-status claims.
- Added experimental read-only Kenwood TK-3401D support from KPG-171D
  reverse-engineering evidence. The driver identifies the radio, reads the
  addressed 64 KiB image, retains the full image even when layout inference
  fails, discovers provisional PMR446 channel records, and blocks writes until
  the physical codeplug layout is validated.
- Expanded the physical Icom ID-50/ID-52 parser after Nick Hale's 1.0.32
  retest. The 500-channel read-only parser now decodes FM, AM, DV, names,
  offsets, duplex direction, CTCSS, tuning step, output level, scan skip, and
  D-STAR calls without the former invalid-mode failure. It also uses the
  radio's channel-availability table so retained factory records in unused
  slots are reported as empty. Writes remain disabled until DTCS,
  reverse/cross tones, and the remaining channel flags are validated.
- Published Linux `1.0.29` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts. Verified the embedded `version.json`,
  package metadata, server checksums, public HTTP 200 checks, and live
  platform manifest.
- Published Linux `1.0.28` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts. Verified the embedded `version.json`,
  package metadata, server checksums, public HTTP 200 checks, and live
  platform manifest.
- Published macOS `1.0.28` as a universal signed, notarized, stapled DMG.
  Verified the embedded version, saved-radio restoration flow, Python
  runtimes, CHIRP pin, IC-E90 and IC-41S driver bundles, strict code
  signatures, Gatekeeper assessment, server checksum, and live platform
  manifest.
- Published macOS `1.0.27` as a universal signed, notarized, stapled DMG.
  Verified the embedded version, Python runtimes, CHIRP pin, IC-E90 and
  IC-41S driver bundles, strict code signatures, Gatekeeper assessment, server
  checksum, and live platform manifest.
- Published macOS `1.0.26` as a universal signed, notarized, stapled DMG.
  Verified the embedded version, Python runtimes, CHIRP pin, IC-41S driver
  bundle, strict code signatures, Gatekeeper assessment, server checksum, and
  live platform manifest.
- Published macOS `1.0.25` as a universal signed, notarized, stapled DMG.
  Verified the embedded version, Python runtimes, CHIRP pin, new handshake
  overrides, strict code signatures, Gatekeeper assessment, server checksum,
  and live platform manifest.
- Published macOS `1.0.24` as a universal signed, notarized, stapled DMG.
  Verified the embedded version, Python runtimes, CHIRP pin, TS-2000 override,
  strict code signatures, Gatekeeper assessment, server checksum, and live
  platform manifest.
- Published Linux `1.0.26` with DEB, RPM, AppImage, and Pacman
  `.pkg.tar.zst` artifacts. The Pacman package targets Arch/Omarchy and
  declares `libglvnd` and `mesa` dependencies for OpenGL runtime support.
- Verified Linux `1.0.26` with `flutter analyze`, `flutter test` (147 tests),
  package metadata checks, matching server hashes, public HTTP 200 checks, and
  container launch smoke tests for DEB on Ubuntu, AppImage on Ubuntu, RPM on
  Fedora, and Pacman on Arch.
- Fixed the live Linux downloads page so AppImage and Pacman are separate
  rows. The Pacman row is labeled Arch/Omarchy/Manjaro and includes the
  copyable `sudo pacman -U` install command.
- Fixed the AppImage builder to bundle architecture-specific Mesa software
  rasterizer drivers from Debian/Ubuntu library paths.
- Native CHIRP image import for `.img`, `.icf`, `.itm`, and `.d72`.
- Radio-aware channel slots and table sorting by memory location.
- Drag-and-drop channel rearrangement through occupied radio memory slots.
- Standard DTCS fallback codes when radio metadata is unavailable.
- TD-H3 uploads now use one clone handshake instead of probing and then
  handshaking again.
- TK-880 channel operations use CHIRP subdevices/zones.
- Multi-zone selector with real zone names and channel counts.
- Added a generic CHIRP banks/zones editor with rename, channel membership,
  and spare-zone creation. DM-32UV offline image tests cover multi-zone
  membership; physical zone write validation is still pending.
- Zone switching reloads from the saved parent image and preserves other zones
  during upload.
- Radio prompt HTML is stripped and driver "click OK" text is rewritten to the
  actual NewChirp button label.
- Searchable abbreviation glossary and channel-header tooltips.
- Update downloads are restricted to exact HTTPS URLs on `newchirp.net`.
- The startup and Help-menu update checks now offer an in-app download and
  install flow. macOS verifies the replacement app before relaunching;
  Windows requires a valid Authenticode signature; Linux hands the downloaded
  package to the native package manager.
- Added read-only MOTOTRBO CPS2 Zone XML import for conventional analog and
  DMR channels.
- Added persistent empty-slot visibility, placement-aware channel insertion,
  and direct drag or menu movement between radio memory slots.
- Bundled Linux and Windows Python runtime hashes are pinned in build scripts.
- CHIRP `.py` and `.mod` driver modules can be loaded from
  **Load CHIRP driver module…** in the top action bar for the current session.
- Loaded modules can add or override radio drivers; the radio catalog refreshes
  after loading and unloading.
- User-loaded CHIRP modules run behind a macOS Seatbelt or Linux bubblewrap
  sandbox; Windows refuses module loading until it can provide an equivalent
  sandbox.
- CHIRP release downloads are pinned to one commit and verified by SHA-256.
- FT-60 reads now tell the user to hold PTT only after the serial port is open,
  with read-specific recovery guidance if the initial frame times out.
- RepeaterBook search supports amateur and GMRS results, optional proximity
  filtering, city/county sorting, local result filtering, an interactive map,
  multi-select, and insertion into the current library.
- Radio model selection now supports type-ahead filtering by manufacturer or
  model, compact queries such as `uv5r`, keyboard selection, and bounded result
  rendering for the growing catalog.
- Added experimental read-only Radtel RT-950 and Connect Systems CS750 support,
  plus reusable raw SCSI/RAP transport for compatible radios.
- Added experimental read-only Retevis RT97L support with 16-channel parsing,
  CTCSS/DCS decoding, and hardware-safe upload blocking.
- Added an experimental Baofeng GM-32 profile derived from the official
  UV-32 CPS, including DTR/RTS handling, ten bank-name records, GMRS channel
  rules, and physical read/write evidence.
- Added an experimental Midland MXT295 driver with physical read/write
  evidence, Midland channel numbering, and Radio & Modes settings.
- Fixed TS-2000 uploads that exceeded the stock one-second command timeout.
- TS-2000 settings requests now stop with a clear unsupported message instead
  of downloading all channels and failing in `get_settings()`.
- Radio bridge failures now include a bounded communication trace with the
  failed command, memory location, timing, result, and detected radio ID while
  omitting channel contents.
- Kept the channel-table vertical scrollbar pinned to the visible right edge
  while the columns scroll horizontally.
- Added CHIRP module sandboxing, pinned CHIRP source downloads, a file-save
  warning that distinguishes files from radio writes, and Channel Library
  Discard/Write controls tied to the stored radio image.

## macOS 1.0.49 verification status

Full verification before and after the macOS `1.0.49` release:

- `flutter analyze`: clean
- `flutter test`: all 206 tests passed
- Python test discovery: 394 tests passed, 2 fixture-dependent tests skipped
- Focused bridge upload suite: 62 tests passed
- Release source commit: `d4b20d0a`
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.49` / `49`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled RT-950 Pro driver SHA-256:
  `6f1be304873772878378ea6fbcc5761881ec5b88fa71fa406aa5e6b318c5ae94`
- Bundled CHIRP bridge SHA-256:
  `ce86a6d850b4d19205a4c1b6b0aeae6b541da977a990718b02d6ccec32ffb1bc`
- DMG SHA-256:
  `b94b57f1f2577fa4d032dd979d6c4e33e6487017007608d19023c54502fd0d79`
- Notarization submission: `45ef102a-4597-47e5-8458-4c4605ec9dab`
- Strict codesigning, Apple stapling validation, Gatekeeper, mounted-DMG
  inspection, launch smoke test, local/server SHA-256, public HTTP, and the
  live macOS manifest entry passed
- `/api/releases/latest` reports macOS `1.0.49`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.48 verification status

Full verification before and after the macOS `1.0.48` release:

- `flutter analyze`: clean
- `flutter test`: all 197 tests passed
- Python test discovery: 381 tests passed, 2 fixture-dependent tests skipped
- Release source commit: `11053cfd`
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.48` / `48`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled BF-V12D driver SHA-256:
  `2adc7e1e35ccb597e5b8ad0580393c3dd9915eebc60794c4953b5ef381bcb93d`
- Bundled UV-K5 override SHA-256:
  `ef1a5561b2bc2e64b8273faec2db8510d5ca29434a9ffce6f44547d59d7cb83a`
- Bundled CHIRP bridge SHA-256:
  `ce86a6d850b4d19205a4c1b6b0aeae6b541da977a990718b02d6ccec32ffb1bc`
- DMG SHA-256:
  `4ef865249f0f72d7c53b8747071b05ca9463dcd0406a2e854edf0be56af279bd`
- Notarization submission: `03759f9e-520c-492e-8eb6-b2677dea1c6c`
- Strict codesigning, Apple stapling validation, Gatekeeper, mounted-DMG
  inspection, launch smoke test, local/server SHA-256, public HTTP, and the
  live macOS manifest entry passed
- `/api/releases/latest` reports macOS `1.0.48`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.47 verification status

Full verification before and after the macOS `1.0.47` release:

- `flutter analyze`: clean
- `flutter test`: all 195 tests passed
- Python test discovery: 362 tests passed, 2 fixture-dependent tests skipped
- Release source commit: `19dcd4c1`
- Release app: universal, signed, notarized, stapled, Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.47` / `47`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled X1 Pro driver SHA-256:
  `4e262b160e698b957b480cacc9df9ac9fa999a1cf429773b70f2e8b516090dd2`
- Bundled BQ-889 probe SHA-256:
  `9e8d50ba78673e295025a84163eeddbbed03f80ec11d4b1b91791650160fd9ae`
- Bundled CHIRP bridge SHA-256:
  `2f83c9ce1d726522ecd1e2ac4865a85d385068d14bf41f5c5961dff5a873d714`
- DMG SHA-256:
  `4a8d8f6f35533ba6824a00ccb9b0f711c5dc1b56f2d77ff4f82efc0cfbc9940a`
- Notarization submission: `62383717-2440-4ac7-aea9-38fd1ef017b9`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.47`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.46 verification status

Full verification before and after the macOS `1.0.46` release:

- `flutter analyze`: clean
- `flutter test`: all 189 tests passed
- Python test discovery: 352 tests passed, 2 fixture-dependent tests skipped
- Standalone CHIRP bridge upload suite: all 57 tests passed
- Release source commit: `e4d4db35`
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.46` / `46`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled X1 Pro driver SHA-256:
  `2ae43ec7302890808f3402f717409eb735bfa23fac77021176bd90849a9d09aa`
- Bundled GA-510 V2 driver SHA-256:
  `397dd55f847983c64cfdc91cb5200d00e20e85b49df62beb09d630aed836bc88`
- Bundled CHIRP bridge SHA-256:
  `905f53f26564e966fd4f7da97ac23672cf5436339c244b6fb345f899712c8fe7`
- DMG SHA-256:
  `572dc95bc348674533d71ffb2ef878d312a1b34b7e8ea69ce171c6912228c9ed`
- Notarization submission: `07c91153-ab4d-4e3b-bdb2-153f17acf283`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.46`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.45 verification status

Full verification before and after the macOS `1.0.45` release:

- `flutter analyze`: clean
- `flutter test`: all 188 tests passed
- Python test discovery: 321 tests passed, 2 fixture-dependent tests skipped
- Standalone CHIRP bridge upload suite: all 57 tests passed
- Release source commit: `4ca2a6f9`
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.45` / `45`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled RA89 driver SHA-256:
  `1df11114ceedcc3c12c1fff1dc088f57e051c61a97e4b12a8d2ca08fafee49cf`
- Bundled CHIRP bridge SHA-256:
  `6433b39508c7e60c6d34711f5e144a46e454d787b15f64c2e5152e1168c59f93`
- DMG SHA-256:
  `be6deab704e7df5383562f7dd26da45fdcf9fb9c0251489bdfd57c6ff1ba2c5c`
- Notarization submission: `b22c8d76-7069-4ed1-9043-35711adfd0d3`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.45`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.44 verification status

Full verification before the macOS `1.0.44` release:

- `flutter analyze`: clean
- `flutter test`: all 188 tests passed
- Python test discovery: 310 tests passed, 2 fixture-dependent tests skipped
- Standalone CHIRP bridge upload suite: all 57 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.44` / `44`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled 5RH Pro v2 driver SHA-256:
  `b9e74ca2e6d367ca205bae3dbac83f641745185157ff32b5efe413307198e10d`
- Bundled CHIRP bridge SHA-256:
  `6433b39508c7e60c6d34711f5e144a46e454d787b15f64c2e5152e1168c59f93`
- Notarization submission: `5492c9f7-182f-47b3-a395-9e1c6b178abf`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.44`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.43 verification status

Full verification before the macOS `1.0.43` release:

- `flutter analyze`: clean
- `flutter test`: all 188 tests passed
- Python test discovery: 304 tests passed, 2 fixture-dependent tests skipped
- Standalone CHIRP bridge upload suite: all 56 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.43` / `43`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled CHIRP bridge SHA-256:
  `0e4db47c304c6ff8b2239f8bf06e4f751ba9f3148bb87920cc115a4d98cb341d`
- Notarization submission: `56f61681-8605-4919-b38a-00c4d3a1ce33`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.43`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.42 verification status

Full verification before the macOS `1.0.42` release:

- `flutter analyze`: clean
- `flutter test`: all 188 tests passed
- Python test discovery: 303 tests passed, 2 fixture-dependent tests skipped
- Standalone CHIRP bridge upload suite: all 55 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.42` / `42`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled UV-17-family handshake driver SHA-256:
  `bba33277d9d64e7c7079507742d97372ccc42332d11c9ead7571b3a0584eb33a`
- Bundled RT-860 driver SHA-256:
  `394c978f4cd62276567fdcb5b21535a2276b7910afea7d0fe5f1b19f7a3f2698`
- Notarization submission: `9696ab38-f44e-482e-b7a5-8bad69be0106`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.42`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.41 verification status

Full verification before the macOS `1.0.41` release:

- `flutter analyze`: clean
- `flutter test`: all 188 tests passed
- Python test discovery: 302 tests passed, 2 fixture-dependent tests skipped
- Standalone CHIRP bridge upload suite: all 55 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.41` / `41`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled RT-860 driver SHA-256:
  `394c978f4cd62276567fdcb5b21535a2276b7910afea7d0fe5f1b19f7a3f2698`
- Bundled UV-K5-family driver SHA-256:
  `ef1a5561b2bc2e64b8273faec2db8510d5ca29434a9ffce6f44547d59d7cb83a`
- Notarization submission: `a69a7f58-069d-42e1-b8c5-afc45baae284`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.41`
- The documented separate raw-SCSI helper remains `arm64`-only.

## macOS 1.0.40 verification status

Full verification before the macOS `1.0.40` release:

- `flutter analyze`: clean
- `flutter test`: all 186 tests passed
- Python test discovery: 265 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.40` / `40`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled KG-905G Plus driver SHA-256:
  `fc4748422a39080c1cee91a253b2a9fe505c4ec63ad0c284938248428f5833a8`
- Notarization submission: `a387d9c2-2953-4383-9612-c370f1c08d8f`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.40`

## macOS 1.0.39 verification status

Full verification before the macOS `1.0.39` release:

- `flutter analyze`: clean
- `flutter test`: all 186 tests passed
- Python test discovery: 254 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.39` / `39`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled A9305B driver SHA-256:
  `efecd7c568f2d162905943e5751eb85a71d875c5b83de07c56cc15c4aff39a85`
- Notarization submission: `4444b0b0-908d-415c-a39e-c1e4617776de`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.39`

## macOS 1.0.38 verification status

Full verification before the macOS `1.0.38` release:

- `flutter analyze`: clean
- `flutter test`: all 183 tests passed
- Python test discovery: 248 tests passed, 2 fixture-dependent tests skipped
- myGMRS relay and desktop session/ZIP-search regression tests passed
- Website forum tests and production build passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.38` / `38`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `4349ae6a-3551-46f9-aa5b-33eab8f006f0`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.38`

## macOS 1.0.37 verification status

Full verification before the macOS `1.0.37` release:

- `flutter analyze`: clean
- `flutter test`: all 178 tests passed
- Python test discovery: 237 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.37` / `37`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `9bd8af3a-c8f0-4193-ac9a-7cfa2827bcdf`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.37`

## macOS 1.0.36 verification status

Full verification before the macOS `1.0.36` release:

- `flutter analyze`: clean
- `flutter test`: all 178 tests passed
- Python test discovery: 237 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.36` / `36`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `6ba8d659-3351-4e90-8825-57835834986d`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.36`

## macOS 1.0.35 verification status

Full verification before the macOS `1.0.35` release:

- `flutter analyze`: clean
- `flutter test`: all 178 tests passed
- Python test discovery: 234 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.35` / `35`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `f5d6e76f-b1dc-49b4-8353-793f8e134f01`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.35`

## macOS 1.0.34 verification status

Full verification before the macOS `1.0.34` release:

- `flutter analyze`: clean
- `flutter test`: all 178 tests passed
- Python test discovery: 224 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.34` / `34`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `65193466-7a9e-4ecf-b4d6-9ea05cefebd2`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.34`

## macOS 1.0.33 verification status

Full verification before the macOS `1.0.33` release:

- `flutter analyze`: clean
- `flutter test`: all 176 tests passed
- Python test discovery: 223 tests passed, 2 fixture-dependent tests skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.33` / `33`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `8d8471ef-eac5-4043-a0fa-4ffdd0aa7b4c`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.33`

## macOS 1.0.31 verification status

Full verification before the macOS `1.0.31` release:

- `dart format`: clean
- `flutter analyze`: clean
- `flutter test`: all 176 tests passed
- Python test discovery: 222 tests passed, 2 fixture-dependent tests skipped
- Website build: passed
- Web Programmer tests: 85 passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.31` / `31`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb bundled for `arm64` and `x86_64`
- Bundled experimental Retevis MA1 A9305B driver SHA-256:
  `730a984d6484dbd85a10c2d9937c750bc1fcb4a2348a7055b58b6cb7341d1fe7`
- Bundled experimental Icom IC-746PRO driver SHA-256:
  `f62e16b6849565bc9283c076a3b1927420123a7c286722d35c91ba211dc736b4`
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `54b5031a-850d-4e8e-a8c1-1cea2e6852a8`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.31`

## macOS 1.0.30 verification status

Full verification before the macOS `1.0.30` release:

- `flutter analyze`: clean
- `flutter test`: all 176 tests passed
- Python test discovery: 186 tests passed, 2 fixture-dependent tests skipped
- Bridge upload/settings suite: all 46 tests passed
- Web Programmer suite: all 84 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.30` / `30`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Universal libusb `1.0.30` bundled and loaded successfully under both
  architectures
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Notarization submission: `ff724cda-5fa6-4267-af71-8e0fcd0ac353`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.30`

## macOS 1.0.29 verification status

Full verification before the macOS `1.0.29` release:

- `flutter analyze`: clean
- `flutter test`: all 176 tests passed
- Python test discovery: 170 tests passed, 2 fixture-dependent tests skipped
- Bridge upload/settings suite: all 46 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.29` / `29`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled IC-E90 completion override SHA-256:
  `2d78ec1f745d424b09b6cdd7d8d832f5af4ea27cd5015a2415118007331256ac`
- Bundled experimental IC-41S driver SHA-256:
  `5f884d58a8bd3dea5d5d8dc4da2137877f5eff9b2d6b97c110851ad4d4dd247c`
- Notarization submission: `ba8ac2b9-6e32-4d43-a8a4-2808d45b9d99`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.29`

## macOS 1.0.28 verification status

Full verification before the macOS `1.0.28` release:

- `flutter analyze`: clean
- `flutter test`: all 175 tests passed
- Python test discovery: 167 tests passed, 2 fixture-dependent tests skipped
- Bridge upload/settings suite: all 43 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.28` / `28`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled IC-E90 completion override SHA-256:
  `2d78ec1f745d424b09b6cdd7d8d832f5af4ea27cd5015a2415118007331256ac`
- Bundled experimental IC-41S driver SHA-256:
  `5f884d58a8bd3dea5d5d8dc4da2137877f5eff9b2d6b97c110851ad4d4dd247c`
- Notarization submission: `36380271-5ee2-4299-89fe-e6ce5c5d976f`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.28`

## macOS 1.0.27 verification status

Full verification before the macOS `1.0.27` release:

- `flutter analyze`: clean
- `flutter test`: all 173 tests passed
- Python test discovery: 167 tests passed, 2 fixture-dependent tests skipped
- Bridge upload/settings suite: all 43 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.27` / `27`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Bundled IC-E90 completion override SHA-256:
  `2d78ec1f745d424b09b6cdd7d8d832f5af4ea27cd5015a2415118007331256ac`
- Bundled experimental IC-41S driver SHA-256:
  `5f884d58a8bd3dea5d5d8dc4da2137877f5eff9b2d6b97c110851ad4d4dd247c`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.27`

## macOS 1.0.24 verification status

Full verification before the macOS `1.0.24` release:

- `flutter analyze`: clean
- `flutter test`: all 135 tests passed
- Python test discovery: 75 tests passed, 2 fixture-dependent tests skipped
- Bridge upload/settings suite: all 14 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.24` / `24`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.24`

## macOS 1.0.23 verification status

Full verification before the macOS `1.0.23` release:

- `flutter analyze`: clean
- `flutter test`: all 132 tests passed
- Python test discovery: all 70 tests passed, 2 skipped
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.23` / `23`
- Main executable architectures: `arm64` and `x86_64`
- Bundled Python: `3.13.15` for both architectures
- Bundled CHIRP commit:
  `21e42e4518c167548af90ed7f9edf75e516c491a`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.23`

## Linux 1.0.17 verification status

Full verification before the Linux `1.0.17` release:

- `flutter analyze`: clean
- `flutter test`: all 70 tests passed
- `python3 test/chirp_bridge_upload_test.py -v`: all 6 tests passed
- `flutter build linux --release`: succeeded
- `scripts/bundle_linux_runtime.sh`: succeeded
- `scripts/build_linux_deb.sh`: built
  `build/NewChirp-linux-x64-1.0.17.deb`
- Server packaging built and published DEB, RPM, and AppImage artifacts
- Public download URLs returned HTTP 200
- `/api/releases/latest` reports Linux `1.0.17`

## Known limitations and follow-ups

- Confirm the FT-60 manual-read sequence on physical hardware. The fix waits
  to tell the user to hold PTT until after the serial port is open.
- TK-880 multi-zone support still needs a report from a physical five-zone
  radio. The automated test uses CHIRP's `Kenwood_TK-880.img`.
- TD-H3 upload uses a protocol-level fake serial test. Physical hardware
  confirmation is still desirable.
- Building a repeater list without radio metadata uses the standard CTCSS and
  DTCS tables, so the TX/RX tone selectors remain usable before a radio image
  is loaded.
- CHIRP drivers can expose additional subdevice types beyond the zones handled
  for the TK-880.
- CHIRP modules run in a sandbox that blocks the home folder, other drives,
  and the network. A module can still use the selected radio and this
  session's files, and a bad module can still damage the radio. Windows
  refuses to load a module until a real Windows sandbox exists. Linux needs
  bubblewrap (`bwrap`). Modules that need packages NewChirp does not bundle
  may fail to import.
- The macOS raw SCSI helper for experimental mass-storage radios is currently
  compiled for Apple Silicon only; live CS750 reads on Intel Macs still need a
  universal or x86_64 helper build and hardware validation.
- The experimental Retevis RT97L channel map and serial handshake still need a
  physical read and comparison against an official CPS export before uploads
  can be enabled.
- Forum like counts and website-side ranking are a separate website project,
  not part of this Flutter repository.
- The direct updater is first shipped in 1.0.23 and has automated coverage.
  Exercise the full in-app update path from 1.0.26 to 1.0.27.
- The roadmap in `docs/SOFTWARE_ROADMAP.md` is older than this handoff and
  contains stale release-status items. Update it when doing broader roadmap
  maintenance.

## Resume checklist

1. Run `git status --short --branch`.
2. Run `git fetch origin` and inspect any new commits before editing.
3. Preserve the untracked T-shirt image and any other unrelated user files.
4. Run `flutter analyze`.
5. Run `flutter test`.
6. Run `python3 test/chirp_bridge_upload_test.py -v`.
7. Run `./scripts/update_okf.sh` after changing `lib/` or `scripts/`.

## macOS release checklist

Only build and publish the macOS artifact from this Mac.

1. Confirm the requested version and update both `pubspec.yaml` and
   `_newChirpVersion` in `lib/main.dart`.
2. Run the verification commands above.
3. Commit and push before producing the artifact.
4. Run `flutter build macos --release`.
5. Verify version, build number, Python runtime, and CHIRP tree in the app.
6. Run `bash scripts/sign_macos_release.sh`.
7. Build the DMG with `scripts/build_macos_dmg.py`.
8. Sign the DMG with the Developer ID Application identity.
9. Submit with `xcrun notarytool submit --keychain-profile newchirp --wait`.
10. Staple and validate the ticket.
11. Mount the DMG and verify:
    - `CFBundleShortVersionString`
    - `CFBundleVersion`
    - strict `codesign`
    - Gatekeeper `spctl`
12. Upload to `/opt/newchirp/public/downloads/NewChirp-<version>.dmg`.
13. Compare the local and server SHA-256 checksums.
14. Verify the platform entry in `/api/releases/latest`.

Do not wait for or trigger Windows or Linux builds from this host. Each
platform is built and published on its native machine.
