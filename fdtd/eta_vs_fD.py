# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Efficiency against f/D for every optimised feed, from its openEMS far field at 24 cells/λ (one simulation per
feed, cached in fdtd/runs/): for each f/D the feed is placed at its best phase centre for that f/D, the dish
efficiency (spillover × taper × phase × cross-pol × blocking) is multiplied by (1 − |S11|²) at f0. One chart tells
which feed to pick for a given f/D and dish size.

    python fdtd/eta_vs_fD.py --f 10.368            # prime-focus dishes 1.0-3.7 m at 10 GHz (feed blocking)
    python fdtd/eta_vs_fD.py --f 24.048 --offset   # at 24 GHz, plus an offset (no blocking) panel

Writes fdtd/results/eta_vs_fD_<band>GHz.json and .png (one panel per dish Ø).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fdtd_eval as fe  # noqa: E402
import optimize as op  # noqa: E402

from feedlab import deep_analysis, efficiency  # noqa: E402
from feedlab.waveguide import wavelength_mm  # noqa: E402

# (label, family, result tag, design f/D)
FEEDS = [
    ("Axial Corrugated ott. f/D 0.4", "axial_corrugated", "fD0.40_3m", 0.4),
    ("Chaparral ott. f/D 0.4", "chaparral", "fD0.40_3m", 0.4),
    ("VE4MA ott. f/D 0.4", "ve4ma", "fD0.40_3m", 0.4),
    ("W2IMU large flare ott. f/D 0.4", "large_w2imu", "fD0.40_3m", 0.4),
    ("W2IMU large flare 30° ott. f/D 0.4", "large_w2imu_30", "fD0.40_3m", 0.4),
    ("Axial Corrugated ott. f/D 0.6", "axial_corrugated", "fD0.60", 0.6),
    ("W2IMU ott. f/D 0.6", "w2imu", "fD0.60", 0.6),
    ("Dual-Flare ott. f/D 0.6", "dualflare", "fD0.60", 0.6),
    ("Profilo liscio ott. f/D 0.6", "profile", "fD0.60", 0.6),
    ("Dual-Flare ott. f/D 0.4", "dualflare_wide", "fD0.40_3m", 0.4),
]
# published designs, as FeedLab builds them for their design f/D: (label, FeedLab kind, design f/D)
PUBLISHED = [
    ("Super-VE4MA (W1GHZ/WD5AGO)", "ve4ma", 0.4),
    ("Chaparral 3 anelli (W1GHZ/WD5AGO)", "chaparral", 0.4),
    ("Axial Corrugated OE2IGL f/D 0.4", "axial_corrugated", 0.4),
    ("Axial Corrugated OE2IGL f/D 0.6", "axial_corrugated", 0.6),
    ("Guida circolare aperta", "open_circular", 0.4),
    ("W2IMU OE2IGL f/D 0.6", "w2imu_oe2igl", 0.6),
    ("Large W2IMU 30° (W1GHZ/W1FKF)", "large_w2imu", 0.8),    # B 1.78 λ: BW-10 ±35°, a feed for f/D ≈ 0.8
    ("W2IMU (W1GHZ, B = 2.35 f/D) f/D 0.6", "w2imu", 0.6),
    ("Skobelev (W1GHZ)", "skobelev", 0.6),
    ("Pickett-Potter (OE2IGL)", "pickett_potter", 0.6),
    ("Dual-Flare IZ0JNY (tabella)", "iz0jny", 0.6),
]
FDS = np.round(np.arange(0.30, 0.9001, 0.025), 3)


DISHES_M = [1.0, 1.5, 2.0, 2.5, 3.0, 3.7]           # prime-focus Ø at --f (blocking scales with Ø/λ)


def far_field(geo, cpl: int):
    d = fe.run_openems(geo, fe.EvalConfig(fD=0.6, cells_per_lambda=cpl), label=f"{geo.kind} eta_vs_fD")
    return geo, deep_analysis.load(d / "results.json")


