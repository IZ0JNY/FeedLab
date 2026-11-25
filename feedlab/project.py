# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""FeedLab project file (.json): everything typed in the design and everything FeedLab computed from it.

It is the exchange format between FeedLab installations and with EMELab: EMELab reads the results stored here
(gain, G/T, efficiency, spillover, edge taper, Tsys, pattern) and never recomputes them. FeedLab can open it again
to restore the design. All lengths in mm, angles in degrees, frequencies in GHz, times in UTC."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import numpy as np

FORMAT = "FeedLab project"
SCHEMA = 1
AUTO_FILE = "feedlab_project.json"         # the open design, kept up to date for EMELab

INPUT_KEYS = ["f_ghz", "feed_kind", "material", "wall", "base_t", "base_shape", "wr_wg", "mount_cfg", "mount_ui",
              "plate_rf", "fd_design", "ill_mode", "ill_taper", "ill_goal", "outer_mode", "outer_fillet", "lab_scenario"]


def _clean(o):
    """JSON-safe copy: numpy → python, NaN → None, complex → [re, im]."""
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return _clean(o.tolist())
    if isinstance(o, (np.floating, float)):
        v = float(o)
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    if isinstance(o, (str, int, bool)) or o is None:
        return o
    return str(o)


def default_scenario(f_ghz: float) -> dict:
    """Receive scenario used when the Laboratory has not set one (same defaults as the Laboratory)."""
    return {"elev_deg": 30.0, "nf_db": 1.0 if f_ghz < 30 else 3.0 if f_ghz < 80 else 8.0, "line_loss_db": 0.1,
            "rms_mm": 0.1, "zenith_db": 0.1 if f_ghz < 20 else 0.3 if f_ghz < 60 else 1.0}


def build(S, geo, fd_design: float, with_sweep: bool = True) -> dict:
    """Project dictionary from the app state S and the current feed geometry."""
    from . import __version__, explore, geometry, i18n, modematch, noise
    f = float(S["f_ghz"])
    d = S["dish"]
    kind = S["feed_kind"]
    sc_d = {**default_scenario(f), **(S.get("lab_scenario") or {})}
    sc = explore.Scenario(d.kind, d.D_mm, d.fD, max(sc_d["elev_deg"], 1), noise.receiver_temp(sc_d["nf_db"]),
                          sc_d["zenith_db"], 290.0, sc_d["rms_mm"], sc_d["line_loss_db"], material=S["material"])
    over = dict((S.get("overrides") or {}).get(kind, {}))
    out = {"format": FORMAT, "schema": SCHEMA, "app_version": __version__,
           "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "inputs": {**{k: S.get(k) for k in INPUT_KEYS}, "overrides": over,
                      "dish": {"kind": d.kind, "D_mm": d.D_mm, "fD": d.fD, "f_mm": d.f_mm, "note": d.note},
                      "feed_name": i18n.tr(geometry.FEED_TYPES.get(kind, kind)), "scenario": sc_d,
                      "fd_design_used": fd_design}}
    out["geometry"] = {"params": {k: v for k, v in geo.params.items() if isinstance(v, (int, float, str))},
                       "length_mm": geo.length, "aperture_diam_mm": 2 * getattr(geo, "r_aperture", 0.0),
                       "input_diam_mm": 2 * getattr(geo, "r_input", 0.0),
                       "outer_diam_mm": 2 * getattr(geo, "outer_radius", 0.0),
                       "profile": [list(p) for p in getattr(geo, "profile", [])]}
    try:
        r = explore.evaluate(kind, f, sc, over, S.get("wall"), fd_design, fast=False)
        out["results"] = {"gain_dbi": r.gain_dbi, "g_over_t": r.g_over_t, "eta": r.eta, "spill": r.spill,
                          "illum": r.illum, "phase": r.phase, "pol": r.pol, "block": r.block,
                          "edge_taper_db": r.edge_taper_db, "t_ant_K": r.t_ant, "s11_db": r.s11_db,
                          "phase_center_mm": r.pc_mm, "ohmic_db": r.ohmic_db, "tsys": r.tsys,
                          "pattern": {"theta_deg": r.pattern.theta_deg[::2],
                                      "E_db": 20 * np.log10(np.abs(r.pattern.E[::2]) / np.max(np.abs(r.pattern.E)) + 1e-12),
                                      "H_db": 20 * np.log10(np.abs(r.pattern.H[::2]) / np.max(np.abs(r.pattern.H)) + 1e-12)}}
    except Exception as e:
        out["results"] = {"error": str(e)}
    if with_sweep and kind in geometry.MODEMATCH_OK:
        try:
            fl = np.linspace(0.95 * f, 1.05 * f, 21)
            mm = modematch.simulate(geo.staircase(geo.lam / 30), fl, n_modes=12)
            out["s11_sweep"] = {"f_ghz": fl, "s11_db": mm.s11_db}
        except Exception:
            pass
    pl = plate_of(S, f)
    if pl is not None:
        out["plate"] = pl
    out["openems"] = openems_runs(kind, f, d, sc_d)
    return _clean(out)


