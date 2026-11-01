#!/usr/bin/env python3
"""The shared radio helper loads CHIRP once and keeps answering."""
import json
import subprocess
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import chirp_bridge as bridge  # noqa: E402


def chirp_source():
    for candidate in (
        ROOT / "build_support/chirp-21e42e4518c167548af90ed7f9edf75e516c491a",
        ROOT / "build_support/chirp-20261023",
        ROOT / "build_support/chirp-20261016",
        ROOT.parent / "chirp-20260626",
    ):
        if (candidate / "chirp/chirp_common.py").is_file():
            return candidate
    return None


class RequestShapeTest(unittest.TestCase):
    def test_list_models_uses_the_same_defaults_as_one_shot(self):
        args = bridge.request_to_namespace({"id": 1, "command": "list-models"})
        self.assertEqual(args.command, "list-models")
        self.assertEqual(args.limit, 200)
        self.assertFalse(args.fm_only)

    def test_unknown_command_and_extra_fields_are_rejected(self):
        with self.assertRaises(RuntimeError):
            bridge.request_to_namespace({"id": 1, "command": "os.system"})
        with self.assertRaises(RuntimeError):
            bridge.request_to_namespace({
                "id": 1,
                "command": "list-models",
                "port": "/dev/tty",
            })
        with self.assertRaises(RuntimeError):
            bridge.request_to_namespace({"command": "list-models"})
        with self.assertRaises(RuntimeError):
            bridge.request_to_namespace({
                "id": True,
                "command": "list-models",
            })

    def test_read_settings_needs_exactly_one_source(self):
        image = bridge.request_to_namespace({
            "id": 4,
            "command": "read-settings",
            "model": "Baofeng_UV-5R",
            "image": "/tmp/radio.img",
        })
        self.assertEqual(image.image, "/tmp/radio.img")
        self.assertIsNone(image.port)
        with self.assertRaises(RuntimeError):
            bridge.request_to_namespace({
                "id": 5,
                "command": "read-settings",
                "model": "Baofeng_UV-5R",
            })


class SessionProcessTest(unittest.TestCase):
    def test_two_catalog_reads_share_one_process_and_match_one_shot(self):
        source = chirp_source()
        if source is None:
            self.skipTest("CHIRP source for tests was not found.")
        wheel = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"
        script = ROOT / "scripts/chirp_bridge.py"
        one_shot = subprocess.run(
            [
                sys.executable,
                str(script),
                "--source",
                str(source),
                "--vendor",
                str(wheel),
                "list-models",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(one_shot.returncode, 0, one_shot.stderr)
        one_shot_payload = json.loads(one_shot.stdout)

        proc = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(script),
                "--source",
                str(source),
                "--vendor",
                str(wheel),
                "--session",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stderr_parts = []

        def drain_stderr():
            stderr_parts.append(proc.stderr.read())

        threading.Thread(target=drain_stderr, daemon=True).start()
        try:
            ready_line = proc.stdout.readline()
            self.assertNotEqual(ready_line, "", "".join(stderr_parts))
            ready = json.loads(ready_line)
            self.assertEqual(ready["type"], "ready")
            self.assertEqual(ready["pid"], proc.pid)

            def call(payload):
                proc.stdin.write(json.dumps(payload) + "\n")
                proc.stdin.flush()
                return json.loads(proc.stdout.readline())

            first = call({"id": 1, "command": "list-models"})
            second = call({"id": 2, "command": "list-models"})
            self.assertTrue(first["ok"], first)
            self.assertEqual(first["result"], one_shot_payload)
            self.assertEqual(second["result"], first["result"])
            self.assertIsNone(proc.poll())

            bad = call({
                "id": 3,
                "command": "model-info",
                "model": "Not_A_Real_Radio_ZZZ",
            })
            self.assertFalse(bad["ok"])
            self.assertIsNone(proc.poll())
            again = call({"id": 4, "command": "list-models"})
            self.assertEqual(again["result"], first["result"])

            quit_reply = call({"id": 5, "command": "quit"})
            self.assertTrue(quit_reply["ok"])
            self.assertEqual(proc.wait(timeout=30), 0)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=30)


if __name__ == "__main__":
    unittest.main()
