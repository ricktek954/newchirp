#!/usr/bin/env python3
"""Manufacturer/model work ledger for NewChirp radio support."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
import sys


ROOT = Path(__file__).resolve().parent.parent
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


def connect(path, create=True):
    path = Path(path)
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
            radio_id, kind, title, status, priority, summary,
            source, source_ref, reporter, occurred_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "%(work_id)i\t%(manufacturer)s\t%(model)s\t"
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
        SELECT work_id, manufacturer, model, kind, title, status,
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
        "#%i %s %s | %s | %s"
        % (
            row["work_id"],
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
        SELECT work_id, manufacturer, model, kind, title, status,
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
        "Generated from `database/driver_work.sqlite3` on %s." % today(),
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
                    "- **#%i %s | %s | %s:** %s"
                    % (
                        item["work_id"],
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


def find_work_id(database, selector):
    if selector.isdigit():
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB))
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

    args = parser.parse_args()
    database = connect(args.db, create=args.command in {"init", "sync-status"})

    try:
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
            print(work_id)
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
            print("%i: %s -> %s" % (work_id, previous, args.value))
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
    finally:
        database.close()


if __name__ == "__main__":
    main()
