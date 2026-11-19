"""Tests for the manufacturer/model driver work ledger."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


def _load_ledger():
    spec = importlib.util.spec_from_file_location(
        "newchirp_driver_work",
        ROOT / "scripts/driver_work.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load driver_work.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DriverWorkLedgerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = _load_ledger()

    def test_status_import_and_work_event_history(self):
        status = """| Radio | Driver | Transport | Read | Write | Settings | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Baofeng K67 Pro | `drivers/k67.py` | CPS serial | Yes | Disabled | Hidden | Experimental read-only |
| Yaesu FT-50 | `drivers/ft50.py` | Clone serial | Yes | Hardware-tested name write | Hidden | Experimental; partial hardware validation |
"""
        with tempfile.TemporaryDirectory() as temp:
            database_path = Path(temp) / "work.sqlite3"
            status_path = Path(temp) / "DRIVER_STATUS.md"
            status_path.write_text(status, encoding="utf-8")

            database = self.ledger.connect(database_path)
            self.ledger.sync_driver_status(database, status_path)
            self.ledger.sync_driver_status(database, status_path)

            k67 = self.ledger.query_work(
                database,
                manufacturer="Baofeng",
                model="K67",
            )
            self.assertEqual(len(k67), 1)
            self.assertEqual(k67[0]["status"], "experimental")
            self.assertEqual(k67[0]["model"], "K67 Pro")

            ft50 = self.ledger.query_work(
                database,
                manufacturer="Yaesu",
                model="FT-50",
                status="experimental",
            )
            self.assertEqual(len(ft50), 1)
            work_id = ft50[0]["work_id"]
            self.ledger.add_event(
                database,
                work_id,
                "hardware_test",
                "Name-only write committed",
                external_ref="email:722",
                occurred_at="2026-11-17",
            )
            self.ledger.add_event(
                database,
                work_id,
                "hardware_test",
                "Name-only write committed",
                external_ref="email:722",
                occurred_at="2026-11-17",
            )
            database.commit()

            events = database.execute(
                """
                SELECT summary FROM work_events
                WHERE work_item_id = ? AND event_type = 'hardware_test'
                """,
                (work_id,),
            ).fetchall()
            self.assertEqual(len(events), 1)
            database.close()

    def test_new_work_evidence_and_hardware_test(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.ledger.connect(Path(temp) / "work.sqlite3")
            work_id = self.ledger.add_work(
                database,
                "Kenwood",
                "TK-350",
                "bug",
                "Identity request returns no bytes",
                status="fix_committed",
                priority="high",
                summary="Three bounded identity attempts.",
                source="email",
                source_ref="INBOX:728",
                reporter="Kenwood TK-350 owner",
                driver_path="drivers/newchirp_kenwood_kpg23.py",
            )
            database.execute(
                """
                INSERT INTO evidence (
                    work_item_id, evidence_type, label, uri, sha256
                )
                VALUES (?, 'protocol', 'KPG-32D sample', 'docs/KPG23_PROTOCOL.md', '')
                """,
                (work_id,),
            )
            database.execute(
                """
                INSERT INTO hardware_tests (
                    work_item_id, tester, tested_at, result, details
                )
                VALUES (?, 'reporter', '2026-11-17', 'blocked',
                        'No identity bytes on COM3 or COM4')
                """,
                (work_id,),
            )
            database.commit()

            row = database.execute(
                "SELECT * FROM work_overview WHERE work_id = ?",
                (work_id,),
            ).fetchone()
            self.assertEqual(row["manufacturer"], "Kenwood")
            self.assertEqual(row["model"], "TK-350")
            self.assertEqual(row["evidence_count"], 1)
            self.assertEqual(row["hardware_test_count"], 1)
            database.close()

    def test_contact_email_addresses_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.ledger.connect(Path(temp) / "work.sqlite3")
            with self.assertRaisesRegex(
                ValueError,
                "Reporter email addresses are not allowed",
            ):
                self.ledger.add_work(
                    database,
                    "Kenwood",
                    "TK-350",
                    "bug",
                    "Email privacy guard",
                    reporter="reporter@example.com",
                )
            with self.assertRaisesRegex(
                ValueError,
                "Tester email addresses are not allowed",
            ):
                self.ledger.sanitize_tester("tester@example.com")
            database.close()

    def test_invalid_status_and_kind_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            database = self.ledger.connect(Path(temp) / "work.sqlite3")
            with self.assertRaisesRegex(ValueError, "Unknown work kind"):
                self.ledger.add_work(
                    database,
                    "Baofeng",
                    "K67 Pro",
                    "unknown",
                    "Invalid",
                )
            with self.assertRaisesRegex(ValueError, "Unknown work status"):
                self.ledger.add_work(
                    database,
                    "Baofeng",
                    "K67 Pro",
                    "bug",
                    "Invalid",
                    status="unknown",
                )
            database.close()


class DriverWorkTextStoreTest(unittest.TestCase):
    """The ledger's source of truth is one JSON file per record."""

    SCRIPT = ROOT / "scripts/driver_work.py"

    def _cli(self, repo, *args):
        result = subprocess.run(
            [sys.executable, str(self.SCRIPT),
             "--store", str(repo / "database/driver_work"),
             "--db", str(repo / "cache.sqlite3"), *args],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def _git(self, repo, *args):
        subprocess.run(["git", "-C", str(repo), *args], check=True,
                       capture_output=True, text=True)

    def _seed(self, repo):
        repo.mkdir()
        self._git(repo, "init", "-q")
        self._git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
        self._git(repo, "config", "user.email", "ledger@example.com")
        self._git(repo, "config", "user.name", "ledger test")
        (repo / ".gitignore").write_text("cache.sqlite3\n")
        self._cli(repo, "init", "--no-status")
        legacy = self._cli(repo, "add", "--manufacturer", "Kenwood",
                           "--model", "TK-350", "--kind", "bug",
                           "--title", "Shared item")
        self._git(repo, "add", "-A")
        self._git(repo, "commit", "-q", "-m", "seed")
        return legacy

    def test_concurrent_ledger_edits_merge_without_conflicts(self):
        with tempfile.TemporaryDirectory() as temp:
            seed = Path(temp) / "seed"
            shared = self._seed(seed)
            origin = Path(temp) / "origin.git"
            subprocess.run(["git", "clone", "-q", "--bare", str(seed),
                            str(origin)], check=True)
            a, b = Path(temp) / "a", Path(temp) / "b"
            for clone in (a, b):
                subprocess.run(["git", "clone", "-q", str(origin), str(clone)],
                               check=True)
                self._git(clone, "config", "user.email", "x@example.com")
                self._git(clone, "config", "user.name", "x")
            item_a = self._cli(a, "add", "--manufacturer", "Baofeng",
                               "--model", "UV-5R", "--kind", "bug",
                               "--title", "From machine A")
            self._cli(a, "event", shared, "--type", "note",
                      "--summary", "A's note")
            self._cli(a, "status", shared, "pending_validation")
            item_b = self._cli(b, "add", "--manufacturer", "Yaesu",
                               "--model", "FT-50", "--kind", "bug",
                               "--title", "From machine B")
            self._cli(b, "event", shared, "--type", "note",
                      "--summary", "B's note")
            self.assertNotEqual(item_a, item_b)
            for clone, message in ((a, "A"), (b, "B")):
                self._git(clone, "add", "-A")
                self._git(clone, "commit", "-q", "-m", message)
            self._git(a, "push", "-q", "origin", "main")
            # B rebases onto A's push: plain git, no manual resolution.
            self._git(b, "pull", "-q", "--rebase", "origin", "main")

            shown = self._cli(b, "show", shared)
            self.assertIn("A's note", shown)
            self.assertIn("B's note", shown)
            self.assertIn("pending_validation", shown)
            listing = self._cli(b, "list")
            self.assertIn("From machine A", listing)
            self.assertIn("From machine B", listing)
            self.assertIn(item_a, listing)
            self.assertIn(item_b, listing)

    def test_event_writes_one_file_and_export_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            shared = self._seed(repo)
            store = repo / "database/driver_work"
            before = {p: p.read_text() for p in store.rglob("*.json")}
            self._cli(repo, "event", shared, "--type", "fix",
                      "--summary", "One change")
            after = {p: p.read_text() for p in store.rglob("*.json")}
            changed = [p for p in after if before.get(p) != after[p]]
            self.assertEqual(len(changed), 1)
            self.assertIn("/events/", str(changed[0]))
            first = self._cli(repo, "export", "--output", "-")
            second = self._cli(repo, "export", "--output", "-")
            self.assertEqual(first, second)
            self.assertNotIn("on 20", first.splitlines()[2])

    def test_duplicate_item_from_two_machines_folds_into_one(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            self._seed(repo)
            first = self._cli(repo, "add", "--manufacturer", "Radtel",
                              "--model", "RT-950 Pro", "--kind", "bug",
                              "--title", "Same report")
            items = repo / "database/driver_work/items"
            copy = (items / ("%s.json" % first)).read_text().replace(
                first, "w-20991231-ffff")
            (items / "w-20991231-ffff.json").write_text(copy)
            listing = self._cli(repo, "list", "--text", "Same report")
            self.assertEqual(len(listing.splitlines()), 1)
            self.assertIn(first, listing)

    def test_migrate_adds_without_removing_other_records(self):
        """A machine with unpushed entries in its old SQLite file can import
        them without deleting records other machines already pushed."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            self._seed(repo)
            pushed = self._cli(repo, "add", "--manufacturer", "Icom",
                               "--model", "IC-41S", "--kind", "bug",
                               "--title", "Pushed elsewhere")
            old = Path(temp) / "old.sqlite3"
            ledger = _load_ledger()
            database = ledger.connect(old)
            ledger.add_work(database, "Alinco", "DR-735", "bug",
                                 "Only in old file")
            database.commit()
            database.execute("UPDATE work_items SET uid = NULL")
            database.commit()
            database.close()
            self._cli(repo, "migrate", "--from", str(old))
            listing = self._cli(repo, "list")
            self.assertIn("Pushed elsewhere", listing)
            self.assertIn(pushed, listing)
            self.assertIn("Only in old file", listing)

    def test_conflict_markers_stop_with_a_clear_message(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            shared = self._seed(repo)
            path = next((repo / "database/driver_work/items").glob("*.json"))
            path.write_text("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> x\n")
            result = subprocess.run(
                [sys.executable, str(self.SCRIPT),
                 "--store", str(repo / "database/driver_work"),
                 "--db", str(repo / "cache.sqlite3"), "show", shared],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Merge conflict markers", result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
