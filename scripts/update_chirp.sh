#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_SUPPORT_DIR="${NEWCHIRP_BUILD_SUPPORT_DIR:-$PROJECT_DIR/build_support}"
CACHE_DIR="$BUILD_SUPPORT_DIR/cache"
CURRENT_VERSION_FILE="$BUILD_SUPPORT_DIR/chirp-version.txt"

mkdir -p "$BUILD_SUPPORT_DIR" "$CACHE_DIR"

apply_newchirp_patches() {
  local target="$1"
  "${NEWCHIRP_PYTHON:-python3}" - "$target" <<'PY'
import sys

path = sys.argv[1] + "/chirp/drivers/baofeng_uv17Pro.py"
try:
    text = open(path, encoding="utf-8").read()
except FileNotFoundError:
    print('warning: CHIRP UV5G driver not found at %s; skipping GMRS preset patch' % path, file=sys.stderr)
    sys.exit(0)

if "UV5G_GMRS_PRESETS" in text:
    sys.exit(0)

anchor = 'MSTRING_BFK6 = b"PROGRAMBF-K6PROU"\n'
insert = (
    anchor
    + "\nUV5G_GMRS_PRESETS = (\n"
    + "    bandplan_na.GMRS_LOW +\n"
    + "    bandplan_na.GMRS_HHONLY +\n"
    + "    bandplan_na.GMRS_HIRPT +\n"
    + "    bandplan_na.GMRS_HIRPT\n"
    + ")\n"
)
if anchor not in text:
    print('warning: CHIRP UV5G patch anchor missing in %s; GMRS presets were not injected (upstream may have renamed MSTRING_BFK6)' % path, file=sys.stderr)
    sys.exit(0)
text = text.replace(anchor, insert, 1)

old = (
    "        if mem.number >= 1 and mem.number <= 30:\n"
    "            mem.immutable = ['freq', 'duplex', 'offset']\n"
)
new = (
    "        if mem.number >= 1 and mem.number <= 30:\n"
    "            mem.freq = UV5G_GMRS_PRESETS[mem.number - 1]\n"
    "            if mem.number >= 15:\n"
    "                mem.duplex = '+'\n"
    "                mem.offset = 5000000\n"
    "            else:\n"
    "                mem.duplex = ''\n"
    "                mem.offset = 0\n"
    "            mem.immutable = ['freq', 'duplex', 'offset']\n"
)
if old not in text:
    print('warning: CHIRP UV5G patch target block missing in %s; GMRS preset frequencies were not applied' % path, file=sys.stderr)
    sys.exit(0)
text = text.replace(old, new, 1)

open(path, "w", encoding="utf-8").write(text)
PY
}

PIN_FILE="$SCRIPT_DIR/chirp-source.pin"
if [[ ! -f "$PIN_FILE" ]]; then
  echo "CHIRP pin file is missing: $PIN_FILE" >&2
  exit 1
fi

COMMIT="$(awk '/^commit / {print $2; exit}' "$PIN_FILE")"
EXPECTED_SHA="$(awk '/^sha256 / {print $2; exit}' "$PIN_FILE")"
if [[ ! "$COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "CHIRP pin commit must be 40 hex characters." >&2
  exit 1
fi
if [[ ! "$EXPECTED_SHA" =~ ^[0-9a-f]{64}$ ]]; then
  echo "CHIRP pin sha256 must be 64 hex characters." >&2
  exit 1
fi

ARCHIVE="$CACHE_DIR/chirp-$COMMIT.tar.gz"
TARGET_DIR="$BUILD_SUPPORT_DIR/chirp-$COMMIT"
URL="https://codeload.github.com/kk7ds/chirp/tar.gz/$COMMIT"

download_pinned_archive() {
  echo "Downloading pinned CHIRP commit $COMMIT..." >&2
  local partial="$ARCHIVE.partial"
  rm -f "$partial"
  curl -fL --retry 3 -o "$partial" "$URL"
  mv "$partial" "$ARCHIVE"
}

verify_pinned_archive() {
  "${NEWCHIRP_PYTHON:-python3}" - "$ARCHIVE" "$EXPECTED_SHA" <<'PY'
import hashlib
import sys
import tarfile

archive, expected = sys.argv[1], sys.argv[2]
digest = hashlib.sha256(open(archive, "rb").read()).hexdigest()
if digest != expected:
    print("CHIRP archive checksum does not match the pin.", file=sys.stderr)
    print("Expected %s" % expected, file=sys.stderr)
    print("Actual   %s" % digest, file=sys.stderr)
    sys.exit(2)

def unsafe_path(value):
    if not isinstance(value, str) or not value:
        return True
    name = value.replace("\\", "/")
    if "\n" in name or "\r" in name or "\0" in name:
        return True
    # A drive letter can escape the extract folder on Windows.
    if len(name) >= 2 and name[0].isalpha() and name[1] == ":":
        return True
    parts = [part for part in name.split("/") if part]
    return name.startswith("/") or any(part == ".." for part in parts)

with tarfile.open(archive, "r:gz") as bundle:
    for member in bundle.getmembers():
        if unsafe_path(member.name):
            print("CHIRP archive has an unsafe path: %s" % member.name, file=sys.stderr)
            sys.exit(3)
        if (member.issym() or member.islnk()) and unsafe_path(member.linkname):
            print("CHIRP archive has an unsafe link: %s" % member.name, file=sys.stderr)
            sys.exit(3)
PY
}

if [[ ! -f "$ARCHIVE" ]]; then
  download_pinned_archive
fi
set +e
verify_pinned_archive
pin_status=$?
set -e
if [[ "$pin_status" -ne 0 ]]; then
  rm -f "$ARCHIVE"
  if [[ "$pin_status" -ne 2 ]]; then
    exit 1
  fi
  download_pinned_archive
  verify_pinned_archive
fi

TMP_DIR="$(mktemp -d "$BUILD_SUPPORT_DIR/chirp-extract.XXXXXX")"
tar -xzf "$ARCHIVE" -C "$TMP_DIR" --strip-components=1
rm -rf "$TARGET_DIR"
mv "$TMP_DIR" "$TARGET_DIR"

apply_newchirp_patches "$TARGET_DIR"

if [[ ! -d "$TARGET_DIR/chirp" ]]; then
  echo "Pinned CHIRP source is missing the chirp package." >&2
  exit 1
fi

printf '%s\n' "$COMMIT" > "$CURRENT_VERSION_FILE"
echo "Using pinned CHIRP commit $COMMIT" >&2
echo "$TARGET_DIR"
