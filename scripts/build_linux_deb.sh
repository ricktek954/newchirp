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

VERSION_LINE="$(sed -n 's/^version:[[:space:]]*\([^+[:space:]]*\).*/\1/p' "$PROJECT_DIR/pubspec.yaml" | head -1)"
if [[ -z "$VERSION_LINE" ]]; then
  echo "Could not read version from pubspec.yaml." >&2
  exit 1
fi
VERSION="${VERSION_LINE}-1"

case "$(uname -m)" in
  x86_64)
    DEB_ARCH="amd64"
    ARCH_LABEL="x64"
    ;;
  aarch64)
    DEB_ARCH="arm64"
    ARCH_LABEL="arm64"
    ;;
  *)
    echo "Unsupported host architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$PROJECT_DIR/build/NewChirp-linux-$ARCH_LABEL-${VERSION_LINE}.deb"
fi
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PROJECT_DIR/$OUTPUT"
fi

PACKAGE_ROOT="$PROJECT_DIR/build/linux-deb/newchirp_${VERSION}_${DEB_ARCH}"
WORK_DIR="$PROJECT_DIR/build/linux-deb/work"

rm -rf "$PACKAGE_ROOT" "$WORK_DIR"
mkdir -p \
  "$PACKAGE_ROOT/DEBIAN" \
  "$PACKAGE_ROOT/opt/newchirp" \
  "$PACKAGE_ROOT/usr/bin" \
  "$PACKAGE_ROOT/usr/share/applications" \
  "$PACKAGE_ROOT/usr/share/doc/newchirp" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/16x16/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/32x32/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/64x64/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/128x128/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/256x256/apps" \
  "$PACKAGE_ROOT/usr/share/icons/hicolor/512x512/apps" \
  "$WORK_DIR"

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
find "$PACKAGE_ROOT/usr/share/icons" -type f -exec chmod 0644 {} +

INSTALLED_SIZE="$(du -sk "$PACKAGE_ROOT" | awk '{print $1}')"
cat > "$PACKAGE_ROOT/DEBIAN/control" <<CONTROL
Package: newchirp
Version: $VERSION
Section: hamradio
Priority: optional
Architecture: $DEB_ARCH
Maintainer: Rick Lopez <rick@newchirp.net>
Depends: libc6, libgtk-3-0, libglib2.0-0, libstdc++6, libgcc-s1, libegl1, libgles2
Installed-Size: $INSTALLED_SIZE
Homepage: https://newchirp.net/
Description: Desktop radio programmer for amateur and GMRS radios
 NewChirp is a Flutter desktop channel editor that uses the CHIRP
 driver tree for radio hardware compatibility.
CONTROL

printf '2.0\n' > "$WORK_DIR/debian-binary"
tar --sort=name --owner=0 --group=0 --numeric-owner \
  -C "$PACKAGE_ROOT/DEBIAN" -czf "$WORK_DIR/control.tar.gz" .
tar --sort=name --owner=0 --group=0 --numeric-owner \
  --exclude=./DEBIAN -C "$PACKAGE_ROOT" -czf "$WORK_DIR/data.tar.gz" .

mkdir -p "$(dirname "$OUTPUT")"
rm -f "$OUTPUT"
(cd "$WORK_DIR" && ar rcs "$OUTPUT" debian-binary control.tar.gz data.tar.gz)

echo "Built $OUTPUT"
