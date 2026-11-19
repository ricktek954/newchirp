#!/usr/bin/env python3
"""Manufacturer/model work ledger for NewChirp radio support."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
# The ledger's source of truth is one JSON file per record under
# DEFAULT_STORE, so concurrent edits on different machines merge in git.
# DEFAULT_DB is a git-ignored cache rebuilt from the store on every run.
DEFAULT_STORE = ROOT / "database" / "driver_work"
DEFAULT_DB = ROOT / "database" / "driver_work.sqlite3"
SCHEMA = ROOT / "database" / "schema.sql"
DEFAULT_STATUS = ROOT / "docs" / "DRIVER_STATUS.md"
DEFAULT_EXPORT = ROOT / "docs" / "DRIVER_WORK.md"

WORK_KINDS = {
    "new_driver",
    "bug",
    "enhancement",
    "maintenance",
    "hardware_validation",
    "release",
}
WORK_STATUSES = {
    "open",
    "investigating",
    "awaiting_user",
    "fix_committed",
    "pending_validation",
    "hardware_tested",
    "experimental",
    "released",
    "blocked",
    "closed",
}
WORK_PRIORITIES = {"critical", "high", "normal", "low"}
TEST_RESULTS = {"pass", "fail", "partial", "blocked"}

MANUFACTURERS = (
    "Connect Systems",
    "AnyTone",
    "Baofeng",
    "Bajeton",
    "Binqi",
    "Icom",
    "Kenwood",
    "KSUN",
    "Midland",
    "Motorola",
    "Quansheng",
    "Radtel",
    "Radioddity",
    "Retevis",
    "TIDRADIO",
    "TYT",
    "Wouxun",
    "Yaesu",
)

EMAIL_ADDRESS_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def today():
    return dt.date.today().isoformat()


def display_path(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def sanitize_reporter(value):
    value = value.strip()
    if EMAIL_ADDRESS_RE.search(value):
        raise ValueError(
            "Reporter email addresses are not allowed in the driver ledger; "
            "use the mailbox UID or Message-ID in source-ref instead"
        )
    return value


def sanitize_tester(value):
    value = value.strip()
    if EMAIL_ADDRESS_RE.search(value):
        raise ValueError(
            "Tester email addresses are not allowed in the driver ledger; "
            "use the mailbox UID or Message-ID in the test details instead"
        )
    return value


def connect(path, create=True, store=None):
    path = Path(path)
    if store is not None:
        rebuild_cache(store, path)
        create = True
    if not create and not path.is_file():
        raise SystemExit("Driver work database does not exist: %s" % path)
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    if create:
        database.executescript(SCHEMA.read_text(encoding="utf-8"))
    return database


def manufacturer_and_model(label):
    for manufacturer in sorted(MANUFACTURERS, key=len, reverse=True):
        if label.casefold().startswith(manufacturer.casefold() + " "):
            return manufacturer, label[len(manufacturer):].strip()
    words = label.split(maxsplit=1)
    if len(words) != 2:
        raise ValueError("Could not identify manufacturer in %r" % label)
    return words[0], words[1]


def get_or_create_radio(
    database,
    manufacturer,
    model,
    *,
    aliases="",
    driver_path="",
    notes="",
):
    database.execute(
        """
        INSERT INTO manufacturers (name)
        VALUES (?)
        ON CONFLICT(name) DO NOTHING
        """,
        (manufacturer,),
    )
    manufacturer_id = database.execute(
        "SELECT id FROM manufacturers WHERE name = ? COLLATE NOCASE",
        (manufacturer,),
    ).fetchone()["id"]
    database.execute(
        """
        INSERT INTO radios (
            manufacturer_id, model, aliases, driver_path, notes
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(manufacturer_id, model) DO UPDATE SET
            aliases = CASE
                WHEN radios.aliases = '' THEN excluded.aliases
                ELSE radios.aliases
            END,
            driver_path = CASE
                WHEN radios.driver_path = '' THEN excluded.driver_path
                ELSE radios.driver_path
            END,
            notes = CASE
                WHEN radios.notes = '' THEN excluded.notes
                ELSE radios.notes
            END,
            updated_at = datetime('now')
        """,
        (manufacturer_id, model, aliases, driver_path, notes),
    )
    return database.execute(
        """
        SELECT id FROM radios
        WHERE manufacturer_id = ? AND model = ? COLLATE NOCASE
        """,
        (manufacturer_id, model),
    ).fetchone()["id"]


def add_event(
    database,
    work_id,
    event_type,
    summary,
    *,
    details="",
    external_ref="",
    occurred_at=None,
):
    occurred_at = occurred_at or today()
    cursor = database.execute(
        """
        INSERT INTO work_events (
            work_item_id, event_type, summary, details,
            external_ref, occurred_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(work_item_id, event_type, occurred_at, summary)
        DO NOTHING
        """,
        (work_id, event_type, summary, details, external_ref, occurred_at),
    )
    database.execute(
        "UPDATE work_items SET updated_at = datetime('now') WHERE id = ?",
        (work_id,),
    )
    return cursor.rowcount


def add_work(
    database,
    manufacturer,
    model,
    kind,
    title,
    *,
    status="open",
    priority="normal",
    summary="",
    source="",
    source_ref="",
    reporter="",
    occurred_at=None,
    aliases="",
    driver_path="",
):
    if kind not in WORK_KINDS:
        raise ValueError("Unknown work kind: %s" % kind)
    if status not in WORK_STATUSES:
        raise ValueError("Unknown work status: %s" % status)
    if priority not in WORK_PRIORITIES:
        raise ValueError("Unknown priority: %s" % priority)
    reporter = sanitize_reporter(reporter)
    radio_id = get_or_create_radio(
        database,
        manufacturer,
        model,
        aliases=aliases,
        driver_path=driver_path,
    )
    database.execute(
        """
        INSERT INTO work_items (
            uid, radio_id, kind, title, status, priority, summary,
            source, source_ref, reporter, occurred_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(radio_id, kind, title) DO UPDATE SET
            status = excluded.status,
            priority = excluded.priority,
            summary = excluded.summary,
            source = excluded.source,
            source_ref = excluded.source_ref,
            reporter = excluded.reporter,
            occurred_at = excluded.occurred_at,
            updated_at = datetime('now')
        """,
        (
            new_uid(),
            radio_id,
            kind,
            title,
            status,
            priority,
            summary,
            source,
            source_ref,
            reporter,
            occurred_at,
        ),
    )
    work_id = database.execute(
        """
        SELECT id FROM work_items
        WHERE radio_id = ? AND kind = ? AND title = ?
        """,
        (radio_id, kind, title),
    ).fetchone()["id"]
    add_event(
        database,
        work_id,
        "created",
        title,
        details=summary,
        external_ref=source_ref or source,
        occurred_at=occurred_at,
    )
    return work_id


def status_from_ledger(value):
    lowered = value.casefold()
    if "hardware-tested" in lowered or "hardware read verified" in lowered:
        return "hardware_tested"
    if "blocked" in lowered:
        return "blocked"
    if "released" in lowered:
        return "released"
    if "experimental" in lowered:
        return "experimental"
    return "open"


def sync_driver_status(database, status_file):
    path = Path(status_file)
    lines = path.read_text(encoding="utf-8").splitlines()
    imported = 0
    for line_number, line in enumerate(lines, start=1):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            continue
        if cells[0] in {"Radio", "---"} or set(cells[0]) <= {"-", ":"}:
            continue
        try:
            manufacturer, model = manufacturer_and_model(cells[0])
        except ValueError:
            continue
        driver_paths = "|".join(re.findall(r"`([^`]+)`", cells[1]))
        summary = (
            "Transport: %s. Read: %s. Write: %s. Settings: %s. "
            "Ledger status: %s." % (cells[2], cells[3], cells[4], cells[5], cells[6])
        )
        radio_id = get_or_create_radio(
            database,
            manufacturer,
            model,
            driver_path=driver_paths,
        )
        work_title = "Current driver status"
        status = status_from_ledger(cells[6])
        existing = database.execute(
            """
            SELECT id, status, summary
            FROM work_items
            WHERE radio_id = ? AND kind = 'maintenance' AND title = ?
            """,
            (radio_id, work_title),
        ).fetchone()
        if existing is None:
            work_id = add_work(
                database,
                manufacturer,
                model,
                "maintenance",
                work_title,
                status=status,
                summary=summary,
                source=display_path(path),
                source_ref="%s:%i" % (display_path(path), line_number),
                driver_path=driver_paths,
            )
        else:
            work_id = existing["id"]
            changed = existing["status"] != status or existing["summary"] != summary
            database.execute(
                """
                UPDATE work_items SET
                    status = ?,
                    summary = ?,
                    source = ?,
                    source_ref = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    status,
                    summary,
                    display_path(path),
                    "%s:%i" % (display_path(path), line_number),
                    work_id,
                ),
            )
            if changed:
                add_event(
                    database,
                    work_id,
                    "status_snapshot",
                    "Imported current driver status from %s"
                    % path.name,
                    details=summary,
                    external_ref="%s:%i"
                    % (display_path(path), line_number),
                )
        imported += 1
    database.commit()
    return imported


def print_work_rows(rows):
    if not rows:
        print("No matching work items.")
        return
    for row in rows:
        print(
            "%(work_ref)s\t%(manufacturer)s\t%(model)s\t"
            "%(kind)s\t%(status)s\t%(priority)s\t%(title)s"
            % row
        )


def query_work(
    database,
    *,
    manufacturer=None,
    model=None,
    status=None,
    kind=None,
    text=None,
    limit=200,
):
    clauses = []
    values = []
    if manufacturer:
        clauses.append("manufacturer = ? COLLATE NOCASE")
        values.append(manufacturer)
    if model:
        clauses.append("model LIKE ? COLLATE NOCASE")
        values.append("%%%s%%" % model)
    if status:
        clauses.append("status = ?")
        values.append(status)
    if kind:
        clauses.append("kind = ?")
        values.append(kind)
    if text:
        clauses.append(
            "(title LIKE ? COLLATE NOCASE OR summary LIKE ? COLLATE NOCASE)"
        )
        values.extend(["%%%s%%" % text, "%%%s%%" % text])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    values.append(limit)
    return database.execute(
        """
        SELECT work_id, work_ref, manufacturer, model, kind, title, status,
               priority, summary, updated_at
        FROM work_overview
        """
        + where
        + " ORDER BY manufacturer COLLATE NOCASE, model COLLATE NOCASE, "
        "priority, work_id LIMIT ?",
        values,
    ).fetchall()


def show_work(database, work_id):
    row = database.execute(
        """
        SELECT wo.*, r.aliases, r.driver_path
        FROM work_overview wo
        JOIN work_items w ON w.id = wo.work_id
        JOIN radios r ON r.id = w.radio_id
        WHERE wo.work_id = ?
        """,
        (work_id,),
    ).fetchone()
    if row is None:
        raise SystemExit("Work item %s was not found." % work_id)
    print(
        "#%s %s %s | %s | %s"
        % (
            row["work_ref"],
            row["manufacturer"],
            row["model"],
            row["kind"],
            row["status"],
        )
    )
    print(row["title"])
    if row["summary"]:
        print(row["summary"])
    if row["driver_path"]:
        print("Driver: %s" % row["driver_path"])
    if row["source"]:
        print("Source: %s %s" % (row["source"], row["source_ref"]))
    events = database.execute(
        """
        SELECT occurred_at, event_type, summary, details, external_ref
        FROM work_events WHERE work_item_id = ?
        ORDER BY occurred_at, id
        """,
        (work_id,),
    ).fetchall()
    if events:
        print("\nEvents:")
        for event in events:
            line = "- %s [%s] %s" % (
                event["occurred_at"],
                event["event_type"],
                event["summary"],
            )
            if event["external_ref"]:
                line += " (%s)" % event["external_ref"]
            print(line)
            if event["details"]:
                print("  %s" % event["details"].replace("\n", "\n  "))
    tests = database.execute(
        """
        SELECT tested_at, tester, result, details
        FROM hardware_tests WHERE work_item_id = ?
        ORDER BY tested_at, id
        """,
        (work_id,),
    ).fetchall()
    for test in tests:
        print(
            "- %s hardware %s by %s: %s"
            % (
                test["tested_at"],
                test["result"],
                test["tester"],
                test["details"],
            )
        )
    artifacts = database.execute(
        """
        SELECT evidence_type, label, uri, sha256, notes
        FROM evidence WHERE work_item_id = ? ORDER BY id
        """,
        (work_id,),
    ).fetchall()
    for artifact in artifacts:
        print(
            "- evidence %s: %s %s%s"
            % (
                artifact["evidence_type"],
                artifact["label"],
                artifact["uri"],
                (
                    " sha256=%s" % artifact["sha256"]
                    if artifact["sha256"]
                    else ""
                ),
            )
        )


def export_markdown(database, output):
    rows = database.execute(
        """
        SELECT work_id, work_ref, manufacturer, model, kind, title, status,
               priority, summary, source, source_ref, reporter, updated_at
        FROM work_overview
        ORDER BY manufacturer COLLATE NOCASE, model COLLATE NOCASE,
                 kind, work_id
        """
    ).fetchall()
    grouped = {}
    for row in rows:
        grouped.setdefault(row["manufacturer"], {}).setdefault(
            row["model"], []
        ).append(row)
    lines = [
        "# NewChirp driver work ledger",
        "",
        # No date: identical data must produce identical text on every
        # machine, so regenerating this file never creates a merge conflict.
        "Generated from `database/driver_work/` by "
        "`python3 scripts/driver_work.py export`.",
        "",
        "Use `python3 scripts/driver_work.py show <id>` for event history.",
        "",
    ]
    for manufacturer, models in grouped.items():
        lines.extend(["## " + manufacturer, ""])
        for model, items in models.items():
            lines.extend(["### " + model, ""])
            for item in items:
                lines.append(
                    "- **#%s %s | %s | %s:** %s"
                    % (
                        item["work_ref"],
                        item["kind"],
                        item["status"],
                        item["priority"],
                        item["title"],
                    )
                )
                if item["summary"]:
                    lines.append("  " + item["summary"])
                if item["source"]:
                    lines.append(
                        "  Source: `%s` %s"
                        % (item["source"], item["source_ref"])
                    )
            lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    if output == "-":
        print(text, end="")
    else:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)


