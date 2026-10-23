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

# The Flutter app is built universal (arm64 + x86_64), so the bundled Python
# must run on both too. Bundling only the build host's architecture leaves the
# app unable to start its CHIRP helper on the other kind of Mac.
read -r -a BUNDLE_ARCHS <<< "${NEWCHIRP_PYTHON_ARCHS:-arm64 x86_64}"

# Downloads and verifies one architecture's runtime, then prints its path.
fetch_runtime() {
  local arch="$1" py_arch expected_sha
  case "$arch" in
    arm64)
      py_arch="aarch64"
      expected_sha="dbadb0ffe46f8bace50daaf8a0c5fc6903c003690776da9eb5269e33c856bb53"
      ;;
    x86_64)
      py_arch="x86_64"
      expected_sha="187eed2282e9c3a5b6b14953d564ee25a9f35cf2c209c9fa292186ee48b0e4a1"
      ;;
    *)
      echo "Unsupported Python architecture: $arch" >&2
      exit 2
      ;;
  esac

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
  printf '%s\n' "$runtime_src"
}

RUNTIME_SRCS=()
for arch in "${BUNDLE_ARCHS[@]}"; do
  RUNTIME_SRCS+=("$(fetch_runtime "$arch")")
done

rm -rf "$RESOURCES_DIR/python"
ditto "${RUNTIME_SRCS[0]}" "$RESOURCES_DIR/python"

# Merge every Mach-O file (interpreter, libpython, extension modules) into a
# fat binary. lipo invalidates the existing signatures, so re-sign ad hoc;
# Apple Silicon refuses to run unsigned code.
if [[ ${#RUNTIME_SRCS[@]} -gt 1 ]]; then
  while IFS= read -r -d '' file; do
    lipo -archs "$file" >/dev/null 2>&1 || continue
    rel="${file#"$RESOURCES_DIR/python/"}"
    slices=()
    for src in "${RUNTIME_SRCS[@]}"; do
      if [[ ! -f "$src/$rel" ]]; then
        echo "Python runtimes differ; $rel is missing from $src" >&2
        exit 1
      fi
      slices+=("$src/$rel")
    done
    lipo -create "${slices[@]}" -output "$file.universal"
    mv "$file.universal" "$file"
    if [[ "$(file -b "$file")" != *"ar archive"* ]]; then
      codesign --force --sign - "$file" >/dev/null 2>&1 || true
    fi
  done < <(find "$RESOURCES_DIR/python" -type f -print0)
fi

if [[ -n "$CHIRP_SOURCE" ]]; then
  CHIRP_ROOT="$CHIRP_SOURCE"
elif [[ "${NEWCHIRP_AUTO_UPDATE_CHIRP:-1}" != "0" ]]; then
  if UPDATED_CHIRP="$(bash "$SCRIPT_DIR/update_chirp.sh")"; then
    CHIRP_ROOT="$UPDATED_CHIRP"
  else
    echo "warning: Could not check for a newer CHIRP build; using the local snapshot." >&2
    CHIRP_ROOT="$PROJECT_DIR/../chirp-20260626"
  fi
else
  CHIRP_ROOT="$PROJECT_DIR/../chirp-20260626"
fi

CHIRP_PACKAGE="$CHIRP_ROOT/chirp"
if [[ ! -d "$CHIRP_PACKAGE" ]]; then
  echo "CHIRP package not found: $CHIRP_PACKAGE" >&2
  exit 1
fi

rm -rf "$RESOURCES_DIR/chirp"
ditto "$CHIRP_PACKAGE" "$RESOURCES_DIR/chirp"

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
