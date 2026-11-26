# SPDX-License-Identifier: GPL-3.0-or-later
# openEMS + FeedLab container for iterative full-wave feed optimisation.
#   docker build -t feedlab-fdtd -f fdtd/Dockerfile .
#   docker run --rm -v "$PWD/fdtd/runs:/work/fdtd/runs" -v "$PWD/fdtd/results:/work/fdtd/results" \
#       feedlab-fdtd python fdtd/optimize.py --family w2imu --fD 0.6 --budget 60
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends python3 python3-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*
COPY fdtd/install_openems.sh /tmp/install_openems.sh
RUN bash /tmp/install_openems.sh && rm -rf /opt/src/openEMS-Project/build /var/lib/apt/lists/*
ENV PATH=/opt/openEMS/venv/bin:/opt/openEMS/bin:$PATH OPENEMS_INSTALL_PATH=/opt/openEMS \
    OPENEMS_PYTHON=/opt/openEMS/venv/bin/python
WORKDIR /work
COPY pyproject.toml README.md ./
COPY feedlab ./feedlab
COPY fdtd ./fdtd
# only what the optimiser needs (the GUI/CAD dependencies are not installed)
RUN pip install -q --no-deps -e . && pip install -q numpy scipy matplotlib
CMD ["python", "fdtd/optimize.py", "--help"]