def work_ref(database, work_id):
    row = database.execute(
        "SELECT COALESCE(uid, CAST(id AS TEXT)) AS ref FROM work_items"
        " WHERE id = ?", (work_id,)).fetchone()
    return row["ref"] if row else str(work_id)


def find_work_id(database, selector):
    selector = selector.lstrip("#")
    row = database.execute(
        "SELECT id FROM work_items WHERE uid = ?", (selector,)
    ).fetchone()
    if row is not None:
        return row["id"]
    if selector.isdigit() and database.execute(
        "SELECT 1 FROM work_items WHERE id = ? AND uid IS NULL",
        (int(selector),),
    ).fetchone():
        return int(selector)
    row = database.execute(
        """
        SELECT work_id FROM work_overview
        WHERE manufacturer || ' ' || model || ' ' || title =
              ? COLLATE NOCASE
        """,
        (selector,),
    ).fetchone()
    if row is None:
        raise SystemExit("No exact work item matched %r." % selector)
    return row["work_id"]


# --- Text store -------------------------------------------------------------
#
# Layout under the store directory (all JSON, sorted keys, one record each):
#   manufacturers/<slug>.json
#   radios/<manufacturer-slug>/<model-slug>-<hash>.json
#   items/<key>.json                 key: legacy number ("0094") or uid
#   events/<key>/<occurred>-<hash>.json
#   tests/<key>/<tested>-<hash>.json
#   evidence/<key>/<hash>.json
# Mutable timestamps (updated_at) are derived, not stored, so recording an
# event never rewrites its item's file. Records added on different machines
# are different files and merge without conflicts.

