# diagnostic_log

## Classs

- [DiagnosticEntry](DiagnosticEntry.md) — One bounded, privacy-conscious diagnostic event.
- [DiagnosticReportException](DiagnosticReportException.md)

## Functions

- [_logDirectory](logDirectory.md) — The log folder: the test override, or the platform's usual per-user log folder.
- [_redact](redact.md) — Replaces the user's home folder with "~" so reports don't reveal the account name.
- [buildReport](buildReport.md) — Text of recent entries for a bug report, newest last, cut to [maxCharacters] and with personal paths removed.
- [DiagnosticLog](DiagnosticLog.md)
- [flush](flush.md)
- [initialize](initialize.md) — Opens diagnostics.jsonl. Over 2 MB it is renamed to
- [record](record.md) — Adds an entry to memory and appends it to the log file.
- [recordError](recordError.md) — Records an error with its stack trace.
- [reportImage](reportImage.md)
- [submit](submit.md) — Sends a bug report (with the diagnostic log and, optionally, the radio image) to the NewChirp website.
- [toJson](toJson.md) — Serialized form: one JSON line per entry in diagnostics.jsonl.
- [toString](toString.md)
