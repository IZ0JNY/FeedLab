# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Turn an openEMS optimum (fdtd/results/<family>_fD<fD>[_tag]_best.json, quotes in λ) into FeedLab project files
(.feedlab.json) for given bands and dishes: open them in FeedLab with «📂 Apri progetto» (drawings, STEP/STL, plate,
mounting, report), as for any other design.

    python fdtd/export_feedlab.py --family ve4ma --fD 0.4 --tag 3m --bands 10.368,24.048 --dishes 3000,3700

The feed is one of FeedLab's own types (VE4MA, Chaparral, Axial Corrugated…) with its dimensions as overrides, so
nothing new is needed in FeedLab to open it. Walls: FeedLab's default for the band (0.06 λ, ≥ 1 mm), ring walls
the same (CNC turning). Files go to fdtd/results/feedlab/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import optimize as op  # noqa: E402

from feedlab import geometry, project, wizard  # noqa: E402
from feedlab.waveguide import wavelength_mm  # noqa: E402

OUT = op.RESULTS / "feedlab"


def overrides(fam, x: list[float], f_ghz: float) -> tuple[str, dict]:
    """FeedLab feed kind and dimension overrides (mm) of a family point x (λ) at f_ghz."""
    lam = wavelength_mm(f_ghz)
    if isinstance(fam, op.ChokeFamily):
        kw = {k: v * lam for k, v in zip(fam.keys, x)}
        kw["ring_wall"] = geometry.wall_default(f_ghz)
        return fam.kind, kw
    if fam.name == "axial_corrugated":
        pitch, wf, axi, delta, Di, Ds, d1, dk = x
        return "axial_corrugated", {"pitch": pitch * lam, "w": wf * pitch * lam, "axi": axi * lam,
                                    "delta": delta * lam, "Di": Di * lam, "Ds": Ds * lam, "d1": d1 * lam,
                                    **{f"d{k}": dk * lam for k in range(2, 9)}}
    if fam.name == "w2imu":
        A, B, a, C = x
        return "w2imu", {"A": A * lam, "B": B * lam, "alpha": a, "C": C * lam}
    if fam.name == "dualflare":
        from feedlab import synth
        return "iz0jny", synth.df_params(x, lam)
    raise ValueError(f"export not available for {fam.name}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", required=True, choices=sorted(op.FAMILIES))
    ap.add_argument("--fD", type=float, required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--source", choices=["best", "confirm"], default="best")
    ap.add_argument("--bands", default="10.368,24.048", help="GHz, comma separated")
    ap.add_argument("--dishes", default="3000,3700", help="prime-focus dish Ø, mm, comma separated")
    ap.add_argument("--material", default="Alluminio 6082/6061 T6")
    ap.add_argument("--name", default="", help="file name prefix (default: family_fD)")
    a = ap.parse_args(argv)

    fam = op.FAMILIES[a.family]
    tag = f"{fam.name}_fD{a.fD:.2f}" + (f"_{a.tag}" if a.tag else "")
    best = json.loads((op.RESULTS / f"{tag}_best.json").read_text())
    x = [best["x"][k] for k in fam.keys]
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for f in map(float, a.bands.split(",")):
        kind, kw = overrides(fam, x, f)
        geo = geometry.build(kind, f, fD=a.fD, **kw)
        for D in map(float, a.dishes.split(",")):
            S = {"f_ghz": f, "dish": wizard.dish_from_prime(D, a.fD), "feed_kind": kind, "material": a.material,
                 "overrides": {kind: kw}, "wall": None, "fd_design": a.fD}
            p = project.build(S, geo, a.fD)
            p["openems_optimum"] = {"source": f"fdtd/results/{tag}_best.json", "family": fam.name, "x_lambda": best["x"],
                                    "eta_mean": best["eta_mean"], "s11_max_db": best["s11_max_db"],
                                    "f0_ghz_simulated": best["f0_ghz"], "cells_per_lambda": 16}
            name = f"{a.name or tag}_{f:g}GHz_{D / 1000:g}m.feedlab.json"
            (OUT / name).write_text(project.to_json(project._clean(p)), encoding="utf-8")
            r = p.get("results", {})
            print(f"{name}: G {r.get('gain_dbi', float('nan')):.2f} dBi, η {r.get('eta', float('nan')):.3f}, "
                  f"feed Ø {geo.blockage_diameter():.1f} mm, L {geo.length:.1f} mm")
            written.append(OUT / name)
    return written


if __name__ == "__main__":
    main()
