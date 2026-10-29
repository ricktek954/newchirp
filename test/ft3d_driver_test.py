"""Offline checks for FT3D connection guidance."""

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_ft3d",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FT3DConnectionGuidanceTest(unittest.TestCase):
    def test_no_response_explains_clone_mode_and_send_button(self):
        bridge = _load_bridge()

        message = bridge.bridge_error_message(
            RuntimeError("No response from radio"),
            command="download",
            model="Yaesu_FT3D_R",
        )

        self.assertIn("hold DISP", message)
        self.assertIn("press Send", message)
        self.assertIn("CLONE", message)

    def test_foreign_model_keeps_the_original_error(self):
        bridge = _load_bridge()

        message = bridge.bridge_error_message(
            RuntimeError("No response from radio"),
            command="download",
            model="Baofeng_UV-5R",
        )

        self.assertEqual(message, "No response from radio")


if __name__ == "__main__":
    unittest.main()
