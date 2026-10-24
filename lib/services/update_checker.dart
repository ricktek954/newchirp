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
  });

  final String currentVersion;
  final String latestVersion;

  /// Page a user should open to download the newest release, when published.
  final String? releaseUrl;

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
  ///       version: 1.0.7,
  ///       release_url: https://newchirp.net/#download,
  ///       downloads: {windows: ..., macos: ..., linux: ...},
  ///       platforms: {
  ///         windows: {version: 1.0.8},
  ///         macos: {version: 1.0.7},
  ///         linux: {version: 1.0.7}
  ///       }
  ///     }
  ///
  /// The app prefers its own entry in `platforms`; `version` (or `latest`) is
  /// the fallback for manifests from older servers. `release_url` (or `url`)
  /// is optional.
  static final Uri defaultManifestUri = Uri.parse(
    'https://newchirp.net/api/releases/latest',
  );

  final Uri manifestUri;
  final String? _platform;
  final Duration _timeout;

  Future<UpdateCheckResult> check(String currentVersion) async {
    final client = HttpClient()..connectionTimeout = _timeout;
    try {
      final request = await client.getUrl(manifestUri).timeout(_timeout);
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
      final manifest = _parseManifest(body);
      final platformRelease =
          manifest.platforms[_platform ?? _currentPlatformKey()];
      return UpdateCheckResult(
        currentVersion: currentVersion,
        latestVersion: platformRelease?.version ?? manifest.version,
        releaseUrl: manifest.releaseUrl,
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

  static _ReleaseManifest _parseManifest(String body) {
    final decoded = jsonDecode(body);
    if (decoded is! Map) {
      throw const FormatException('Manifest is not a JSON object.');
    }
    final version = decoded['version'] ?? decoded['latest'];
    final platforms = <String, _PlatformRelease>{};
    final platformValues = decoded['platforms'];
    if (platformValues is Map) {
      for (final entry in platformValues.entries) {
        final key = entry.key;
        final value = entry.value;
        if (key is! String || value is! Map) continue;
        final platformVersion = value['version'];
        if (platformVersion is! String || platformVersion.trim().isEmpty) {
          continue;
        }
        platforms[key] = _PlatformRelease(version: platformVersion.trim());
      }
    }
    if ((version is! String || version.trim().isEmpty) && platforms.isEmpty) {
      throw const FormatException('Manifest is missing a version.');
    }
    final urlValue = decoded['release_url'] ?? decoded['url'];
    return _ReleaseManifest(
      version: version is String && version.trim().isNotEmpty
          ? version.trim()
          : platforms.values.first.version,
      platforms: platforms,
      releaseUrl: urlValue is String && urlValue.trim().isNotEmpty
          ? urlValue.trim()
          : null,
    );
  }
}

class _ReleaseManifest {
  const _ReleaseManifest({
    required this.version,
    required this.platforms,
    this.releaseUrl,
  });

  final String version;
  final Map<String, _PlatformRelease> platforms;
  final String? releaseUrl;
}

class _PlatformRelease {
  const _PlatformRelease({required this.version});

  final String version;
}

String _currentPlatformKey() {
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
  if (uri == null || !uri.isAbsolute) return false;
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

/// Opens a newchirp.net download page in the default browser.
///
/// Returns false when [url] is not an allowed download page, or when no
/// usable launcher is available. The launched address is rebuilt as https on
/// newchirp.net, so a tricky string cannot change the site.
Future<bool> openExternalUrl(String url) async {
  if (!isAllowedDownloadUrl(url)) return false;
  final allowed = trustedDownloadUrl(url);
  if (!isAllowedDownloadUrl(allowed)) return false;
  try {
    if (Platform.isMacOS) {
      await Process.run('/usr/bin/open', [allowed]);
    } else if (Platform.isWindows) {
      await Process.run(r'C:\Windows\System32\rundll32.exe', [
        'url.dll,FileProtocolHandler',
        allowed,
      ]);
    } else {
      await Process.run('xdg-open', [allowed]);
    }
    return true;
  } on ProcessException {
    return false;
  }
}
