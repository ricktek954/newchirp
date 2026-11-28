#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="$(sed -n 's/^version:[[:space:]]*\([^+[:space:]]*\).*/\1/p' \
  "$PROJECT_DIR/pubspec.yaml" | head -1)"
if [[ -z "$VERSION" ]]; then
  echo "Could not read version from pubspec.yaml." >&2
  exit 1
fi

APPIMAGETOOL="${APPIMAGETOOL:-/tmp/newchirp-release-tools/appimagetool-x86_64.AppImage}"
if [[ ! -x "$APPIMAGETOOL" ]]; then
  mkdir -p "$(dirname "$APPIMAGETOOL")"
  curl -fL --retry 3 \
    https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
    -o "$APPIMAGETOOL"
  chmod 0755 "$APPIMAGETOOL"
fi

python3 "$SCRIPT_DIR/check_linux_release_abi.py" "$PROJECT_DIR/pubspec.yaml" \
  >/dev/null

flutter config --enable-linux-desktop
flutter pub get
CHIRP_ROOT="$(bash "$SCRIPT_DIR/update_chirp.sh")"
flutter analyze lib test
flutter test test/update_checker_test.dart
flutter build linux --release

BUNDLE="$PROJECT_DIR/build/linux/x64/release/bundle"
bash "$SCRIPT_DIR/bundle_linux_runtime.sh" \
  --bundle-dir "$BUNDLE" \
  --chirp-source "$CHIRP_ROOT"

BUNDLED_PYTHON="$BUNDLE/python/bin/python3"
SERIAL_WHEEL="$BUNDLE/data/flutter_assets/assets/python/pyserial-3.5-py2.py3-none-any.whl"
PYTHONPATH="$SERIAL_WHEEL${PYTHONPATH:+:$PYTHONPATH}" \
  "$BUNDLED_PYTHON" -m unittest discover \
    -s "$PROJECT_DIR/test" \
    -p '*_test.py'

"$BUNDLED_PYTHON" -I -B "$SCRIPT_DIR/check_bundle_drivers.py" \
  --resources "$BUNDLE" \
  --bridge "$BUNDLE/data/flutter_assets/scripts/chirp_bridge.py" \
  --vendor "$SERIAL_WHEEL" \
  --expect-drivers "$PROJECT_DIR/drivers"

bash "$SCRIPT_DIR/build_linux_deb.sh" \
  --bundle-dir "$BUNDLE" \
  --output "$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.deb"
bash "$SCRIPT_DIR/build_linux_rpm.sh" \
  --bundle-dir "$BUNDLE" \
  --output "$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.rpm"
APPIMAGE_EXTRACT_AND_RUN=1 \
  bash "$SCRIPT_DIR/build_linux_appimage.sh" \
    --bundle-dir "$BUNDLE" \
    --appimagetool "$APPIMAGETOOL" \
    --output "$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.AppImage"
bash "$SCRIPT_DIR/build_linux_pacman.sh" \
  --bundle-dir "$BUNDLE" \
  --output "$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.pkg.tar.zst"

DEB="$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.deb"
RPM="$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.rpm"
APPIMAGE="$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.AppImage"
PACMAN="$PROJECT_DIR/build/NewChirp-linux-x64-${VERSION}.pkg.tar.zst"

dpkg-deb --field "$DEB" Version | grep -Fx "${VERSION}-1"
dpkg-deb --field "$DEB" Depends | grep -E 'libegl1.*libgles2|libgles2.*libegl1'
rpm -qp --requires "$RPM" | grep -Fx 'libEGL.so.1()(64bit)'
rpm -qp --requires "$RPM" | grep -Fx 'libGLESv2.so.2()(64bit)'
tar -xOf "$PACMAN" .PKGINFO | grep -Fx "pkgver = ${VERSION}-1"
tar -xOf "$PACMAN" .PKGINFO | grep -Fx 'depend = libglvnd'
tar -xOf "$PACMAN" .PKGINFO | grep -Fx 'depend = mesa'

SMOKE_ROOT="$(mktemp -d)"
cleanup() {
  rm -rf "$SMOKE_ROOT"
}
trap cleanup EXIT

dpkg-deb -x "$DEB" "$SMOKE_ROOT/deb"
set +e
timeout 10s xvfb-run -a -s '-screen 0 1280x800x24' \
  "$SMOKE_ROOT/deb/opt/newchirp/newchirp" >"$SMOKE_ROOT/deb.log" 2>&1
DEB_STATUS=$?
APPIMAGE_EXTRACT_AND_RUN=1 \
  timeout 10s xvfb-run -a -s '-screen 0 1280x800x24' \
    "$APPIMAGE" >"$SMOKE_ROOT/appimage.log" 2>&1
APPIMAGE_STATUS=$?
set -e

cat "$SMOKE_ROOT/deb.log"
cat "$SMOKE_ROOT/appimage.log"
if [[ "$DEB_STATUS" -ne 124 ]]; then
  echo "DEB launch smoke test failed with exit $DEB_STATUS." >&2
  exit 1
fi
if [[ "$APPIMAGE_STATUS" -ne 124 ]]; then
  echo "AppImage launch smoke test failed with exit $APPIMAGE_STATUS." >&2
  exit 1
fi

sha256sum "$DEB" "$RPM" "$APPIMAGE" "$PACMAN"
