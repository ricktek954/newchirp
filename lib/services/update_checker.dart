import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Outcome of comparing the installed NewChirp version against the release
/// manifest published by newchirp.net.
class UpdateCheckResult {
  const UpdateCheckResult({
    required this.currentVersion,
    required this.latestVersion,
    required this.releaseUrl,
    this.downloadUrl,
    this.sha256,
  });

  final String currentVersion;
  final String latestVersion;

  /// Page a user should open to download the newest release, when published.
  final String? releaseUrl;

  /// Direct installer artifact published for this platform, when available.
  final String? downloadUrl;

  /// Optional SHA-256 of the installer artifact.
  final String? sha256;

  bool get updateAvailable =>
      compareVersions(latestVersion, currentVersion) > 0;
}

/// Raised when the release manifest cannot be retrieved or parsed.
class UpdateCheckException implements Exception {
  UpdateCheckException(this.message);

  final String message;

  @override
  String toString() => message;
}

/// Queries the NewChirp download server for the newest published release.
class UpdateChecker {
  UpdateChecker({
    Uri? manifestUri,
    Duration timeout = const Duration(seconds: 12),
    String? platform,
  }) : manifestUri = manifestUri ?? defaultManifestUri,
       _platform = platform,
       _timeout = timeout;

  /// Machine-readable release manifest served by newchirp.net.
  ///
  /// Expected JSON body:
  ///
  ///     {
  ///       platform: macos,
  ///       version: 1.0.7,
  ///       download_url: https://newchirp.net/downloads/NewChirp-1.0.7.dmg,
  ///       release_url: https://newchirp.net/#download,
  ///     }
  ///
  /// The client requests only its own platform, whose version is authoritative.
  /// `release_url` (or `url`) is optional.
  static final Uri defaultManifestUri = Uri.parse(
    'https://newchirp.net/api/releases/latest',
  );

  final Uri manifestUri;
  final String? _platform;
  final Duration _timeout;

  Future<UpdateCheckResult> check(String currentVersion) async {
    final client = HttpClient()..connectionTimeout = _timeout;
    try {
      final platform = _platform ?? currentUpdatePlatform();
      if (platform.isEmpty) {
        throw const FormatException('This platform cannot check for updates.');
      }
      final requestUri = manifestUri.replace(
        queryParameters: {...manifestUri.queryParameters, 'platform': platform},
      );
      final request = await client.getUrl(requestUri).timeout(_timeout);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      final response = await request.close().timeout(_timeout);
      if (response.statusCode != HttpStatus.ok) {
        throw UpdateCheckException(
          'The update service returned status ${response.statusCode}.',
        );
      }
      final body = await response
          .transform(utf8.decoder)
          .join()
          .timeout(_timeout);
      final release = _parsePlatformRelease(body);
      return UpdateCheckResult(
        currentVersion: currentVersion,
        latestVersion: release.version,
        releaseUrl: release.releaseUrl,
        downloadUrl: release.downloadUrl,
        sha256: release.sha256,
      );
    } on UpdateCheckException {
      rethrow;
    } on TimeoutException {
      throw UpdateCheckException('The update check timed out.');
    } on SocketException {
      throw UpdateCheckException('Could not reach the update service.');
    } on FormatException {
      throw UpdateCheckException(
        'The update service returned an unexpected response.',
      );
    } finally {
      client.close(force: true);
    }
  }

  static _PlatformRelease _parsePlatformRelease(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map) {
      throw const FormatException('Manifest is not a JSON object.');
    }
    final version = decoded['version'];
    if (version is! String || version.trim().isEmpty) {
      throw const FormatException('Manifest is missing a version.');
    }
    final downloadUrl = decoded['download_url'] ?? decoded['downloadUrl'];
    final sha256 = decoded['sha256'];
    final urlValue = decoded['release_url'] ?? decoded['url'];
    return _PlatformRelease(
      version: version.trim(),
      downloadUrl: downloadUrl is String && downloadUrl.trim().isNotEmpty
          ? downloadUrl.trim()
          : null,
      sha256: sha256 is String && sha256.trim().isNotEmpty
          ? sha256.trim()
          : null,
      releaseUrl: urlValue is String && urlValue.trim().isNotEmpty
          ? urlValue.trim()
          : null,
    );
  }
}

class _PlatformRelease {
  const _PlatformRelease({
    required this.version,
    this.downloadUrl,
    this.sha256,
    this.releaseUrl,
  });

  final String version;
  final String? downloadUrl;
  final String? sha256;
  final String? releaseUrl;
}

String currentUpdatePlatform() {
  if (Platform.isWindows) return 'windows';
  if (Platform.isMacOS) return 'macos';
  if (Platform.isLinux) return 'linux';
  if (Platform.isAndroid) return 'android';
  return '';
}

