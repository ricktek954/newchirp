# NewChirp Project State

Last updated: 2026-10-26

This is the short operational handoff for restarting work with no conversation
history. `README.md` and `AGENTS.md` remain authoritative for build rules and
release requirements.

## Resume here

- The Linux `1.0.20` release is built, uploaded, and live as DEB.
- The macOS `1.0.21` release is built, signed, notarized, stapled, uploaded,
  and live. It includes the experimental Baofeng GM-32 profile, the TS-2000
  write-timeout override, multi-county repeater filtering, and the fixed
  channel-table vertical scrollbar.
- The RT97L serial protocol is implemented and offline-tested, but its
  provisional channel map still requires validation on physical hardware.
- The experimental GM-32 and TS-2000 changes still require physical-radio
  validation before they should be described as hardware-tested.
- `tshirt - i chirp often.png` is an untracked user asset and must not be
  committed or deleted.
- `pubspec.lock` may be locally modified by the installed Flutter SDK. Do not
  include it unless the next task intentionally changes dependencies.
- After rebooting, run `git fetch origin` and inspect new commits before
  choosing the next task.
- Build only for this Mac unless the user explicitly requests otherwise.

## Repository state

- Local path: `/Volumes/RICKEXT/desktop/newchirp`
- Branch: `main`
- Release source commit: `8e4f7e5` (`Bump version to 1.0.21`)
- Open pull requests: none
- Checked-out source version: `1.0.21+21`
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
| macOS | 1.0.21 |
| Windows | 1.0.18 |
| Linux | 1.0.20 |
| Legacy shared manifest version | 1.0.17 |

macOS artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.21.dmg`
- Version/build: `1.0.21` / `21`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `3283bcea0e4df62d038042abf2e2288ac781c6a9aa5e66182672b457a84e4f49`
- Size: `91,667,505` bytes
- Notarization submission: `c67daefe-ad4e-4063-970e-38c1fcbfaa67`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum matched the local artifact

Linux artifacts:

- DEB URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.20.deb`
- RPM URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.20.rpm`
- AppImage URL:
  `https://newchirp.net/downloads/NewChirp-linux-x64-1.0.20.AppImage`

## Recently completed

- Native CHIRP image import for `.img`, `.icf`, `.itm`, and `.d72`.
- Radio-aware channel slots and table sorting by memory location.
- Drag-and-drop channel rearrangement through occupied radio memory slots.
- Standard DTCS fallback codes when radio metadata is unavailable.
- TD-H3 uploads now use one clone handshake instead of probing and then
  handshaking again.
- TK-880 channel operations use CHIRP subdevices/zones.
- Multi-zone selector with real zone names and channel counts.
- Zone switching reloads from the saved parent image and preserves other zones
  during upload.
- Radio prompt HTML is stripped and driver "click OK" text is rewritten to the
  actual NewChirp button label.
- Searchable abbreviation glossary and channel-header tooltips.
- Update downloads are restricted to exact HTTPS URLs on `newchirp.net`.
- Bundled Linux and Windows Python runtime hashes are pinned in build scripts.
- CHIRP `.py` and `.mod` driver modules can be loaded from
  **Help > Load CHIRP driver module…** for the current session.
- Loaded modules can add or override radio drivers; the radio catalog refreshes
  after loading and unloading.
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
  UV-32 CPS, including DTR/RTS handling and ten bank-name records.
- Fixed TS-2000 uploads that exceeded the stock one-second command timeout.
- Kept the channel-table vertical scrollbar pinned to the visible right edge
  while the columns scroll horizontally.

## macOS 1.0.21 verification status

Full verification before the macOS `1.0.21` release:

- `flutter analyze`: clean
- `flutter test`: all 86 tests passed
- Python test discovery: all 40 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- App version/build in the mounted DMG: `1.0.21` / `21`
- Main executable architectures: `arm64` and `x86_64`
- Server SHA-256 matched the final stapled DMG
- `/api/releases/latest` reports macOS `1.0.21`

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
- Building a repeater list without radio metadata currently has a fallback for
  DTCS but not for the standard CTCSS tone list. This can make the TX/RX tone
  selector appear to offer only `88.5`.
- CHIRP drivers can expose additional subdevice types beyond the zones handled
  for the TK-880.
- CHIRP modules execute arbitrary Python without sandboxing. Only trusted
  modules should be loaded, and modules requiring packages not bundled with
  NewChirp may fail to import.
- The macOS raw SCSI helper for experimental mass-storage radios is currently
  compiled for Apple Silicon only; live CS750 reads on Intel Macs still need a
  universal or x86_64 helper build and hardware validation.
- The experimental Retevis RT97L channel map and serial handshake still need a
  physical read and comparison against an official CPS export before uploads
  can be enabled.
- Forum like counts and website-side ranking are a separate website project,
  not part of this Flutter repository.
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
