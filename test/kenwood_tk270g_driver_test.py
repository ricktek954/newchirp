"""Offline checks for TK-270G unprogrammed bank metadata."""

import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_tk270g",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class KenwoodTK270GDriverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.bridge = bridge
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )

    def test_unprogrammed_bank_index_is_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "Kenwood_TK-270G.img"
            data = bytearray(
                (SOURCE / "tests/images/Kenwood_TK-272G.img").read_bytes()
            )
            data[0xA7:0xAE] = b"P2700\x05\xff"
            image.write_bytes(data)

            radio = self.bridge.radio_from_image(
                self.directory,
                "Kenwood_TK-270G",
                str(image),
            )
            radio._memobj.memory[0].bnumb = 128

            memory = radio.get_memory(1)
            bnumb = next(
                setting
                for setting in memory.extra
                if setting.get_name() == "bnumb"
            )

        self.assertEqual(int(radio._memobj.memory[0].bnumb), 0)
        self.assertEqual(int(radio._memobj.memory[0].bank), 1)
        self.assertEqual(int(bnumb.value), 0)


if __name__ == "__main__":
    unittest.main()