def plate_obj(S, f):
    """The λ/4 matching plate object as set in the WR plate tab (None if not designed yet)."""
    from . import plate
    wg = S.get("wr_wg")
    rf = S.get("plate_rf")
    if not wg or not rf:
        return None
    pol, dcirc, rr, opt = rf
    mu = S.get("mount_ui") or {}
    return plate.design_plate(f, wg, dcirc, pol, rr, opt, holes=mu.get("system", "metric") if mu.get("holes") else None,
                                plate_screw=mu.get("plate_screw"), base_holes=mu.get("base_holes", "flange"),
                                hole_dia=mu.get("hole_dia"), thread=mu.get("thread"), cbore=bool(mu.get("cbore")),
                                cb_depth=mu.get("cb_depth"), cb_dia=mu.get("cb_dia"), pins=bool(mu.get("pins", True)),
                                plate_t=mu.get("plate_t"), plate_head=mu.get("plate_head", "allen"),
                                plate_tap=bool(mu.get("plate_tap")), outer_mm=mu.get("outer_mm"), outer_r=mu.get("outer_r", 0.0),
                                plate_hole_dia=mu.get("plate_hole_dia"), plate_cb_dia=mu.get("plate_cb_dia"),
                                plate_cb_depth=mu.get("plate_cb_depth"))


def plate_of(S, f):
    """The plate as a dictionary for the project file."""
    wg = S.get("wr_wg")
    if not wg:
        return None
    try:
        pl = plate_obj(S, f)
        if pl is None:
            return {"wg": wg}
        pol, dcirc, rr, opt = S["plate_rf"]
        return {"wg": wg, "pol": pol, "circ_diam_mm": dcirc, "corner_r_mm": rr, "optimised": opt,
                **{k: v for k, v in pl.__dict__.items() if isinstance(v, (int, float, str, bool))}}
    except Exception as e:
        return {"wg": wg, "error": str(e)}


def openems_runs(kind: str, f: float, dish=None, sc: dict | None = None) -> list[dict]:
    """Finished openEMS simulations of this feed type and band found on this PC, with the dish results
    computed from their full-wave pattern (same formulas as the fast simulator)."""
    try:
        from . import deep_analysis, openems_local
        from pathlib import Path
        out = []
        for j in openems_local.list_jobs():
            if not (j.get("kind") == kind and j.get("f_ghz") and abs(float(j["f_ghz"]) - f) < 0.5 and j.get("has_results")):
                continue
            row = {"label": j.get("label"), "dir": j.get("dir"), "cells_per_lambda": j.get("cells_per_lambda"),
                   "params": j.get("params")}
            if dish is not None:
                try:
                    sc = sc or default_scenario(f)
                    spec = deep_analysis.DishSpec(dish.kind, dish.D_mm, dish.fD, sc["elev_deg"], sc["nf_db"],
                                                  sc["zenith_db"], sc["rms_mm"], sc["line_loss_db"])
                    a = deep_analysis.analyze(deep_analysis.load(Path(j["dir"]) / "results.json"), spec)
                    det = a["f0_detail"]
                    row.update(f0_ghz=a["f0"], s11=a["s11"], gain_dbi=det["gain_dbi"], g_over_t=det["g_over_t_db"],
                               eta=det["eta_total"], eff=det["eff"], phase_center_mm=det["phase_center"]["d_mm"],
                               hpbw_deg=det["hpbw_deg"], t_sys=det["t_sys"], warnings=a.get("warnings"))
                except Exception as e:
                    row["error"] = str(e)
            out.append(row)
        return out
    except Exception:
        return []


def to_json(p: dict) -> str:
    return json.dumps(p, indent=1, ensure_ascii=False)


def load(text: str | bytes) -> dict:
    p = json.loads(text)
    if p.get("format") != FORMAT:
        raise ValueError("non è un file di progetto FeedLab")
    return p


def auto_path():
    from . import openems_local
    return openems_local.config_dir() / AUTO_FILE


def save_auto(p: dict) -> None:
    """Keep the open design for EMELab (only when it changed)."""
    path = auto_path()
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("inputs") == p.get("inputs") and old.get("results") == p.get("results"):
            return
    except Exception:
        pass
    path.write_text(to_json(p), encoding="utf-8")


def load_auto() -> dict | None:
    try:
        return load(auto_path().read_text(encoding="utf-8"))
    except Exception:
        return None


def apply(S, p: dict) -> None:
    """Restore a project in FeedLab's session (dish, feed, dimensions, material, illumination, mounting)."""
    from .wizard import Dish
    i = p["inputs"]
    d = i["dish"]
    S["dish"] = Dish(d["kind"], d["D_mm"], d["fD"], d.get("f_mm"), d.get("note", ""))
    for k in INPUT_KEYS:
        if i.get(k) is not None:
            S[k] = i[k]
    S["overrides"] = {i["feed_kind"]: dict(i.get("overrides") or {})}
