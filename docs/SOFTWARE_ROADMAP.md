# NewChirp Software Roadmap

Last updated: August 22, 2026

This document is the durable project handoff for NewChirp. It records what has
already been built, the decisions behind it, how the application works, and the
remaining work. Update it whenever behavior, packaging, licensing, or release
plans change.

## Product direction

NewChirp is a modern Flutter desktop channel editor and radio programmer for
amateur and GMRS radios. It presents a simpler interface while using the CHIRP
driver tree as its hardware-compatibility layer.

The intended workflow is:

1. Start with a blank configuration, a CHIRP CSV, the standard GMRS template,
   or a read from a connected radio.
2. Review and edit the channel list.
3. Save a CHIRP-compatible CSV or write changes back to the radio image that
   was read during the current session.

### Product requirements that should not regress

- Do not open into a pre-populated GMRS list.
- The startup screen must explain the available starting options.
- Keep the standard 22-channel GMRS template available from the **New** menu,
  not on the welcome screen before a radio image has been read.
- A single click must select a row immediately; a double-click opens the full
  channel editor.
- Show the relevant CHIRP channel fields, including radio-specific per-channel
  extras when the driver exposes them.
- Reading and writing must block the rest of the interface with a visible
  transfer overlay.
- Confirm before discarding an open list or deleting a channel.
- Persist the macOS window frame and table column layout.
- Do not require users to install packages with `pip`. pySerial is bundled.
- Credit **Rick Lopez · Lead Programmer · rick@newchirp.net** in the interface
  and native macOS About panel.

## Current status

The application is a functional macOS development build. Reading a Baofeng
UV-5R Mini has been verified manually after matching CHIRP's serial setup. The
Flutter analysis and automated test suite are clean, and a debug macOS `.app`
build succeeds.

The macOS app is now self-contained at build time, but it is not yet signed,
notarized, or legally packaged as a public release. See the release-critical
roadmap below.

A Windows debug build and Inno Setup installer are also produced by
`scripts/build_windows_installer.ps1`. The Windows installer currently packages
a JIT debug Flutter bundle because Smart App Control blocks the unsigned
`gen_snapshot.exe` used by release AOT builds; a release build is expected to
succeed once Smart App Control is turned off and the machine is restarted.
Because the debug build links the Visual Studio debug CRT, it should be treated
as a development artifact; the release build is the clean-machine package.

## Completed work

### Startup and navigation

- [x] Replaced automatic GMRS startup with a welcome screen.
- [x] Added startup actions for CSV import and radio connection; blank
  configuration and the GMRS starter template live in the **New** menu.
- [x] Added a **New** menu with blank and GMRS choices.
- [x] Added discard confirmation before replacing an open configuration.
- [x] Added sidebar navigation for Channel library, Radio connection, and
  About & licenses.

### Channel library

- [x] Added CHIRP-compatible CSV import and export.
- [x] Allowed CSV/GMRS templates to be inserted starting at a chosen channel
  number without replacing the rest of the library.
- [x] Added the standard 22 GMRS channels as an optional starter template.
- [x] Added searchable channel rows.
- [x] Added channel creation and duplication.
- [x] Added right-click copy, cut, paste, and duplicate actions in the channel
  table.
- [x] Added right-click **Clear channel**, which marks that memory slot to be
  cleared on the next radio write.
- [x] Added undo/redo with Cmd/Ctrl+Z / Cmd/Ctrl+Shift+Z keyboard shortcuts and
  native macOS Edit-menu integration.
- [x] Added delete confirmation.
- [x] Made row selection happen on pointer-down to eliminate the prior
  single-click delay.
- [x] Added a double-click modal editor for complete channel editing.
- [x] Added validation before radio writes.
- [x] Added dirty/edited state and save handling.

### Channel fields

The current core data model supports:

- Location
- Name
- Receive frequency
- Duplex
- Offset or split transmit frequency
- Tone mode
- Transmit CTCSS tone
- Receive CTCSS tone
- DTCS code
- Receive DTCS code
- DTCS polarity
- Cross mode
- Modulation mode
- Tuning step
- Scan/skip state
- Power
- Comment
- Driver-provided per-channel extra settings

The table displays the core fields in CHIRP-like columns and dynamically adds
columns for radio-specific extras returned by the selected CHIRP driver.

### Channel table behavior

- [x] Added horizontal and vertical scrolling.
- [x] Added resizable columns with sensible limits.
- [x] Added drag-and-drop column reordering.
- [x] Persisted column order and widths between launches.
- [x] Added full editor choices driven by the radio's CHIRP capabilities.

Column layout is stored at:

- macOS: `~/Library/Application Support/NewChirp/column-layout.json`
- Windows: `%APPDATA%\NewChirp\column-layout.json`
- Linux: `$XDG_CONFIG_HOME/newchirp/column-layout.json`, falling back to
  `~/.config/newchirp/column-layout.json`

