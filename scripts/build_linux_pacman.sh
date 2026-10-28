#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BUNDLE_DIR="$PROJECT_DIR/build/linux/x64/release/bundle"
OUTPUT=""

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
    PACMAN_ARCH="x86_64"
    ARCH_LABEL="x64"
    ;;
  aarch64)
    PACMAN_ARCH="aarch64"
    ARCH_LABEL="arm64"
    ;;
  *)
    echo "Unsupported host architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

if ! tar --help 2>/dev/null | grep -q -- '--zstd'; then
  echo "GNU tar with zstd support is required to build the Pacman package." >&2
  exit 1
fi
if ! command -v zstd >/dev/null 2>&1; then
  echo "zstd is required to build the Pacman package." >&2
  exit 1
fi

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$PROJECT_DIR/build/NewChirp-linux-$ARCH_LABEL-${VERSION}.pkg.tar.zst"
fi
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PROJECT_DIR/$OUTPUT"
fi

PACKAGE_ROOT="$PROJECT_DIR/build/linux-pacman/pkgroot"
rm -rf "$PACKAGE_ROOT"
mkdir -p \
  "$PACKAGE_ROOT/opt/newchirp" \
  "$PACKAGE_ROOT/usr/bin" \
  "$PACKAGE_ROOT/usr/share/applications" \
  "$PACKAGE_ROOT/usr/share/doc/newchirp" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/16x16/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/32x32/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/64x64/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/128x128/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/256x256/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/512x512/apps"

cp -a "$BUNDLE_DIR/." "$PACKAGE_ROOT/opt/newchirp/"
find "$PACKAGE_ROOT/opt/newchirp" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$PACKAGE_ROOT/opt/newchirp" -type f -name '*.pyc' -delete
ln -s /opt/newchirp/newchirp "$PACKAGE_ROOT/usr/bin/newchirp"

for size in 16 32 64 128 256 512; do
  icon="$PROJECT_DIR/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_${size}.png"
  if [[ -f "$icon" ]]; then
    cp "$icon" "$PACKAGE_ROOT/usr/share/icons/hicolor/${size}x${size}/apps/newchirp.png"
  fi
done

cat > "$PACKAGE_ROOT/usr/share/applications/newchirp.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=NewChirp
Comment=Desktop radio programmer for amateur and GMRS radios
Exec=newchirp
Icon=newchirp
Categories=Utility;HamRadio;
Terminal=false
DESKTOP

cat > "$PACKAGE_ROOT/usr/share/doc/newchirp/copyright" <<'COPYRIGHT'
NewChirp is distributed with the CHIRP driver tree and pyserial.
See /opt/newchirp/chirp-COPYING.txt and /opt/newchirp/data/flutter_assets/assets/licenses/
for bundled third-party license texts.
COPYRIGHT

chmod 0755 "$PACKAGE_ROOT/opt/newchirp/newchirp"
chmod 0644 "$PACKAGE_ROOT/usr/share/applications/newchirp.desktop"
find "$PACKAGE_ROOT" -type d -exec chmod 0755 {} +
find "$PACKAGE_ROOT/usr/share/icons" -type f -exec chmod 0644 {} +

SIZE="$(du -sb "$PACKAGE_ROOT" | awk '{print $1}')"
BUILD_DATE="$(date -u +%s)"
cat > "$PACKAGE_ROOT/.PKGINFO" <<PKGINFO
pkgname = newchirp
pkgbase = newchirp
pkgver = ${VERSION}-1
pkgdesc = Desktop radio programmer for amateur and GMRS radios
url = https://newchirp.net/
builddate = $BUILD_DATE
packager = Rick Lopez <rick@newchirp.net>
size = $SIZE
arch = $PACMAN_ARCH
license = GPL-3.0-or-later
depend = glibc
depend = gtk3
depend = glib2
depend = gcc-libs
depend = libglvnd
depend = mesa
PKGINFO

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"
tar --sort=name --owner=0 --group=0 --numeric-owner \
  --zstd -C "$PACKAGE_ROOT" -cf "$OUTPUT" .PKGINFO opt usr

echo "Built $OUTPUT"
