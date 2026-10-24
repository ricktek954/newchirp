#!/usr/bin/env bash
set -euo pipefail

RELEASE_TAG="20260807"
PYTHON_VERSION="3.13.15"

# Fingerprints for the 20260807 install_only_stripped builds.
python_runtime_sha256() {
  case "$1" in
    x86_64)
      printf '%s\n' '44bf9ae71f4b45e3ba3104ae331c6eff3f7002593c26fd12453eb9310c4f259a'
      ;;
    aarch64)
      printf '%s\n' 'aa90bcd4eccbec2753cd6e134d7a0477b23f2f972d83c7894e507bbc874c4fef'
      ;;
    *)
      return 1
      ;;
  esac
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_SUPPORT_DIR="${NEWCHIRP_BUILD_SUPPORT_DIR:-$PROJECT_DIR/build_support}"
CACHE_DIR="$BUILD_SUPPORT_DIR/cache"
mkdir -p "$CACHE_DIR"

BUNDLE_DIR=""
CHIRP_SOURCE_ENV="${CHIRP_SOURCE:-}"
CHIRP_SOURCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle-dir)
      BUNDLE_DIR="$2"
      shift 2
      ;;
    --chirp-source)
      CHIRP_SOURCE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done
if [[ -z "$CHIRP_SOURCE" && -n "$CHIRP_SOURCE_ENV" ]]; then
  CHIRP_SOURCE="$CHIRP_SOURCE_ENV"
fi

# Normalize Windows paths so the MSYS bash environment can use them directly.
to_posix() {
  local path="$1"
  if [[ -n "$path" && "$path" =~ ^[A-Za-z]:[\\/] ]] && command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$path"
  else
    printf '%s' "$path"
  fi
}
BUNDLE_DIR="$(to_posix "$BUNDLE_DIR")"
CHIRP_SOURCE="$(to_posix "$CHIRP_SOURCE")"

if [[ -z "$BUNDLE_DIR" ]]; then
  BUNDLE_DIR="$PROJECT_DIR/build/windows/x64/runner/Release"
fi
if [[ ! -d "$BUNDLE_DIR" ]]; then
  echo "Flutter release bundle not found: $BUNDLE_DIR" >&2
  echo "Run 'flutter build windows --release' first, or pass --bundle-dir." >&2
  exit 1
fi

case "$(uname -m)" in
  x86_64|AMD64)
    PY_ARCH="x86_64"
    ;;
  aarch64|ARM64)
    PY_ARCH="aarch64"
    ;;
  *)
    echo "Unsupported host architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

ASSET="cpython-${PYTHON_VERSION}+${RELEASE_TAG}-${PY_ARCH}-pc-windows-msvc-install_only_stripped.tar.gz"
ARCHIVE="$CACHE_DIR/$ASSET"
EXTRACT_DIR="$CACHE_DIR/python-${PYTHON_VERSION}-${PY_ARCH}"
RUNTIME_SRC="$EXTRACT_DIR/python"

if [[ ! -f "$RUNTIME_SRC/python.exe" ]]; then
  if [[ ! -f "$ARCHIVE" ]]; then
    URL="https://github.com/astral-sh/python-build-standalone/releases/download/${RELEASE_TAG}/${ASSET//+/%2B}"
    echo "Downloading bundled Python runtime: $URL" >&2
    curl -fL --retry 3 -o "$ARCHIVE" "$URL"
  fi

  EXPECTED_SHA="$(python_runtime_sha256 "$PY_ARCH")" || {
    echo "No saved Python fingerprint for $ASSET" >&2
    exit 1
  }
  ACTUAL_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
  if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]]; then
    echo "Checksum mismatch for $ASSET" >&2
    echo "Expected $EXPECTED_SHA" >&2
    echo "Actual   $ACTUAL_SHA" >&2
    rm -f "$ARCHIVE"
    exit 1
  fi

  rm -rf "$EXTRACT_DIR"
  mkdir -p "$EXTRACT_DIR"
  tar -xzf "$ARCHIVE" -C "$EXTRACT_DIR"
fi

if [[ ! -f "$RUNTIME_SRC/python.exe" ]]; then
  echo "Bundled Python runtime is missing: $RUNTIME_SRC/python.exe" >&2
  exit 1
fi
PYTHON_EXE="$RUNTIME_SRC/python.exe"

