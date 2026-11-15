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
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/16x16/apps" \
  "$APPDIR/usr/share/icons/hicolor/32x32/apps" \
  "$APPDIR/usr/share/icons/hicolor/64x64/apps" \
  "$APPDIR/usr/share/icons/hicolor/128x128/apps" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
  "$APPDIR/usr/share/icons/hicolor/512x512/apps"

cp -a "$BUNDLE_DIR/." "$APPDIR/opt/newchirp/"
find "$APPDIR/opt/newchirp" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$APPDIR/opt/newchirp" -type f -name '*.pyc' -delete

# GLVND, EGL, and GLES loaders must match the host graphics driver. Bundling the
# Ubuntu 20.04 loader alongside a newer Mesa or NVIDIA driver can create the
# Flutter engine but leave its first window blank. Keep these system-provided,
# just like X11, Wayland, and Mesa.
for glvnd_library in libEGL.so.1 libGLESv2.so.2 libGLdispatch.so.0; do
  if [[ -e "$APPDIR/opt/newchirp/lib/$glvnd_library" ]]; then
    echo "Refusing to bundle host GLVND library: $glvnd_library" >&2
    exit 1
  fi
done

python3 "$SCRIPT_DIR/check_linux_release_abi.py" \
  "$APPDIR/opt/newchirp" \
  "$APPDIR/usr"

cat > "$APPDIR/AppRun" <<'APPRUN'
#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LD_LIBRARY_PATH="$HERE/opt/newchirp/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
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