def curve(geo, r, fDs, dish_lambda: float):
    lam0 = wavelength_mm(r.f0)
    pat = r.ff_at(r.f0).pattern()
    g = float(np.interp(r.f0, np.asarray(r.freq_ghz), np.abs(np.asarray(r.s11))))
    blk = geo.blockage_diameter() / (dish_lambda * lam0) if dish_lambda > 0 else 0.0
    out = []
    for fD in fDs:
        pc = deep_analysis.phase_center(pat, float(fD), lam0, blk)["d_lambda"]
        out.append(efficiency.dish_efficiency(pat.shifted(pc), float(fD), blk).total * (1 - g * g))
    return out, 20 * np.log10(g + 1e-12), geo.blockage_diameter() / lam0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--f", type=float, default=10.368, help="band of the dish diameters in the panels, GHz")
    ap.add_argument("--dishes", default=",".join(map(str, DISHES_M)), help="prime-focus Ø, m")
    ap.add_argument("--f0", type=float, default=10.368)
    ap.add_argument("--cpl", type=int, default=24)
    ap.add_argument("--offset", action="store_true", help="add an offset (no blocking) panel")
    ap.add_argument("--lang", choices=["it", "en"], default="it", help="chart language (en: files *_EN.png)")
    ap.add_argument("--replot", action="store_true", help="only redraw from the saved json (no openEMS, no phase centres)")
    ap.add_argument("--set", choices=["all", "opt", "pub"], default="all",
                    help="optimised feeds, published designs or both")
    a = ap.parse_args(argv)
    global LANG
    LANG = a.lang
    sfx = "_EN" if a.lang == "en" else ""
    if a.replot:
        out = f"eta_vs_fD_{a.f:g}GHz" + {"pub": "_pubblicati", "opt": "_ottimizzati"}.get(a.set, "")
        d = json.loads((op.RESULTS / f"{out}.json").read_text())
        plot(d["feeds"], d["meta"], op.RESULTS / f"{out}{sfx}.png")
        return d["feeds"]
    lam = wavelength_mm(a.f)
    cases = ([("offset", 0.0)] if a.offset else []) + [(f"{float(D):g}", float(D) * 1000 / lam) for D in a.dishes.split(",")]
    rows = {}
    from feedlab import geometry
    todo = []
    if a.set in ("all", "opt"):
        for label, name, tag, fd in FEEDS:
            bf = op.RESULTS / f"{name}_{tag}_best.json"
            if not bf.exists():
                print(f"{label}: no result, skipped", flush=True)
                continue
            fam = op.FAMILIES[name]
            best = json.loads(bf.read_text())
            todo.append((label, name, fd, True, lambda fam=fam, best=best: fam.build([best["x"][k] for k in fam.keys], a.f0, 0.6)))
    if a.set in ("all", "pub"):
        for label, kind, fd in PUBLISHED:
            todo.append((label, kind, fd, False, lambda kind=kind, fd=fd: geometry.build(kind, a.f0, fD=fd)))
    for label, name, fd, optimised, mk in todo:
        try:
            geo, r = far_field(mk(), a.cpl)
        except Exception as e:
            print(f"{label}: {e}", flush=True)
            continue
        row = {"family": name, "optimised": optimised, "design_fD": fd, "fD": FDS.tolist(), "eta": {}}
        for cname, dl in cases:
            row["eta"][cname], row["s11_f0_db"], row["outer_diam_lambda"] = curve(geo, r, FDS, dl)
        rows[label] = row
        print(f"{label}: " + ", ".join(f"{c} {max(v):.3f}@{FDS[int(np.argmax(v))]:.2f}" for c, v in row["eta"].items()),
              flush=True)
    meta = {"note": "openEMS 24 celle/λ a f0, centro di fase ottimo per ogni f/D, × (1−|S11|²) a f0; primo fuoco: "
                    "blocking del Ø esterno del feed, sostegni esclusi", "dish_band_ghz": a.f, "f0_ghz": a.f0,
            "dish_lambda": {c: dl for c, dl in cases}}
    meta["set"] = a.set
    out = f"eta_vs_fD_{a.f:g}GHz" + ({"pub": "_pubblicati", "opt": "_ottimizzati"}.get(a.set, ""))
    (op.RESULTS / f"{out}.json").write_text(json.dumps({"meta": meta, "feeds": rows}, indent=1))
    plot(rows, meta, op.RESULTS / f"{out}{sfx}.png")
    return rows


