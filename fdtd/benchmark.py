# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Published feeds simulated with openEMS under the same rules as the optimiser (reference table).

    python fdtd/benchmark.py --fD 0.6 [--cpl 16] [--feeds w2imu,iz0jny,skobelev,axial_corrugated]

Writes fdtd/results/benchmark_fD<fD>_<cpl>cpl.json and prints a table (η = illuminator efficiency with the
phase centre fixed at f0, × (1 − |S11|²), at f0 and averaged over f0·(1 ± band)).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fdtd_eval as fe  # noqa: E402

from feedlab import geometry  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
DEFAULT = ["w2imu", "iz0jny", "skobelev", "w2imu_oe2igl", "axial_corrugated", "pickett_potter"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fD", type=float, default=0.6)
    ap.add_argument("--f0", type=float, default=10.368)
    ap.add_argument("--cpl", type=int, default=16)
    ap.add_argument("--band", type=float, default=0.02)
    ap.add_argument("--feeds", default=",".join(DEFAULT))
    ap.add_argument("--dish-lambda", type=float, default=0.0, help="prime focus: dish Ø in λ (adds blocking)")
    ap.add_argument("--tag", default="")
    a = ap.parse_args(argv)
    cfg = fe.EvalConfig(fD=a.fD, band=a.band, cells_per_lambda=a.cpl, dish_diam_lambda=a.dish_lambda)
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / (f"benchmark_fD{a.fD:.2f}_{a.cpl}cpl" + (f"_{a.tag}" if a.tag else "") + ".json")
    rows = json.loads(out.read_text()) if out.exists() else {}
    for kind in a.feeds.split(","):
        try:
            geo = geometry.build(kind, a.f0, fD=a.fD)
            rows[kind] = fe.evaluate(geo, cfg, label=kind)
        except Exception as e:
            print(f"{kind}: {e}", flush=True)
            continue
        out.write_text(json.dumps(rows, indent=1, default=float))
        r = rows[kind]
        print(f"{kind:18s} η f0 {r['eta_f0']:.4f}  η mean {r['eta_mean']:.4f}  S11max {r['s11_max_db']:6.1f} dB  "
              f"L {r['length_lambda']:.2f} λ", flush=True)
    return rows


if __name__ == "__main__":
    main()
