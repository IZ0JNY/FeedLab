#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Installs openEMS (FDTD) + Python bindings from source, reproducibly, on Debian/Ubuntu.
# Used by fdtd/Dockerfile and directly in a clean cloud container:
#     sudo bash fdtd/install_openems.sh     # -> /opt/openEMS, Python venv in /opt/openEMS/venv
# Variables: OPENEMS_TAG (default v0.37.0), OPENEMS_PREFIX (/opt/openEMS), PYTHON (python3), JOBS (nproc)
set -euo pipefail
OPENEMS_TAG="${OPENEMS_TAG:-v0.37.0}"
PREFIX="${OPENEMS_PREFIX:-/opt/openEMS}"
VENV="${OPENEMS_VENV:-$PREFIX/venv}"   # dedicated venv (ignored if PYTHON is given)
PYTHON="${PYTHON:-$VENV/bin/python}"
JOBS="${JOBS:-$(nproc)}"
SRC="${OPENEMS_SRC:-/opt/src/openEMS-Project}"

if [ -x "$PREFIX/bin/openEMS" ] && "$PYTHON" -c "import openEMS, CSXCAD" 2>/dev/null; then
  echo "openEMS already installed in $PREFIX"; exit 0
fi

export DEBIAN_FRONTEND=noninteractive
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq --no-install-recommends build-essential git cmake ca-certificates \
  libhdf5-dev libtinyxml-dev libboost-all-dev libcgal-dev libvtk9-dev >/dev/null

if [ ! -d "$SRC/.git" ]; then
  $SUDO mkdir -p "$(dirname "$SRC")"; $SUDO chown "$(id -u)" "$(dirname "$SRC")"
  git clone --recursive --depth 1 --branch "$OPENEMS_TAG" https://github.com/thliebig/openEMS-Project.git "$SRC"
fi

mkdir -p "$SRC/build" && cd "$SRC/build"
cmake .. -DCMAKE_INSTALL_PREFIX="$PREFIX" -DBUILD_APPCSXCAD=NO -DCMAKE_BUILD_TYPE=Release >/dev/null
$SUDO make -j"$JOBS"

# Python bindings into the chosen interpreter (CSXCAD first, openEMS needs it)
if [ ! -x "$PYTHON" ] && [ "$PYTHON" = "$VENV/bin/python" ]; then
  $SUDO python3 -m venv "$VENV" && $SUDO chown -R "$(id -u)" "$VENV"
fi
"$PYTHON" -m pip install -q --upgrade pip
"$PYTHON" -m pip install -q "numpy" "h5py" "cython>=3" "setuptools" "setuptools-scm" "wheel" "scipy" "matplotlib"
export CSXCAD_INSTALL_PATH="$PREFIX" OPENEMS_INSTALL_PATH="$PREFIX"
for pkg in CSXCAD openEMS; do
  (cd "$SRC/$pkg/python" && "$PYTHON" -m pip install -q --no-build-isolation .)
done
echo "$PREFIX/lib" | $SUDO tee /etc/ld.so.conf.d/openems.conf >/dev/null && $SUDO ldconfig
"$PYTHON" -c "import openEMS, CSXCAD; print('openEMS bindings OK:', openEMS.__file__)"
