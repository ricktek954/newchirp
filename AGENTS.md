# NewChirp Agent Guide

This repository keeps generated OKF knowledge bundles so coding agents can
answer structural questions without re-reading large source files.

## Session handoff

When the user asks where work left off, asks to resume, or starts a fresh
session without context, read `docs/PROJECT_STATE.md` in full before answering.
Check `git status` and fetch the latest `origin/main` so the handoff is compared
with the actual repository state. Keep any local user assets and unrelated
changes out of commits.

When adding or changing a NewChirp-maintained radio driver, update
`docs/DRIVER_STATUS.md`. Record transport details, implemented fields,
read/write policy, evidence hashes, physical-radio validation, and the next
milestone. Do not infer hardware-tested or released status from offline tests.

## Release artifact requirements

Every production installer build must contain and expose its version.

1. Use the app version from `pyproject.toml`, `pubspec.yaml`, or the relevant
   build configuration.
2. Embed that version in the artifact metadata.
3. Include the complete semantic version in the filename:
   - Windows: `NewChirp-Installer-1.0.3.exe`
   - macOS: `NewChirp-1.0.3.dmg`
   - Debian: `NewChirp-linux-x64-1.0.3.deb`
   - RPM: `NewChirp-linux-x64-1.0.3.rpm`
   - AppImage: `NewChirp-linux-x64-1.0.3.AppImage`
4. Never overwrite a previously released versioned artifact.
5. Upload to `/opt/newchirp/public/downloads/` with the versioned filename.
6. Verify the embedded version after building.
7. Do not rely solely on generic filenames such as `newchirp-setup.exe` or
   `newchirp.dmg`. The website intentionally ignores generic filenames when
   determining the published version.

The website uses the version in the filename as its source of truth. Each
versioned artifact becomes that platform's current download as soon as it is
uploaded, so platform versions can differ. The update manifest's per-platform
entries are authoritative; its top-level `version` remains the newest release
shared by Windows, macOS, and Linux for older clients. The `.rpm` and AppImage
extra buttons appear when matching files are present.

Build release artifacts only on their native platform:

- Build the Windows installer on Windows.
- Build the macOS DMG on macOS.
- Build the Linux packages on Linux.

Do not trigger, wait for, or emulate another platform's build workflow from the
current host. Each machine publishes only the artifact it built.

## Automatic freshness

VS Code is configured to run `Watch OKF knowledge graph` when the workspace
opens. That task performs an initial refresh and then watches `lib/` and
`scripts/` for saves, updating only the concepts affected by the changed files.
There is also a manual `Refresh OKF knowledge graph` task.

## Knowledge bundles

- `okf_bundle` — Dart application code under `lib/`
- `okf_bundle_scripts` — Python support scripts under `scripts/`

## Use the bundle first

For a focused question, run an OKF lookup before opening a whole source file:

```sh
/tmp/newchirp-okf-venv/bin/okf lookup --bundle ./okf_bundle --compact NewChirpHome
/tmp/newchirp-okf-venv/bin/okf lookup --bundle ./okf_bundle --compact RadioChannel
/tmp/newchirp-okf-venv/bin/okf lookup --bundle ./okf_bundle_scripts --compact chirp_bridge
```

For broader context, start with:

```sh
sed -n '1,220p' okf_bundle/SUMMARY.md
sed -n '1,220p' okf_bundle_scripts/SUMMARY.md
```

If the OKF binary is not installed, read the summary and index files directly
and use `find okf_bundle -name '<ConceptName>.md'`.

## Keep the bundles up to date

After editing anything under `lib/` or `scripts/`, refresh the relevant bundle:

```sh
./scripts/update_okf.sh
```

Useful modes:

```sh
./scripts/update_okf.sh --bootstrap   # create the isolated venv and install okf-generator
./scripts/update_okf.sh --watch       # run incremental watchers for lib and scripts
```

Do not index `build/`, `build_support/`, or cached CHIRP/Python trees. The
bundles intentionally cover only source directories.
