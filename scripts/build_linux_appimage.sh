#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BUNDLE_DIR="$PROJECT_DIR/build/linux/x64/release/bundle"
OUTPUT=""
APPIMAGETOOL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle-dir)
      BUNDLE_DIR="$2"
      shift 2
      ;;
    --output)
      OUTPUT="$2"
      shift 2
      ;;
    --appimagetool)
      APPIMAGETOOL="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! -x "$BUNDLE_DIR/newchirp" ]]; then
  echo "Linux release bundle not found: $BUNDLE_DIR" >&2
  echo "Run 'flutter build linux --release' and scripts/bundle_linux_runtime.sh first." >&2
  exit 1
fi

VERSION="$(sed -n 's/^version:[[:space:]]*\([^+[:space:]]*\).*/\1/p' "$PROJECT_DIR/pubspec.yaml" | head -1)"
if [[ -z "$VERSION" ]]; then
  echo "Could not read version from pubspec.yaml." >&2
  exit 1
fi

case "$(uname -m)" in
  x86_64)
    ARCH_LABEL="x64"
    APPIMAGE_ARCH="x86_64"
    ;;
  aarch64)
    ARCH_LABEL="arm64"
    APPIMAGE_ARCH="aarch64"
    ;;
  *)
    echo "Unsupported host architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

if [[ -z "$APPIMAGETOOL" ]]; then
  if command -v appimagetool >/dev/null 2>&1; then
    APPIMAGETOOL="$(command -v appimagetool)"
  elif [[ -x "/tmp/newchirp-release-tools/appimagetool-${APPIMAGE_ARCH}.AppImage" ]]; then
    APPIMAGETOOL="/tmp/newchirp-release-tools/appimagetool-${APPIMAGE_ARCH}.AppImage"
  else
    echo "appimagetool is required. Pass --appimagetool PATH." >&2
    exit 1
  fi
fi

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$PROJECT_DIR/build/NewChirp-linux-$ARCH_LABEL-${VERSION}.AppImage"
fi
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PROJECT_DIR/$OUTPUT"
fi

APPDIR="$PROJECT_DIR/build/linux-appimage/NewChirp.AppDir"
rm -rf "$APPDIR"
mkdir -p \
  "$APPDIR/opt/newchirp" \
  "$APPDIR/opt/newchirp/dri" \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/glvnd/egl_vendor.d" \
  "$APPDIR/usr/share/icons/hicolor/16x16/apps" \
  "$APPDIR/usr/share/icons/hicolor/32x32/apps" \
  "$APPDIR/usr/share/icons/hicolor/64x64/apps" \
  "$APPDIR/usr/share/icons/hicolor/128x128/apps" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
  "$APPDIR/usr/share/icons/hicolor/512x512/apps"

cp -a "$BUNDLE_DIR/." "$APPDIR/opt/newchirp/"
find "$APPDIR/opt/newchirp" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$APPDIR/opt/newchirp" -type f -name '*.pyc' -delete

copy_host_library() {
  local soname="$1"
  local path=""

  if command -v ldconfig >/dev/null 2>&1; then
    path="$(ldconfig -p 2>/dev/null | awk -v soname="$soname" '$1 == soname {print $NF; exit}')"
  fi
  if [[ -z "$path" || ! -r "$path" ]]; then
    for candidate in \
      "/usr/lib/$soname" \
      "/usr/lib64/$soname" \
      "/usr/lib/x86_64-linux-gnu/$soname" \
      "/usr/lib/aarch64-linux-gnu/$soname" \
      "/lib/x86_64-linux-gnu/$soname" \
      "/lib/aarch64-linux-gnu/$soname"; do
      if [[ -r "$candidate" ]]; then
        path="$candidate"
        break
      fi
    done
  fi
  if [[ -z "$path" || ! -r "$path" ]]; then
    echo "Could not find $soname on the build host." >&2
    exit 1
  fi

  cp -L "$path" "$APPDIR/opt/newchirp/lib/$soname"

  if command -v ldd >/dev/null 2>&1; then
    ldd "$path" | awk '/=> \// {print $3}' | while read -r dep; do
      case "$(basename "$dep")" in
        libc.so.*|libdl.so.*|libm.so.*|libpthread.so.*|librt.so.*|ld-linux*.so.*)
          continue
          ;;
      esac
      cp -Ln "$dep" "$APPDIR/opt/newchirp/lib/$(basename "$dep")" 2>/dev/null || true
    done
  fi
}

