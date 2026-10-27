import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// One bounded, privacy-conscious diagnostic event.
class DiagnosticEntry {
  const DiagnosticEntry({
    required this.timestamp,
    required this.category,
    required this.message,
    this.context = const {},
  });

  final DateTime timestamp;
  final String category;
  final String message;
  final Map<String, Object?> context;

  Map<String, Object?> toJson() => {
    'timestamp': timestamp.toUtc().toIso8601String(),
    'category': category,
    'message': message,
    if (context.isNotEmpty) 'context': context,
  };
}

/// Keeps recent application diagnostics for support reports.
class DiagnosticLog {
  DiagnosticLog({
    this.maxEntries = 250,
    Uri? endpoint,
    Directory? rootDirectory,
  }) : endpoint = endpoint ?? defaultEndpoint,
       _rootDirectory = rootDirectory;

  static final Uri defaultEndpoint = Uri.parse(
    'https://newchirp.net/api/bug-report',
  );

  final int maxEntries;
  final Uri endpoint;
  final Directory? _rootDirectory;
  final List<DiagnosticEntry> _entries = [];
  Future<void> _pendingWrite = Future.value();
  File? _logFile;

  int get entryCount => _entries.length;

  Future<void> flush() => _pendingWrite;

  Future<void> initialize() async {
    try {
      final directory = _logDirectory();
      await directory.create(recursive: true);
      _logFile = File('${directory.path}/diagnostics.jsonl');
      if (await _logFile!.exists() &&
          await _logFile!.length() > 2 * 1024 * 1024) {
        final previous = File('${directory.path}/diagnostics.previous.jsonl');
        if (await previous.exists()) await previous.delete();
        await _logFile!.rename(previous.path);
      }
    } on FileSystemException {
      // Diagnostics must never prevent the app from opening.
    }
  }

  void record(
    String category,
    String message, {
    Map<String, Object?> context = const {},
  }) {
    final entry = DiagnosticEntry(
      timestamp: DateTime.now(),
      category: _redact(category),
      message: _redact(message),
      context: {
        for (final item in context.entries)
          _redact(item.key): item.value is String
              ? _redact(item.value! as String)
              : item.value,
      },
    );
    _entries.add(entry);
    if (_entries.length > maxEntries) {
      _entries.removeRange(0, _entries.length - maxEntries);
    }

    final file = _logFile;
    if (file == null) return;
    _pendingWrite = _pendingWrite.then((_) async {
      try {
        await file.writeAsString(
          '${jsonEncode(entry.toJson())}\n',
          mode: FileMode.append,
          flush: true,
        );
      } on FileSystemException {
        // A full or read-only disk should not interrupt the application.
      }
    });
  }

  void recordError(
    String category,
    Object error,
    StackTrace stackTrace, {
    Map<String, Object?> context = const {},
  }) {
    record(category, '$error\n\n$stackTrace', context: context);
  }

  String buildReport({int maxCharacters = 48000}) {
    final lines = <String>[];
    for (final entry in _entries) {
      final context = entry.context.isEmpty
          ? ''
          : ' | ${jsonEncode(entry.context)}';
      lines.add(
        '${entry.timestamp.toUtc().toIso8601String()} '
        '[${entry.category}] ${entry.message}$context',
      );
    }
    final report = lines.join('\n');
    if (report.length <= maxCharacters) return report;
    return report.substring(report.length - maxCharacters);
  }

  Future<void> submit({
    required String email,
    required String description,
    required String radio,
    required String version,
    required String cable,
  }) async {
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 20);
    try {
      final request = await client
          .postUrl(endpoint)
          .timeout(const Duration(seconds: 20));
      request.headers.contentType = ContentType.json;
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      request.followRedirects = false;
      request.write(
        jsonEncode({
          'email': email.trim(),
          'radio': radio,
          'os': Platform.operatingSystemVersion,
          'version': version,
          'cable': cable,
          'description': description.trim(),
          'debugLog': buildReport(),
          'source': 'newchirp-desktop',
        }),
      );
      final response = await request.close().timeout(
        const Duration(seconds: 30),
      );
      final responseBody = await response
          .transform(utf8.decoder)
          .join()
          .timeout(const Duration(seconds: 30));
      if (response.statusCode != HttpStatus.ok) {
        String message = 'The report service returned ${response.statusCode}.';
        try {
          final decoded = jsonDecode(responseBody);
          if (decoded is Map && decoded['error'] is String) {
            message = decoded['error'] as String;
          }
        } on FormatException {
          // Use the status-based message above.
        }
        throw DiagnosticReportException(message);
      }
    } on DiagnosticReportException {
      rethrow;
    } on TimeoutException {
      throw DiagnosticReportException(
        'The report submission timed out. Please try again.',
      );
    } on SocketException {
      throw DiagnosticReportException(
        'Could not reach the NewChirp report service.',
      );
    } on FormatException {
      throw DiagnosticReportException(
        'The report service returned an unexpected response.',
      );
    } finally {
      client.close(force: true);
    }
  }

  String _redact(String value) {
    var redacted = value;
    final home =
        Platform.environment['HOME'] ?? Platform.environment['USERPROFILE'];
    if (home != null && home.isNotEmpty) {
      redacted = redacted.replaceAll(home, '~');
    }
    return redacted.length <= 8000
        ? redacted
        : '${redacted.substring(0, 8000)}\n… truncated …';
  }

  Directory _logDirectory() {
    if (_rootDirectory != null) return _rootDirectory;
    if (Platform.isMacOS) {
      final home = Platform.environment['HOME'] ?? '.';
      return Directory('$home/Library/Logs/NewChirp');
    }
    if (Platform.isWindows) {
      final appData =
          Platform.environment['APPDATA'] ??
          Platform.environment['USERPROFILE'] ??
          '.';
      return Directory('$appData\\NewChirp\\logs');
    }
    final stateHome =
        Platform.environment['XDG_STATE_HOME'] ??
        '${Platform.environment['HOME'] ?? '.'}/.local/state';
    return Directory('$stateHome/newchirp/logs');
  }
}

class DiagnosticReportException implements Exception {
  const DiagnosticReportException(this.message);

  final String message;

  @override
  String toString() => message;
}