### Radio connection and CHIRP bridge

- [x] Added USB serial-port discovery for macOS and Linux.
- [x] Added CHIRP radio catalog loading and model selection.
- [x] Added driver-provided instructions and experimental warnings before
  reading.
- [x] Added radio download and upload through a headless Python bridge.
- [x] Skip protected/immutable radio memories during upload and report the
  skipped channels instead of failing the whole write.
- [x] Matched CHIRP's baud rate, hardware flow control, RTS, and DTR behavior.
- [x] Added CHIRP driver auto-detection where supported.
- [x] Added compatibility for drivers that expect CHIRP's serial logging hook.
- [x] Prevented CHIRP status/debug output from corrupting the JSON protocol.
- [x] Bundled the pure-Python pySerial 3.5 wheel, avoiding `pip` and wxPython.
- [x] Preserved the downloaded radio image for the current edit/write session.
- [x] Disabled writing until an image has been read.
- [x] Cleared the loaded image when the user changes radio model.
- [x] Added a gray blocking transfer overlay with status and Cancel control.
- [x] Added write confirmation and channel validation.
- [x] Persisted the last serial port and radio model between launches.
- [x] Warn before a radio read replaces an open channel list.
- [x] Confirm before a CSV import replaces the current channel list.
- [x] Stored the first read as a reusable per-model image so matching radios can
  be written again without reading.
- [x] Added help-context icons with detailed instructions to the main commands.
- [x] Added a **Restore stock channels** action using the bundled CHIRP stock
  GMRS config.
- [x] Patched the UV-5G Mini driver so channels 1-30 report their factory GMRS
  frequencies. This tweak is reapplied automatically whenever the CHIRP source
  updates, and is experimental until verified on a radio.

The bridge protocol uses JSON over a spawned process:

```text
Flutter UI
  -> materialized scripts/chirp_bridge.py
  -> bundled Python runtime
  -> bundled pySerial wheel
  -> bundled/upstream CHIRP source
  -> serial programming cable
  -> radio
```

The bridge currently supports these commands:

- `list-models`
- `model-info`
- `download`
- `upload`

### Window and platform integration

- [x] Persisted macOS window size and position with AppKit frame autosave.
- [x] Re-centers a restored window if its saved frame is no longer on any
  connected display.
- [x] Fixed layout overflows at the default macOS window size.
- [x] Added native macOS metadata for Rick Lopez and the CHIRP license notice.
- [x] Replaced the default Flutter macOS icon with the NewChirp mint waveform
  icon at all required macOS sizes.
- [x] Preserved the editable vector icon source at
  `assets/branding/newchirp_app_icon.svg`.

### About and licensing UI

- [x] Added an About & licenses screen.
- [x] Added Rick Lopez's lead programmer credit and email to the About screen
  and lower-left footer.
- [x] Added CHIRP GPL-3.0-or-later attribution and warranty language.
- [x] Added the independent/non-endorsement statement.
- [x] Bundled the complete CHIRP GPLv3 text.
- [x] Bundled the pySerial BSD-3-Clause notice.
- [x] Registered CHIRP and pySerial with Flutter's license viewer.
- [x] Confirmed both notice files are packaged inside the built macOS app.

Important: showing license notices is necessary but is not, by itself,
complete GPL distribution compliance. See the release roadmap.

### Tests and verification

Automated coverage currently includes:

- CHIRP CSV parsing, escaping, and round-trip behavior
- The 22-channel GMRS template
- Column order and width persistence
- Startup choices and no automatic GMRS load
- GMRS selection and availability from the New menu
- Immediate row selection
- Double-click modal editing
- Column resizing and reordering
- New/discard confirmation
- Delete confirmation
- Default macOS window fit
- About/license attribution
- Loading representative models from the CHIRP catalog

Last verified commands:

```sh
flutter analyze
flutter test
flutter build macos --debug
```

Last known result: analysis clean, 14 tests passing, macOS debug build
successful.

To regenerate the native macOS icon set after editing the SVG source:

```sh
rsvg-convert -w 1024 -h 1024 assets/branding/newchirp_app_icon.svg \
  -o macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_1024.png
sips -z 512 512 macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_1024.png \
  --out macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_512.png
```

Repeat the `sips` command for 256, 128, 64, 32, and 16 pixels. The Xcode asset
catalog packages these files into `AppIcon.icns` during the macOS build.

## Architecture and important files

