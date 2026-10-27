# NewChirp

NewChirp is a Flutter desktop channel editor for amateur and GMRS radios. It
uses the CHIRP driver tree as a compatibility layer for safe radio transfers
while presenting a fresh desktop interface.

See [docs/SOFTWARE_ROADMAP.md](docs/SOFTWARE_ROADMAP.md) for the complete
implementation history, architecture, known risks, and prioritized next work.

## Included

- CHIRP-compatible CSV import and export
- CSV/GMRS template insertion starting at any channel number
- Searchable channel library with validation and detailed editing
- Drag-and-drop channel rearrangement across the radio's occupied memory slots
- Optional empty-slot view that keeps memory gaps visible and lets a channel
  be created directly in a specific slot
- Right-click copy, cut, paste, and duplicate for channel rows
- Right-click clear channel, which clears it from the radio on the next write
- Undo/redo with keyboard shortcuts
- 22-channel GMRS starter library
- RepeaterBook search with state, location, radius, mode, and open-repeater
  filters; preview on a synchronized interactive map and selectively insert
  amateur or GMRS repeater channels
- USB serial-port discovery
- CHIRP radio-model catalog and guarded read/write workflow
- Session-scoped loading of experimental CHIRP `.py` and `.mod` driver modules
- Reusable per-model radio images after the first read
- Multi-zone channel selection for radios that expose CHIRP subdevices
- Radio-aware channel slot allocation within each model's memory range
- Real transfer progress from CHIRP read/write status with percentage and elapsed time
- Radio-wide settings editor for drivers that expose CHIRP global settings
- Help-context icons with detailed instructions
- Hover definitions for channel-column abbreviations and a searchable Help glossary
- Restore stock channels from the bundled CHIRP GMRS config
- macOS, Windows, and Linux Flutter projects
- In-app update download, installation, and restart against the newchirp.net
  release manifest

## Updates

NewChirp checks newchirp.net for a newer release on startup and from
**Help > Check for updates**. Startup checks stay quiet when the app is current
or offline. When an installer is available, one **Download and install**
button downloads it with progress, starts the native installer, closes
NewChirp, and reopens the updated app. The user does not need to visit the
download page. The app reads a JSON manifest (default
`https://newchirp.net/api/releases/latest`) shaped like:

```json
{
  "version": "1.0.7",
  "release_url": "https://newchirp.net/#download",
  "downloads": { "windows": "...", "macos": "...", "linux": "..." },
  "platforms": {
    "windows": { "version": "1.0.8", "download_url": "...", "sha256": "..." },
    "macos": { "version": "1.0.7", "download_url": "...", "sha256": "..." },
    "linux": { "version": "1.0.7", "download_url": "..." }
  }
}
```

The app reads its own entry from `platforms`, so each platform can publish on
its own schedule. The top-level `version` is the newest release shared by all
desktop platforms and remains for older clients that only understand that
field. Direct artifacts and redirects are restricted to HTTPS on
`newchirp.net`. An optional per-platform `sha256` is verified before
installation. macOS also verifies the downloaded app's code signature,
notarization, and bundle identifier. Windows requires a valid Authenticode
signature. `release_url` (or `url`) remains the fallback when no installable
artifact is available.

The installed version is `_newChirpVersion` in `lib/main.dart` and should be
kept in sync with `version` in `pubspec.yaml`. Update checking lives in
`lib/services/update_checker.dart`; downloading and platform installation live
in `lib/services/update_installer.dart`.

When cutting a desktop release, bump both app version locations so they agree:

- `_newChirpVersion` in `lib/main.dart`
- `version` in `pubspec.yaml`

Then upload the versioned artifact for that platform. The website discovers it
without a code or release-constant change, and other platforms can keep serving
their previous versions.

## Run

```sh
flutter pub get
flutter run -d macos
```

The macOS app build now bundles a private Python runtime and the CHIRP driver
tree inside `NewChirp.app`, so end users do not need to install Python or CHIRP.
For development, a custom CHIRP location may still be selected by setting
`CHIRP_SOURCE` to the folder containing the `chirp` Python package. Release
builds download the CHIRP commit named in `scripts/chirp-source.pin` and reject
the archive when its checksum does not match. NewChirp bundles the headless
serial dependency used by the CHIRP drivers; do not install CHIRP's wxPython
GUI requirements.

Always read a radio before writing it. NewChirp intentionally keeps writing
locked until a matching radio image has been downloaded in the current session.

Use **Open file** to load a CHIRP-compatible CSV, a MOTOTRBO CPS 2.0 Zone XML
export, or a native CHIRP image such as `.img`, `.icf`, `.itm`, or `.d72`.
CPS 2.0 XML is read-only and imports conventional channels, including basic
analog and DMR fields. Native CHIRP images use model detection, retain the
original image for radio transfer, and unlock upload when the detected model is
selected.

