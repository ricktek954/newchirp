"""Images saved by F4HWN's own CHIRP module open in the built-in profile.

2026-11-19 Linux report: "Unsupported model Quansheng UV-K1 & UV-K5 V3
(F4HWN)" for an image made with f4hwn.chirp.v6.3.0.py, which NewChirp cannot
load because it imports wx.
"""

from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_f4hwn_alias", ROOT / "scripts/chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class F4HWNModuleImageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = _load_bridge().load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"))
        cls.profile = cls.directory.get_radio("Quansheng_UV-K1_F4HWN_6.3")
        cls.uvk5 = sys.modules["newchirp.drivers.newchirp_uvk5"]

    def _module_image(self, path, size):
        from chirp import memmap

        class ModuleNamed(self.profile):
            MODEL = "UV-K1 & UV-K5 V3 (F4HWN)"

            def process_mmap(self):
                return None

        ModuleNamed(memmap.MemoryMapBytes(b"\xff" * size)).save_mmap(
            str(path))

    def test_module_image_opens_in_the_built_in_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "k1 6.3 firmware code plug.img"
            self._module_image(path, self.uvk5.F4HWN_MEM_SIZE)
            radio = self.directory.get_radio_by_image(str(path))
            self.assertIsInstance(radio, self.profile)
            self.assertEqual(radio.get_features().memory_bounds[1], 1024)

    def test_other_layout_is_refused_not_misread(self):
        from chirp import errors
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "other.img"
            self._module_image(path, 0x2000)
            with self.assertRaisesRegex(errors.RadioError, "F4HWN 6.3"):
                self.directory.get_radio_by_image(str(path))


class F4HWNModuleLoadMessageTest(unittest.TestCase):
    def test_wx_module_error_names_the_built_in_profile(self):
        bridge = _load_bridge()
        directory = bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"))
        with tempfile.TemporaryDirectory() as temp:
            module = Path(temp) / "module.py"
            module.write_text('import wx\nMODEL = "UV-K1 & UV-K5 V3 (F4HWN)"\n')
            with self.assertRaisesRegex(RuntimeError,
                                        "Quansheng UV-K1 \\(F4HWN 6.3\\)"):
                bridge._load_module(str(module), directory)


if __name__ == "__main__":
    unittest.main()