| Path | Responsibility |
| --- | --- |
| `lib/main.dart` | Main application state, screens, table, dialogs, transfer UI, and About page |
| `lib/models/radio_channel.dart` | Channel model, validation, extra fields, and GMRS template |
| `lib/services/chirp_csv.dart` | CHIRP CSV encode/decode |
| `lib/services/column_layout_store.dart` | Cross-platform table layout persistence |
| `lib/services/radio_image_store.dart` | Per-model reusable radio image storage |
| `lib/services/radio_bridge.dart` | Process lifecycle, serial-port list, JSON bridge calls, and cancellation |
| `scripts/chirp_bridge.py` | Headless CHIRP adapter, serial setup, radio read/write, and field translation |
| `assets/python/` | Bundled pySerial wheel |
| `assets/licenses/` | CHIRP GPL and pySerial BSD license texts |
| `assets/branding/` | Editable NewChirp app icon source |
| `macos/Runner/MainFlutterWindow.swift` | macOS window restoration |
| `macos/Runner/Configs/AppInfo.xcconfig` | App name, bundle ID, and native About copyright text |
| `macos/Runner/Assets.xcassets/AppIcon.appiconset/` | Generated native macOS icon sizes |
| `test/` | Unit and widget tests |

## Runtime and development requirements

- Flutter SDK path is set per machine in the local (untracked) VS Code
  `dart.flutterSdkPath` setting; each machine points it at its own SDK.
- The macOS build bundles a private Python 3.13 runtime and the CHIRP driver
  tree, so users do not need to install Python or keep a CHIRP source folder.
- No user-installed Python packages are required because pySerial is bundled.
- Builds download the CHIRP commit in `scripts/chirp-source.pin` and check its
  sha256 before unpacking. `CHIRP_SOURCE` still overrides the source explicitly.
- CHIRP GUI dependencies such as wxPython are not used.
- CHIRP GUI dependencies such as wxPython are not used.

Development run:

```sh
flutter pub get
flutter run -d macos
```

## Known limitations and risks

### Release blockers

1. **The macOS app is self-contained at build time but has not been verified on
   a clean customer Mac.** It bundles Python and CHIRP, yet signing,
   notarization, and clean-machine testing are still required.
2. **NewChirp's own license has not been formally selected or added at the
   repository root.** The current tight CHIRP integration creates substantial
   GPL-combination risk.
3. **Corresponding source delivery is not implemented as a release process.**
   License notices alone do not satisfy GPL source obligations.
4. **The build is not signed, notarized, packaged as a DMG/installer, or tested
   through Gatekeeper on a clean Mac.**
5. **Transfer cancellation is process termination.** Killing the helper during
   a radio write may leave the radio partially programmed. The UI currently
   calls this safe cancellation, but cooperative cancellation or a more
   conservative write policy is required.
6. **Deleted channels are not explicitly cleared from the radio on upload.**
   Upload updates channels present in the list but does not yet mark removed
   memory locations empty. The on-screen list and radio can therefore diverge.

### Functional gaps

- CSV files preserve the standard CHIRP columns listed in `ChirpCsv.headers`,
  but radio-specific `extras` are not exported to or restored from CSV.
- The downloaded image is temporary and session-only; there is no native CHIRP
  image open/save workflow.
- Temporary bridge, upload JSON, wheel, and radio image files are not fully
  isolated per operation or cleaned up after use.
- Errors are shown in dialogs but there is no user-accessible diagnostic log.
- There are no keyboard shortcuts, undo/redo, multi-row editing, bulk paste, or
  import conflict tools.
- Search state, selected page, and selected row are not persisted.
- Column layout has no visible **Reset columns** command.
- Accessibility, screen-reader, keyboard-only, localization, and high-contrast
  audits have not been completed.

### Platform gaps

- macOS is the only platform manually hardware-tested. Windows debug builds and
  an Inno Setup installer are now produced by the build script, but release AOT
  Windows builds are blocked by Smart App Control.
- Windows serial discovery is currently a placeholder list of `COM1` through
  `COM4`, not actual device enumeration.
- Linux serial access and group/permission guidance are not implemented.
- Window frame persistence is currently macOS-specific.
- The proper NewChirp native icon has only been generated for macOS; the
  Windows `.ico` and Linux packaging still need branding work.
- Hardware testing currently covers one known Baofeng UV-5R Mini workflow.

## Roadmap

### P0 — Make radio writing and distribution safe

- [ ] Implement deletion semantics during upload by comparing the original
  downloaded image/memory map with the edited list and explicitly clearing
  removed locations through the CHIRP driver.
- [ ] Replace SIGTERM-based write cancellation with cooperative cancellation.
  If a driver cannot safely cancel, disable Cancel during its critical write
  phase and clearly explain why.
- [ ] Store the model identity with the downloaded image and enforce it at the
  service layer, not only by clearing UI state when model selection changes.
- [ ] Use a unique temporary directory for every bridge operation and remove
  temporary files after success, failure, or cancellation.
- [ ] Add automated bridge tests using a fake serial transport and representative
  CHIRP drivers before expanding hardware support.
