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
from feedlab.waveguide import RECT_WG, suggest_rect_wg, wavelength_mm  # noqa: E402

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
    if fam.name in ("w2imu", "large_w2imu"):
        A, B, a, C = x
        return fam.name, {"A": A * lam, "B": B * lam, "alpha": a, "C": C * lam}
    if isinstance(fam, op.DualFlare):
        from feedlab import synth
        return "iz0jny", synth.df_params(x, lam)
    raise ValueError(f"export not available for {fam.name}")


def openems_results(family: str, fD: float, f_ghz: float, S: dict, geo) -> dict | None:
    """Dish results (same formulas and fields as FeedLab's project file) from the confirmed openEMS far field in
    fdtd/results/openems_fD<fD>/<family>/ (simulated at 10.368 GHz; quotes in λ, so the pattern holds at f_ghz)."""
    import numpy as np
    from feedlab import deep_analysis, explore
    path = op.RESULTS / f"openems_fD{fD:.2f}" / family / "results.json"
    if not path.exists():
        return None
    r = deep_analysis.load(path)
    lam0 = wavelength_mm(r.f0)
    pat = r.ff_at(r.f0).pattern()
    pc = deep_analysis.phase_center(pat, fD, lam0)["d_mm"] / lam0          # λ, from the aperture
    d = S["dish"]
    sc_d = project.default_scenario(f_ghz)
    sc = explore.Scenario(d.kind, d.D_mm, d.fD, sc_d["elev_deg"], __import__("feedlab").noise.receiver_temp(sc_d["nf_db"]),
                          sc_d["zenith_db"], 290.0, sc_d["rms_mm"], sc_d["line_loss_db"], material=S["material"])
    res = explore.performance(geo.kind, f_ghz, sc, geo, pat.shifted(pc), None)
    g = np.interp(r.f0, np.asarray(r.freq_ghz), np.abs(np.asarray(r.s11)))
    lam = wavelength_mm(f_ghz)
    return {"source": f"openEMS {path.parent.relative_to(op.RESULTS.parent.parent)} (24 celle/λ, {r.f0:g} GHz)",
            "gain_dbi": res.gain_dbi, "g_over_t": res.g_over_t, "eta": res.eta, "spill": res.spill, "illum": res.illum,
            "phase": res.phase, "pol": res.pol, "block": res.block, "edge_taper_db": res.edge_taper_db,
            "t_ant_K": res.t_ant, "s11_db": 20 * np.log10(g + 1e-12), "phase_center_mm": pc * lam + res.pc_mm,
            "ohmic_db": res.ohmic_db, "tsys": res.tsys,
            "pattern": {"theta_deg": res.pattern.theta_deg[::2],
                        "E_db": 20 * np.log10(np.abs(res.pattern.E[::2]) / np.max(np.abs(res.pattern.E)) + 1e-12),
                        "H_db": 20 * np.log10(np.abs(res.pattern.H[::2]) / np.max(np.abs(res.pattern.H)) + 1e-12)}}


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
    ap.add_argument("--wr", default="", help="WR guide for the λ/4 plate (default: first of the band; none = no plate)")
    ap.add_argument("--pol", default="V", choices=["V", "H"])
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
            # λ/4 plate circular feed guide → WR (tab «Piastrina WR»), already filled in: first standard WR of the
            # band, polarisation V, mill radius as FeedLab's default, optimised version
            wgs = suggest_rect_wg(f)
            if wgs and a.wr != "none":
                wg = a.wr or wgs[0]
                S["wr_wg"] = wg
                S["plate_rf"] = (a.pol, float(round(2 * geo.r_input, 3)), float(round(min(2.0, 0.08 * RECT_WG[wg].a_mm), 2)), True)
            p = project.build(S, geo, a.fD)
            p["openems_optimum"] = {"source": f"fdtd/results/{tag}_best.json", "family": fam.name, "x_lambda": best["x"],
                                    "eta_mean": best["eta_mean"], "s11_max_db": best["s11_max_db"],
                                    "f0_ghz_simulated": best["f0_ghz"], "cells_per_lambda": 16}
            cf = op.RESULTS / f"{tag}_confirm.json"
            if cf.exists():
                c = json.loads(cf.read_text())["best"]
                p["openems_optimum"]["confirm_24cpl"] = {"eta_mean": c["eta_mean"], "eta_f0": c["eta_f0"],
                                                         "s11_max_db": c["s11_max_db"], "per_freq": c["per_freq"]}
            name = f"{a.name or tag}_{f:g}GHz_{D / 1000:g}m.feedlab.json"
            ow = openems_results(fam.name, a.fD, f, S, geo)
            if ow:                  # FeedLab's fast solver ignores chokes/slots: dish results from the openEMS pattern
                p["results_fast_solver"] = p.get("results")
                p["results"] = ow
            (OUT / name).write_text(project.to_json(project._clean(p)), encoding="utf-8")
            r = p.get("results", {})
            print(f"{name}: G {r.get('gain_dbi', float('nan')):.2f} dBi, η {r.get('eta', float('nan')):.3f}, "
                  f"feed Ø {geo.blockage_diameter():.1f} mm, L {geo.length:.1f} mm")
            written.append(OUT / name)
    return written


if __name__ == "__main__":
    main()