STORE_KINDS = ("manufacturers", "radios", "items", "events", "tests",
               "evidence")


class StoreError(SystemExit):
    pass


def new_uid():
    return "w-%s-%s" % (dt.date.today().strftime("%Y%m%d"),
                        secrets.token_hex(2))


def _slug(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return slug or "x"


def _digest(*parts, length=10):
    joined = "\x00".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def _item_file_key(uid):
    return uid.zfill(4) if uid.isdigit() else uid


def _dump(record):
    return json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _read_store(store):
    """Load every record, refusing files that are not clean JSON."""
    store = Path(store)
    records = {kind: [] for kind in STORE_KINDS}
    for kind in STORE_KINDS:
        base = store / kind
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.json")):
            text = path.read_text(encoding="utf-8")
            if "<<<<<<<" in text or ">>>>>>>" in text:
                raise StoreError(
                    "Merge conflict markers in %s. Keep the correct values, "
                    "then run the command again." % display_path(path))
            try:
                records[kind].append((path, json.loads(text)))
            except json.JSONDecodeError as exc:
                raise StoreError("Invalid JSON in %s: %s"
                                 % (display_path(path), exc))
    return records


def rebuild_cache(store, cache_path):
    """Build a fresh SQLite cache from the text store (atomic replace)."""
    records = _read_store(store)
    cache_path = Path(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(
        prefix=".driver_work-", suffix=".sqlite3", dir=cache_path.parent)
    os.close(handle)
    database = sqlite3.connect(temp_name)
    database.row_factory = sqlite3.Row
    try:
        database.executescript(SCHEMA.read_text(encoding="utf-8"))
        for _path, row in records["manufacturers"]:
            database.execute(
                "INSERT INTO manufacturers (name, aliases, notes, created_at,"
                " updated_at) VALUES (?, ?, ?, ?, ?)",
                (row["name"], row.get("aliases", ""), row.get("notes", ""),
                 row["created_at"], row["created_at"]))
        manufacturer_ids = {
            r["name"].casefold(): r["id"]
            for r in database.execute("SELECT id, name FROM manufacturers")}

        def manufacturer_id(name):
            key = name.casefold()
            if key not in manufacturer_ids:
                cursor = database.execute(
                    "INSERT INTO manufacturers (name) VALUES (?)", (name,))
                manufacturer_ids[key] = cursor.lastrowid
            return manufacturer_ids[key]

        for _path, row in records["radios"]:
            database.execute(
                "INSERT INTO radios (manufacturer_id, model, aliases,"
                " driver_path, notes, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (manufacturer_id(row["manufacturer"]), row["model"],
                 row.get("aliases", ""), row.get("driver_path", ""),
                 row.get("notes", ""), row["created_at"], row["created_at"]))

        def radio_id(manufacturer, model):
            mid = manufacturer_id(manufacturer)
            found = database.execute(
                "SELECT id FROM radios WHERE manufacturer_id = ?"
                " AND model = ? COLLATE NOCASE", (mid, model)).fetchone()
            if found:
                return found["id"]
            return database.execute(
                "INSERT INTO radios (manufacturer_id, model) VALUES (?, ?)",
                (mid, model)).lastrowid

        # Legacy items keep their numbers; newer items follow in creation
        # order. A natural-key duplicate (the same item added on two
        # machines) folds into the earliest key.
        items = sorted(
            (row for _path, row in records["items"]),
            key=lambda row: (0, int(row["uid"]), "") if row["uid"].isdigit()
            else (1, row["created_at"], row["uid"]))
        next_id = max([int(r["uid"]) for r in items if r["uid"].isdigit()]
                      + [0]) + 1
        key_to_id = {}
        natural = {}
        for row in items:
            rid = radio_id(row["manufacturer"], row["model"])
            nkey = (rid, row["kind"], row["title"])
            if nkey in natural:
                key_to_id[row["uid"]] = natural[nkey]
                continue
            if row["uid"].isdigit():
                item_id = int(row["uid"])
            else:
                item_id = next_id
                next_id += 1
            database.execute(
                "INSERT INTO work_items (id, uid, radio_id, kind, title,"
                " status, priority, summary, source, source_ref, reporter,"
                " occurred_at, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (item_id, row["uid"], rid, row["kind"], row["title"],
                 row["status"], row.get("priority", "normal"),
                 row.get("summary", ""), row.get("source", ""),
                 row.get("source_ref", ""), row.get("reporter", ""),
                 row.get("occurred_at"), row["created_at"],
                 row["created_at"]))
            natural[nkey] = item_id
            key_to_id[row["uid"]] = item_id

        def owner(row, path):
            item = key_to_id.get(row["item"])
            if item is None:
                raise StoreError("%s refers to unknown work item %r"
                                 % (display_path(path), row["item"]))
            return item

        for path, row in sorted(records["events"],
                                key=lambda pair: (pair[1]["occurred_at"],
                                                  pair[1]["created_at"],
                                                  pair[1]["summary"])):
            database.execute(
                "INSERT INTO work_events (work_item_id, event_type, summary,"
                " details, external_ref, occurred_at, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(work_item_id, event_type, occurred_at, summary)"
                " DO NOTHING",
                (owner(row, path), row["event_type"], row["summary"],
                 row.get("details", ""), row.get("external_ref", ""),
                 row["occurred_at"], row["created_at"]))
        for path, row in sorted(records["tests"],
                                key=lambda pair: (pair[1]["tested_at"],
                                                  pair[1]["created_at"])):
            database.execute(
                "INSERT INTO hardware_tests (work_item_id, tester, tested_at,"
                " result, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (owner(row, path), row["tester"], row["tested_at"],
                 row["result"], row.get("details", ""), row["created_at"]))
        for path, row in sorted(records["evidence"],
                                key=lambda pair: (pair[1]["created_at"],
                                                  pair[1]["label"])):
            database.execute(
                "INSERT INTO evidence (work_item_id, evidence_type, label,"
                " uri, sha256, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (owner(row, path), row["evidence_type"], row["label"],
                 row.get("uri", ""), row.get("sha256", ""),
                 row.get("notes", ""), row["created_at"]))
        # updated_at is derived from the newest event.
        database.execute(
            "UPDATE work_items SET updated_at = COALESCE((SELECT"
            " MAX(created_at) FROM work_events e WHERE e.work_item_id ="
            " work_items.id), created_at)")
        database.commit()
    except BaseException:
        database.close()
        os.unlink(temp_name)
        raise
    database.close()
    os.replace(temp_name, cache_path)


