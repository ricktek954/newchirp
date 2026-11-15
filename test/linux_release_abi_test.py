import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_linux_release_abi",
    ROOT / "scripts" / "check_linux_release_abi.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class LinuxReleaseAbiTest(unittest.TestCase):
    def test_version_tuple_compares_release_versions_numerically(self):
        self.assertGreater(
            MODULE.version_tuple("2.38"),
            MODULE.version_tuple("2.35"),
        )
        self.assertEqual(
            MODULE.version_tuple("2.35"),
            MODULE.version_tuple("2.35.0"),
        )

    def test_glibc_versions_are_extracted_from_readelf_output(self):
        output = (
            "Name: GLIBC_2.2.5 Flags: none Version: 2\n"
            "Name: GLIBC_2.35 Flags: none Version: 3\n"
            "Name: GLIBC_ABI_DT_RELR Flags: none Version: 4\n"
        )
        self.assertEqual(
            set(MODULE.GLIBC_VERSION_RE.findall(output)),
            {"2.2.5", "2.35"},
        )

    def test_payload_check_rejects_new_glibc_and_glib_symbols(self):
        with tempfile.TemporaryDirectory() as temporary:
            payload = Path(temporary) / "newchirp"
            payload.write_bytes(
                b"\x7fELF"
                + b"\0" * 8
                + b"g_once_init_enter_pointer"
                + b"\0"
            )
            with mock.patch.object(
                MODULE,
                "required_glibc_versions",
                return_value=({"2.38"}, True),
            ):
                errors, maximum = MODULE.check_roots([payload])

        self.assertEqual(maximum, (2, 38, 0))
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("GLIBC_2.38" in error for error in errors))
        self.assertTrue(any("GLIBC_ABI_DT_RELR" in error for error in errors))
        self.assertTrue(any("g_once_init_enter_pointer" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
