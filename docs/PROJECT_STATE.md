# NewChirp Project State

Last updated: 2026-10-24

This is the short operational handoff for restarting work with no conversation
history. `README.md` and `AGENTS.md` remain authoritative for build rules and
release requirements.

## Resume here

- The macOS `1.0.17` release is built, signed, notarized, stapled, uploaded,
  and live. It includes session-scoped CHIRP `.py` and `.mod` module loading.
- GitHub HEAD is the independently published Linux `1.0.13` release commit.
- An unreleased FT-60 manual-read timing fix is present in the working tree.
- No build, upload, or deployment is currently in progress.
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
- Latest release commit fetched from GitHub: `964acc0`
  (`Release Linux 1.0.13`)
- Previous release commit: `f69b325` (`Release macOS 1.0.17`)
- Open pull requests: none
- Checked-out source version: `1.0.13+13`
  - The Linux release commit changed the shared app version after the macOS
    release was published.
  - Do not assume this is the next macOS version; wait for the requested
    version before changing it.
- Intended untracked file: `tshirt - i chirp often.png`
  - This is a user asset, not application source.
  - Do not commit or delete it unless explicitly requested.

## Live releases

Latest public artifacts reported by
`https://newchirp.net/api/releases/latest`:

| Platform | Version |
|---|---:|
| macOS | 1.0.17 |
| Windows | 1.0.15 |
| Linux | 1.0.13 |
| Legacy shared manifest version | 1.0.13 |

macOS artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.17.dmg`
- Version/build: `1.0.17` / `17`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `72a5b43363b33f7dd0aa698a4fe1fab72d543c066171d8c8ae68d39ccb85daaa`
- Notarization submission: `4715fccb-b65b-4098-9297-562c6d7733af`
- Gatekeeper result: accepted as Notarized Developer ID
- Server checksum matched the local artifact

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

## macOS 1.0.17 verification status

Full verification before the macOS `1.0.17` release:

- `flutter analyze`: clean
- `flutter test`: all 70 tests passed
- `python3 test/chirp_bridge_upload_test.py -v`: all 4 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted
- Server SHA-256 matched the final stapled DMG

## Known limitations and follow-ups

- The published Windows `1.0.15` installer predates the FT-60 manual-read
  timing fix. The fix waits to tell the user to hold PTT until after the
  serial port is open. Confirm the read sequence on a physical FT-60 before
  building the next Windows release.
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