/// Compares two dotted version strings, ignoring any `+build` metadata.
///
/// Returns a positive number when [a] is newer than [b], a negative number
/// when [a] is older, and zero when they are equivalent.
int compareVersions(String a, String b) {
  final aParts = _versionParts(a);
  final bParts = _versionParts(b);
  final length = aParts.length > bParts.length ? aParts.length : bParts.length;
  for (var i = 0; i < length; i++) {
    final aPart = i < aParts.length ? aParts[i] : 0;
    final bPart = i < bParts.length ? bParts[i] : 0;
    if (aPart != bPart) return aPart - bPart;
  }
  return 0;
}

List<int> _versionParts(String version) {
  final core = version.split('+').first.split('-').first.trim();
  return core
      .split('.')
      .map((part) {
        final digits = RegExp(r'\d+').stringMatch(part);
        return digits == null ? 0 : int.parse(digits);
      })
      .toList(growable: false);
}

/// Download page used when a manifest link is missing or not on this site.
const String officialDownloadPageUrl = 'https://newchirp.net/#download';

/// True when [url] is an https link on newchirp.net, with no login or odd port.
bool isAllowedDownloadUrl(String url) {
  final trimmed = url.trim();
  if (trimmed.isEmpty || trimmed.contains(RegExp(r'[\s\\]'))) return false;
  final uri = Uri.tryParse(trimmed);
  // `Uri.isAbsolute` is false for any URI with a fragment, and the published
  // download page is `https://newchirp.net/#download`.
  if (uri == null || !uri.hasScheme) return false;
  if (uri.scheme != 'https') return false;
  if (uri.userInfo.isNotEmpty) return false;
  if (uri.host != 'newchirp.net') return false;
  if (uri.hasPort && uri.port != 443) return false;
  return true;
}

/// Address the Update button may open. Untrusted links use the official page.
String trustedDownloadUrl(String? raw) {
  final candidate = (raw ?? '').trim();
  if (!isAllowedDownloadUrl(candidate)) return officialDownloadPageUrl;
  final uri = Uri.parse(candidate);
  return Uri(
    scheme: 'https',
    host: 'newchirp.net',
    path: uri.path,
    query: uri.hasQuery ? uri.query : null,
    fragment: uri.hasFragment ? uri.fragment : null,
  ).toString();
}

/// File extension used by an installable desktop update for [platform].
String? updateArtifactExtension([String? platform]) {
  return switch (platform ?? currentUpdatePlatform()) {
    'macos' => '.dmg',
    // Windows installers are not code-signed yet, so updates remain manual.
    'windows' => null,
    'linux' => '.deb',
    _ => null,
  };
}

/// Validated installer URL for [platform], or null when it is not installable.
///
/// The artifact must be HTTPS on newchirp.net and have the native desktop
/// package extension. Fragments are discarded before the URL is used.
String? trustedUpdateArtifactUrl(String? raw, {String? platform}) {
  final extension = updateArtifactExtension(platform);
  if (extension == null || !isAllowedDownloadUrl(raw ?? '')) return null;
  final trusted = trustedDownloadUrl(raw);
  final uri = Uri.parse(trusted);
  if (!uri.path.toLowerCase().endsWith(extension)) return null;
  return Uri(
    scheme: 'https',
    host: 'newchirp.net',
    path: uri.path,
    query: uri.hasQuery ? uri.query : null,
  ).toString();
}

/// Opens a newchirp.net download page in the default browser.
///
/// Returns false when [url] is not an allowed download page, or when the
/// launcher refused to start. The launched address is rebuilt as https on
/// newchirp.net, so a tricky string cannot change the site.
///
/// [launcher] replaces the platform launcher in tests.
Future<bool> openExternalUrl(
  String url, {
  Future<bool> Function(String url)? launcher,
}) async {
  if (!isAllowedDownloadUrl(url)) return false;
  final allowed = trustedDownloadUrl(url);
  if (!isAllowedDownloadUrl(allowed)) return false;
  final launch = launcher ?? _launchExternalUrl;
  try {
    return await launch(allowed);
  } on ProcessException {
    return false;
  } on ArgumentError {
    return false;
  }
}

/// Starts the platform browser for an already validated address.
///
/// Windows hands the address to Explorer, the shell entry point a user reaches
/// by clicking a link. Earlier builds shelled out to
/// `rundll32 url.dll,FileProtocolHandler`, which endpoint protection software
/// blocks by policy and which reports no error at all when it does nothing.
/// Explorer exits with a non-zero code even when it opens the page, so only a
/// failure to start the process counts as a failed launch.
Future<bool> _launchExternalUrl(String url) async {
  if (Platform.isWindows) {
    await Process.start(r'C:\Windows\explorer.exe', [
      url,
    ], mode: ProcessStartMode.detached);
    return true;
  }
  final result = Platform.isMacOS
      ? await Process.run('/usr/bin/open', [url])
      : await Process.run('xdg-open', [url]);
  return result.exitCode == 0;
}
