#!/usr/bin/env python3
"""Reject Linux release payloads built against a newer desktop ABI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
from typing import Iterable


UBUNTU_RELEASE = "20.04"
MAX_GLIBC = (2, 31)
MAX_GLIB = (2, 64)
GLIBC_VERSION_RE = re.compile(r"\bGLIBC_(\d+(?:\.\d+)+)\b")
FORBIDDEN_SYMBOLS = {
    b"g_once_init_enter_pointer": "GLib 2.80",
    b"g_once_init_leave_pointer": "GLib 2.80",
}


def version_tuple(value: str, width: int = 3) -> tuple[int, ...]:
    parts = [int(part) for part in value.split(".")]
    return tuple((parts + [0] * width)[:width])


def read_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        parsed = shlex.split(raw)
        values[key] = parsed[0] if parsed else ""
    return values


def command_version(command: list[str], pattern: str) -> str:
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(pattern, result.stdout + result.stderr)
    if not match:
        raise RuntimeError(
            "Could not read a version from: %s" % " ".join(command)
        )
    return match.group(1)


def require_release_host() -> list[str]:
    errors: list[str] = []
    os_release = read_os_release()
    distro = os_release.get("ID", "")
    version = os_release.get("VERSION_ID", "")
    if distro != "ubuntu" or not version.startswith(UBUNTU_RELEASE):
        errors.append(
            "Linux release builds must run on Ubuntu %s; found %s %s"
            % (UBUNTU_RELEASE, distro or "unknown", version or "unknown")
        )

    try:
        host_glibc = command_version(
            ["ldd", "--version"],
            r"(?:GNU libc|GLIBC)\s+(\d+\.\d+)",
        )
        if version_tuple(host_glibc)[:2] > MAX_GLIBC:
            errors.append(
                "Host glibc %s exceeds the release ceiling %s"
                % (host_glibc, ".".join(map(str, MAX_GLIBC)))
            )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        errors.append(str(exc))

    if shutil.which("pkg-config"):
        try:
            host_glib = command_version(
                ["pkg-config", "--modversion", "glib-2.0"],
                r"(\d+\.\d+(?:\.\d+)?)",
            )
            if version_tuple(host_glib)[:2] > MAX_GLIB:
                errors.append(
                    "Host GLib %s exceeds the Ubuntu %s ceiling %s"
                    % (
                        host_glib,
                        UBUNTU_RELEASE,
                        ".".join(map(str, MAX_GLIB)),
                    )
                )
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            errors.append(str(exc))
    else:
        errors.append("pkg-config is required to verify the release GLib baseline")

    return errors


def elf_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            candidates = [root]
        else:
            candidates = root.rglob("*")
        for path in candidates:
            if not path.is_file():
                continue
            try:
                with path.open("rb") as handle:
                    if handle.read(4) == b"\x7fELF":
                        yield path
            except OSError:
                continue


def required_glibc_versions(path: Path) -> tuple[set[str], bool]:
    if not shutil.which("readelf"):
        raise RuntimeError("readelf is required to verify the Linux release ABI")
    result = subprocess.run(
        ["readelf", "--version-info", "--wide", os.fspath(path)],
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    )
    output = result.stdout + result.stderr
    return set(GLIBC_VERSION_RE.findall(output)), "GLIBC_ABI_DT_RELR" in output


def check_roots(
    roots: list[Path],
) -> tuple[list[str], tuple[int, ...] | None]:
    errors: list[str] = []
    maximum: tuple[int, ...] | None = None
    for path in elf_files(roots):
        versions, requires_dt_relr = required_glibc_versions(path)
        for version in sorted(versions, key=version_tuple):
            parsed = version_tuple(version)
            if maximum is None or parsed > maximum:
                maximum = parsed
            if parsed[:2] > MAX_GLIBC:
                errors.append("%s requires GLIBC_%s" % (path, version))
        if requires_dt_relr:
            errors.append("%s requires GLIBC_ABI_DT_RELR" % path)

        content = path.read_bytes()
        for symbol, introduced_by in FORBIDDEN_SYMBOLS.items():
            if symbol in content:
                errors.append(
                    "%s requires %s from %s"
                    % (path, symbol.decode("ascii"), introduced_by)
                )
    return errors, maximum


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that Linux release payloads are compatible with the "
            "Ubuntu 20.04 desktop ABI baseline."
        )
    )
    parser.add_argument(
        "roots",
        nargs="+",
        type=Path,
        help="Bundled payload files or directories to inspect",
    )
    parser.add_argument(
        "--skip-host-check",
        action="store_true",
        help="Inspect payloads without requiring an Ubuntu 20.04 build host",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    missing = [path for path in args.roots if not path.exists()]
    if missing:
        for path in missing:
            print("Linux release payload does not exist: %s" % path, file=sys.stderr)
        return 2

    errors = [] if args.skip_host_check else require_release_host()
    payload_errors, maximum = check_roots(args.roots)
    errors.extend(payload_errors)
    if errors:
        for error in errors:
            print("Linux release ABI check failed: %s" % error, file=sys.stderr)
        return 1

    maximum_label = ".".join(map(str, maximum)) if maximum else "none"
    print(
        "Linux release ABI check passed: max GLIBC_%s, "
        "Ubuntu %s / GLib %s ceiling"
        % (
            maximum_label,
            UBUNTU_RELEASE,
            ".".join(map(str, MAX_GLIB[:2])),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
