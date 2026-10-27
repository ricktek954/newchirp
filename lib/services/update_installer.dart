import 'dart:async';
import 'dart:io';

import 'package:crypto/crypto.dart';

import 'update_checker.dart';

/// Progress for an in-app update download.
class UpdateDownloadProgress {
  const UpdateDownloadProgress({required this.receivedBytes, this.totalBytes});

  final int receivedBytes;
  final int? totalBytes;

  double? get fraction {
    final total = totalBytes;
    if (total == null || total <= 0) return null;
    return (receivedBytes / total).clamp(0.0, 1.0);
  }
}

/// A downloaded installer ready for the platform-specific update helper.
class DownloadedUpdate {
  const DownloadedUpdate({
    required this.path,
    required this.platform,
    required this.version,
  });

  final String path;
  final String platform;
  final String version;
}

/// Raised when an update cannot be downloaded, verified, or started.
class UpdateInstallException implements Exception {
  const UpdateInstallException(this.message);

  final String message;

  @override
  String toString() => message;
}

typedef UpdateProgressCallback = void Function(UpdateDownloadProgress progress);

/// Downloads a direct NewChirp installer and starts the native update helper.
///
/// The app exits after [install] returns. Each helper waits for that exit,
/// replaces the application, and relaunches NewChirp.
class UpdateInstaller {
  const UpdateInstaller();

  static const _maxDownloadBytes = 1024 * 1024 * 1024;

