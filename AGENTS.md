# NewChirp Agent Guide

This repository keeps generated OKF knowledge bundles so coding agents can
answer structural questions without re-reading large source files.

## Product standard

The goal is for NewChirp to be the best radio-programming software in the
world. Optimize for accuracy, safety, broad radio support, understandable
failure recovery, and an excellent user experience. Do not treat "works on my
machine" or parity with an OEM programmer as the final standard.

## Session handoff

When the user asks where work left off, asks to resume, or starts a fresh
session without context, read `docs/PROJECT_STATE.md` in full before answering.
Check `git status` and fetch the latest `origin/main` so the handoff is compared
with the actual repository state. Keep any local user assets and unrelated
changes out of commits.

## Driver work ledger

Before debugging or extending a radio driver, query the manufacturer/model
history in the driver ledger. Its source of truth is one JSON file per record
under `database/driver_work/` (merges cleanly when several machines record
work at once); `database/driver_work.sqlite3` is a git-ignored cache that
`scripts/driver_work.py` rebuilds on every run. Never edit or commit the
cache, and never hand-edit the JSON except to resolve a merge conflict:

```sh
python3 scripts/driver_work.py list --manufacturer Kenwood --model TK-350
```

Record each actionable bug, new driver, enhancement, validation request, and
release as a work item. After meaningful analysis, commits, tests, emails, CPS
recovery, or hardware reports, add an event with the commit SHA, Message-ID,
artifact hash, or relative evidence path. Use:

```sh
python3 scripts/driver_work.py show <work-id>
python3 scripts/driver_work.py event <work-id> --type fix \
  --summary "..." --ref desktop:<commit>
```

Use `database/README.md` for the full command and status conventions. Run
`python3 scripts/driver_work.py export` after changes so
`docs/DRIVER_WORK.md` remains readable. Keep `docs/DRIVER_STATUS.md` as the
concise current-state ledger and the SQLite history as the complete timeline.
Never infer physical validation from offline tests.

When adding or changing a NewChirp-maintained radio driver, update
`docs/DRIVER_STATUS.md`. Record transport details, implemented fields,
read/write policy, evidence hashes, physical-radio validation, and the next
milestone. Do not infer hardware-tested or released status from offline tests.

Every new radio driver must also be exposed on the website before handoff:

1. Add the exact radio to the local site's experimental catalog by updating
   `scripts/sync-chirp-radios.mjs` in `/Volumes/RICKEXT/web/newchirpweb` and
   running `npm run sync:radios`.
2. Add a matching Web Programmer profile using the same transport and
   read/write safety policy as the desktop driver, then verify it appears in
   both the catalog and the Web Programmer picker.

Both website steps are required even when the browser transport is read-only.

### Graduating a radio out of Experimental

A radio leaves Experimental once its core operations are confirmed on a
physical radio: a full read, and a channel write that reads back correctly
after a power cycle. Any owner's confirmation counts, not only the original
reporter's. Offline, replay, and OEM-capture tests never count. Individual
features that are still untested (for example one channel field or a
settings page) do not hold a radio back. List them as known limitations in
`docs/DRIVER_STATUS.md` and keep their ledger items open.

When the core confirmation is recorded:

1. Ledger: record `driver_work.py test <id> --result pass` on the radio's
   status item, citing the mailbox UID or Message-ID, then
   `driver_work.py status <id> hardware_tested` (or `released` once a build
   containing the fix is out).
2. Desktop: remove the driver's `experimental` prompt if it has one, and
   change its `docs/DRIVER_STATUS.md` row to `Supported; core read/write
   hardware-confirmed <date>`, followed by the known limitations.
3. Website: if the model is in `newChirpExperimentalModels` in
   `scripts/sync-chirp-radios.mjs`, remove it. Add it to
   `newChirpSupportedModels` only if upstream CHIRP's catalog does not
   already list it. Run `npm run sync:radios` and check that it is gone from
   **New Experimental Radio Support** and appears under its manufacturer
   without the `(experimental)` suffix. Keep the Web Programmer profile.
4. Deploy the website if step 3 changed it, and record the graduation as a
   ledger event.

If the core operations are still unconfirmed two weeks after a fix ships,
send the reporter one reminder and post a short request for owners of that
model on the forum. Never graduate a radio on elapsed time alone. A
read-only radio (`NEWCHIRP_WRITE_DISABLED`) stays experimental until its
write path is built and confirmed.

Show radios by the manufacturer's official model name wherever people read
it (desktop picker, website catalog, Web Programmer, messages and replies),
for example "DR-735T", not CHIRP's "DR735T". CHIRP driver IDs, catalog model
strings and Web Programmer profile `model` values stay unchanged because
images and matching depend on them. Add verified names to both
`officialRadioModelNames` (`lib/widgets/radio_model_picker.dart`) and
`lib/radio-display-names.ts` in the website, and keep both spellings
searchable.

When a ledger item closes with a user-side cause (cable, port, model
choice, setup) or a fix users must update for, update the website FAQ
(`app/faq/page.tsx` in `/Volumes/RICKEXT/web/newchirpweb`, with its source in
`docs/FAQ_DRAFT.md`). In support replies, link the matching answer as
`https://newchirp.net/faq#<id>`.

