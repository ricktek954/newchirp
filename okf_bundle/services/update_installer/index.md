# update_installer

## Classs

- [DownloadedUpdate](DownloadedUpdate.md) — A downloaded installer ready for the platform-specific update helper.
- [UpdateDownloadProgress](UpdateDownloadProgress.md) — Progress for an in-app update download.
- [UpdateInstaller](UpdateInstaller.md) — Downloads a direct NewChirp installer and starts the native update helper.
- [UpdateInstallException](UpdateInstallException.md) — Raised when an update cannot be downloaded, verified, or started.

## Functions

- [_installLinuxUpdate](installLinuxUpdate.md) — Installs the downloaded .deb/.rpm/etc. through a small helper script run with /bin/sh; output goes to a log file.
- [_installMacUpdate](installMacUpdate.md) — Finds the running .app bundle and starts a detached helper script that
- [_installWindowsUpdate](installWindowsUpdate.md) — Refuses an installer whose Authenticode signature isn't valid (PowerShell
- [download](download.md) — Downloads this platform's installer for [update] into a temp folder.
- [install](install.md) — Starts the detached native helper that will install after the app exits.
- [toString](toString.md) — Installs the downloaded .deb/.rpm/etc. through a small helper script run with /bin/sh; output goes to a log file.