def _store_records(database):
    """Yield (relative path, record) for every row in the cache."""
    for row in database.execute(
            "SELECT name, aliases, notes, created_at FROM manufacturers"):
        yield ("manufacturers/%s.json" % _slug(row["name"]), {
            "name": row["name"], "aliases": row["aliases"],
            "notes": row["notes"], "created_at": row["created_at"]})
    for row in database.execute(
            "SELECT m.name AS manufacturer, r.model, r.aliases,"
            " r.driver_path, r.notes, r.created_at FROM radios r"
            " JOIN manufacturers m ON m.id = r.manufacturer_id"):
        yield ("radios/%s/%s-%s.json" % (
            _slug(row["manufacturer"]), _slug(row["model"]),
            _digest(row["model"].casefold(), length=6)), dict(row))
    keys = {}
    for row in database.execute(
            "SELECT w.id, w.uid, m.name AS manufacturer, r.model, w.kind,"
            " w.title, w.status, w.priority, w.summary, w.source,"
            " w.source_ref, w.reporter, w.occurred_at, w.created_at"
            " FROM work_items w JOIN radios r ON r.id = w.radio_id"
            " JOIN manufacturers m ON m.id = r.manufacturer_id"):
        record = dict(row)
        item_id = record.pop("id")
        uid = record["uid"] or str(item_id)
        record["uid"] = uid
        keys[item_id] = uid
        yield ("items/%s.json" % _item_file_key(uid), record)
    for row in database.execute(
            "SELECT work_item_id, event_type, summary, details, external_ref,"
            " occurred_at, created_at FROM work_events"):
        record = dict(row)
        item = keys[record.pop("work_item_id")]
        record["item"] = item
        yield ("events/%s/%s-%s.json" % (
            _item_file_key(item), record["occurred_at"],
            _digest(record["event_type"], record["summary"])), record)
    for row in database.execute(
            "SELECT work_item_id, tester, tested_at, result, details,"
            " created_at FROM hardware_tests"):
        record = dict(row)
        item = keys[record.pop("work_item_id")]
        record["item"] = item
        yield ("tests/%s/%s-%s.json" % (
            _item_file_key(item), record["tested_at"],
            _digest(record["tester"], record["result"], record["details"])),
            record)
    for row in database.execute(
            "SELECT work_item_id, evidence_type, label, uri, sha256, notes,"
            " created_at FROM evidence"):
        record = dict(row)
        item = keys[record.pop("work_item_id")]
        record["item"] = item
        yield ("evidence/%s/%s.json" % (
            _item_file_key(item), _digest(
                record["evidence_type"], record["label"], record["uri"],
                record["sha256"], record["notes"])), record)


