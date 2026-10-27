# update_checker

## Classs

- [_PlatformRelease](PlatformRelease.md)
- [_ReleaseManifest](ReleaseManifest.md)
- [UpdateCheckResult](UpdateCheckResult.md) — Outcome of comparing the installed NewChirp version against the release

## Functions

- [_parseManifest](parseManifest.md) — Opens a newchirp.net download page in the default browser.
- [_versionParts](versionParts.md)
- [check](check.md) — Opens a newchirp.net download page in the default browser.
- [compareVersions](compareVersions.md) — Compares two dotted version strings, ignoring any `+build` metadata.
- [currentUpdatePlatform](currentUpdatePlatform.md)
- [isAllowedDownloadUrl](isAllowedDownloadUrl.md) — True when [url] is an https link on newchirp.net, with no login or odd port.
- [openExternalUrl](openExternalUrl.md) — Opens a newchirp.net download page in the default browser.
- [toString](toString.md) — Opens a newchirp.net download page in the default browser.
- [trustedDownloadUrl](trustedDownloadUrl.md) — Address the Update button may open. Untrusted links use the official page.
- [trustedUpdateArtifactUrl](trustedUpdateArtifactUrl.md) — Validated installer URL for [platform], or null when it is not installable.
- [updateArtifactExtension](updateArtifactExtension.md) — File extension used by an installable desktop update for [platform].
- [UpdateChecker](UpdateChecker.md)
- [UpdateCheckException](UpdateCheckException.md)
