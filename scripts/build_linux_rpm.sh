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
    RPM_ARCH="x86_64"
    ARCH_LABEL="x64"
    GL_REQUIRES="libEGL.so.1()(64bit), libGLESv2.so.2()(64bit)"
    ;;
  aarch64)
    RPM_ARCH="aarch64"
    ARCH_LABEL="arm64"
    GL_REQUIRES="libEGL.so.1()(64bit), libGLESv2.so.2()(64bit)"
    ;;
  *)
    echo "Unsupported host architecture: $(uname -m)" >&2
    exit 2
    ;;
esac

if ! command -v rpmbuild >/dev/null 2>&1; then
  echo "rpmbuild is required to build the RPM package." >&2
  exit 1
fi

if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$PROJECT_DIR/build/NewChirp-linux-$ARCH_LABEL-${VERSION}.rpm"
fi
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$PROJECT_DIR/$OUTPUT"
fi

TOPDIR="$PROJECT_DIR/build/linux-rpm"
SOURCES_DIR="$TOPDIR/SOURCES"
SPEC_DIR="$TOPDIR/SPECS"

rm -rf "$TOPDIR"
mkdir -p "$SOURCES_DIR/bundle" "$SOURCES_DIR/project" "$SPEC_DIR" "$TOPDIR/BUILD" "$TOPDIR/BUILDROOT" "$TOPDIR/RPMS" "$TOPDIR/SRPMS"

cp -a "$BUNDLE_DIR/." "$SOURCES_DIR/bundle/"
find "$SOURCES_DIR/bundle" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$SOURCES_DIR/bundle" -type f -name '*.pyc' -delete
mkdir -p "$SOURCES_DIR/project/macos/Runner/Assets.xcassets"
cp -a "$PROJECT_DIR/macos/Runner/Assets.xcassets/AppIcon.appiconset" \
  "$SOURCES_DIR/project/macos/Runner/Assets.xcassets/"

cat > "$SPEC_DIR/newchirp.spec" <<SPEC
Name:           newchirp
Version:        $VERSION
Release:        1%{?dist}
Summary:        Desktop radio programmer for amateur and GMRS radios
License:        GPL-3.0-or-later
URL:            https://newchirp.net/
BuildArch:      $RPM_ARCH
Requires:       glibc, gtk3, glib2, libstdc++, libgcc, $GL_REQUIRES

%description
NewChirp is a Flutter desktop channel editor that uses the CHIRP driver tree for radio hardware compatibility.

%prep

%build

%install
rm -rf %{buildroot}
mkdir -p \\
  %{buildroot}/opt/newchirp \\
  %{buildroot}/usr/bin \\
  %{buildroot}/usr/share/applications \\
  %{buildroot}/usr/share/doc/newchirp \\
  %{buildroot}/usr/share/icons/hicolor/16x16/apps \\
  %{buildroot}/usr/share/icons/hicolor/32x32/apps \\
  %{buildroot}/usr/share/icons/hicolor/64x64/apps \\
  %{buildroot}/usr/share/icons/hicolor/128x128/apps \\
  %{buildroot}/usr/share/icons/hicolor/256x256/apps \\
  %{buildroot}/usr/share/icons/hicolor/512x512/apps
cp -a %{_sourcedir}/bundle/. %{buildroot}/opt/newchirp/
find %{buildroot}/opt/newchirp -type d -name __pycache__ -prune -exec rm -rf {} +
find %{buildroot}/opt/newchirp -type f -name '*.pyc' -delete
ln -s /opt/newchirp/newchirp %{buildroot}/usr/bin/newchirp
for size in 16 32 64 128 256 512; do
  icon="%{_sourcedir}/project/macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_\${size}.png"
  if [ -f "\$icon" ]; then
    cp "\$icon" "%{buildroot}/usr/share/icons/hicolor/\${size}x\${size}/apps/newchirp.png"
  fi
done
cat > %{buildroot}/usr/share/applications/newchirp.desktop <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=NewChirp
Comment=Desktop radio programmer for amateur and GMRS radios
Exec=newchirp
Icon=newchirp
Categories=Utility;HamRadio;
Terminal=false
DESKTOP
cat > %{buildroot}/usr/share/doc/newchirp/copyright <<'COPYRIGHT'
NewChirp is distributed with the CHIRP driver tree and pyserial.
See /opt/newchirp/chirp-COPYING.txt and /opt/newchirp/data/flutter_assets/assets/licenses/
for bundled third-party license texts.
COPYRIGHT
chmod 0755 %{buildroot}/opt/newchirp/newchirp
chmod 0644 %{buildroot}/usr/share/applications/newchirp.desktop
find %{buildroot}/usr/share/icons -type f -exec chmod 0644 {} +

%files
/opt/newchirp
/usr/bin/newchirp
/usr/share/applications/newchirp.desktop
/usr/share/doc/newchirp/copyright
/usr/share/icons/hicolor/*/apps/newchirp.png
SPEC

rpmbuild --define "_topdir $TOPDIR" -bb "$SPEC_DIR/newchirp.spec"

mkdir -p "$(dirname "$OUTPUT")"
rpm_path="$(find "$TOPDIR/RPMS" -type f -name 'newchirp-*.rpm' | head -1)"
if [[ -z "$rpm_path" ]]; then
  echo "RPM build completed but no package was found." >&2
  exit 1
fi
rm -f "$OUTPUT"
cp "$rpm_path" "$OUTPUT"
echo "Built $OUTPUT"