def persist(database, store, remove_missing=True):
    """Write the cache back to the store, touching only changed files."""
    store = Path(store)
    wanted = {}
    for relative, record in _store_records(database):
        wanted[store / relative] = _dump(record)
    written = 0
    for path, text in wanted.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written += 1
    # Remove records the cache no longer has (for example a duplicate item
    # folded into its earlier copy). The cache was built from this store, so
    # nothing here is lost. Imports (migrate) never remove anything.
    if not remove_missing:
        return written
    for kind in STORE_KINDS:
        base = store / kind
        if not base.is_dir():
            continue
        for path in base.rglob("*.json"):
            if path not in wanted:
                path.unlink()
                written += 1
        for directory in sorted(base.rglob("*"), reverse=True):
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
    return written


def migrate_from_sqlite(legacy_path, store):
    """One-time import of a schema-1 database into the text store."""
    legacy = sqlite3.connect("file:%s?mode=ro" % legacy_path, uri=True)
    legacy.row_factory = sqlite3.Row
    columns = {row["name"] for row in
               legacy.execute("PRAGMA table_info(work_items)")}
    memory = sqlite3.connect(":memory:")
    legacy.backup(memory)
    legacy.close()
    memory.row_factory = sqlite3.Row
    if "uid" not in columns:
        memory.execute("ALTER TABLE work_items ADD COLUMN uid TEXT")
    memory.execute("UPDATE work_items SET uid = CAST(id AS TEXT)"
                   " WHERE uid IS NULL")
    # Add and update only: other machines' records already in the store
    # must survive importing an older local database.
    written = persist(memory, store, remove_missing=False)
    memory.close()
    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--store", default=str(DEFAULT_STORE),
                        help="Text store (source of truth)")
    parser.add_argument("--no-store", action="store_true",
                        help="Use --db directly without the text store")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--status-file", default=str(DEFAULT_STATUS))
    init.add_argument("--no-status", action="store_true")

    sync = commands.add_parser("sync-status")
    sync.add_argument("--status-file", default=str(DEFAULT_STATUS))

    list_command = commands.add_parser("list")
    list_command.add_argument("--manufacturer")
    list_command.add_argument("--model")
    list_command.add_argument("--status", choices=sorted(WORK_STATUSES))
    list_command.add_argument("--kind", choices=sorted(WORK_KINDS))
    list_command.add_argument("--text")
    list_command.add_argument("--limit", type=int, default=200)
    list_command.add_argument("--json", action="store_true")

    show = commands.add_parser("show")
    show.add_argument("work")

    add = commands.add_parser("add")
    add.add_argument("--manufacturer", required=True)
    add.add_argument("--model", required=True)
    add.add_argument("--kind", required=True, choices=sorted(WORK_KINDS))
    add.add_argument("--title", required=True)
    add.add_argument("--status", default="open", choices=sorted(WORK_STATUSES))
    add.add_argument("--priority", default="normal", choices=sorted(WORK_PRIORITIES))
    add.add_argument("--summary", default="")
    add.add_argument("--source", default="")
    add.add_argument("--source-ref", default="")
    add.add_argument("--reporter", default="")
    add.add_argument("--occurred-at")
    add.add_argument("--aliases", default="")
    add.add_argument("--driver-path", default="")

    event = commands.add_parser("event")
    event.add_argument("work")
    event.add_argument("--type", default="note")
    event.add_argument("--summary", required=True)
    event.add_argument("--details", default="")
    event.add_argument("--ref", default="")
    event.add_argument("--occurred-at")

    status = commands.add_parser("status")
    status.add_argument("work")
    status.add_argument("value", choices=sorted(WORK_STATUSES))

    test = commands.add_parser("test")
    test.add_argument("work")
    test.add_argument("--tester", required=True)
    test.add_argument("--result", required=True, choices=sorted(TEST_RESULTS))
    test.add_argument("--details", default="")
    test.add_argument("--tested-at")

    evidence = commands.add_parser("evidence")
    evidence.add_argument("work")
    evidence.add_argument("--type", required=True)
    evidence.add_argument("--label", required=True)
    evidence.add_argument("--uri", default="")
    evidence.add_argument("--sha256", default="")
    evidence.add_argument("--notes", default="")

    export = commands.add_parser("export")
    export.add_argument("--output", default=str(DEFAULT_EXPORT))

    rebuild = commands.add_parser(
        "rebuild", help="Rebuild the SQLite cache and docs from the store")
    rebuild.add_argument("--output", default=str(DEFAULT_EXPORT))

    migrate = commands.add_parser(
        "migrate", help="Import a schema-1 SQLite ledger into the store")
    migrate.add_argument("--from", dest="source", required=True)

    args = parser.parse_args()
    store = None if args.no_store else Path(args.store)
    if args.command == "migrate":
        written = migrate_from_sqlite(args.source, store)
        rebuild_cache(store, args.db)
        print("Wrote %i store files to %s." % (written, display_path(store)))
        return
    if store is not None and args.command == "init":
        store.mkdir(parents=True, exist_ok=True)
    # The store directory existing is what switches the ledger to text mode;
    # without it (an unmigrated checkout) --db is used directly.
    store_mode = store is not None and store.is_dir()
    database = connect(
        args.db,
        create=args.command in {"init", "sync-status", "rebuild"},
        store=store if store_mode else None,
    )
    try:
        if args.command == "rebuild":
            export_markdown(database, args.output)
            return
        _execute(args, database)
        if store_mode and args.command in MUTATING_COMMANDS:
            persist(database, store)
    finally:
        database.close()