  Future<DownloadedUpdate> download(
    UpdateCheckResult update, {
    UpdateProgressCallback? onProgress,
  }) async {
    final platform = currentUpdatePlatform();
    final extension = updateArtifactExtension(platform);
    final url = trustedUpdateArtifactUrl(
      update.downloadUrl,
      platform: platform,
    );
    if (extension == null || url == null) {
      throw UpdateInstallException(
        'This release does not publish an installable package for your system.',
      );
    }

    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 20);
    Directory? directory;
    var keepDirectory = false;
    try {
      final request = await client
          .getUrl(Uri.parse(url))
          .timeout(const Duration(seconds: 20));
      request.followRedirects = false;
      request.headers.set(HttpHeaders.acceptHeader, 'application/octet-stream');
      final response = await request.close().timeout(
        const Duration(seconds: 20),
      );
      if (response.statusCode != HttpStatus.ok) {
        throw UpdateInstallException(
          'The update download returned status ${response.statusCode}.',
        );
      }

      final declaredLength = response.contentLength;
      if (declaredLength > _maxDownloadBytes) {
        throw UpdateInstallException(
          'The update download is unexpectedly large.',
        );
      }

      directory = await Directory.systemTemp.createTemp('newchirp-update-');
      final safeVersion = update.latestVersion.replaceAll(
        RegExp(r'[^A-Za-z0-9._-]'),
        '_',
      );
      final file = File('${directory.path}/NewChirp-$safeVersion$extension');
      final sink = file.openWrite();
      var received = 0;
      onProgress?.call(
        UpdateDownloadProgress(
          receivedBytes: received,
          totalBytes: declaredLength > 0 ? declaredLength : null,
        ),
      );
      try {
        await for (final chunk in response.timeout(
          const Duration(seconds: 30),
        )) {
          received += chunk.length;
          if (received > _maxDownloadBytes) {
            throw UpdateInstallException(
              'The update download is unexpectedly large.',
            );
          }
          sink.add(chunk);
          onProgress?.call(
            UpdateDownloadProgress(
              receivedBytes: received,
              totalBytes: declaredLength > 0 ? declaredLength : null,
            ),
          );
        }
      } finally {
        await sink.close();
      }

      if (declaredLength > 0 && received != declaredLength) {
        throw UpdateInstallException(
          'The update download was incomplete. Try again.',
        );
      }
      if (received == 0) {
        throw const UpdateInstallException('The update download was empty.');
      }

      final expectedHash = update.sha256?.trim().toLowerCase();
      if (expectedHash != null && expectedHash.isNotEmpty) {
        if (!RegExp(r'^[a-f0-9]{64}$').hasMatch(expectedHash)) {
          throw const UpdateInstallException(
            'The update manifest contains an invalid checksum.',
          );
        }
        final actualHash = (await sha256.bind(file.openRead()).first)
            .toString();
        if (actualHash != expectedHash) {
          throw const UpdateInstallException(
            'The downloaded update failed its integrity check.',
          );
        }
      }

      keepDirectory = true;
      return DownloadedUpdate(
        path: file.path,
        platform: platform,
        version: update.latestVersion,
      );
    } on UpdateInstallException {
      rethrow;
    } on TimeoutException {
      throw const UpdateInstallException('The update download timed out.');
    } on SocketException {
      throw const UpdateInstallException('Could not reach the update server.');
    } on FileSystemException {
      throw const UpdateInstallException(
        'Could not save the downloaded update.',
      );
    } finally {
      client.close(force: true);
      if (!keepDirectory && directory != null) {
        try {
          await directory.delete(recursive: true);
        } on FileSystemException {
          // A failed download should not mask the original error.
        }
      }
    }
  }

  /// Starts the detached native helper that will install after the app exits.
  Future<void> install(DownloadedUpdate update) async {
    final file = File(update.path);
    if (!await file.exists()) {
      throw const UpdateInstallException('The downloaded update is missing.');
    }
    try {
      switch (update.platform) {
        case 'macos':
          await _installMacUpdate(file);
        case 'windows':
          await _installWindowsUpdate(file);
        case 'linux':
          await _installLinuxUpdate(file);
        default:
          throw const UpdateInstallException(
            'Automatic installation is not supported on this platform.',
          );
      }
    } on UpdateInstallException {
      rethrow;
    } on ProcessException {
      throw const UpdateInstallException(
        'Could not start the update installer.',
      );
    } on FileSystemException {
      throw const UpdateInstallException(
        'Could not prepare the update installer.',
      );
    }
  }

  Future<void> _installMacUpdate(File dmg) async {
    final executable = Platform.resolvedExecutable;
    const marker = '/Contents/MacOS/';
    final markerIndex = executable.indexOf(marker);
    if (markerIndex <= 0) {
      throw const UpdateInstallException(
        'Could not locate the NewChirp application bundle.',
      );
    }
    final appPath = executable.substring(0, markerIndex);
    if (!appPath.endsWith('.app')) {
      throw const UpdateInstallException(
        'Could not locate the NewChirp application bundle.',
      );
    }

    final directory = Directory.systemTemp.createTempSync('newchirp-install-');
    final helper = File('${directory.path}/install-update.sh');
    final log = '${directory.path}/install-update.log';
    await helper.writeAsString(_macInstallScript, flush: true);
    await Process.run('/bin/chmod', ['700', helper.path]);
    await Process.start('/bin/sh', [
      helper.path,
      pid.toString(),
      dmg.path,
      appPath,
      log,
    ], mode: ProcessStartMode.detached);
  }

  Future<void> _installWindowsUpdate(File installer) async {
    final signature = await Process.run(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        r'$s = Get-AuthenticodeSignature -LiteralPath $env:NEWCHIRP_INSTALLER;'
            r'if ($s.Status -ne "Valid") { exit 7 }',
      ],
      environment: {'NEWCHIRP_INSTALLER': installer.path},
    );
    if (signature.exitCode != 0) {
      throw const UpdateInstallException(
        'The downloaded Windows installer does not have a valid signature.',
      );
    }

    final directory = Directory.systemTemp.createTempSync('newchirp-install-');
    final helper = File('${directory.path}/install-update.ps1');
    final log = '${directory.path}/install-update.log';
    await helper.writeAsString(_windowsInstallScript, flush: true);
    await Process.start('powershell.exe', [
      '-NoProfile',
      '-ExecutionPolicy',
      'Bypass',
      '-File',
      helper.path,
      pid.toString(),
      installer.path,
      log,
    ], mode: ProcessStartMode.detached);
  }

  Future<void> _installLinuxUpdate(File package) async {
    final directory = Directory.systemTemp.createTempSync('newchirp-install-');
    final helper = File('${directory.path}/install-update.sh');
    final log = '${directory.path}/install-update.log';
    await helper.writeAsString(_linuxInstallScript, flush: true);
    await Process.run('/bin/chmod', ['700', helper.path]);
    await Process.start('/bin/sh', [
      helper.path,
      pid.toString(),
      package.path,
      Platform.resolvedExecutable,
      log,
    ], mode: ProcessStartMode.detached);
  }
}

