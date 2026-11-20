# RepeaterBook API integration

Last checked: 2026-11-20

RepeaterBook approved NewChirp's centralized-server application on
2026-11-20 for the `api.export` and `api.export_row` scopes. The issued
application token has no expiry.

## Credential boundary

The shared `app_` token is a server-only credential. It belongs in
`/opt/newchirp/.env.repeaterbook` with mode `0600` on `newchirp.net` and must
never appear in this repository, a desktop or mobile build, browser JavaScript,
diagnostics, logs, radio images, or support artifacts.

The exact approved User-Agent is:

```text
NewChirp/1.0.51 (+https://newchirp.net; rick@newchirp.net)
```

RepeaterBook binds API requests to both the token and this User-Agent.

## Request path

Desktop repeater searches call:

```text
POST https://newchirp.net/api/repeaters/repeaterbook/search
```

The `newchirp.net` server calls RepeaterBook directly, adds the protected
`X-RB-App-Token` header and approved User-Agent, disables redirects, and returns
only the bounded result rows needed by the active search. Desktop installs and
the browser Web Programmer never receive the shared provider token.

The US, Canada, and Mexico use the North America `api/export.php` endpoint.
US searches add a FIPS state ID; Canada and Mexico do not. GMRS requests add
`stype=gmrs`. Other countries use `api/exportROW.php`. Non-US regions are
filtered locally after retrieval.

The desktop ZIP lookup remains local to the bridge search flow. A valid US ZIP
is resolved to coordinates by the existing Zippopotam lookup, then the relay is
asked for repeaters within the default 50 km radius in the selected region.

## Response mapping

The relay returns normalized rows with receive/transmit frequencies in Hz,
CTCSS or DTCS tone objects, FM/NFM mode, status, coordinates, and attribution
metadata. The Python bridge converts those rows through CHIRP's normal memory
model so offsets and tone modes continue to use the same validation as channel
editing.

RepeaterBook is attributed as "Data courtesy of RepeaterBook.com." in the
desktop search dialog and with a link in the browser programmer.

## Verification

Focused checks:

```sh
python3 -m unittest discover -s test -p 'chirp_bridge_upload_test.py' -k repeaterbook
flutter test test/widget_test.dart --plain-name 'RepeaterBook'
```

The website relay tests live in
`/Volumes/RICKEXT/web/newchirpweb/scripts/test-repeater-search.mjs`.
