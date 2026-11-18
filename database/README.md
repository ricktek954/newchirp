# NewChirp driver work ledger

`driver_work.sqlite3` is the queryable history of NewChirp-maintained radio
drivers, bugs, enhancements, evidence, and hardware validation. It complements
`docs/DRIVER_STATUS.md`, which remains the concise current-state report.

Use the database when you need to know what was attempted, which commits and
emails belong to a radio, what evidence exists, or what remains blocked. Do not
replace it with ad-hoc notes in `PROJECT_STATE.md`.

## Query the ledger

The command-line interface uses only Python's standard library:

```sh
# All open work for one model
python3 scripts/driver_work.py list \
  --manufacturer Kenwood --model TK-350

# Open work grouped by status
python3 scripts/driver_work.py list --status awaiting_user

# Search titles and summaries
python3 scripts/driver_work.py list --text checksum

# Full event, evidence, and hardware-test history
python3 scripts/driver_work.py show 68
```

The generated human-readable view is `docs/DRIVER_WORK.md`. Regenerate it after
changes:

```sh
python3 scripts/driver_work.py export
```

Raw SQL is supported:

```sh
sqlite3 database/driver_work.sqlite3 \
  "SELECT * FROM work_overview WHERE manufacturer='Baofeng' ORDER BY model;"
```

## Record work

Add a new bug, driver, enhancement, or validation task:

```sh
python3 scripts/driver_work.py add \
  --manufacturer Kenwood \
  --model TK-350 \
  --kind bug \
  --title "Identity request receives zero bytes" \
  --status investigating \
  --priority high \
  --summary "Reporter sees no response on COM3 or COM4." \
  --source email \
  --source-ref INBOX:728 \
  --reporter [redacted-email]
```

Append an event with an external reference:

```sh
python3 scripts/driver_work.py event 71 \
  --type fix \
  --summary "Added three bounded identity startup attempts" \
  --ref desktop:eb6d2239
```

Record evidence or a physical test:

```sh
python3 scripts/driver_work.py evidence 68 \
  --type cps --label "K6/K63 CPS 1.1.2" \
  --uri https://baofeng.s3.amazonaws.com/BAOFENG_K6_CPS_1.1.2_20240913.zip \
  --sha256 3f9c52ece3a8b6726fba4135b5a0f458b5d81f47d2e83af75045e82d8931b917

python3 scripts/driver_work.py test 69 \
  --tester [redacted-email] --result partial \
  --details "Name-only write and restore committed on 1.0.56."
```

Change the current status:

```sh
python3 scripts/driver_work.py status 71 pending_validation
python3 scripts/driver_work.py export
```

## Status policy

- `open`: reported or planned, no active investigation yet.
- `investigating`: analysis or reproduction is underway.
- `awaiting_user`: requires a reporter, hardware, cable, CPS, or sysadmin data.
- `fix_committed`: code or documentation is committed but not validated.
- `pending_validation`: a fix exists and requires physical or release testing.
- `experimental`: supported in source with incomplete real-radio validation.
- `hardware_tested`: a complete named operation succeeded on physical hardware.
- `released`: users can obtain the supporting build.
- `blocked`: no safe progress is possible without a specific external change.
- `closed`: intentionally complete with no follow-up.

Do not claim `hardware_tested` from synthetic tests. Record the tester, date,
exact operation, and limitations in `hardware_tests`.

## Evidence policy

- Store commit SHAs, email Message-IDs, forum/topic references, artifact hashes,
  and relative repository paths.
- Do not store passwords, tokens, full customer emails, private codeplugs, or
  radio images in SQLite.
- Keep generated prose and protocol notes in `docs/`; link to them from the
  evidence table.

## Initialization and migration

`database/schema.sql` is the schema source. A fresh database can be created and
seeded from the current driver-status inventory with:

```sh
python3 scripts/driver_work.py init
```

After changing the schema or rebuilding the database in a disposable worktree,
run the focused ledger tests:

```sh
python3 test/driver_work_test.py -v
```