const _macInstallScript = r"""
#!/bin/sh
set -u

parent_pid="$1"
dmg="$2"
target_app="$3"
log="$4"
exec >>"$log" 2>&1

while kill -0 "$parent_pid" 2>/dev/null; do
  sleep 0.2
done

mount_point="$(mktemp -d "${TMPDIR:-/tmp}/newchirp-update-mount.XXXXXX")"
staging_root="$(mktemp -d "${TMPDIR:-/tmp}/newchirp-update-stage.XXXXXX")"
staged_app="$staging_root/NewChirp.app"
keep_mounted=0
cleanup() {
  if [ "$keep_mounted" -eq 0 ]; then
    /usr/bin/hdiutil detach "$mount_point" -quiet >/dev/null 2>&1 || true
  fi
  /bin/rmdir "$mount_point" >/dev/null 2>&1 || true
  /bin/rm -rf "$staging_root"
}
fallback() {
  keep_mounted=1
  /usr/bin/osascript -e 'display notification "Automatic installation could not finish. The downloaded disk image is open so you can install manually." with title "NewChirp update"'
  /usr/bin/open "$dmg"
  exit 1
}
trap cleanup EXIT INT TERM

if ! /usr/bin/hdiutil attach -nobrowse -readonly -mountpoint "$mount_point" "$dmg" >/dev/null; then
  fallback
fi

source_app="$(/usr/bin/find "$mount_point" -maxdepth 1 -name '*.app' -print -quit)"
if [ -z "$source_app" ] || [ ! -d "$source_app" ]; then
  fallback
fi

if ! /usr/bin/codesign --verify --deep --strict "$source_app"; then
  fallback
fi
if ! /usr/sbin/spctl --assess --type execute "$source_app"; then
  fallback
fi

bundle_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$source_app/Contents/Info.plist" 2>/dev/null || true)"
if [ "$bundle_id" != "com.rickext.newchirp" ]; then
  fallback
fi

if ! /usr/bin/ditto "$source_app" "$staged_app"; then
  fallback
fi

backup_app="${target_app}.newchirp-backup.$$"

if [ -w "$(dirname "$target_app")" ]; then
  if ! /bin/mv "$target_app" "$backup_app"; then
    fallback
  fi
  if ! /bin/mv "$staged_app" "$target_app"; then
    /bin/mv "$backup_app" "$target_app"
    fallback
  fi
  /bin/rm -rf "$backup_app"
else
  if ! /usr/bin/osascript - "$target_app" "$staged_app" "$backup_app" <<'APPLESCRIPT'
on run argv
  set targetPath to item 1 of argv
  set stagedPath to item 2 of argv
  set backupPath to item 3 of argv
  set commandText to "/bin/mv " & quoted form of targetPath & " " & quoted form of backupPath
  set commandText to commandText & " && if /bin/mv " & quoted form of stagedPath & " " & quoted form of targetPath
  set commandText to commandText & "; then /bin/rm -rf " & quoted form of backupPath
  set commandText to commandText & "; else /bin/mv " & quoted form of backupPath & " " & quoted form of targetPath & "; exit 1; fi"
  do shell script commandText with administrator privileges
end run
APPLESCRIPT
  then
    fallback
  fi
fi

/usr/bin/open "$target_app"
/bin/rm -f "$dmg"
/bin/rm -rf "$(dirname "$dmg")"
""";

const _windowsInstallScript = r"""
param(
  [Parameter(Mandatory = $true)][int]$ParentPid,
  [Parameter(Mandatory = $true)][string]$Installer,
  [Parameter(Mandatory = $true)][string]$LogPath
)

Start-Transcript -Path $LogPath -Append
while (Get-Process -Id $ParentPid -ErrorAction SilentlyContinue) {
  Start-Sleep -Milliseconds 200
}

$arguments = @(
  '/VERYSILENT',
  '/SUPPRESSMSGBOXES',
  '/NORESTART',
  '/CLOSEAPPLICATIONS',
  '/FORCECLOSEAPPLICATIONS',
  '/LAUNCHAPP=1'
)
$process = Start-Process -FilePath $Installer -ArgumentList $arguments -Wait -PassThru
if ($process.ExitCode -ne 0) {
  Start-Process -FilePath $Installer
}
Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
Stop-Transcript
""";

const _linuxInstallScript = r"""
#!/bin/sh
set -u

parent_pid="$1"
package="$2"
app_path="$3"
log="$4"
exec >>"$log" 2>&1

while kill -0 "$parent_pid" 2>/dev/null; do
  sleep 0.2
done

installed=1
if command -v pkexec >/dev/null 2>&1; then
  if pkexec env DEBIAN_FRONTEND=noninteractive apt-get install -y "$package"; then
    installed=0
  fi
elif command -v apt-get >/dev/null 2>&1; then
  if apt-get install -y "$package"; then
    installed=0
  fi
fi

if [ "$installed" -eq 0 ]; then
  /bin/rm -f "$package"
  if [ -x "$app_path" ]; then
    nohup "$app_path" >/dev/null 2>&1 &
  elif command -v newchirp >/dev/null 2>&1; then
    nohup newchirp >/dev/null 2>&1 &
  fi
else
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "NewChirp update" "Automatic installation could not finish. The downloaded package is open so you can install it with your package manager." || true
  fi
  xdg-open "$package" >/dev/null 2>&1 || true
fi
""";