For any driver derived from an OEM programming application, follow
`docs/REA_PLAYBOOK.md`. Trace both the UI-to-serial and serial-to-decoder call
paths, document the wire encoding and response-length rules for every
operation, and distinguish static, replay, OEM-capture, and physical-radio
evidence. A recovered memory map or command list is not a complete transport.

## Pull request security review

Treat every pull request as untrusted input, especially when the author is not
a known maintainer. Review the complete diff, not only the PR description,
tests, or generated summaries. Do not merge until both correctness and security
have been reviewed.

Before executing code from a PR:

1. Fetch the current `origin/main` and review in a disposable worktree.
2. Inspect every changed executable file and test, including hidden Unicode,
   encoded payloads, unusually long lines, and generated files that may conceal
   hand-written changes.
3. Search for process execution, shell commands, network access, credential or
   environment access, arbitrary file reads/writes/deletes, telemetry, and
   obfuscation.
4. Check dependency manifests, lockfiles, build scripts, CI workflows, release
   scripts, signing steps, and downloaded artifacts. Dependency, workflow, and
   release changes require an additional explicit review.
5. Verify that radio drivers cannot write outside documented regions, retry
   unsafe flash operations, bypass confirmation, or transmit user/radio data.
6. Scan for secrets, personal paths, private radio images, tokens, passwords,
   and unexpected external URLs.

Run untrusted tests only after the initial audit and use an isolated worktree.
Do not expose real credentials, mail passwords, API tokens, cloud credentials,
signing keys, private codeplugs, or production data to PR code. Prefer the
normal sandbox; request escalation only when required and only after the code
that will run has been audited.

If anything is suspicious or cannot be explained, stop, leave the PR unmerged,
and report the exact file, line, and behavior to the user. A clean test run does
not make an unsafe or unexplained change acceptable.

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
   - Pacman: `NewChirp-linux-x64-1.0.3.pkg.tar.zst`
4. Never overwrite a previously released versioned artifact.
5. Upload to `/opt/newchirp/public/downloads/` with the versioned filename.
6. Verify the embedded version after building.
7. Do not rely solely on generic filenames such as `newchirp-setup.exe` or
   `newchirp.dmg`. The website intentionally ignores generic filenames when
   determining the published version.

The AppImage must not bundle GLVND, EGL, or GLES loader libraries. They must
match the host Mesa or proprietary driver; an old bundled loader can produce a
blank Flutter window on newer distributions.

Linux artifacts must be built on the Ubuntu 20.04 baseline used by the release
workflow. `scripts/check_linux_release_abi.py` must pass before publication; it
rejects newer glibc/GLib requirements, `GLIBC_ABI_DT_RELR`, and GLib 2.80-only
symbols. Do not publish Linux packages built on a rolling desktop host.

The website uses the version in the filename as its source of truth. Each
versioned artifact becomes that platform's current download as soon as it is
uploaded, so platform versions can differ. The current app requests
`/api/releases/latest?platform=<windows|macos|linux>` and receives only that
installer's release object. There is no shared top-level desktop version. The
`.rpm`, AppImage, and Pacman extra buttons appear when matching files are
present.

The Linux download page must distinguish each package format. Keep the helper
text and badges near the matching download:

- DEB: Ubuntu / Debian / Mint.
- RPM: Fedora / RHEL / openSUSE.
- AppImage: Portable Linux or double-click run.
- Pacman: Arch / Omarchy / Manjaro, with a copyable
  `sudo pacman -U ~/Downloads/NewChirp-linux-x64-<version>.pkg.tar.zst`
  command. Do not label the Pacman package as AppImage.

When Android minimum support changes, update every public website reference at
the same time, including the Android download card, hero/platform copy, mobile
guide, and beginner guide. The download-card helper text must match the current
Android minimum, for example `Android 9+ beta build`.

Build release artifacts only on their native platform:

- Build the Windows installer on Windows.
- Build the macOS DMG on macOS.
- Build the Linux packages on Linux.

Do not trigger, wait for, or emulate another platform's build workflow from the
current host. Each machine publishes only the artifact it built.

For the current macOS development host:

- Build, verify, sign, and publish only the macOS DMG here.
- Windows and Linux builds are owned by their respective machines. Do not
  trigger, monitor, or treat their CI jobs as release blockers from this host.
- Coordinate a shared release version with the other platform owners before
  pushing release tags or publishing a cross-platform release.
- Notifying an external reporter requires an explicit request in the current
  task. A completed build, fix, or release upload is not permission to send
  email.

## Privacy and local-only data

- Never store a reporter or tester email address in Git, the driver-work
  database, generated documentation, or commit data. Use the mailbox UID,
  Message-ID, or a non-identifying role such as `reporter`.
- `scripts/check_private_data.py` is mandatory before every commit. The
  checked-in `.githooks/pre-commit` hook runs it automatically when
  `core.hooksPath=.githooks` is configured.
- `build_support` is a machine-local symlink and must remain untracked.
- When the user says "commit everything", inspect and include every intended
  repository change while still excluding or redacting private data and
  machine-local artifacts. Report any intentionally excluded private material
  explicitly.

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