if [[ -n "$CHIRP_SOURCE" ]]; then
  CHIRP_ROOT="$CHIRP_SOURCE"
else
  CHIRP_ROOT=""
  if [[ "${NEWCHIRP_AUTO_UPDATE_CHIRP:-1}" != "0" ]]; then
    if UPDATED_CHIRP="$(NEWCHIRP_PYTHON="$PYTHON_EXE" bash "$SCRIPT_DIR/update_chirp.sh" 2>/dev/null)"; then
      CHIRP_ROOT="$UPDATED_CHIRP"
    fi
  fi
  if [[ -z "$CHIRP_ROOT" ]]; then
    CHIRP_VERSION=""
    if [[ -s "$BUILD_SUPPORT_DIR/chirp-version.txt" ]]; then
      CHIRP_VERSION="$(tr -d '[:space:]' < "$BUILD_SUPPORT_DIR/chirp-version.txt")"
    fi
    if [[ -n "$CHIRP_VERSION" && -d "$BUILD_SUPPORT_DIR/chirp-$CHIRP_VERSION/chirp" ]]; then
      CHIRP_ROOT="$BUILD_SUPPORT_DIR/chirp-$CHIRP_VERSION"
      echo "warning: Could not check for a newer CHIRP build; using cached next-$CHIRP_VERSION." >&2
    elif [[ -d "$BUILD_SUPPORT_DIR/chirp-master/chirp" ]]; then
      CHIRP_ROOT="$BUILD_SUPPORT_DIR/chirp-master"
      echo "warning: No versioned CHIRP snapshot is available; using cached chirp-master." >&2
    elif [[ -n "${CHIRP_FALLBACK:-}" && -d "$CHIRP_FALLBACK/chirp" ]]; then
      CHIRP_ROOT="$CHIRP_FALLBACK"
    else
      echo "warning: Upstream CHIRP archive is unreachable; fetching master directly from GitHub." >&2
      curl -fL --retry 3 -o "$CACHE_DIR/chirp-master.tar.gz" \
        "https://codeload.github.com/kk7ds/chirp/tar.gz/refs/heads/master"
      rm -rf "$BUILD_SUPPORT_DIR/chirp-master"
      mkdir -p "$BUILD_SUPPORT_DIR/chirp-master"
      tar -xzf "$CACHE_DIR/chirp-master.tar.gz" \
        -C "$BUILD_SUPPORT_DIR/chirp-master" --strip-components=1
      CHIRP_ROOT="$BUILD_SUPPORT_DIR/chirp-master"
    fi
  fi
fi

CHIRP_PACKAGE="$CHIRP_ROOT/chirp"
if [[ ! -d "$CHIRP_PACKAGE" ]]; then
  echo "CHIRP package not found: $CHIRP_PACKAGE" >&2
  exit 1
fi

rm -rf "$BUNDLE_DIR/python"
cp -a "$RUNTIME_SRC" "$BUNDLE_DIR/python"

rm -rf "$BUNDLE_DIR/chirp"
cp -a "$CHIRP_PACKAGE" "$BUNDLE_DIR/chirp"
if [[ -d "$PROJECT_DIR/drivers" ]]; then
  mkdir -p "$BUNDLE_DIR/chirp/drivers"
  cp "$PROJECT_DIR"/drivers/*.py "$BUNDLE_DIR/chirp/drivers/"
fi

if [[ -f "$CHIRP_ROOT/COPYING" ]]; then
  cp "$CHIRP_ROOT/COPYING" "$BUNDLE_DIR/chirp-COPYING.txt"
fi

if [[ -f "$BUILD_SUPPORT_DIR/chirp-version.txt" ]]; then
  cp "$BUILD_SUPPORT_DIR/chirp-version.txt" "$BUNDLE_DIR/chirp-version.txt"
else
  CHIRP_VERSION_LINE="$(sed -n 's/.*next-\([0-9]\{8\}\).*/\1/p' \
    "$CHIRP_ROOT/chirp/__init__.py" 2>/dev/null | head -1)"
  if [[ -n "$CHIRP_VERSION_LINE" ]]; then
    printf '%s\n' "$CHIRP_VERSION_LINE" > "$BUNDLE_DIR/chirp-version.txt"
  fi
fi

echo "Bundled Python and CHIRP source into $BUNDLE_DIR"