### Experimental CHIRP modules

**Help > Load CHIRP driver module…** loads a trusted CHIRP `.py` or `.mod`
module for the current NewChirp session and refreshes the radio catalog. Modules
can replace built-in drivers or add experimental driver classes.

CHIRP modules are executable Python code. NewChirp runs a loaded module in a
sandbox that blocks the home folder, other drives, and the network. The module
can still use the selected radio and the files for this session. A bad module
can still damage the radio. Only load a module from a source you trust.
NewChirp does not automatically download, remember, or reload modules after
the app closes. On Windows, module loading is refused because NewChirp cannot
sandbox it there yet. On Linux, bubblewrap (`bwrap`) must be installed or
loading is refused. This feature loads desktop CHIRP drivers; it does not
flash or install radio firmware.

## Verify and build

```sh
flutter analyze
flutter test
flutter build macos
```

### Windows

Build status and resumption checklist: `docs/BUILD_PROGRESS.md`.

Windows release builds use Flutter 3.44.2. Flutter 3.47.x can crash on startup
or render a black window on older Windows 10 GPUs limited to D3D11 feature
level 9_3, so do not use it for a Windows release until that fix reaches a
stable Flutter release.

On a Windows machine with the Flutter SDK and Visual Studio (C++ workload)
installed, build the release bundle and Inno Setup installer with:

```powershell
.\scripts\build_windows_installer.ps1 -FlutterRoot C:\flutter-3.44.2
```

The script runs `flutter pub get`, `flutter build windows --release`, bundles a
private Python runtime, the CHIRP driver tree, and the Visual C++ runtime next
to `newchirp.exe`, and then compiles
`build\NewChirp-Installer-<version>.exe`. Pass
`-Configuration debug` to build a JIT debug app instead, or `-BundleDir` to
package an already-built bundle. The runtime and CHIRP sources are downloaded
the first time and cached under `build_support\`.

### Cross-platform releases

`.github/workflows/release.yml` builds the Windows installer, macOS DMG, and
Linux Debian package. Run it with **Actions > Build release artifacts > Run
workflow**, or push a tag named `v<version>`. The workflow verifies each
artifact's embedded version and versioned filename. Tag builds attach the three
artifacts to a GitHub release. Platforms do not need the same version or need
to publish together; each versioned artifact becomes that platform's current
download as soon as it is uploaded.

Release AOT builds need `gen_snapshot.exe`, which Windows Smart App Control
blocks when it is enabled. If `flutter build windows --release` fails with an
Application Control message, turn Smart App Control off (Windows Security →
App & browser control → Smart App Control), restart, and re-run the script.
Use `-Configuration debug` only for a local dev build; debug Flutter binaries
link the Visual Studio debug CRT and are not intended for clean end-user
machines.

### Experimental FTM-150 support

NewChirp includes an experimental Yaesu FTM-150R/E/ASP memory-channel driver
maintained outside upstream CHIRP. It uses the AH086 layout documented by
ADMS-17 v1.0.1 and the same clone transport as the FTM-300DR family. Memory
channel reads and writes are available; APRS, GPS, and digital settings remain
hidden until verified with real hardware.

Use an SCU-56 USB cable or CT-163 serial cable on the DATA jack. Keep a complete
microSD ALL backup before uploading. The radio-side menu entries are
**59 Other -> This** for download and **58 This -> Other** for upload.

### Experimental RT-950 support

NewChirp also includes a read-only driver for the Radtel RT-950. Select
**Radtel RT-950**, connect the USB programming cable, and download to inspect
the 960 channel memories. Uploads are disabled because the CPS write path has
not yet been independently validated. Protocol details and reverse-engineering
evidence are recorded in `docs/RT950_PROTOCOL.md`.

### Experimental CS750 codeplug support

NewChirp includes a read-only Connect Systems CS750 transport for macOS. It
uses NewChirp's own raw SCSI/RAP bridge instead of CHIRP's serial drivers, and
exposes ordered channels, RX/TX frequencies, channel names, and analog/DMR
mode from M100000/2000-channel radios. `.rdb` codeplugs saved by the official
CPS can also be imported directly. Uploads remain disabled. Protocol and
reverse-engineering notes are recorded in `docs/CS750_PROTOCOL.md`.

## Code knowledge graph

This project keeps OKF knowledge bundles for coding agents:

- `okf_bundle` indexes the Dart application source under `lib/`.
- `okf_bundle_scripts` indexes the Python support scripts under `scripts/`.

Read `AGENTS.md` for lookup instructions. Refresh the bundles after source
changes with:

```sh
./scripts/update_okf.sh
```

VS Code is configured to refresh the bundles when the workspace opens and to
watch `lib/` and `scripts/` for saves automatically.
