# NewChirp driver work ledger

The driver ledger is the queryable history of NewChirp-maintained radio
drivers, bugs, enhancements, evidence, and hardware validation. It complements
`docs/DRIVER_STATUS.md`, which remains the concise current-state report.

## Storage (since 2026-11-19)

The source of truth is `database/driver_work/`, one JSON file per record:

| Path | Record |
| --- | --- |
| `manufacturers/<slug>.json` | manufacturer |
| `radios/<manufacturer>/<model>-<hash>.json` | radio model |
| `items/<id>.json` | work item (`0094` = legacy #94; new items use `w-YYYYMMDD-xxxx`) |
| `events/<id>/<date>-<hash>.json` | event (status changes are events too) |
| `tests/<id>/<date>-<hash>.json` | hardware test |
| `evidence/<id>/<hash>.json` | evidence |

`database/driver_work.sqlite3` is a git-ignored cache. `scripts/driver_work.py`
rebuilds it from the JSON on every command and writes back only the records
that changed, so all commands and raw SQL below work as before. Records added
on different machines are different files and merge without conflicts; the
same event recorded twice is the same file. `updated_at` is derived from the
newest event rather than stored, so adding an event never rewrites its item.

- Item IDs: legacy items keep their numbers (`show 94`). New items get a
  collision-proof ID (`show w-20261119-a3f2`); `add` prints it.
- `docs/DRIVER_WORK.md` is deterministic (no date) and uses `merge=union`;
  the `.githooks` post-merge, post-rewrite and post-checkout hooks run
  `python3 scripts/driver_work.py rebuild` to regenerate it and the cache.
- If a pull ever leaves conflict markers in a JSON file (two machines editing
  the same item's status or summary at once), keep the correct values and
  rerun any ledger command; it refuses to run on a damaged file.
- `python3 scripts/driver_work.py migrate --from <schema-1.sqlite3>` imports
  an old database (used once for the 2026-11-19 migration).

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

Run the repository privacy check before committing or exporting:

```sh
python3 scripts/check_private_data.py
```

Raw SQL is supported against the cache (run any ledger command first so it
is current):

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
  --reporter "Kenwood TK-350 owner"
```

Do not store a reporter's email address in `reporter`. Use the mailbox UID or
Message-ID in `source-ref` when correspondence needs to be correlated. The
database rejects contact addresses in both reporter and tester fields.

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
  When the core operations (full read and a channel write read back after a
  power cycle) are confirmed, the radio graduates out of Experimental (see "Graduating a radio out of
  Experimental" in `AGENTS.md`).
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
