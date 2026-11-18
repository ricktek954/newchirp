"""Regression: Kenwood live writes on a fresh connection.

NewChirp 1.0.57 report (TM-D710, 2026-11-18): the read succeeded, but the
write failed with "Reported error: 0". Stock ``KenwoodLiveRadio.set_memory``
deleted ``_memcache[0]`` on a new instance whose cache was empty.
"""

from pathlib import Path
import importlib.util
import sys
import unittest

from chirp_test_source import chirp_source


ROOT = Path(__file__).resolve().parent.parent
SOURCE = chirp_source()
VENDOR = ROOT / "assets/python/pyserial-3.5-py2.py3-none-any.whl"


def _load_bridge():
    spec = importlib.util.spec_from_file_location(
        "newchirp_chirp_bridge_kenwood_live_cache",
        ROOT / "scripts/chirp_bridge.py",
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = bridge
    spec.loader.exec_module(bridge)
    return bridge


class FakeTMD710Live:
    """Answers TM-D710 ME/MN commands from an in-memory channel table."""

    def __init__(self, channels):
        # number -> ME spec string (without the leading "ME ")
        self.channels = dict(channels)
        self.names = {}
        self.sent = []
        self._pending = b""
        self.timeout = 0.1
        self.baudrate = 9600

    def write(self, data):
        cmd = data.decode("cp1252").rstrip("\r")
        self.sent.append(cmd)
        op, _, args = cmd.partition(" ")
        fields = args.split(",") if args else []
        if op == "ME" and len(fields) == 1:
            number = int(fields[0])
            reply = ("ME " + self.channels[number]) if number in self.channels \
                else "N"
        elif op == "ME" and len(fields) == 2 and fields[1] == "":
            self.channels.pop(int(fields[0]), None)
            reply = cmd
        elif op == "ME":
            self.channels[int(fields[0])] = args
            reply = cmd
        elif op == "MN" and len(fields) == 1:
            number = int(fields[0])
            reply = "MN %03i,%s" % (number, self.names.get(number, ""))
        elif op == "MN":
            self.names[int(fields[0])] = fields[1]
            reply = cmd
        else:
            reply = "?"
        self._pending += (reply + "\r").encode("cp1252")

    def read(self, size):
        chunk, self._pending = self._pending[:size], self._pending[size:]
        return chunk


def _spec(number, freq):
    return ("%03i,%010i,0,0,0,0,0,0,08,08,000,00600000,0,0000000000,0,0"
            % (number, freq))


class KenwoodLiveWriteCacheTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = _load_bridge()
        cls.directory = cls.bridge.load_chirp(
            str(SOURCE), str(VENDOR), str(ROOT / "drivers"),
        )

    def _fresh_radio(self, fake):
        from chirp.drivers import kenwood_live
        radio = object.__new__(kenwood_live.TMD710Radio)
        kenwood_live.KenwoodLiveRadio.__init__(radio, None)
        radio.pipe = fake
        return radio

    def test_set_memory_on_fresh_connection_does_not_raise_keyerror(self):
        from chirp import chirp_common
        fake = FakeTMD710Live({})
        radio = self._fresh_radio(fake)
        self.assertEqual(radio._memcache, {})

        mem = chirp_common.Memory()
        mem.number = 0
        mem.freq = 146520000
        mem.name = "SIMPLEX"
        radio.set_memory(mem)

        self.assertIn(0, fake.channels)
        self.assertEqual(fake.names[0], "SIMPLEX")
        self.assertEqual(radio.get_memory(0).freq, 146520000)

    def test_failed_spec_does_not_leave_cache_placeholder(self):
        from chirp import chirp_common
        fake = FakeTMD710Live({})
        radio = self._fresh_radio(fake)
        mem = chirp_common.Memory()
        mem.number = 3
        mem.freq = 146520000
        mem.tuning_step = 2.5  # not a TM-D710 step; spec construction fails
        with self.assertRaises(ValueError):
            radio.set_memory(mem)
        self.assertNotIn(3, radio._memcache)
        self.assertEqual(fake.sent, [])

    def test_erase_on_fresh_connection_clears_occupied_slot(self):
        fake = FakeTMD710Live({5: _spec(5, 147000000)})
        radio = self._fresh_radio(fake)
        radio.erase_memory(5)
        self.assertNotIn(5, fake.channels)
        self.assertIn("ME 005,", fake.sent)

    def test_erase_on_fresh_connection_skips_already_empty_slot(self):
        fake = FakeTMD710Live({})
        radio = self._fresh_radio(fake)
        radio.erase_memory(7)
        self.assertEqual(fake.sent, ["ME 007"])

    def test_old_live_subclass_uses_safe_path(self):
        from chirp.drivers import kenwood_live
        self.assertTrue(getattr(
            kenwood_live.KenwoodLiveRadio.set_memory,
            "newchirp_cache_safe", False))
        self.assertIs(kenwood_live.TMV71Radio.set_memory,
                      kenwood_live.KenwoodLiveRadio.set_memory)


if __name__ == "__main__":
    unittest.main()