copy_library_dependencies() {
  local path="$1"

  if command -v ldd >/dev/null 2>&1; then
    ldd "$path" | awk '/=> \// {print $3}' | while read -r dep; do
      case "$(basename "$dep")" in
        libc.so.*|libdl.so.*|libm.so.*|libpthread.so.*|librt.so.*|ld-linux*.so.*)
          continue
          ;;
      esac
      cp -Ln "$dep" "$APPDIR/opt/newchirp/lib/$(basename "$dep")" 2>/dev/null || true
    done
  fi
}

copy_host_library libEGL.so.1
copy_host_library libGLESv2.so.2
copy_host_library libEGL_mesa.so.0

if [[ -f /usr/share/glvnd/egl_vendor.d/50_mesa.json ]]; then
  cp /usr/share/glvnd/egl_vendor.d/50_mesa.json "$APPDIR/usr/share/glvnd/egl_vendor.d/"
fi
for driver in \
  /usr/lib/dri/swrast_dri.so \
  /usr/lib/dri/kms_swrast_dri.so \
  /usr/lib/x86_64-linux-gnu/dri/swrast_dri.so \
  /usr/lib/x86_64-linux-gnu/dri/kms_swrast_dri.so \
  /usr/lib/aarch64-linux-gnu/dri/swrast_dri.so \
  /usr/lib/aarch64-linux-gnu/dri/kms_swrast_dri.so; do
  if [[ -r "$driver" ]]; then
    cp -L "$driver" "$APPDIR/opt/newchirp/dri/$(basename "$driver")"
    copy_library_dependencies "$driver"
  fi
done

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$HERE/opt/newchirp/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if ! ldconfig -p 2>/dev/null | grep -q 'libEGL\.so\.1' ||
  ! ldconfig -p 2>/dev/null | grep -q 'libGLESv2\.so\.2'; then
  export __EGL_VENDOR_LIBRARY_DIRS="$HERE/usr/share/glvnd/egl_vendor.d"
  export __EGL_VENDOR_LIBRARY_FILENAMES="$HERE/usr/share/glvnd/egl_vendor.d/50_mesa.json"
  export LIBGL_DRIVERS_PATH="$HERE/opt/newchirp/dri"
fi
exec "$HERE/opt/newchirp/newchirp" "$@"
APPRUN
chmod 0755 "$APPDIR/AppRun"
ln -s /opt/newchirp/newchirp "$APPDIR/usr/bin/newchirp"

for size in 16 32 64 128 256 512; do
  icon="$PROJECT_DIR/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_${size}.png"
  if [[ -f "$icon" ]]; then
    cp "$icon" "$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps/newchirp.png"
    if [[ "$size" == "512" ]]; then
      cp "$icon" "$APPDIR/newchirp.png"
    fi
  fi
done
if [[ -f "$APPDIR/newchirp.png" ]]; then
  ln -s newchirp.png "$APPDIR/.DirIcon"
fi

cat > "$APPDIR/newchirp.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=NewChirp
Comment=Desktop radio programmer for amateur and GMRS radios
Exec=newchirp
Icon=newchirp
Categories=Utility;HamRadio;
Terminal=false
DESKTOP
cp "$APPDIR/newchirp.desktop" "$APPDIR/usr/share/applications/newchirp.desktop"

chmod 0755 "$APPDIR/opt/newchirp/newchirp"
find "$APPDIR/usr/share/icons" -type f -exec chmod 0644 {} +

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"
ARCH="$APPIMAGE_ARCH" "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
chmod 0755 "$OUTPUT"
echo "Built $OUTPUT"
