"""Tests for the manufacturer/model driver work ledger."""

import importlib.util
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