- [ ] Test read/edit/write and interrupted-transfer recovery on each officially
  supported radio model.

### P0 — Decide and implement the release/license model

- [ ] Obtain qualified open-source licensing advice for whether the Flutter UI,
  custom bridge, and CHIRP driver tree are one GPL-covered combined work.
- [ ] Choose and document NewChirp's license. The safest current assumption for
  distribution is GPL-3.0-or-later for the complete combined application.
- [ ] Add the selected root `LICENSE`, copyright headers where appropriate, and
  a source-code offer/link in the About screen and release download page.
- [ ] Publish the exact corresponding source used for each binary release,
  including Flutter source, bridge source, CHIRP source/version, build scripts,
  patches, and installation information required by the GPL.
- [ ] Keep license texts and notices bundled in every platform package.
- [ ] Document third-party dependency versions and notices in a reproducible
  release manifest or software bill of materials.

### P0 — Make the macOS app distributable

- [x] Bundle a compatible Python runtime instead of relying on system Python.
  macOS builds now include python-build-standalone 3.13.
- [x] Package the CHIRP driver tree/source inside the installed app and add an
  upstream update check that pulls the newest master source.
- [x] Make bridge resource discovery work from a `.app` without environment
  variables or adjacent development folders.
- [ ] Configure Developer ID signing and hardened runtime entitlements.
- [ ] Notarize and staple the application.
- [ ] Build a DMG or installer and verify on a clean supported macOS machine.
- [ ] Define minimum macOS and CPU support, including Apple Silicon and Intel.

### P1 — Complete editing fidelity

- [ ] Compare NewChirp field-by-field with current CHIRP for several radio
  families and record unsupported fields.
- [x] Add global radio settings where drivers expose them.
- [ ] Preserve supported radio-specific extras through an image/native project
  format; define what CSV can and cannot retain.
- [ ] Add multi-select, bulk edit, copy/paste, row movement, and import merge.
- [ ] Add undo/redo and stronger unsaved-change protection on app close.
- [ ] Add keyboard navigation and common desktop shortcuts.
- [ ] Add **Reset columns** and optionally persist table sort/filter state.

### P1 — Improve transfer experience

- [x] Forward CHIRP status callbacks as structured progress events.
- [x] Show phase, percentage, elapsed time, and model-specific instructions in
  the blocking overlay.
- [ ] Add a diagnostic log users can copy when a transfer fails, while
  redacting sensitive paths where appropriate.
- [ ] Improve serial device identity display so users can distinguish multiple
  cables.
- [ ] Detect disconnects and provide model-specific recovery instructions.

### P1 — Quality and platform support

- [ ] Add integration tests for CSV open/save dialogs and complete editing
  workflows.
- [ ] Add golden tests for welcome, library, radio, About, transfer overlay,
  and narrow-window layouts.
- [ ] Perform accessibility and keyboard-only audits.
- [ ] Implement real Windows COM-port enumeration and test the Python/CHIRP
  bridge on Windows.
- [ ] Test Linux serial permissions and packaging.
- [ ] Generate NewChirp icons and metadata for Windows and Linux.
- [ ] Add CI for format, analyze, tests, and platform builds.

### P2 — Product polish

- [ ] Add release notes, Help, troubleshooting, and supported-radio guidance.
- [ ] Add optional recent files and restore-last-workflow behavior without
  automatically loading a starter library.
- [ ] Add localization infrastructure.
- [ ] Consider an update mechanism after signing and release hosting are
  established.
- [ ] Add telemetry only if explicitly chosen, privacy-reviewed, disclosed, and
  opt-in. There is currently no telemetry.

## Suggested next implementation sequence

1. Fix radio deletion/write semantics and transfer cancellation safety.
2. Lock the downloaded image to an explicit radio/model session object.
3. Decide the GPL/source distribution approach.
4. [x] Make Python and CHIRP packaging self-contained for macOS; clean-machine
   verification remains part of step 6.
5. Add bridge-level fake-radio tests.
6. Sign/notarize a clean-machine macOS beta.
7. Expand field fidelity and hardware coverage.
8. Begin Windows and Linux production support only after macOS transfer safety
   is solid.

## Context recovery checklist

If work resumes with no conversation history:

1. Read this file and `README.md`.
2. Run `flutter analyze` and `flutter test` before editing.
3. Run `scripts/update_chirp.sh` to fetch the pinned CHIRP source, or set
   `CHIRP_SOURCE` to use a specific tree.
4. Never test **Write to radio** without first reading the same model and
   understanding the current deletion/cancellation limitations.
5. Preserve unrelated user changes; this workspace may not be under Git.
6. Use `apply_patch` for source edits.
7. Rebuild the macOS app after modifying native metadata, entitlements, or icon
   assets.
8. Update this roadmap when a checkbox changes or a new risk is discovered.
