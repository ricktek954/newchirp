# Linux Wayland write-freeze test

Instructions for the Linux build machine (or its agent). No radio is needed.
Do not publish anything built for this test.

## Why

Ledger item `w-20261121-ab4d` (Baofeng DM-32UV, Manjaro KDE Plasma on
Wayland, AppImage 1.0.68 and 1.0.72): during a write the NewChirp window
stays on 18% and must be killed. The owner's diagnostics show every write
completing normally ("Radio write completed" after 51-55 s, no adjustments),
and the radio reboots as it should. After the write, the NewChirp app process
was at 98.5% CPU and 4.9 GB RSS. An earlier upload showed Cancel clicks
registering while the window looked frozen.

So the Dart side keeps running but the window stops showing new frames. The
leading theory is Flutter's Linux/GTK presentation on KDE Wayland; it is not
proven. The radio transfer is not the cause, so it can be reproduced with a
simulated write.

## What the app now provides (commit on main after 2026-11-24)

- `NEWCHIRP_SIMULATE_WRITE=<seconds>`: about one second after startup, the
  app runs the normal write progress window with no radio. It shows the
  DM-32UV's real messages ("Scanning flash pages" up to 18%, then "Writing to
  radio ... (memory page N)" for 120 pages) and logs "Simulated write
  started/completed", including `XDG_SESSION_TYPE`, `GDK_BACKEND` and
  `XDG_CURRENT_DESKTOP`.
- During every transfer (real or simulated) the diagnostics log gets a
  "Transfer heartbeat" entry every 5 s with `framesLast5s` (frames Flutter
  rasterized), `rssMB` (app memory) and `fraction`.

Diagnostics log: `~/.local/state/newchirp/logs/diagnostics.jsonl`
(or `$XDG_STATE_HOME/newchirp/logs/`).

Healthy baseline (macOS, 20 s run): `framesLast5s` 41-49 in every entry,
`rssMB` steady at about 300, then "Simulated write completed".

## Setup

1. `git pull` on main, then build as usual:
   `flutter build linux --release`, then
   `scripts/build_linux_appimage.sh --output /tmp/NewChirp-freeze-test.AppImage`.
   Testing the AppImage matters because that is what the owner runs; a
   `flutter run -d linux` debug run is a useful extra data point.
2. Log in to a **KDE Plasma Wayland** session (`echo $XDG_SESSION_TYPE`
   prints `wayland`). A virtual machine may not reproduce GPU presentation
   problems; prefer real hardware or a live USB of Manjaro KDE or Kubuntu.
3. Keep a system monitor open (`btop` or `htop`) filtered to `newchirp`.
4. Record the GPU and driver (`inxi -G` or `glxinfo -B`) and the Plasma and
   Mesa versions.

## Runs

Clear the old log between runs (`mv` it aside) so each run's entries are easy
to read. Use 60 seconds, about as long as a real DM-32UV write.

| Run | Command | During the write |
|-----|---------|------------------|
| A | `NEWCHIRP_SIMULATE_WRITE=60 /tmp/NewChirp-freeze-test.AppImage` | Leave the NewChirp window in front |
| B | same as A | At about 10 s, switch to another window or virtual desktop; return at about 40 s |
| C | same as A | Minimise NewChirp for 30 s |
| D | `GDK_BACKEND=x11 NEWCHIRP_SIMULATE_WRITE=60 /tmp/NewChirp-freeze-test.AppImage` | Repeat B (XWayland) |
| E | Log in to a Plasma **X11** session, repeat B | Control |

For each run, note:

- whether the window reaches 100% and the progress window closes;
- the highest CPU and memory for the `newchirp` process, and whether they
  stay high after "Simulated write completed";
- the heartbeat lines: `framesLast5s` dropping to 0 while the window shows a
  stale percentage, and `rssMB` climbing, are the freeze signature.

If none of A-C freezes, try a real-length run of 120 s and a run with
NewChirp on a second monitor at a different scale factor, then report the
negative result. It is useful too.

## Reporting back

Add a ledger event (do not include personal data):

```sh
python3 scripts/driver_work.py event w-20261121-ab4d --type test \
  --summary "Wayland freeze test: A=..., B=..., C=..., D=..., E=...; GPU/driver/Plasma/Mesa ..." \
  --ref "linux:<commit>"
python3 scripts/driver_work.py export
```

Commit the ledger JSON and `docs/DRIVER_WORK.md`, and keep the relevant
diagnostics lines (heartbeat entries) in the event summary or a short note
under `docs/`. Do not commit the AppImage.

## If it reproduces

Likely next steps, in order:

1. Check whether frames stop only while the window is hidden or occluded
   (runs B/C freeze, A does not). If so, look at the GTK frame clock and the
   Flutter engine version for known Linux Wayland presentation issues, and
   test the current Flutter stable.
2. Check whether `GDK_BACKEND=x11` (run D) is clean. If it is, a short-term
   fix is for the AppImage launcher to prefer X11 when XWayland is
   available, until the engine issue is fixed.
3. Reduce animation during transfers (the indeterminate spinner and the
   1-second elapsed-time ticker) and retest, to see whether continuous
   repaint requests are what pile up.

## Outcome (2026-11-24)

The owner confirmed that `GDK_BACKEND=x11` (XWayland) avoids the freeze on
1.0.72 (INBOX:958). Their setup: KDE Plasma `kwin_wayland`, Intel TigerLake
Iris Xe (i915, Mesa 26.2.7) plus NVIDIA GTX 1650 Mobile (driver 620.70.06).
A Hyprland session on Intel graphics did not reproduce it.

`linux/runner/main.cc` now sets `GDK_BACKEND=x11` before GTK starts when a
Wayland session also offers XWayland (`WAYLAND_DISPLAY` and `DISPLAY` set).
An existing `GDK_BACKEND` is respected, and `NEWCHIRP_WAYLAND=1` keeps the
native Wayland backend. The startup diagnostics entry records `session` and
`gdkBackend` on Linux. This covers every Linux package format because they
all start the same binary.
