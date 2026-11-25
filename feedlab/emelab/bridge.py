# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Link between FeedLab and EMELab (two separate programs on the same PC).

FeedLab keeps the design that is open (dish, feed type, edited dimensions, material, illumination) in a small
file of the settings folder; EMELab asks for it ("📥 Prendi da FeedLab") and computes gain, efficiency,
spillover and edge taper by itself for the band it needs (10, 24 or 47 GHz), with FeedLab's own models."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

FILE = "feedlab_design.json"


def _path() -> Path:
    from .. import openems_local
    return openems_local.config_dir() / FILE


def save_design(S) -> bool:
    """Called by FeedLab at every run: writes the open design when it is complete and changed."""
    d = S.get("dish")
    if not (d and S.get("feed_kind") and S.get("material")):
        return False
    data = {"dish": {"kind": d.kind, "D_mm": d.D_mm, "fD": d.fD, "f_mm": d.f_mm, "note": d.note},
            "feed_kind": S["feed_kind"], "overrides": dict((S.get("overrides") or {}).get(S["feed_kind"], {})),
            "material": S["material"], "fd_design": S.get("fd_design"), "f_ghz": S.get("f_ghz"),
            "wall": S.get("wall"), "wr_wg": S.get("wr_wg")}
    p = _path()
    try:
        old = json.loads(p.read_text(encoding="utf-8"))
        if {k: v for k, v in old.items() if k != "saved_utc"} == data:
            return False
    except Exception:
        pass
    data["saved_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return True


def load_design() -> dict | None:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except Exception:
        return None


def describe(des: dict) -> str:
    from .. import geometry, i18n
    d = des["dish"]
    return (f"{i18n.tr(geometry.FEED_TYPES.get(des['feed_kind'], des['feed_kind']))} · "
            f"{'offset' if d['kind'] == 'offset' else 'prime focus'} D {d['D_mm']:.0f} mm f/D {d['fD']:.3f} · "
            f"{i18n.tr(des['material'])}")


def setup_from_design(des: dict, band: float, extra: dict) -> dict:
    """Gain, efficiency, spillover and edge taper of FeedLab's design at this band (dimensions rebuilt for the band;
    edited dimensions are kept only at the band they were made for)."""
    from .. import explore
    from . import analysis
    d = des["dish"]
    sc = explore.Scenario(dish_kind=d["kind"], D_mm=d["D_mm"], fD=d["fD"], elev_deg=30,
                          t_rx_K=analysis.t_rx(extra.get("nf_db", 1.5)), surface_rms_mm=extra.get("rms_mm", 0.3),
                          feedline_loss_db=0.0, material=des.get("material") or "Ottone CuZn39Pb3")
    same_band = des.get("f_ghz") and abs(float(des["f_ghz"]) - band) < 0.5
    over = (des.get("overrides") or {}) if same_band else {}
    r = explore.evaluate(des["feed_kind"], band, sc, dict(over), fD_design=des.get("fd_design"))
    return {"band_ghz": band, "D_m": d["D_mm"] / 1000, "eta_ap": r.eta, "gain_dbi": r.gain_dbi,
            "edge_taper_db": r.edge_taper_db, "spill": r.spill, "ground_frac": 0.25 if d["kind"] == "offset" else 0.5,
            "feed": des["feed_kind"], "dish": f"{d['kind']} D {d['D_mm']:.0f} mm f/D {d['fD']:.3f}",
            "material": des.get("material"), "pc_mm": r.pc_mm, "source": "FeedLab", **extra}
