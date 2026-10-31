"""Regression tests for packaged CHIRP/NewChirp driver catalog loading."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


class ColocatedDriverCatalogTest(unittest.TestCase):
    def test_packaged_overrides_do_not_duplicate_tdh3_registration(self):
        with tempfile.TemporaryDirectory() as temp:
            packaged_source = Path(temp) / "Resources"
            packaged_source.mkdir()
            shutil.copytree(
                SOURCE / "chirp",
                packaged_source / "chirp",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            packaged_drivers = packaged_source / "chirp" / "drivers"
            for driver in (ROOT / "drivers").glob("*.py"):
                shutil.copy2(driver, packaged_drivers / driver.name)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/chirp_bridge.py"),
                    "--source",
                    str(packaged_source),
                    "--vendor",
                    str(VENDOR),
                    "list-models",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            models = json.loads(result.stdout)["models"]
            self.assertIn("TIDRADIO_TD-H3", models)
            self.assertIn("Icom_ID-50", models)
            self.assertIn("Icom_ID-52", models)


if __name__ == "__main__":
    unittest.main()
