#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Builds FeedLab for Linux (x86_64), same idea as windows/build.ps1: its own Python + packages + app.
#
#   build/linux/root/opt/feedlab/              the program (python/, app/, bin/feedlab)
#   dist/feedlab_<ver>_amd64.deb               Debian/Ubuntu package (/opt/feedlab, /usr/bin/feedlab, menu entry)
#   dist/FeedLab-<ver>-x86_64.AppImage         one file, no installation: chmod +x and run it
#   dist/SHA256SUMS-linux.txt
#
# The interpreter is a relocatable python-build-standalone CPython (glibc >= 2.17), the one `uv python install`
# provides. Native window: pywebview with the system's GTK/WebKit2GTK (PyGObject built here); without them
# FeedLab opens in the browser.
#
# Requirements: uv, dpkg-deb, desktop-file-validate, curl (appimagetool, or set APPIMAGETOOL), a C compiler, pkg-config, libgirepository1.0-dev, libcairo2-dev (to build
# PyGObject), internet access.
# Usage:  linux/build.sh [--version 0.4.26] [--python /path/to/python-build-standalone/bin/python3.13] [--no-appimage]
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VERSION=""
PY=""
PYMINOR=3.13
APPIMAGE=1
APPIMAGETOOL_VERSION=1.9.0
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION=$2; shift 2 ;;
    --python) PY=$2; shift 2 ;;
    --no-appimage) APPIMAGE=0; shift ;;
    *) echo "opzione sconosciuta: $1" >&2; exit 2 ;;
  esac
done
[ -n "$VERSION" ] || VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/pyproject.toml" | head -1)
if [ -z "$PY" ]; then
  uv python install "$PYMINOR"
  PY=$(uv python find --managed-python "$PYMINOR")
fi
PY=$(readlink -f "$PY")
PYHOME=$(cd "$(dirname "$PY")/.." && pwd)
PYVER=$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "FeedLab $VERSION  -  Python $("$PY" -c 'import platform; print(platform.python_version())') da $PYHOME"

STAGE="$ROOT/build/linux/root"
DEST="$STAGE/opt/feedlab"
DIST="$ROOT/dist"
rm -rf "$ROOT/build/linux"
mkdir -p "$DEST/python/bin" "$DEST/python/lib" "$DIST"

# 1. Python: interpreter, libpython and the standard library (no tests, IDLE, tkinter, installed packages)
cp "$PYHOME/bin/python$PYVER" "$DEST/python/bin/"
ln -s "python$PYVER" "$DEST/python/bin/python3"
ln -s "python$PYVER" "$DEST/python/bin/python"
cp -a "$PYHOME"/lib/libpython3*.so* "$DEST/python/lib/" 2>/dev/null || true
( cd "$PYHOME/lib" && tar cf - --exclude="python$PYVER/site-packages" --exclude="python$PYVER/dist-packages" \
    --exclude="python$PYVER/test" --exclude="python$PYVER/idlelib" --exclude="python$PYVER/tkinter" \
    --exclude="python$PYVER/turtledemo" --exclude="python$PYVER/config-$PYVER*" --exclude=__pycache__ \
    "python$PYVER" ) | ( cd "$DEST/python/lib" && tar xf - )
SP="$DEST/python/lib/python$PYVER/site-packages"
mkdir -p "$SP"
BPY="$DEST/python/bin/python3"
export PYTHONNOUSERSITE=1

# 2. packages: the Windows program's ones (requirements-desktop.txt) plus PyGObject for the GTK window.
# PyGObject < 3.51 uses girepository-1.0, present on Debian 12 / Ubuntu 22.04 too.
uv pip install --python "$BPY" --target "$SP" -r "$ROOT/requirements-desktop.txt" \
  "pygobject>=3.48,<3.51" pycairo pip
rm -rf "$SP/bin"

# 3. the app (the manual's sources and the web site stay in the repository, as on Windows)
mkdir -p "$DEST/app"
cp -r "$ROOT/feedlab" "$ROOT/.streamlit" "$ROOT/docs" "$DEST/app/"
rm -rf "$DEST/app/docs/manual/img" "$DEST/app/docs/manual/tools" "$DEST/app/docs/web"
cp "$ROOT/feedlab_main.py" "$ROOT/README.md" "$ROOT/LICENSE" "$DEST/app/"
cp "$ROOT/LICENSE" "$DEST/"
echo "../../../../app" > "$SP/feedlab-app.pth"           # relative: the portable folder works anywhere

