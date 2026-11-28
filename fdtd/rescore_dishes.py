# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Efficiency of the confirmed designs on several prime-focus dishes and bands, from the cached openEMS runs
(no new simulation: quotes in λ, only the blocking ratio feed Ø / dish Ø changes).

    python fdtd/rescore_dishes.py --fD 0.4 --tag 3m --families axial_corrugated,chaparral,ve4ma \
        --dishes 3000,3700 --bands 10.368,24.048
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fdtd_eval as fe  # noqa: E402
import optimize as op  # noqa: E402

from feedlab.waveguide import wavelength_mm  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fD", type=float, default=0.4)
    ap.add_argument("--tag", default="3m")
    ap.add_argument("--families", default="axial_corrugated,chaparral,ve4ma")
    ap.add_argument("--dishes", default="3000,3700")
    ap.add_argument("--bands", default="10.368,24.048")
    ap.add_argument("--f0", type=float, default=10.368)
    ap.add_argument("--cpl", type=int, default=24)
    a = ap.parse_args(argv)
    out = {}
    for name in a.families.split(","):
        fam = op.FAMILIES[name]
        tag = f"{fam.name}_fD{a.fD:.2f}" + (f"_{a.tag}" if a.tag else "")
        conf = json.loads((op.RESULTS / f"{tag}_confirm.json").read_text())
        for case in ("best", "seed0"):
            x = [conf[case]["x"][k] for k in fam.keys]
            geo = fam.build(x, a.f0, a.fD)
            for f in map(float, a.bands.split(",")):
                for D in map(float, a.dishes.split(",")):
                    cfg = fe.EvalConfig(fD=a.fD, cells_per_lambda=a.cpl, dish_diam_lambda=D / wavelength_mm(f))
                    r = fe.evaluate(geo, cfg, label=f"{name} {case}")
                    key = f"{name}|{case}|{f:g}|{D / 1000:g}"
                    out[key] = {"eta_mean": r["eta_mean"], "eta_f0": r["eta_f0"], "s11_max_db": r["s11_max_db"],
                                "block": r["per_freq"][1]["block"], "feed_diam_mm": r["block_diam_lambda"] * wavelength_mm(f)}
                    print(f"{key:40s} η {r['eta_mean']:.4f}  blocking {r['per_freq'][1]['block']:.4f}  "
                          f"feed Ø {out[key]['feed_diam_mm']:.0f} mm", flush=True)
    (op.RESULTS / f"dishes_fD{a.fD:.2f}.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    main()