COLORS = {"axial_corrugated": "#1f77b4", "chaparral": "#2ca02c", "ve4ma": "#9467bd", "large_w2imu": "#d62728",
          "large_w2imu_30": "#ff7f0e", "w2imu": "#8c564b", "dualflare": "#e377c2", "profile": "#17becf",
          "dualflare_wide": "#bcbd22", "iz0jny": "#e377c2", "open_circular": "#555555", "w2imu_oe2igl": "#8c564b",
          "skobelev": "#17becf", "pickett_potter": "#bcbd22"}
SHORT = {"axial_corrugated": "Corrugato", "chaparral": "Chaparral", "ve4ma": "VE4MA", "large_w2imu": "W2IMU LF",
         "large_w2imu_30": "W2IMU LF 30°", "w2imu": "W2IMU", "dualflare": "Dual-Flare", "profile": "Liscio",
         "dualflare_wide": "Dual-Flare", "iz0jny": "Dual-Flare IZ0JNY", "open_circular": "Guida aperta",
         "w2imu_oe2igl": "W2IMU OE2IGL", "skobelev": "Skobelev", "pickett_potter": "Pickett-Potter"}


def _labels(ax, items, ymin, ymax):
    """Feed names written on their lines. Greedy: highest curves first; each label goes on its own curve at the
    point (near its peak) farthest from the labels already placed, so names do not pile up."""
    placed = []
    for fd, y, text, col in sorted(items, key=lambda t: -np.max(t[1])):
        ok = np.where(y > ymin + 1)[0]
        if not len(ok):
            continue
        k0 = int(np.argmax(y))
        cand = [k for k in ok if abs(fd[k] - fd[k0]) <= 0.2]
        def score(k):
            if not placed:
                return -abs(fd[k] - fd[k0])
            d = min(np.hypot((fd[k] - px) / 0.12, (y[k] - py) / 2.2) for px, py in placed)
            return min(d, 1.5) - 0.3 * abs(fd[k] - fd[k0])
        k = max(cand, key=score)
        placed.append((fd[k], y[k]))
        ax.text(fd[k], y[k], text, fontsize=7, color=col, ha="center", va="center", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec=col, lw=0.5, alpha=0.85), zorder=5)


def _panel(ax, rows, c, meta):
    f = meta["dish_band_ghz"]
    dl = meta["dish_lambda"][c]
    if c == "offset":
        title = T("Offset (nessun blocking del feed)")
    elif LANG == "en":
        title = f"Prime-focus dish Ø {float(c) * 100:.0f} cm at {f:g} GHz ({dl:.0f} λ)"
    else:
        title = f"Parabola primo fuoco Ø {float(c) * 100:.0f} cm a {f:g} GHz ({dl:.0f} λ)"
    env, labels = None, []
    for label, r in rows.items():
        fd, y = np.array(r["fD"]), 100 * np.array(r["eta"][c])
        env = y if env is None else np.maximum(env, y)
        col = COLORS.get(r["family"], "k")
        opt = r.get("optimised", True)
        ax.plot(fd, y, "-" if opt else ":", color=col, lw=2.2 if opt else 1.5, zorder=3 if opt else 2)
        i = int(np.argmin(abs(fd - r["design_fD"])))
        ax.plot(fd[i], y[i], "o" if opt else "s", color=col, ms=5, mec="k", mew=0.5, zorder=4)
        name = f"{T(SHORT.get(r['family'], label))} {T('ott.')}" if opt else T(PUB_SHORT.get(label, label))
        labels.append((fd, y, f"{name} ({r['design_fD']:g})", col))
    ax.fill_between(np.array(rows[next(iter(rows))]["fD"]), env, 40, color="0.85", alpha=0.3, lw=0)
    _labels(ax, labels, 55, 88)
    ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.35)
    ax.set_xlim(0.3, 0.9)
    ax.set_ylim(55, 88)
    ax.set_xlabel(T("f/D della parabola"))
    ax.set_ylabel(T("η illuminazione × (1 − |S11|²)  [%]"))


