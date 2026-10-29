"""Checks for the Yaesu clone-read timeout ordering fix."""

from collections import deque
import importlib
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "build_support/chirp-20261023"
PYTHON_VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_yaesu_timing",
        ROOT / "scripts/chirp_bridge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load chirp_bridge.py")
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class _ChunkPipe:
    def __init__(self, chunks):
        self.chunks = deque(chunks)

    def read(self, size):
        if not self.chunks:
            return b""
        return self.chunks.popleft()[:size]


class YaesuCloneTimingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge = _load_bridge()
        cls.directory = bridge.load_chirp(
            str(SOURCE),
            str(PYTHON_VENDOR),
            str(ROOT / "drivers"),
        )
        cls.driver = importlib.import_module(
            "newchirp.drivers.newchirp_yaesu_clone"
        )

    def test_custom_driver_keeps_ft5d_registered(self):
        self.assertIsNotNone(self.directory.get_radio("Yaesu_FT5D_R"))
        self.assertTrue(
            getattr(
                self.driver.yaesu_clone._chunk_read,
                "newchirp_completion_first",
                False,
            )
        )

    def test_complete_final_chunk_wins_over_idle_timeout(self):
        pipe = _ChunkPipe([b"A" * 32, b"B" * 32])
        clock_values = iter([0.0, 0.1, 0.1, 3.2])

        data = self.driver._chunk_read(
            pipe,
            64,
            lambda _status: None,
            clock=lambda: next(clock_values),
        )

        self.assertEqual(data, b"A" * 32 + b"B" * 32)

    def test_incomplete_slow_read_still_raises(self):
        now = [0.0]

        def clock():
            now[0] += 1.0
            return now[0]

        with self.assertRaisesRegex(Exception, "Timed out reading"):
            self.driver._chunk_read(
                _ChunkPipe([b"A" * 32]),
                64,
                lambda _status: None,
                clock=clock,
            )


if __name__ == "__main__":
    unittest.main()
