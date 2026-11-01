"""Resolve the local CHIRP source used by offline tests."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PIN_FILE = ROOT / "scripts/chirp-source.pin"
VERSION_FILE = ROOT / "build_support/chirp-version.txt"


def _pinned_commit():
    for line in PIN_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("commit "):
            commit = line.split(maxsplit=1)[1]
            if len(commit) == 40 and all(char in "0123456789abcdef" for char in commit):
                return commit
            raise RuntimeError("CHIRP source pin contains an invalid commit.")
    raise RuntimeError("CHIRP source pin is missing its commit.")


def chirp_source():
    """Return the downloaded source for the currently pinned CHIRP commit."""
    commit = _pinned_commit()
    if VERSION_FILE.is_file():
        current = VERSION_FILE.read_text(encoding="utf-8").strip()
        if current != commit:
            raise RuntimeError(
                "CHIRP build metadata is stale. "
                "Run scripts/update_chirp.sh before running tests."
            )
    return ROOT / "build_support" / ("chirp-" + commit)
