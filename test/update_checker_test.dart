import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:newchirp/services/update_checker.dart';

void main() {
  group('compareVersions', () {
    test('orders dotted versions numerically', () {
      expect(compareVersions('1.0.2', '1.0.1'), greaterThan(0));
      expect(compareVersions('1.0.1', '1.0.2'), lessThan(0));
      expect(compareVersions('1.0.1', '1.0.1'), 0);
      expect(compareVersions('1.10.0', '1.9.9'), greaterThan(0));
      expect(compareVersions('2.0', '1.9.9'), greaterThan(0));
      expect(compareVersions('1.2', '1.2.0'), 0);
    });

    test('ignores build metadata and pre-release suffixes', () {
      expect(compareVersions('1.0.1+7', '1.0.1'), 0);
      expect(compareVersions('1.0.2-beta', '1.0.1'), greaterThan(0));
    });
  });

  group('UpdateChecker', () {
    HttpServer? server;

    Future<Uri> serve(String body, {int status = 200}) async {
      final bound = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
      server = bound;
      bound.listen((request) async {
        request.response.statusCode = status;
        request.response.headers.contentType = ContentType.json;
        request.response.write(body);
        await request.response.close();
      });
      return Uri.parse('http://127.0.0.1:${bound.port}/api/releases/latest');
    }

    tearDown(() async {
      await server?.close(force: true);
      server = null;
    });

    test('reports an update when the manifest is newer', () async {
      final uri = await serve(
        jsonEncode({
          'version': '1.0.2',
          'release_url': 'https://newchirp.net/#download',
        }),
      );
      final result = await UpdateChecker(manifestUri: uri).check('1.0.1');
      expect(result.updateAvailable, isTrue);
      expect(result.latestVersion, '1.0.2');
      expect(result.releaseUrl, 'https://newchirp.net/#download');
    });

    test('uses the version published for the current platform', () async {
      final uri = await serve(
        jsonEncode({
          'version': '1.0.7',
          'platforms': {
            'windows': {'version': '1.0.8'},
            'macos': {'version': '1.0.7'},
            'linux': {'version': '1.0.7'},
          },
        }),
      );

      final windows = await UpdateChecker(
        manifestUri: uri,
        platform: 'windows',
      ).check('1.0.7');
      final macos = await UpdateChecker(
        manifestUri: uri,
        platform: 'macos',
      ).check('1.0.7');

      expect(windows.latestVersion, '1.0.8');
      expect(windows.updateAvailable, isTrue);
      expect(macos.latestVersion, '1.0.7');
      expect(macos.updateAvailable, isFalse);
    });

    test('returns the direct platform installer and checksum', () async {
      final uri = await serve(
        jsonEncode({
          'version': '1.0.7',
          'platforms': {
            'macos': {
              'version': '1.0.8',
              'download_url':
                  'https://newchirp.net/downloads/NewChirp-1.0.8.dmg',
              'sha256':
                  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            },
          },
        }),
      );

      final result = await UpdateChecker(
        manifestUri: uri,
        platform: 'macos',
      ).check('1.0.7');

      expect(
        result.downloadUrl,
        'https://newchirp.net/downloads/NewChirp-1.0.8.dmg',
      );
      expect(
        result.sha256,
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
      );
    });

    test('uses legacy downloads when platform metadata has no URL', () async {
      final uri = await serve(
        jsonEncode({
          'version': '1.0.8',
          'downloads': {
            'macos': 'https://newchirp.net/downloads/NewChirp-1.0.8.dmg',
          },
          'checksums': {
            'macos':
                'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
          },
          'platforms': {
            'macos': {'version': '1.0.8'},
          },
        }),
      );

      final result = await UpdateChecker(
        manifestUri: uri,
        platform: 'macos',
      ).check('1.0.7');

      expect(
        result.downloadUrl,
        'https://newchirp.net/downloads/NewChirp-1.0.8.dmg',
      );
      expect(
        result.sha256,
        'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
      );
    });

    test('accepts platform versions without a legacy version', () async {
      final uri = await serve(
        jsonEncode({
          'platforms': {
            'windows': {'version': '1.0.8'},
          },
        }),
      );

      final result = await UpdateChecker(
        manifestUri: uri,
        platform: 'windows',
      ).check('1.0.7');

      expect(result.latestVersion, '1.0.8');
      expect(result.updateAvailable, isTrue);
    });

    test('reports up to date when versions match', () async {
      final uri = await serve(jsonEncode({'version': '1.0.1'}));
      final result = await UpdateChecker(manifestUri: uri).check('1.0.1');
      expect(result.updateAvailable, isFalse);
      expect(result.releaseUrl, isNull);
    });

    test('accepts the latest alias for the version field', () async {
      final uri = await serve(jsonEncode({'latest': '2.0.0'}));
      final result = await UpdateChecker(manifestUri: uri).check('1.0.1');
      expect(result.latestVersion, '2.0.0');
      expect(result.updateAvailable, isTrue);
    });

    test('throws UpdateCheckException when the response is not JSON', () async {
      final uri = await serve('<html></html>');
      await expectLater(
        UpdateChecker(manifestUri: uri).check('1.0.1'),
        throwsA(isA<UpdateCheckException>()),
      );
    });

    test('throws UpdateCheckException on a server error', () async {
      final uri = await serve('{}', status: 500);
      await expectLater(
        UpdateChecker(manifestUri: uri).check('1.0.1'),
        throwsA(isA<UpdateCheckException>()),
      );
    });
  });

  group('trustedDownloadUrl', () {
    test('keeps https pages on newchirp.net', () {
      expect(
        trustedDownloadUrl('https://newchirp.net/#download'),
        'https://newchirp.net/#download',
      );
      expect(
        trustedDownloadUrl(
          'https://NEWCHIRP.NET/downloads/NewChirp-1.0.15.dmg',
        ),
        'https://newchirp.net/downloads/NewChirp-1.0.15.dmg',
      );
      expect(
        trustedDownloadUrl('https://newchirp.net:443/#download'),
        'https://newchirp.net/#download',
      );
    });

    test('replaces links that are not the NewChirp site', () {
      const rejected = [
        'http://newchirp.net/#download',
        'https://www.newchirp.net/#download',
        'https://newchirp.net.evil.com/setup',
        'https://evil.example/newchirp.net',
        'https://user:pass@newchirp.net/#download',
        'https://newchirp.net:8443/setup',
        'https://newchirp.net\\@evil.example',
        'file:///etc/passwd',
        'calc.exe',
        '',
      ];
      for (final url in rejected) {
        expect(trustedDownloadUrl(url), officialDownloadPageUrl, reason: url);
      }
      expect(trustedDownloadUrl(null), officialDownloadPageUrl);
    });

    test('does not launch a page outside newchirp.net', () async {
      expect(await openExternalUrl('https://evil.example/setup.exe'), isFalse);
      expect(await openExternalUrl('calc.exe'), isFalse);
      expect(await openExternalUrl('http://newchirp.net/#download'), isFalse);
    });
  });

  group('trustedUpdateArtifactUrl', () {
    test('accepts packages for platforms with automatic updates', () {
      expect(
        trustedUpdateArtifactUrl(
          'https://newchirp.net/downloads/NewChirp-1.0.23.dmg',
          platform: 'macos',
        ),
        'https://newchirp.net/downloads/NewChirp-1.0.23.dmg',
      );
      expect(
        trustedUpdateArtifactUrl(
          'https://newchirp.net/downloads/NewChirp-linux-x64-1.0.23.deb',
          platform: 'linux',
        ),
        'https://newchirp.net/downloads/NewChirp-linux-x64-1.0.23.deb',
      );
    });

    test('keeps Windows updates manual until installers are signed', () {
      expect(
        trustedUpdateArtifactUrl(
          'https://newchirp.net/downloads/NewChirp-Installer-1.0.23.exe',
          platform: 'windows',
        ),
        isNull,
      );
      expect(
        trustedUpdateArtifactUrl(
          'https://newchirp.net/downloads/NewChirp-1.0.23.dmg',
          platform: 'windows',
        ),
        isNull,
      );
    });

    test('rejects untrusted hosts and insecure downloads', () {
      expect(
        trustedUpdateArtifactUrl(
          'https://evil.example/NewChirp-1.0.23.dmg',
          platform: 'macos',
        ),
        isNull,
      );
      expect(
        trustedUpdateArtifactUrl(
          'http://newchirp.net/downloads/NewChirp-1.0.23.dmg',
          platform: 'macos',
        ),
        isNull,
      );
      expect(
        trustedUpdateArtifactUrl(
          'https://newchirp.net/downloads/NewChirp-1.0.23.dmg#fragment',
          platform: 'macos',
        ),
        isNull,
      );
    });
  });
}
