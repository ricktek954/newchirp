#!/usr/bin/env python3
"""Fail when private email addresses or local build paths are tracked."""

from __future__ import annotations

import re
import sqlite3
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "database" / "driver_work.sqlite3"
EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
ALLOWED_DOMAINS = {
    "newchirp.net",
    "users.noreply.github.com",
    "example.com",
    "example.org",
}


def allowed_email(value: str) -> bool:
    domain = value.rsplit("@", 1)[-1].casefold()
    return domain in ALLOWED_DOMAINS


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
    )
    return [ROOT / name.decode() for name in output.split(b"\0") if name]


def main() -> int:
    failures = []
    tracked = tracked_files()

    if any(path.relative_to(ROOT) == Path("build_support") for path in tracked):
        failures.append("build_support is tracked; it is a machine-local symlink")

    for path in tracked:
        if path == DATABASE or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(
                not allowed_email(match.group(0))
                for match in EMAIL_RE.finditer(line)
            ):
                failures.append(
                    f"{path.relative_to(ROOT)}:{line_number}: "
                    "private email address"
                )

    if DATABASE.is_file():
        database = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True)
        try:
            tables = [
                row[0]
                for row in database.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            ]
            for table in tables:
                columns = list(database.execute(f'PRAGMA table_info("{table}")'))
                text_columns = [
                    row[1]
                    for row in columns
                    if "TEXT" in (row[2] or "").upper()
                    or row[1] in {"reporter", "tester"}
                ]
                if not text_columns:
                    continue
                selection = ", ".join(
                    ["rowid"] + [f'"{column}"' for column in text_columns]
                )
                for row in database.execute(f'SELECT {selection} FROM "{table}"'):
                    for column, value in zip(text_columns, row[1:]):
                        if not isinstance(value, str):
                            continue
                        if any(
                            not allowed_email(match.group(0))
                            for match in EMAIL_RE.finditer(value)
                        ):
                            failures.append(
                                f"driver_work.sqlite3:{table}:{row[0]}:"
                                f"{column}: private email address"
                            )
        finally:
            database.close()

    if failures:
        print("Private-data check failed:")
        for failure in sorted(set(failures)):
            print(f"  {failure}")
        return 1

    print("Private-data check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
