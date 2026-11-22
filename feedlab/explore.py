"""Interactive exploration: evaluate a feed variant on a given dish, sensitivity sweeps, optimisation
for TX (gain), RX (G/T) or EME (both), and plain-language advice.

Signal-to-noise bookkeeping (dB changes relative to a baseline):
  * TX (terrestrial, your signal at the other station):  ΔSNR = ΔG
  * RX (receiving weak signals):                          ΔSNR = Δ(G/T)
  * EME / own echoes (same dish TX and RX):              ΔSNR = ΔG + Δ(G/T)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import efficiency, geometry, materials, modematch, noise, patterns, reflector
from .waveguide import wavelength_mm

OBJECTIVES = {
    "tx": "TX — massimo guadagno",
    "rx": "RX — massimo G/T (segnali deboli)",
    "eme": "EME — guadagno + G/T (eco proprie)",
}

# design parameters that can be explored per feed type (override key, label, relative span)
TUNABLE = {
    "open_circular": [("diam", "Ø guida", 0.25), ("length", "Lunghezza", 0.3)],
    "w2imu": [("B", "Ø apertura B", 0.15), ("C", "Lunghezza di fase C", 0.2), ("alpha", "Semiangolo flare", 0.3),
              ("A", "Ø ingresso A", 0.08)],
    "w2imu_oe2igl": [("B", "Ø apertura B", 0.15), ("C", "Lunghezza C", 0.2), ("alpha", "Semiangolo flare", 0.3),
                     ("A", "Ø ingresso A", 0.08)],
    "large_w2imu": [("B", "Ø apertura B", 0.12), ("C", "Lunghezza C", 0.2), ("alpha", "Semiangolo flare", 0.3)],
    # flare given by its half-angle (the length follows, with the aperture fixed)
    "skobelev": [("Dap", "Ø apertura", 0.2), ("alpha", "Semiangolo flare", 0.5), ("Ds", "Ø dopo il gradino", 0.08)],
    "pickett_potter": [("Dap", "Ø apertura", 0.2), ("alpha", "Semiangolo flare", 0.5), ("Ds", "Ø dopo il gradino", 0.08)],
    "conical": [("D", "Ø apertura", 0.3), ("alpha", "Semiangolo flare", 0.5)],
    "rect_horn": [("aperture_H", "Apertura piano H", 0.25), ("aperture_E", "Apertura piano E", 0.25),
                  ("axial_length", "Lunghezza", 0.4)],
}

PARAM_FROM_GEOM = {  # override key -> key in geometry.params
    "diam": "diam", "length": "length", "B": "B_aperture", "C": "C_phasing", "alpha": "flare_half_deg",
    "A": "A_input", "Dap": "D_aperture", "flare_length": "flare_length", "Ds": "Ds_step", "D": "D_aperture",
    "aperture_H": "aperture_H", "aperture_E": "aperture_E", "axial_length": "axial_length",
}


@dataclass
class Scenario:
    dish_kind: str = "offset"       # prime | offset
    D_mm: float = 600.0
    fD: float = 0.7
    elev_deg: float = 30.0
    t_rx_K: float = 75.0            # receiver noise temperature (NF 1 dB ≈ 75 K)
    zenith_atten_db: float = 0.3
    t_ground: float = 290.0
    surface_rms_mm: float = 0.1
    feedline_loss_db: float = 0.0   # loss between feed and LNA/PA
    offset_spill_ground_frac: float = 0.25   # offset feed points to the sky: small part of spillover sees ground
    material: str = "Ottone CuZn39Pb3"


@dataclass
class Result:
    params: dict
    eta: float
    spill: float
    illum: float
    phase: float
    pol: float
    block: float
    edge_taper_db: float
    gain_dbi: float
    t_ant: float
    g_over_t: float
    s11_db: float | None
    pc_mm: float
    ohmic_db: float = 0.0
    pattern: patterns.Pattern = field(repr=False, default=None)
    modes: dict = field(default_factory=dict, repr=False)

    def snr_delta(self, base: "Result", objective: str) -> float:
        dG = self.gain_dbi - base.gain_dbi
        dGT = self.g_over_t - base.g_over_t
        return {"tx": dG, "rx": dGT, "eme": dG + dGT}[objective]


def _geo(kind, f, fD, overrides, wall):
    if kind == "rect_horn":
        from .wizard import _wg_for
        return geometry.build_rect(f, fD, _wg_for(f), wall=wall, **overrides)
    return geometry.build(kind, f, fD=fD, wall=wall, **overrides)


def base_values(kind, f, fD, wall=None) -> dict:
    g = _geo(kind, f, fD, {}, wall)
    return {k: float(g.params[PARAM_FROM_GEOM[k]]) for k, _, _ in TUNABLE[kind]}


def evaluate(kind: str, f_ghz: float, sc: Scenario, overrides: dict | None = None, wall: float | None = None,
             fD_design: float | None = None, with_s11: bool = True, fast: bool = True) -> Result:
    overrides = overrides or {}
    geo = _geo(kind, f_ghz, fD_design or sc.fD, overrides, wall)
    lam = wavelength_mm(f_ghz)
    s11 = None
    modes = {}
    if isinstance(geo, geometry.RectHornGeometry):
        p = geo.params
        RH = math.hypot(p["axial_length"], (p["aperture_H"] - p["a"]) / 2) * p["aperture_H"] / max(p["aperture_H"] - p["a"], 1e-6)
        RE = math.hypot(p["axial_length"], (p["aperture_E"] - p["b"]) / 2) * p["aperture_E"] / max(p["aperture_E"] - p["b"], 1e-6)
        pat = patterns.rectangular_aperture_pattern(p["aperture_H"] / lam, p["aperture_E"] / lam, RH / lam, RE / lam,
                                                    n=48, n_theta=181)
    else:
        secs = geo.staircase(lam / (20 if fast else 40))
        r = modematch.simulate(secs, [f_ghz], n_modes=10 if fast else 16)
        s11 = float(r.s11_db[0]) if with_s11 else None
        modes = r.aperture_modes[0]
        pat = modematch.aperture_pattern(r, 0, f_ghz, n_rho=28 if fast else 48, n_phi=32 if fast else 60,
                                         n_theta=181 if fast else 361)
    return performance(kind, f_ghz, sc, geo, pat, s11, modes)


def performance(kind: str, f_ghz: float, sc: Scenario, geo, pat: patterns.Pattern, s11: float | None = None,
                modes: dict | None = None) -> Result:
    """Dish performance of a feed pattern (from the fast solver or from openEMS): the same formulas for both,
    so that fast vs full-wave differences come only from the solvers."""
    lam = wavelength_mm(f_ghz)
    modes = modes or {}
    blk = geo.blockage_diameter() / sc.D_mm if sc.dish_kind == "prime" else 0.0
    e = efficiency.dish_efficiency(pat, sc.fD, blk)
    pc, _ = efficiency.phase_center_by_efficiency(pat, sc.fD, span_lambda=0.8, step=0.02, block_diam_ratio=blk)
    eta_tot = e.total * reflector.ruze(sc.surface_rms_mm, lam)
    mat = materials.MATERIALS.get(sc.material, materials.MATERIALS["Ottone CuZn39Pb3"])
    if isinstance(geo, geometry.RectHornGeometry):
        ohm = 0.0
    else:
        ohm = materials.feed_ohmic_loss_db(geo.staircase(lam / 10), f_ghz, mat)
    line = 10 ** (-(sc.feedline_loss_db + ohm) / 10)
    G = reflector.gain_dbi(sc.D_mm, lam, max(eta_tot * line, 1e-6))
    tsky = noise.sky_temp(sc.elev_deg, sc.zenith_atten_db, f_ghz=f_ghz)
    if sc.dish_kind == "prime":
        ta = noise.antenna_temp_prime_focus(pat, sc.fD, sc.elev_deg, tsky, sc.t_ground, n_phi=72)
    else:
        spill_T = sc.offset_spill_ground_frac * sc.t_ground + (1 - sc.offset_spill_ground_frac) * tsky
        ta = e.spillover * tsky + (1 - e.spillover) * spill_T
    t_sys = ta * line + (1 - line) * 290.0 + sc.t_rx_K
    gt = G - 10 * math.log10(t_sys)
    params = {k: float(geo.params[PARAM_FROM_GEOM[k]]) for k, _, _ in TUNABLE.get(kind, [])}
    return Result(params, eta_tot * line, e.spillover, e.illumination, e.phase, e.polarization, e.blockage,
                  e.edge_taper_db, G, ta, gt, s11, pc * lam, ohm, pat, modes)


STEP_HORNS = ("pickett_potter", "skobelev")
TM11_TARGET = (0.08, 0.22)        # Jeff WA6KBL (DUBUS): TM11 at the step ≈ 15 % of the dominant mode


def tm11_power_ratio(modes: dict) -> float | None:
    """|TM11|²/|TE11|² at the aperture (power-normalised modes from mode matching)."""
    if not modes or "TE11" not in modes or abs(modes["TE11"]) == 0:
        return None
    return abs(modes.get("TM11", 0)) ** 2 / abs(modes["TE11"]) ** 2


def metric(res: Result, objective: str) -> float:
    return {"tx": res.gain_dbi, "rx": res.g_over_t, "eme": res.gain_dbi + res.g_over_t}[objective]


def sensitivity(kind, f, sc, base_over: dict, objective: str, n: int = 7, wall=None, fD_design=None):
    """For each tunable parameter: sweep ±span around the current value, return curves and the best step."""
    out = {}
    cur = {**base_values(kind, f, fD_design or sc.fD, wall), **base_over}
    for key, label, span in TUNABLE[kind]:
        x0 = cur[key]
        xs = x0 * (1 + np.linspace(-span, span, n))
        rows = []
        for x in xs:
            try:
                r = evaluate(kind, f, sc, {**base_over, key: float(x)}, wall, fD_design, with_s11=True)
                rows.append((float(x), metric(r, objective), r.eta, r.gain_dbi, r.g_over_t, r.s11_db, r.edge_taper_db))
            except Exception:
                rows.append((float(x), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan))
        out[key] = {"label": label, "x0": x0, "rows": np.array(rows, float)}
    return out


def optimize(kind, f, sc, start_over: dict, objective: str, keys: list[str] | None = None, max_eval: int = 40,
             wall=None, fD_design=None, s11_limit_db: float = -18.0, progress=None):
    """Nelder-Mead on relative changes of the chosen parameters (bounded by the tunable span).
    Penalises S11 worse than s11_limit_db."""
    from scipy.optimize import minimize
    cur = {**base_values(kind, f, fD_design or sc.fD, wall), **start_over}
    tun = {k: (lab, sp) for k, lab, sp in TUNABLE[kind]}
    keys = keys or [k for k in tun][:3]
    x0 = np.zeros(len(keys))
    calls = {"n": 0, "best": None}

    def f_obj(x):
        calls["n"] += 1
        over = dict(start_over)
        for k, v in zip(keys, x):
            v = float(np.clip(v, -tun[k][1], tun[k][1]))
            over[k] = cur[k] * (1 + v)
        try:
            r = evaluate(kind, f, sc, over, wall, fD_design)
        except Exception:
            return 1e3
        val = -metric(r, objective)
        if r.s11_db is not None and r.s11_db > s11_limit_db:
            val += (r.s11_db - s11_limit_db) * 0.5
        if calls["best"] is None or val < calls["best"][0]:
            calls["best"] = (val, over, r)
        if progress:
            progress(calls["n"], max_eval, -val)
        return val

    minimize(f_obj, x0, method="Nelder-Mead", options={"maxfev": max_eval, "initial_simplex":
             np.vstack([x0] + [np.eye(len(keys))[i] * 0.06 for i in range(len(keys))]), "xatol": 0.003, "fatol": 0.005})
    return calls["best"][1], calls["best"][2]


def advice(r: Result, base: Result | None, sc: Scenario, objective: str, kind: str, f_ghz: float) -> list[str]:
    """Plain-language hints distilled from W1GHZ/OE2IGL rules."""
    tips = []
    lam = wavelength_mm(f_ghz)
    if r.edge_taper_db < 9:
        tips.append(f"Taper al bordo {r.edge_taper_db:.1f} dB: il dish è sovra-illuminato (spillover {100 * (1 - r.spill):.0f}%). "
                    "Aumenta il diametro d'apertura del feed (fascio più stretto) per ridurre spillover e rumore di terra.")
    elif r.edge_taper_db > 16:
        tips.append(f"Taper al bordo {r.edge_taper_db:.1f} dB: dish sotto-illuminato (illuminazione {100 * r.illum:.0f}%). "
                    "Riduci l'apertura del feed per guadagnare in TX; per RX/EME un po' di sotto-illuminazione è utile.")
    else:
        tips.append(f"Taper al bordo {r.edge_taper_db:.1f} dB: nella zona buona (10 dB per guadagno, 12–16 dB per G/T).")
    if objective in ("rx", "eme"):
        tips.append("Per il G/T: preferisci un feed con f/D ottimo un po' maggiore della tua parabola (W1GHZ 2014); "
                    "su offset il W2IMU da 1.88λ ha dato +2.3 dB di sole rispetto a 1.34λ (W1GHZ 2024).")
        if sc.feedline_loss_db > 0:
            tips.append(f"Linea feed→LNA {sc.feedline_loss_db:.2f} dB: ogni 0.1 dB peggiora il G/T di ~0.1–0.5 dB. "
                        "Monta l'LNA direttamente sul feed.")
        if sc.t_rx_K > 100:
            tips.append("Il ricevitore domina il rumore: abbassare NF rende più di qualunque ritocco al feed.")
    if objective == "tx":
        tips.append("Per il TX conta solo il guadagno: punta al massimo η (taper ~10–11 dB), poi riduci le perdite di linea.")
    if r.phase < 0.98:
        tips.append(f"Efficienza di fase {100 * r.phase:.1f}%: i modi non arrivano in fase all'apertura. "
                    "Sui dual-mode regola la lunghezza della sezione di fase C (o del flare): pochi % cambiano molto.")
    if r.pol < 0.985:
        tips.append(f"Cross-pol {100 * (1 - r.pol):.1f}% di potenza: piani E e H diversi. Nel W2IMU/Potter correggi il rapporto "
                    "TM11/TE11 (angolo di flare / gradino); un pattern simmetrico migliora anche la CP.")
    q = tm11_power_ratio(r.modes)
    if kind in STEP_HORNS and q is not None and not (TM11_TARGET[0] <= q <= TM11_TARGET[1]):
        tips.append(f"TM11 all'apertura {100 * q:.0f}% del TE11 in potenza: Jeff WA6KBL indica ~15% per un "
                    f"Pickett-Potter. {'Aumenta' if q < TM11_TARGET[0] else 'Riduci'} il gradino (Ø dopo il gradino) "
                    "e poi riallinea la lunghezza del flare perché i due modi arrivino in fase alla bocca.")
    if r.s11_db is not None and r.s11_db > -18:
        tips.append(f"S11 {r.s11_db:.1f} dB: adattamento scarso (in TX potenza riflessa {100 * 10 ** (r.s11_db / 10):.1f}%). "
                    "Addolcisci flare/gradini o allunga la transizione d'ingresso.")
    if sc.dish_kind == "prime":
        tips.append(f"Posiziona il centro di fase sul fuoco: {abs(r.pc_mm):.2f} mm "
                    f"{'davanti' if r.pc_mm > 0 else 'dentro'} all'apertura (errore λ/4 = {lam / 4:.2f} mm costa ~1 dB su dish profondi).")
    else:
        tips.append("Sull'offset la posizione assiale è poco critica (inclina il fascio); punta il feed verso il punto più profondo.")
    if base is not None:
        d = r.snr_delta(base, objective)
        if abs(d) >= 0.05:
            tips.insert(0, f"Rispetto al progetto di partenza: {'+' if d > 0 else ''}{d:.2f} dB di S/N "
                           f"({OBJECTIVES[objective]}).")
    return tips
