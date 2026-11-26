#!/usr/bin/env bash
# Clean cloud container (Ubuntu 24.04, no Docker): openEMS + FeedLab in /opt/openEMS/venv, ~5 min.
#   bash fdtd/setup_cloud.sh && /opt/openEMS/venv/bin/python fdtd/optimize.py --family w2imu --fD 0.6
set -euo pipefail
cd "$(dirname "$0")/.."
bash fdtd/install_openems.sh
/opt/openEMS/venv/bin/pip install -q --no-deps -e . && /opt/openEMS/venv/bin/pip install -q numpy scipy matplotlib
/opt/openEMS/venv/bin/python -c "import openEMS, feedlab; print('ready')"
