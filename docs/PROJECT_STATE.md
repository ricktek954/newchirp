# NewChirp Project State

Last updated: 2026-10-24

This is the short operational handoff for restarting work with no conversation
history. `README.md` and `AGENTS.md` remain authoritative for build rules and
release requirements.

## Resume here

- The macOS `1.0.16` release is built, signed, notarized, uploaded, and live.
- GitHub also contains the independently published Linux `1.0.12` release
  commit.
- No source change, build, upload, or deployment is currently in progress.
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
- Latest release commit fetched from GitHub: `0695274`
  (`Release Linux 1.0.12`)
- Previous release commit: `5f95fae` (`Release macOS 1.0.16`)
- Open pull requests: none
- Checked-out source version: `1.0.12+12`
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
| macOS | 1.0.16 |
| Windows | 1.0.15 |
| Linux | 1.0.12 |
| Legacy shared manifest version | 1.0.10 |

macOS artifact:

- URL: `https://newchirp.net/downloads/NewChirp-1.0.16.dmg`
- Version/build: `1.0.16` / `16`
- Architectures: `arm64` and `x86_64`
- SHA-256:
  `5c74c560c81e856428513e5e418be7db42deb7a5c527e83a3b463fe439b53846`
- Notarization submission: `8af1a744-b30a-4335-9b7f-06b8073d3b19`
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

## macOS 1.0.16 verification status

Last full verification before the macOS `1.0.16` release:

- `flutter analyze`: clean
- `flutter test`: all 66 tests passed
- `python3 test/chirp_bridge_upload_test.py -v`: all 4 tests passed
- Release app: universal, signed, notarized, stapled, and Gatekeeper-accepted

## Known limitations and follow-ups

- TK-880 multi-zone support still needs a report from a physical five-zone
  radio. The automated test uses CHIRP's `Kenwood_TK-880.img`.
- TD-H3 upload uses a protocol-level fake serial test. Physical hardware
  confirmation is still desirable.
- Building a repeater list without radio metadata currently has a fallback for
  DTCS but not for the standard CTCSS tone list. This can make the TX/RX tone
  selector appear to offer only `88.5`.
- CHIRP drivers can expose additional subdevice types beyond the zones handled
  for the TK-880.
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