MUTATING_COMMANDS = {
    "init", "sync-status", "add", "event", "status", "test", "evidence",
}


def _execute(args, database):
    if args.command == "init":
        if not args.no_status:
            count = sync_driver_status(database, args.status_file)
            print("Initialized %s and imported %i status rows." % (args.db, count))
        else:
            print("Initialized %s." % args.db)
        return
    if args.command == "sync-status":
        count = sync_driver_status(database, args.status_file)
        print("Imported %i driver status rows." % count)
        return
    if args.command == "list":
        rows = query_work(
            database,
            manufacturer=args.manufacturer,
            model=args.model,
            status=args.status,
            kind=args.kind,
            text=args.text,
            limit=args.limit,
        )
        if args.json:
            print(json.dumps([dict(row) for row in rows], indent=2))
        else:
            print_work_rows(rows)
        return
    if args.command == "show":
        show_work(database, find_work_id(database, args.work))
        return
    if args.command == "add":
        work_id = add_work(
            database,
            args.manufacturer,
            args.model,
            args.kind,
            args.title,
            status=args.status,
            priority=args.priority,
            summary=args.summary,
            source=args.source,
            source_ref=args.source_ref,
            reporter=args.reporter,
            occurred_at=args.occurred_at,
            aliases=args.aliases,
            driver_path=args.driver_path,
        )
        database.commit()
        print(work_ref(database, work_id))
        return
    if args.command == "export":
        export_markdown(database, args.output)
        return
    work_id = find_work_id(database, args.work)
    if args.command == "event":
        inserted = add_event(
            database,
            work_id,
            args.type,
            args.summary,
            details=args.details,
            external_ref=args.ref,
            occurred_at=args.occurred_at,
        )
        database.commit()
        print("recorded" if inserted else "already recorded")
        return
    if args.command == "status":
        previous = database.execute(
            "SELECT status FROM work_items WHERE id = ?", (work_id,)
        ).fetchone()["status"]
        database.execute(
            "UPDATE work_items SET status = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (args.value, work_id),
        )
        if previous != args.value:
            add_event(
                database,
                work_id,
                "status_change",
                "Status changed from %s to %s" % (previous, args.value),
            )
        database.commit()
        print("%s: %s -> %s" % (work_ref(database, work_id), previous,
                                args.value))
        return
    if args.command == "test":
        tested_at = args.tested_at or today()
        tester = sanitize_tester(args.tester)
        database.execute(
            """
            INSERT INTO hardware_tests (
                work_item_id, tester, tested_at, result, details
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (work_id, tester, tested_at, args.result, args.details),
        )
        add_event(
            database,
            work_id,
            "hardware_test",
            "%s hardware test: %s" % (tester, args.result),
            details=args.details,
            occurred_at=tested_at,
        )
        database.commit()
        print("recorded")
        return
    if args.command == "evidence":
        database.execute(
            """
            INSERT INTO evidence (
                work_item_id, evidence_type, label, uri, sha256, notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                work_id,
                args.type,
                args.label,
                args.uri,
                args.sha256,
                args.notes,
            ),
        )
        add_event(
            database,
            work_id,
            "evidence",
            "Evidence recorded: %s" % args.label,
            details=args.notes,
            external_ref=args.uri,
        )
        database.commit()
        print("recorded")
        return


if __name__ == "__main__":
    main()
