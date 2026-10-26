#!/usr/bin/env bash
set -euo pipefail

RELEASE_TAG="20260807"
PYTHON_VERSION="3.13.15"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_SUPPORT_DIR="${NEWCHIRP_BUILD_SUPPORT_DIR:-$PROJECT_DIR/build_support}"
CACHE_DIR="$BUILD_SUPPORT_DIR/cache"
mkdir -p "$CACHE_DIR"

RESOURCES_DIR=""
CHIRP_SOURCE_ENV="${CHIRP_SOURCE:-}"
CHIRP_SOURCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --resources-dir)
      RESOURCES_DIR="$2"
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

if [[ -z "$RESOURCES_DIR" ]]; then
  if [[ -z "${BUILT_PRODUCTS_DIR:-}" || -z "${UNLOCALIZED_RESOURCES_FOLDER_PATH:-}" ]]; then
    echo "Provide --resources-dir or run inside an Xcode build phase." >&2
    exit 2
  fi
  RESOURCES_DIR="$BUILT_PRODUCTS_DIR/$UNLOCALIZED_RESOURCES_FOLDER_PATH"
fi
mkdir -p "$RESOURCES_DIR"

bundle_python_runtime() {
  local py_arch="$1"
  local expected_sha="$2"
  local runtime_name="$3"
  local asset="cpython-${PYTHON_VERSION}+${RELEASE_TAG}-${py_arch}-apple-darwin-install_only_stripped.tar.gz"
  local archive="$CACHE_DIR/$asset"
  local extract_dir="$CACHE_DIR/python-${PYTHON_VERSION}-${py_arch}"
  local runtime_src="$extract_dir/python"

  if [[ ! -x "$runtime_src/bin/python3" ]]; then
    if [[ ! -f "$archive" ]]; then
      local url="https://github.com/astral-sh/python-build-standalone/releases/download/${RELEASE_TAG}/${asset//+/%2B}"
      echo "Downloading bundled Python runtime: $url" >&2
      curl -fL --retry 3 -o "$archive" "$url"
    fi

    local actual_sha
    actual_sha="$(shasum -a 256 "$archive" | awk '{print $1}')"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
      echo "Checksum mismatch for $asset" >&2
      echo "Expected $expected_sha" >&2
      echo "Actual   $actual_sha" >&2
      exit 1
    fi

    rm -rf "$extract_dir"
    mkdir -p "$extract_dir"
    tar -xzf "$archive" -C "$extract_dir"
  fi

  if [[ ! -x "$runtime_src/bin/python3" ]]; then
    echo "Bundled Python runtime is missing: $runtime_src/bin/python3" >&2
    exit 1
  fi

  rm -rf "$RESOURCES_DIR/$runtime_name"
  ditto "$runtime_src" "$RESOURCES_DIR/$runtime_name"
}

bundle_python_runtime \
  aarch64 \
  dbadb0ffe46f8bace50daaf8a0c5fc6903c003690776da9eb5269e33c856bb53 \
  python-arm64
bundle_python_runtime \
  x86_64 \
  187eed2282e9c3a5b6b14953d564ee25a9f35cf2c209c9fa292186ee48b0e4a1 \
  python-x64

rm -rf "$RESOURCES_DIR/python"
case "$(uname -m)" in
  arm64) ln -s python-arm64 "$RESOURCES_DIR/python" ;;
  x86_64) ln -s python-x64 "$RESOURCES_DIR/python" ;;
  *)
    echo "Unsupported host architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

if [[ -n "$CHIRP_SOURCE" ]]; then
  CHIRP_ROOT="$CHIRP_SOURCE"
else
  CHIRP_ROOT="$(NEWCHIRP_PYTHON="${NEWCHIRP_PYTHON:-python3}" bash "$SCRIPT_DIR/update_chirp.sh")"
fi

CHIRP_PACKAGE="$CHIRP_ROOT/chirp"
if [[ ! -d "$CHIRP_PACKAGE" ]]; then
  echo "CHIRP package not found: $CHIRP_PACKAGE" >&2
  exit 1
fi

rm -rf "$RESOURCES_DIR/chirp"
ditto "$CHIRP_PACKAGE" "$RESOURCES_DIR/chirp"
if [[ -d "$PROJECT_DIR/drivers" ]]; then
  mkdir -p "$RESOURCES_DIR/chirp/drivers"
  cp "$PROJECT_DIR"/drivers/*.py "$RESOURCES_DIR/chirp/drivers/"
fi

if [[ -f "$PROJECT_DIR/tools/newchirp_scsi_mac.c" ]]; then
  clang \
    -O2 \
    -Wall \
    -Wextra \
    -Werror \
    -framework IOKit \
    -framework CoreFoundation \
    "$PROJECT_DIR/tools/newchirp_scsi_mac.c" \
    -o "$RESOURCES_DIR/newchirp_scsi"
fi

if [[ -f "$CHIRP_ROOT/COPYING" ]]; then
  cp "$CHIRP_ROOT/COPYING" "$RESOURCES_DIR/chirp-COPYING.txt"
fi

if [[ -f "$BUILD_SUPPORT_DIR/chirp-version.txt" ]]; then
  cp "$BUILD_SUPPORT_DIR/chirp-version.txt" "$RESOURCES_DIR/chirp-version.txt"
else
  CHIRP_VERSION_LINE="$(sed -n 's/.*next-\([0-9]\{8\}\).*/\1/p' \
    "$CHIRP_ROOT/chirp/__init__.py" 2>/dev/null | head -1)"
  if [[ -n "$CHIRP_VERSION_LINE" ]]; then
    printf '%s\n' "$CHIRP_VERSION_LINE" > "$RESOURCES_DIR/chirp-version.txt"
  fi
fi

echo "Bundled Python and CHIRP source into $RESOURCES_DIR"
