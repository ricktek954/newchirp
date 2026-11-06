# NewChirp Project State

Last updated: 2026-11-06

This is the short operational handoff for restarting work with no conversation
history. `README.md` and `AGENTS.md` remain authoritative for build rules and
release requirements.

## Resume here

- UID 464 reported that `Quansheng_UV-K1` rejected an `F4HWN v6.3.0`
  handshake on Linux. The current UV-K1 profile supports only stock 7.03.x and
  the official Quansheng CPS is also stock-only. NewChirp now routes a
  manually selected UV-K1 to an experimental F4HWN 6.3 profile with the
  firmware's 1,024-channel `0xB190` memory map, 128-byte transfers, and a
  write ceiling of `0xA178` so calibration is preserved. Offline protocol
  coverage uses the reporter's exact hello frame. Physical read/write and
  read-back validation are still pending.
- Verification for the F4HWN 6.3 profile: the complete Python suite ran 278
  tests with 2 fixture-dependent skips, `flutter analyze` is clean, and all
  186 Flutter tests pass.
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
- The Windows `1.0.40` installer is live from source commit `8fdcef21`.
  It adds the CPS-derived Wouxun KG-905G Plus driver and keeps multi-row channel
  editing, the A9305B read checksum correction, UV-5G Mini simplex support,
  TD-H8 Gen 4 read-only identity support, myGMRS ZIP-radius search, and Windows
  serial diagnostics. The versioned installer is
  `NewChirp-Installer-1.0.40.exe`, SHA-256
  `16c99f969b05b742497eaf23f943a12c2384e756bf931987fed881b0544ddf90`,
  size `61,124,631` bytes.
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
- The Linux `1.0.40` DEB, RPM, AppImage, and Pacman artifacts are live from
  source commit `8fdcef21`. This release includes the experimental Wouxun
  KG-905G Plus driver, multi-row channel copy/cut/paste and bulk properties
  editing, the A9305B read checksum correction, UV-5G Mini simplex channels
  15-22, and TD-H8 Gen 4 read-only identity support.
- Linux `1.0.40` verification: quick safety scan of the new KG-905G driver and
  tests found no process execution, network, environment, or arbitrary
  filesystem access; `flutter analyze` is clean; all 186 Flutter tests pass;
  all 265 Python tests pass with 2 fixture-dependent skips; embedded
  `version.json`, package metadata, package payloads, extracted AppImage
  payload, bundled Python/CHIRP runtime, bundled `libusb-1.0.so.0`, absence of
  GLib 2.80 once-init pointer symbols, server checksums, public HTTP 200
  checks, and the live platform manifest were verified.
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
- The macOS `1.0.40` release is live. It adds the official-CPS-derived Wouxun
  KG-905G Plus driver with all 400 channels and retains the A9305B,
  multi-row editing, UV-5G Mini, and myGMRS fixes from `1.0.39`.
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
  by Linux `1.0.40`. The `1.0.37` release was built from `5a5e79a9` and
  included the RT-950 transport correction while keeping the GLib 2.74 API cap
  so Debian 12/MX Linux systems do not fail at startup with missing
  `g_once_init_enter_pointer` / `g_once_init_leave_pointer` symbols.
- The live downloads page shows separate Linux rows for DEB, RPM, AppImage,
  and Pacman. Keep Pacman labeled for Arch/Omarchy/Manjaro and keep the
  copyable `sudo pacman -U ~/Downloads/NewChirp-linux-x64-<version>.pkg.tar.zst`
  helper under that row.
- The macOS `1.0.40` release is built, signed, notarized, stapled, uploaded,
  and live. The universal DMG contains both Python architectures and universal
  libusb.
- The RT97L serial protocol is implemented and offline-tested, but its
  provisional channel map still requires validation on physical hardware.
- The experimental GM-32 has physical read/write evidence from 2026-10-25.
  The TS-2000 write-timeout fix still needs a physical upload/read-back retest.
  TS-2000 settings reads now report unsupported cleanly, and failed serial
  operations include a sanitized command trace for support reports.
- The Midland MXT295 has completed physical read and write testing and remains
  labeled experimental.
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
- macOS `1.0.40` artifact source commit: `8fdcef21`
- Windows `1.0.40` artifact source commit: `8fdcef21`
- Linux `1.0.40` artifact source commit: `8fdcef21`
- Open pull requests: none
- Checked-out source version: `1.0.40+40`
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
| macOS | 1.0.40 |
| Windows | 1.0.40 |
| Linux | 1.0.40 |
| Legacy shared manifest version | 1.0.40 |

macOS artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.40.dmg`
- Version/build: `1.0.40` / `40`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `318630cd494fe8e8620a1ccddd8e7fd0f8846fb068300bbeb1a5ec6b75f1ea62`
- Size: `81,283,507` bytes
- Notarization submission: `a387d9c2-2953-4383-9612-c370f1c08d8f`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum recorded from the live artifact

Windows artifact:

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

Linux artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.40.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.40.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.40.AppImage`
- Pacman URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.40.pkg.tar.zst`

Linux 1.0.40 SHA-256:

- DEB:
  `c30ed97a95e406b371c94dccaffa97e9fcaa1c865137431da72fe7fa5a2100ac`
- RPM:
  `11225c702eb408e097cb5702264bbad71676ad52203744e6f87886669e39d54b`
- AppImage:
  `79c272e8fd0cf93a6625b006e30d655aa38db56a2dada65f0192180c72949268`
- Pacman:
  `3f8147564daad683c6d82f8f11d65f894168288bcd8768371e0a47251042c8e8`

Linux 1.0.40 sizes:

- DEB: `48,412,260` bytes
- RPM: `38,883,730` bytes
- AppImage: `144,401,600` bytes
- Pacman: `46,895,161` bytes

## Recently completed

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