PUB_SHORT = {"Super-VE4MA (W1GHZ/WD5AGO)": "Super-VE4MA", "Chaparral 3 anelli (W1GHZ/WD5AGO)": "Chaparral W1GHZ",
             "Axial Corrugated OE2IGL f/D 0.4": "Corrugato OE2IGL", "Axial Corrugated OE2IGL f/D 0.6": "Corrugato OE2IGL",
             "Guida circolare aperta": "Guida aperta", "W2IMU OE2IGL f/D 0.6": "W2IMU OE2IGL",
             "Large W2IMU 30° (W1GHZ/W1FKF)": "Large W2IMU W1GHZ", "W2IMU (W1GHZ, B = 2.35 f/D) f/D 0.6": "W2IMU W1GHZ",
             "Skobelev (W1GHZ)": "Skobelev", "Pickett-Potter (OE2IGL)": "Pickett-Potter",
             "Dual-Flare IZ0JNY (tabella)": "Dual-Flare IZ0JNY"}
EN = {
    "Offset (nessun blocking del feed)": "Offset (no feed blockage)",
    "f/D della parabola": "Dish f/D",
    "η illuminazione × (1 − |S11|²)  [%]": "η illumination × (1 − |S11|²)  [%]",
    "Efficienza dei feed (openEMS) al variare della f/D": "Feed efficiency (openEMS) versus f/D",
    "Efficienza dei feed (openEMS) al variare di f/D e diametro della parabola":
        "Feed efficiency (openEMS) versus f/D and dish diameter",
    "ott.": "opt.", "Corrugato": "Corrugated", "Liscio": "Smooth profile", "Guida aperta": "Open waveguide",
    "Corrugato OE2IGL": "Corrugated OE2IGL",
}
SUB_EN = ("name on the line = feed (design f/D) · solid line ● = optimised with openEMS · dotted ■ = published design · "
          "grey: best feed at each f/D")
FOOT_EN = ("Each curve comes from one openEMS far field (24 cells/λ, dimensions in λ: valid on every band); feed at its best "
           "phase centre for each f/D; blockage = feed outer Ø. Ruze, ohmic losses and struts not included.")
LANG = "it"


def T(text: str) -> str:
    return EN.get(text, text) if LANG == "en" else text


SUB = ("nome sulla linea = feed (f/D di progetto) · linea continua ● = ottimizzato openEMS · punti ■ = progetto "
       "pubblicato · grigio: il migliore per ogni f/D")
FOOT = ("Ogni curva viene da un solo campo lontano openEMS (24 celle/λ, quote in λ: vale per ogni banda); feed nel centro "
        "di fase migliore per ogni f/D; blocking = Ø esterno del feed. Esclusi Ruze, perdite ohmiche e sostegni.")


def plot(rows, meta, path):
    """One large chart per dish Ø (path stem + _<Ø>cm.png) and an overview grid (path)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cases = list(meta["dish_lambda"])
    for c in cases:
        fig, ax = plt.subplots(figsize=(13, 8.5))
        _panel(ax, rows, c, meta)
        fig.suptitle(T("Efficienza dei feed (openEMS) al variare della f/D") + "\n" + (SUB_EN if LANG == "en" else SUB),
                     fontsize=11)
        fig.text(0.5, 0.005, FOOT_EN if LANG == "en" else FOOT, ha="center", fontsize=8)
        fig.tight_layout(rect=(0, 0.02, 1, 0.94))
        tag = "offset" if c == "offset" else f"{float(c) * 100:.0f}cm"
        stem, en = (path.stem[:-3], "_EN") if path.stem.endswith("_EN") else (path.stem, "")
        fig.savefig(path.with_name(f"{stem}_{tag}{en}.png"), dpi=110)
        plt.close(fig)
    nc = 2
    nr = (len(cases) + nc - 1) // nc
    fig, axs = plt.subplots(nr, nc, figsize=(11 * nc, 7.5 * nr), squeeze=False)
    for ax, c in zip(axs.flat, cases):
        _panel(ax, rows, c, meta)
    for ax in axs.flat[len(cases):]:
        ax.set_axis_off()
    fig.suptitle(T("Efficienza dei feed (openEMS) al variare di f/D e diametro della parabola") + "\n"
                 + (SUB_EN if LANG == "en" else SUB), fontsize=13)
    fig.text(0.5, 0.004, FOOT_EN if LANG == "en" else FOOT, ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.015, 1, 0.965))
    fig.savefig(path, dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    main()