# 4. launcher, menu entry, icons
mkdir -p "$DEST/bin"
cat > "$DEST/bin/feedlab" <<'EOF'
#!/bin/sh
# FeedLab (Linux). Options: --browser (default browser instead of the window), --server-only --port N, --selftest
HERE=$(dirname "$(readlink -f "$0")")
export PYTHONNOUSERSITE=1
unset PYTHONHOME PYTHONPATH
exec "$HERE/../python/bin/python3" -m feedlab.desktop "$@"
EOF
chmod 755 "$DEST/bin/feedlab"
mkdir -p "$STAGE/usr/bin" "$STAGE/usr/share/applications" "$STAGE/usr/share/doc/feedlab"
ln -s /opt/feedlab/bin/feedlab "$STAGE/usr/bin/feedlab"
cp "$ROOT/linux/feedlab.desktop" "$STAGE/usr/share/applications/"
cp "$ROOT/LICENSE" "$STAGE/usr/share/doc/feedlab/copyright"
"$BPY" - "$ROOT/windows/feedlab.ico" "$STAGE/usr/share/icons/hicolor" "$DEST/feedlab.png" <<'EOF'
import sys
from pathlib import Path
from PIL import Image
ico = Image.open(sys.argv[1])
ico.size = max(ico.info.get("sizes", [ico.size]))
big = ico.convert("RGBA")
for s in (256, 128, 64, 48, 32, 16):
    p = Path(sys.argv[2]) / f"{s}x{s}" / "apps" / "feedlab.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    big.resize((s, s), Image.LANCZOS).save(p)
big.resize((256, 256), Image.LANCZOS).save(sys.argv[3])
EOF

# 5. precompile (paths as installed in /opt/feedlab) and self-test with the bundled interpreter
"$BPY" -m compileall -q -j 0 -s "$STAGE" -p / "$DEST/app" "$DEST/python/lib/python$PYVER" > /dev/null
( cd / && HOME=$(mktemp -d) "$DEST/bin/feedlab" --selftest )

# 6. Debian package
mkdir -p "$STAGE/DEBIAN"
SIZE=$(du -sk --exclude=DEBIAN "$STAGE" | cut -f1)
sed -e "s/@VERSION@/$VERSION/" -e "s/@SIZE@/$SIZE/" "$ROOT/linux/control.in" > "$STAGE/DEBIAN/control"
find "$STAGE" -type d -exec chmod 755 {} +
chmod -R go-w "$STAGE"
DEB="$DIST/feedlab_${VERSION}_amd64.deb"
rm -f "$DEB"
dpkg-deb --root-owner-group -Zxz -z6 --build "$STAGE" "$DEB"

# 7. AppImage: the same folder in one self-mounting file (no installation, no root)
FILES=("$(basename "$DEB")")
if [ "$APPIMAGE" = 1 ]; then
  TOOL=${APPIMAGETOOL:-}
  if [ -z "$TOOL" ]; then
    TOOL="$ROOT/build/linux/appimagetool"
    curl -fsSL -o "$TOOL" \
      "https://github.com/AppImage/appimagetool/releases/download/$APPIMAGETOOL_VERSION/appimagetool-x86_64.AppImage"
    chmod +x "$TOOL"
  fi
  APPDIR="$ROOT/build/linux/FeedLab.AppDir"
  cp -a "$DEST" "$APPDIR"
  printf '%s\n' '#!/bin/sh' 'HERE=$(dirname "$(readlink -f "$0")")' 'exec "$HERE/bin/feedlab" "$@"' > "$APPDIR/AppRun"
  chmod 755 "$APPDIR/AppRun"
  cp "$ROOT/linux/feedlab.desktop" "$APPDIR/feedlab.desktop"
  ln -s feedlab.png "$APPDIR/.DirIcon"
  NAME="FeedLab-$VERSION-x86_64.AppImage"
  # APPIMAGE_EXTRACT_AND_RUN: appimagetool itself runs without FUSE (containers, CI)
  ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" --no-appstream "$APPDIR" "$DIST/$NAME"
  FILES+=("$NAME")
fi

# 8. SHA-256 checksums (users check the download with: sha256sum -c SHA256SUMS.txt)
( cd "$DIST" && sha256sum "${FILES[@]}" > SHA256SUMS-linux.txt )
ls -la "$DIST"
