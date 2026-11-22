"""Guided feed selection: given dish + frequency + constraints, rank candidate feeds.

Rules distilled from W1GHZ (book ch.6, MUD 2006/2014/2023/2024) and OE2IGL (Dorsten 2025/2026):
  * prime focus f/D < 0.3: Chaparral (shallow rings) best; consider Cassegrain if D > ~40 λ
  * prime focus 0.3-0.45: Super-VE4MA / Chaparral (choke) ; cavity feed (OE2IGL, not modelled yet)
  * f/D (or offset-equivalent) 0.5-0.8: W2IMU / Pickett-Potter / Skobelev dual-mode
  * f/D > 0.8: Skobelev larger apertures / large W2IMU (≤ 1.9 λ) / Cassegrain feeds
  * offset dishes: dual-mode horns (no blockage, low spillover); larger horn for G/T
  * > 76 GHz: lathe-made dual-mode (W2IMU 30° centre drill, Pickett-Potter); avoid septum/corrugations
  * rectangular horn: only linear pol, WR-fed, f/D ≥ 0.45-0.48
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import efficiency, geometry, modematch, reflector
from .waveguide import wavelength_mm


@dataclass
class Dish:
    kind: str                 # "prime" | "offset"
    D_mm: float               # aperture diameter (offset: projected/short axis)
    fD: float                 # prime f/D, or offset-equivalent f/D seen by the feed
    f_mm: float | None = None
    note: str = ""

    @property
    def opening_deg(self) -> float:
        return 2 * reflector.half_angle_from_fD(self.fD)


def dish_from_prime(D: float, fD: float | None = None, depth: float | None = None) -> Dish:
    if fD is None:
        f = reflector.focal_length_from_depth(D, depth)
        fD = f / D
    return Dish("prime", D, fD, fD * D)


def dish_from_offset_tv(long_axis: float, short_axis: float, depth: float) -> Dish:
    r = reflector.offset_from_tv_measurements(long_axis, short_axis, depth)
    g = r["geometry"]
    return Dish("offset", short_axis, g.fD_equiv, r["f"],
                note=f"f={r['f']:.1f} mm, stringa inferiore {r['bottom_string']:.1f} mm, superiore {r['top_string']:.1f} mm, "
                     f"illuminazione {g.psi_L:.1f}°…{g.psi_U:.1f}°, puntamento feed {g.feed_pointing():.1f}° dall'asse")


def dish_from_catalog(dm) -> Dish:
    """Dish from a catalogue entry (feedlab.dishes.DishModel) using the required illumination angle."""
    f, src = dm.focal()
    note = f"{dm.maker} {dm.model}: focale {f:.0f} mm ({src})" if f else f"{dm.maker} {dm.model}: focale ignota"
    if dm.offset_deg:
        note += f", angolo offset {dm.offset_deg}°"
    note += f" — fonte: {dm.source}"
    return Dish(dm.kind, dm.D_mm, dm.fD_equiv(), f, note=note)


def dish_from_offset_fD(D: float, f: float, h: float = 0.0) -> Dish:
    g = reflector.offset_geometry(f, D, h)
    return Dish("offset", D, g.fD_equiv, f, note=f"illuminazione {g.psi_L:.1f}°…{g.psi_U:.1f}°")


@dataclass
class Candidate:
    kind: str
    label: str
    score: float
    eta_est: float | None
    best_fD: float | None
    blockage_diam_mm: float
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    geometry: object = None


def _quick_eta(geo, fD_dish, block_ratio):
    """Mode-matching + aperture model efficiency at the dish f/D (only for circular-guide feeds)."""
    if geo.kind not in geometry.MODEMATCH_OK:
        return None, None
    try:
        r = modematch.simulate(geo.staircase(), [geo.f_ghz], n_modes=12)
        p = modematch.aperture_pattern(r, 0, geo.f_ghz, n_rho=30, n_phi=36, n_theta=181)
        e = efficiency.dish_efficiency(p, fD_dish, block_ratio).total
        b = efficiency.best_fD(p, np.arange(0.25, 2.0, 0.01))
        return e, b.fD
    except Exception:
        return None, None


DESIGN_GUIDE_ETA = {   # typical calculated efficiencies from W1GHZ/OE2IGL simulations (incl. xpol/phase)
    "ve4ma": 0.77, "chaparral": 0.77, "skobelev": 0.79, "pickett_potter": 0.79, "w2imu_oe2igl": 0.78,
    "large_w2imu": 0.78, "w2imu": 0.76, "open_circular": 0.65, "conical": 0.62, "rect_horn": 0.70,
}


def recommend(dish: Dish, f_ghz: float, polarization: str = "linear", priority: str = "gain",
              tools: str = "lathe", quick_sim: bool = True) -> list[Candidate]:
    lam = wavelength_mm(f_ghz)
    D_l = dish.D_mm / lam
    fD = dish.fD
    # G/T priority -> design the feed for a slightly larger f/D (under-illuminate, W1GHZ 2014/2024)
    fD_feed = fD * (1.08 if priority == "gt" else 1.0)
    cands = []

    def add(kind, why, warn=(), **kw):
        try:
            geo = geometry.build(kind, f_ghz, fD=fD_feed, **kw) if kind != "rect_horn" else \
                geometry.build_rect(f_ghz, fD_feed, kw.get("wg", "WR-90"))
        except Exception as ex:  # outside the validity range
            return
        blk = geo.blockage_diameter() if dish.kind == "prime" else 0.0
        block_ratio = blk / dish.D_mm
        eta, bfd = (None, None)
        if quick_sim:
            eta, bfd = _quick_eta(geo, fD, block_ratio)
        base = geo.params["eta_guide_pct"] / 100 if "eta_guide_pct" in geo.params else DESIGN_GUIDE_ETA.get(kind, 0.6)
        est = eta if eta is not None else base * reflector.blocking_efficiency(blk, dish.D_mm, 0.8)
        score = est
        w = list(warn)
        cands.append(Candidate(kind, geometry.FEED_TYPES[kind], score, est, bfd, blk, list(why), w, geo))

    # ---------- candidate generation ----------
    hi_freq = f_ghz > 70
    if dish.kind == "offset" or fD >= 0.5:
        if 0.5 <= fD_feed <= 0.95:
            add("w2imu_oe2igl", ["dual-mode, PC sull'apertura, facile al tornio",
                                 "OE2IGL: 77-80% (openEMS)"])
            add("pickett_potter", ["gradino + flare: ~80% (OE2IGL), consigliato anche oltre 76 GHz"])
            add("skobelev", ["tabella HFSS W1GHZ: 77-81%, lobi molto bassi"],
                ["Jeff WA6KBL (DUBUS): le quote di Skobelev in CST hanno dato risultati deludenti a 10 GHz — "
                 "verifica full-wave (openEMS) prima di costruire"])
            add("w2imu", ["classico W1GHZ (B ≈ 2.35 f/D)"])
        if 0.65 <= fD_feed <= 0.85:
            add("large_w2imu", ["flare 30° con punta da centri: ideale 47-241 GHz", "migliore G/T su offset (+1.6…2.3 dB sun noise)"])
        if fD_feed > 0.95:
            add("skobelev", ["unico dual-mode adatto a f/D > 0.9 (apertura 2-6 λ)"])
        if polarization == "linear" and f_ghz < 40 and fD_feed >= 0.48:
            add("rect_horn", ["semplice da lamiera, diretto da guida WR"], wg=_wg_for(f_ghz))
    if dish.kind == "prime" and fD < 0.5:
        add("ve4ma", ["Super-VE4MA: 79% calc., 65% misurato (record prime-focus)"],
            ["simulazione rapida non disponibile (anello coassiale): usare openEMS"] +
            (["blocking alto su dish piccolo"] if D_l < 12 else []), variant="super")
        add("chaparral", ["3 anelli bassi 0.2×0.2λ: 78% @ f/D 0.35; migliore per f/D < 0.33"],
            ["simulazione rapida non disponibile: usare openEMS"], variant="best" if fD >= 0.3 else "deep_dish")
        add("open_circular", ["semplicissimo, blocking minimo per dish < 10 λ"], ["F/B scarso, ~10 punti sotto i choke"])
        if D_l > 40:
            for c in cands:
                c.warnings.append("dish > 40λ: valutare Cassegrain con feed dual-mode (vedi modulo Cassegrain)")
    # axial corrugated (Gerald OE2IGL v1.4): 10-76 GHz, prime f/D 0.33-0.9, offset-equivalent 0.33-0.8
    if 10 <= f_ghz <= 76 and 0.33 <= fD_feed <= (0.9 if dish.kind == "prime" else 0.8):
        add("axial_corrugated", ["corrugato assiale 8 gole: 81-86% (Gerald OE2IGL, openEMS), ampio campo di f/D",
                                 "facile al tornio fino a 47 GHz; da 76 GHz meglio Pickett-Potter o cavity feed"],
            ["simulazione rapida non disponibile (gole assiali): verifica con openEMS"]
            + (["sopra 47 GHz le gole diventano molto strette"] if f_ghz > 47 else []))
    # ---------- adjustments ----------
    for c in cands:
        if polarization == "circular":
            if c.kind == "rect_horn":
                c.score -= 1
                c.warnings.append("solo polarizzazione lineare")
            else:
                c.reasons.append("CP: aggiungere polarizzatore (septum in guida 0.71λ o dielettrico)")
                if f_ghz > 60:
                    c.warnings.append("septum oltre 60 GHz: simmetria guida entro ~1% (pochi µm)")
        if hi_freq and c.kind in ("ve4ma", "chaparral"):
            c.score -= 0.05
            c.warnings.append("anelli sottili difficili oltre 70 GHz (OE2IGL: cavity feed o Pickett-Potter)")
        if tools == "sheet" and c.kind not in ("rect_horn", "open_circular", "w2imu"):
            c.score -= 0.03
            c.warnings.append("richiede tornio")
        if priority == "gt" and c.kind in ("large_w2imu", "skobelev", "pickett_potter"):
            c.score += 0.01
    if dish.kind == "prime" and fD < 0.3:
        for c in cands:
            if c.kind == "chaparral":
                c.score += 0.03
    cands.sort(key=lambda c: -c.score)
    # deduplicate by kind
    seen, out = set(), []
    for c in cands:
        if c.kind not in seen:
            seen.add(c.kind); out.append(c)
    return out


def _wg_for(f):
    from .waveguide import suggest_rect_wg
    s = suggest_rect_wg(f)
    return s[0] if s else "WR-90"
