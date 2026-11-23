"""Deep analysis of openEMS full-wave results (results.json written by the scripts of openems_sim).

From the raw fields it derives what matters for a dish feed:
  * match: S11, return loss, VSWR, -15/-20 dB bandwidth, input impedance;
  * pattern at each simulated frequency: Ludwig-3 co/cross-polar cuts, -3/-10 dB beamwidths, E/H symmetry,
    front-to-back, peak cross-polar level, BOR1 directivity and (from the full sphere) true directivity,
    radiated/accepted power (radiation efficiency, also a convergence check of the run);
  * phase centre: PHASEPAT method (best efficiency) and the W1GHZ formula in the E and H planes;
  * reflector performance on the user's dish: efficiency and its decomposition, best f/D, gain, T_antenna, G/T;
  * comparison of several runs (mesh convergence, parameter sweeps) and with FeedLab's fast model;
  * exports: HTML report, CSV, W1GHZ .dat (FEEDPATT/PHASEPAT).
"""
from __future__ import annotations

import base64
import csv
import io
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from . import efficiency, noise, reflector
from .patterns import Pattern, save_w1ghz_dat

DEG = math.pi / 180.0
C0 = 299792458.0


def _trap(y, x):
    return np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x)


def _cplx(d, key):
    return np.array(d[key + "_re"], float) + 1j * np.array(d[key + "_im"], float)


@dataclass
class FarField:
    f_ghz: float
    theta: np.ndarray
    phis: np.ndarray
    Et: np.ndarray             # complex [n_theta, n_phi]
    Ep: np.ndarray
    Prad: float = float("nan")
    Pacc: float = float("nan")
    Dmax_nf2ff_dbi: float = float("nan")

    @property
    def lam_mm(self) -> float:
        return C0 / (self.f_ghz * 1e9) * 1e3

    def _idx(self, phi: float) -> int:
        d = np.abs(((self.phis - phi) + 180) % 360 - 180)
        return int(np.argmin(d))

    def ludwig3(self, phi: float) -> tuple[np.ndarray, np.ndarray]:
        """Co- and cross-polar (Ludwig-3, reference x-polarisation) on the cut nearest to phi."""
        i = self._idx(phi)
        c, s = math.cos(self.phis[i] * DEG), math.sin(self.phis[i] * DEG)
        co = self.Et[:, i] * c - self.Ep[:, i] * s
        cr = self.Et[:, i] * s + self.Ep[:, i] * c
        return co, cr

    def pattern(self, name: str = "") -> Pattern:
        A, _ = self.ludwig3(0.0)
        B, _ = self.ludwig3(90.0)
        p = Pattern(self.theta, A, B, name or f"openEMS {self.f_ghz:g} GHz")
        # fine angular grid: the efficiency integrals stop at the rim angle, a coarse grid makes them jagged
        return p.resample(0.05)

    def xpol_peak_db(self, theta_max: float = 90.0) -> float:
        co0 = max(np.abs(self.ludwig3(0)[0]).max(), np.abs(self.ludwig3(90)[0]).max(), 1e-30)
        m = self.theta <= theta_max
        peak = max(np.abs(self.ludwig3(p)[1][m]).max() for p in self.phis)
        return float(20 * math.log10(peak / co0 + 1e-15))

    def radiation_efficiency(self) -> float:
        return float(self.Prad / self.Pacc) if self.Pacc and np.isfinite(self.Pacc) and self.Pacc > 0 else float("nan")


@dataclass
class Sphere:
    f_ghz: float
    theta: np.ndarray
    phi: np.ndarray
    Et: np.ndarray
    Ep: np.ndarray
    Prad: float = float("nan")
    Pacc: float = float("nan")
    Dmax_nf2ff_dbi: float = float("nan")

    def directivity_dbi(self) -> float:
        U = np.abs(self.Et) ** 2 + np.abs(self.Ep) ** 2
        t = self.theta * DEG
        dphi = (self.phi[1] - self.phi[0]) * DEG if len(self.phi) > 1 else 2 * math.pi
        P = _trap(U.sum(axis=1) * dphi * np.sin(t), t)
        return float(10 * math.log10(4 * math.pi * U.max() / P)) if P > 0 else float("nan")

    def bor_deviation_db(self, A: np.ndarray, B: np.ndarray, theta_cut: np.ndarray, floor_db: float = -25.0) -> float:
        """RMS difference (dB) between the full-sphere power and the BOR1 reconstruction from the cuts
        (|A|²cos²φ + |B|²sin²φ), over the region above `floor_db` — small = BOR1 assumption holds."""
        U = np.abs(self.Et) ** 2 + np.abs(self.Ep) ** 2
        a2 = np.interp(self.theta, theta_cut, np.abs(A) ** 2)
        b2 = np.interp(self.theta, theta_cut, np.abs(B) ** 2)
        ph = self.phi * DEG
        R = a2[:, None] * np.cos(ph)[None, :] ** 2 + b2[:, None] * np.sin(ph)[None, :] ** 2
        Un, Rn = U / U.max(), R / max(R.max(), 1e-30)
        m = 10 * np.log10(Un + 1e-30) > floor_db
        if not m.any():
            return float("nan")
        d = 10 * np.log10(Un[m] + 1e-30) - 10 * np.log10(Rn[m] + 1e-30)
        return float(np.sqrt(np.mean(d ** 2)))


@dataclass
class DeepResult:
    meta: dict
    freq_ghz: np.ndarray
    s11: np.ndarray
    zin: np.ndarray | None
    pacc: np.ndarray | None
    ff: list
    sphere: Sphere | None = None
    config: dict = field(default_factory=dict)
    geometry: dict = field(default_factory=dict)
    mesh: dict = field(default_factory=dict)
    timing: dict = field(default_factory=dict)
    path: str = ""

    @property
    def f0(self) -> float:
        return float(self.meta.get("f0_ghz") or self.ff[len(self.ff) // 2].f_ghz)

    def ff_at(self, f_ghz: float) -> FarField:
        return min(self.ff, key=lambda x: abs(x.f_ghz - f_ghz))

    @property
    def s11_db(self) -> np.ndarray:
        return 20 * np.log10(np.abs(self.s11) + 1e-15)


def load(path: str | Path) -> DeepResult:
    path = Path(path)
    if path.is_dir():
        path = path / "results.json"
    d = json.loads(path.read_text())
    freq = np.array(d["freq_ghz"], float)
    s11 = _cplx(d, "s11")
    zin = _cplx(d, "zin") if "zin_re" in d else None
    pacc = np.array(d["pacc"], float) if "pacc" in d else None
    ffs = []
    if d.get("ff"):
        for x in d["ff"]:
            ffs.append(FarField(float(x["f_ghz"]), np.array(x["theta"], float), np.array(x["phis"], float),
                                _cplx(x, "Et"), _cplx(x, "Ep"), float(x.get("Prad", np.nan)), float(x.get("Pacc", np.nan)),
                                float(x.get("Dmax_nf2ff_dbi", np.nan))))
    else:                                                   # v1 file: cuts at f0 only
        ffs.append(FarField(float(d["meta"]["f0_ghz"]), np.array(d["theta"], float),
                            np.array(d.get("phis", [0, 45, 90]), float), _cplx(d, "Et"), _cplx(d, "Ep"),
                            float(d.get("Prad", np.nan)), float("nan"), float(d.get("Dmax_dbi", np.nan))))
    sph = None
    if d.get("sphere"):
        x = d["sphere"]
        sph = Sphere(float(x["f_ghz"]), np.array(x["theta"], float), np.array(x["phi"], float), _cplx(x, "Et"),
                     _cplx(x, "Ep"), float(x.get("Prad", np.nan)), float(x.get("Pacc", np.nan)),
                     float(x.get("Dmax_dbi", np.nan)))
    return DeepResult(d.get("meta", {}), freq, s11, zin, pacc, ffs, sph, d.get("config", {}), d.get("geometry", {}),
                      d.get("mesh", {}), d.get("timing", {}), str(path))


# ------------------------------------------------------------------ metrics
def _band_around(f, ok, f0):
    """Contiguous interval around f0 where ok is True: (f_a, f_b) or None."""
    i0 = int(np.argmin(np.abs(f - f0)))
    if not ok[i0]:
        return None
    a = i0
    while a > 0 and ok[a - 1]:
        a -= 1
    b = i0
    while b < len(f) - 1 and ok[b + 1]:
        b += 1
    return float(f[a]), float(f[b]), bool(a == 0 or b == len(f) - 1)


def s11_metrics(r: DeepResult) -> dict:
    f, s = r.freq_ghz, r.s11
    db = r.s11_db
    f0 = r.f0
    s0 = np.interp(f0, f, s.real) + 1j * np.interp(f0, f, s.imag)
    g = abs(s0)
    i = int(np.argmin(db))
    out = {"s11_f0_db": 20 * math.log10(g + 1e-15), "rl_f0_db": -20 * math.log10(g + 1e-15),
           "vswr_f0": (1 + g) / (1 - g) if g < 1 else float("inf"), "s11_min_db": float(db[i]), "f_min_ghz": float(f[i]),
           "s11_max_band_db": float(db.max()), "mismatch_loss_f0_db": -10 * math.log10(max(1 - g * g, 1e-12))}
    for lvl in (15, 20):
        bw = _band_around(f, db <= -lvl, f0)
        out[f"bw{lvl}"] = None if bw is None else {"f_lo": bw[0], "f_hi": bw[1], "pct": 100 * (bw[1] - bw[0]) / f0,
                                                   "beyond_sweep": bw[2]}
    if r.zin is not None and np.all(np.isfinite(r.zin)):
        out["zin_f0"] = complex(np.interp(f0, f, r.zin.real), np.interp(f0, f, r.zin.imag))
    return out


def directivity_bor_dbi(p: Pattern) -> float:
    t = p.theta_deg * DEG
    P = math.pi * _trap((np.abs(p.E) ** 2 + np.abs(p.H) ** 2) * np.sin(t), t)
    U0 = 0.5 * (abs(p.E[0]) ** 2 + abs(p.H[0]) ** 2)
    return float(10 * math.log10(4 * math.pi * U0 / P)) if P > 0 else float("nan")


def pattern_metrics(ff: FarField) -> dict:
    p = ff.pattern()
    e_db, h_db = p.db()
    out = {"f_ghz": ff.f_ghz}
    for lvl in (3, 10, 15):
        aE = p.angle_at_level(-lvl, "E")
        aH = p.angle_at_level(-lvl, "H")
        out[f"bw{lvl}_E"], out[f"bw{lvl}_H"] = 2 * aE, 2 * aH
    out["eh_asym_deg"] = abs(out["bw10_E"] - out["bw10_H"])
    out["fb_db"] = float(-0.5 * (e_db[-1] + h_db[-1]))
    out["xpol_peak_db"] = ff.xpol_peak_db()
    co45, cr45 = ff.ludwig3(45.0)
    ref = max(np.abs(p.E).max(), np.abs(p.H).max(), 1e-30)
    out["xpol45_peak_db"] = float(20 * np.log10(np.abs(cr45).max() / ref + 1e-15))
    out["D_bor_dbi"] = directivity_bor_dbi(p)
    out["D_nf2ff_dbi"] = ff.Dmax_nf2ff_dbi
    out["rad_eff"] = ff.radiation_efficiency()
    return out


@dataclass
class DishSpec:
    kind: str = "offset"            # offset | prime
    D_mm: float = 600.0
    fD: float = 0.7                 # prime f/D or offset-equivalent f/D
    elev_deg: float = 30.0
    nf_db: float = 1.0
    zenith_db: float = 0.3
    rms_mm: float = 0.1
    line_loss_db: float = 0.0       # feed ohmic + feed→LNA line
    t_ground: float = 290.0
    block_diam_mm: float = 0.0      # feed + support blockage (prime focus)
    offset_spill_ground_frac: float = 0.25


def phase_center(p: Pattern, fD: float, lam_mm: float, block: float = 0.0) -> dict:
    """PHASEPAT search (coarse + fine) and the W1GHZ formula at the -10 dB angle of each plane."""
    d0, _ = efficiency.phase_center_by_efficiency(p, fD, span_lambda=3.0, step=0.02, block_diam_ratio=block)
    best = (d0, -1.0)
    for d in np.arange(d0 - 0.03, d0 + 0.0301, 0.002):
        e = efficiency.dish_efficiency(p.shifted(d), fD, block).total
        if e > best[1]:
            best = (float(d), e)
    out = {"d_lambda": best[0], "d_mm": best[0] * lam_mm, "eta_at_pc": best[1],
           "eta_at_aperture": efficiency.dish_efficiency(p, fD, block).total}
    for pl in ("E", "H"):
        a = p.angle_at_level(-10.0, pl)
        try:
            out[f"d_{pl}_mm"] = efficiency.phase_center_at_angle(p, a, pl) * lam_mm if np.isfinite(a) else float("nan")
        except Exception:
            out[f"d_{pl}_mm"] = float("nan")
    return out


def dish_performance(p: Pattern, f_ghz: float, dish: DishSpec) -> dict:
    """Efficiency (decomposed), gain, antenna temperature and G/T with the feed at its phase centre."""
    lam = C0 / (f_ghz * 1e9) * 1e3
    blk = dish.block_diam_mm / dish.D_mm if dish.kind == "prime" and dish.block_diam_mm else 0.0
    pc = phase_center(p, dish.fD, lam, blk)
    pp = p.shifted(pc["d_lambda"])
    e = efficiency.dish_efficiency(pp, dish.fD, blk)
    ruze = reflector.ruze(dish.rms_mm, lam)
    line = 10 ** (-dish.line_loss_db / 10)
    eta = e.total * ruze * line
    G = reflector.gain_dbi(dish.D_mm, lam, max(eta, 1e-9))
    tsky = noise.sky_temp(dish.elev_deg, dish.zenith_db, f_ghz=f_ghz)
    if dish.kind == "prime":
        ta = noise.antenna_temp_prime_focus(pp, dish.fD, dish.elev_deg, tsky, dish.t_ground, n_phi=72)
    else:
        spill_T = dish.offset_spill_ground_frac * dish.t_ground + (1 - dish.offset_spill_ground_frac) * tsky
        ta = e.spillover * tsky + (1 - e.spillover) * spill_T
    trx = noise.receiver_temp(dish.nf_db)
    tsys = ta * line + (1 - line) * 290.0 + trx
    curve = efficiency.efficiency_vs_fD(pp, np.arange(0.25, 1.505, 0.01), blk)
    best = max(curve, key=lambda x: x.total)
    beam = efficiency.dish_beam(pp, dish.fD, dish.D_mm, lam, blk)
    return {"phase_center": pc, "eff": e.as_dict(), "eta_total": eta, "hpbw_deg": beam.hpbw_deg,
            "hpbw_E_deg": beam.hpbw_E_deg, "hpbw_H_deg": beam.hpbw_H_deg, "sidelobe_db": beam.first_sidelobe_db, "ruze": ruze, "gain_dbi": G, "t_sky": tsky,
            "t_ant": ta, "t_rx": trx, "t_sys": tsys, "g_over_t_db": G - 10 * math.log10(tsys),
            "best_fD": best.fD, "best_eta": best.total,
            "curve": {"fD": [c.fD for c in curve], "total": [c.total for c in curve], "spill": [c.spillover for c in curve],
                      "illum": [c.illumination for c in curve], "phase": [c.phase for c in curve],
                      "pol": [c.polarization for c in curve]}}


def analyze(r: DeepResult, dish: DishSpec) -> dict:
    """Full deep analysis: match, every far-field frequency, dish performance, sphere checks."""
    out = {"label": r.meta.get("label") or r.meta.get("kind", ""), "kind": r.meta.get("kind", ""), "f0": r.f0,
           "s11": s11_metrics(r), "per_freq": [], "mesh": r.mesh, "timing": r.timing,
           "cells_per_lambda": r.config.get("cells_per_lambda")}
    for ff in r.ff:
        pm = pattern_metrics(ff)
        dp = dish_performance(ff.pattern(), ff.f_ghz, dish)
        pm.update({"eta_total": dp["eta_total"], "spill": dp["eff"]["spillover"], "illum": dp["eff"]["illumination"],
                   "phase": dp["eff"]["phase"], "pol": dp["eff"]["polarization"], "edge_taper_db": dp["eff"]["edge_taper_db"],
                   "pc_mm": dp["phase_center"]["d_mm"], "gain_dbi": dp["gain_dbi"], "g_over_t_db": dp["g_over_t_db"],
                   "t_ant": dp["t_ant"], "best_fD": dp["best_fD"]})
        out["per_freq"].append(pm)
    ff0 = r.ff_at(r.f0)
    out["f0_detail"] = dish_performance(ff0.pattern(), ff0.f_ghz, dish)
    # spread of the phase centre over the band (the feed can only sit in one place)
    pcs = [x["pc_mm"] for x in out["per_freq"]]
    out["pc_spread_mm"] = float(max(pcs) - min(pcs)) if pcs else float("nan")
    if r.sphere is not None:
        A, _ = ff0.ludwig3(0)
        B, _ = ff0.ludwig3(90)
        out["sphere"] = {"D_dbi": r.sphere.directivity_dbi(), "D_nf2ff_dbi": r.sphere.Dmax_nf2ff_dbi,
                         "bor_dev_db": r.sphere.bor_deviation_db(A, B, ff0.theta),
                         "rad_eff": (r.sphere.Prad / r.sphere.Pacc) if r.sphere.Pacc and r.sphere.Pacc > 0 else float("nan")}
    out["empty_far_field"] = bool(r.ff) and all(not np.any(np.abs(f.Et)) and not np.any(np.abs(f.Ep)) for f in r.ff)
    out["warnings"] = warnings(out)
    return out


def warnings(a: dict) -> list[str]:
    w = []
    s = a["s11"]
    if s["s11_f0_db"] > -15:
        w.append(f"Adattamento scarso a f0: S11 {s['s11_f0_db']:.1f} dB (VSWR {s['vswr_f0']:.2f}). "
                 "Verifica la transizione d'ingresso o le quote del gradino/flare.")
    if s.get("bw20") and s["bw20"]["beyond_sweep"]:
        w.append("La banda a -20 dB esce dallo sweep simulato: allarga la banda per misurarla.")
    sph = a.get("sphere")
    if sph and np.isfinite(sph.get("rad_eff", np.nan)) and not 0.9 < sph["rad_eff"] < 1.1:
        w.append(f"Potenza irradiata / accettata = {sph['rad_eff']:.2f}: la simulazione non è ben convergente "
                 "(energia residua, mesh grossolana o NF2FF troppo vicino al feed). Aumenta celle/λ o la soglia di fine.")
    if sph and np.isfinite(sph.get("bor_dev_db", np.nan)) and sph["bor_dev_db"] > 1.0:
        w.append(f"Il lobo si discosta dall'ipotesi BOR1 di {sph['bor_dev_db']:.1f} dB RMS: l'efficienza calcolata "
                 "dai soli tagli E/H è approssimata (modi superiori o asimmetrie).")
    if a.get("empty_far_field"):
        w.insert(0, "Diagrammi di radiazione vuoti (tutti zero): file results.json di FeedLab fino alla 0.4.10, che "
                    "arrotondava il campo lontano. S11 è valido. Rigenera lo script con questa versione e lancialo "
                    "con --post nella stessa cartella: ricalcola i diagrammi da sim_data in pochi secondi.")
    f0 = [x for x in a["per_freq"] if abs(x["f_ghz"] - a["f0"]) < 1e-6]
    if f0 and f0[0]["xpol_peak_db"] > -20:
        w.append(f"Cross-polare di picco {f0[0]['xpol_peak_db']:.1f} dB: alta per EME/polarizzazione circolare.")
    if np.isfinite(a.get("pc_spread_mm", np.nan)) and a["pc_spread_mm"] > 0.25 * C0 / (a["f0"] * 1e9) * 1e3:
        w.append(f"Il centro di fase si sposta di {a['pc_spread_mm']:.1f} mm nella banda (> λ/4).")
    return w


# ------------------------------------------------------------------ comparisons
def compare(results: list[tuple[str, DeepResult]], dish: DishSpec) -> list[dict]:
    """One row per run, for mesh-convergence studies and parameter sweeps."""
    rows = []
    for label, r in results:
        a = analyze(r, dish)
        f0 = min(a["per_freq"], key=lambda x: abs(x["f_ghz"] - a["f0"]))
        rows.append({"label": label, "cells_per_lambda": r.config.get("cells_per_lambda"),
                     "cells_M": (r.mesh.get("cells") or 0) / 1e6, "time_min": (r.timing.get("total_s") or 0) / 60,
                     "s11_f0_db": a["s11"]["s11_f0_db"], "s11_max_band_db": a["s11"]["s11_max_band_db"],
                     "D_dbi": (a.get("sphere") or {}).get("D_dbi", f0["D_bor_dbi"]), "eta": f0["eta_total"],
                     "pc_mm": f0["pc_mm"], "xpol_db": f0["xpol_peak_db"], "bw10_E": f0["bw10_E"], "bw10_H": f0["bw10_H"],
                     "gain_dbi": f0["gain_dbi"], "g_over_t_db": f0["g_over_t_db"], "params": r.meta.get("params", {})})
    return rows


def convergence(rows: list[dict]) -> dict:
    """Differences of each run from the finest mesh; converged if the last step changes little."""
    rows = sorted([r for r in rows if r.get("cells_per_lambda")], key=lambda r: r["cells_per_lambda"])
    if len(rows) < 2:
        return {"ok": None, "rows": rows}
    ref = rows[-1]
    for r in rows:
        r["d_s11_db"] = r["s11_f0_db"] - ref["s11_f0_db"]
        r["d_D_db"] = r["D_dbi"] - ref["D_dbi"]
        r["d_eta_pct"] = 100 * (r["eta"] - ref["eta"])
        r["d_pc_mm"] = r["pc_mm"] - ref["pc_mm"]
    last = rows[-2]
    ok = abs(last["d_D_db"]) < 0.1 and abs(last["d_eta_pct"]) < 0.5 and abs(last["d_s11_db"]) < 2.0
    return {"ok": ok, "rows": rows}


def compare_fast_model(r: DeepResult) -> dict | None:
    """FeedLab's mode-matching S11 on the same geometry (rebuilt from the saved parameters), when applicable."""
    from . import geometry, modematch
    kind = r.meta.get("kind")
    if kind not in geometry.MODEMATCH_OK:
        return None
    g = r.geometry
    try:
        prof_secs = _sections_from_polys(g)
        mm = modematch.simulate(prof_secs, np.linspace(r.freq_ghz[0], r.freq_ghz[-1], 21), n_modes=12)
        return {"freq_ghz": mm.f_ghz, "s11_db": mm.s11_db}
    except Exception:
        return None


def _sections_from_polys(g: dict) -> list[tuple[float, float]]:
    """Inner wall of the first polygon (the horn wall) → staircase [(r, L)] for mode matching."""
    r_list, z_list = g["polys"][0]
    pts = list(zip(z_list, r_list))
    n = len(pts)
    # the wall polygon starts with the inner profile (increasing z), then the outer one going back
    inner = [pts[0]]
    for z, r in pts[1:n]:
        if z + 1e-9 < inner[-1][0]:
            break
        inner.append((z, r))
    lam = C0 / (g["f0_ghz"] * 1e9) * 1e3
    secs = []
    for (z0, r0), (z1, r1) in zip(inner[:-1], inner[1:]):
        L = z1 - z0
        if L <= 1e-9:
            continue
        k = max(1, int(math.ceil(L / (lam / 30)))) if abs(r1 - r0) > 1e-9 else 1
        for i in range(k):
            secs.append((r0 + (r1 - r0) * (i + 0.5) / k, L / k))
    return secs


# ------------------------------------------------------------------ exports
def export_csv(r: DeepResult, folder: str | Path) -> list[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    p = folder / "s11.csv"
    with open(p, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["f_GHz", "S11_dB", "S11_phase_deg", "Zin_re_ohm", "Zin_im_ohm"])
        for i, f in enumerate(r.freq_ghz):
            z = r.zin[i] if r.zin is not None else complex("nan")
            w.writerow([f"{f:.6f}", f"{r.s11_db[i]:.4f}", f"{np.degrees(np.angle(r.s11[i])):.3f}", f"{z.real:.4f}", f"{z.imag:.4f}"])
    out.append(p)
    for ff in r.ff:
        p = folder / f"cuts_{ff.f_ghz:g}GHz.csv"
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            hdr = ["theta_deg"]
            cols = []
            for ph in ff.phis:
                co, cr = ff.ludwig3(ph)
                hdr += [f"co_phi{ph:g}_dB", f"co_phi{ph:g}_phase", f"x_phi{ph:g}_dB"]
                cols.append((co, cr))
            ref = max(np.abs(c[0]).max() for c in cols)
            w.writerow(hdr)
            for i, t in enumerate(ff.theta):
                row = [f"{t:g}"]
                for co, cr in cols:
                    row += [f"{20 * np.log10(abs(co[i]) / ref + 1e-15):.3f}", f"{np.degrees(np.angle(co[i])):.2f}",
                            f"{20 * np.log10(abs(cr[i]) / ref + 1e-15):.3f}"]
                w.writerow(row)
        out.append(p)
    return out


def export_dat(r: DeepResult, folder: str | Path) -> list[Path]:
    """W1GHZ FEEDPATT/PHASEPAT files (E and H plane, phase referred to the aperture plane)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for ff in r.ff:
        pre = folder / f"{r.meta.get('kind', 'feed')}_{ff.f_ghz:g}GHz"
        save_w1ghz_dat(ff.pattern(f"openEMS {r.meta.get('kind', '')} {ff.f_ghz:g} GHz"), pre)
        out += [Path(f"{pre}_e.dat"), Path(f"{pre}_h.dat")]
    return out


def _fig_png(fig) -> str:
    from . import i18n
    i18n.translate_figure_mpl(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def figures(r: DeepResult, a: dict) -> dict[str, str]:
    """Matplotlib figures (base64 PNG) for the HTML report."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figs = {}
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.plot(r.freq_ghz, r.s11_db, lw=1.6, label="openEMS")
    fm = compare_fast_model(r)
    if fm:
        ax.plot(fm["freq_ghz"], fm["s11_db"], "--", lw=1.2, label="FeedLab mode matching")
    for lvl in (-15, -20):
        ax.axhline(lvl, color="0.7", lw=0.8, ls=":")
    ax.axvline(r.f0, color="0.6", lw=0.8)
    ax.set_xlabel("GHz"); ax.set_ylabel("S11 (dB)"); ax.grid(alpha=0.3); ax.legend()
    figs["s11"] = _fig_png(fig)
    ff0 = r.ff_at(r.f0)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    ref = max(np.abs(ff0.ludwig3(0)[0]).max(), np.abs(ff0.ludwig3(90)[0]).max())
    for ph, col in ((0, "C3"), (45, "C2"), (90, "C0")):
        co, cr = ff0.ludwig3(ph)
        axs[0].plot(ff0.theta, 20 * np.log10(np.abs(co) / ref + 1e-12), color=col, label=f"co φ={ph}°")
        if ph == 45:
            axs[0].plot(ff0.theta, 20 * np.log10(np.abs(cr) / ref + 1e-12), color=col, ls="--", label="cross φ=45°")
    axs[0].set_ylim(-45, 1); axs[0].set_xlim(0, 180); axs[0].set_xlabel("θ (°)"); axs[0].set_ylabel("dB")
    axs[0].grid(alpha=0.3); axs[0].legend(fontsize=8); axs[0].set_title(f"Lobo a {ff0.f_ghz:g} GHz (Ludwig-3)")
    pp = ff0.pattern().shifted(a["f0_detail"]["phase_center"]["d_lambda"])
    for v, col, n in ((pp.E, "C3", "E"), (pp.H, "C0", "H")):
        axs[1].plot(pp.theta_deg, np.degrees(np.angle(v * np.conj(v[0]))), color=col, label=f"piano {n}")
    axs[1].set_xlim(0, 120); axs[1].set_ylim(-180, 180); axs[1].set_xlabel("θ (°)"); axs[1].set_ylabel("fase (°)")
    axs[1].grid(alpha=0.3); axs[1].legend(fontsize=8); axs[1].set_title("Fase riferita al centro di fase")
    figs["pattern"] = _fig_png(fig)
    c = a["f0_detail"]["curve"]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for k, n, st in (("total", "totale", "-"), ("spill", "spillover", "--"), ("illum", "illuminazione", "--"),
                     ("phase", "fase", ":"), ("pol", "polarizzazione", ":")):
        ax.plot(c["fD"], np.array(c[k]) * 100, st, label=n, lw=1.8 if k == "total" else 1.1)
    ax.set_xlabel("f/D"); ax.set_ylabel("%"); ax.set_ylim(40, 101); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax.set_title("Efficienza vs f/D (feed nel centro di fase)")
    figs["eff"] = _fig_png(fig)
    return figs


def html_report(r: DeepResult, a: dict, dish: DishSpec, path: str | Path) -> Path:
    figs = figures(r, a)
    s = a["s11"]
    d0 = a["f0_detail"]

    def f(x, n=2):
        return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{n}f}"
    rows = "".join(
        f"<tr><td>{x['f_ghz']:g}</td><td>{f(x['bw10_E'], 1)}</td><td>{f(x['bw10_H'], 1)}</td><td>{f(x['xpol_peak_db'], 1)}</td>"
        f"<td>{f(x['D_bor_dbi'])}</td><td>{f(x['pc_mm'])}</td><td>{f(100 * x['eta_total'], 1)}</td><td>{f(x['gain_dbi'])}</td>"
        f"<td>{f(x['g_over_t_db'])}</td></tr>" for x in a["per_freq"])
    bw = lambda b: "—" if not b else f"{b['f_lo']:.3f}–{b['f_hi']:.3f} GHz ({b['pct']:.1f}%{'+' if b['beyond_sweep'] else ''})"  # noqa: E731
    warn = "".join(f"<li>{w}</li>" for w in a["warnings"]) or "<li>Nessuna anomalia rilevata.</li>"
    sph = a.get("sphere") or {}
    e = d0["eff"]
    html = f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><title>FeedLab deep analysis</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:980px;margin:24px auto;padding:0 16px;color:#222}}
h1{{font-size:22px}}h2{{font-size:17px;margin-top:28px;border-bottom:1px solid #ddd}}table{{border-collapse:collapse;font-size:13px}}
td,th{{border:1px solid #ccc;padding:4px 8px;text-align:right}}th{{background:#f3f3f3}}img{{max-width:100%}}.k{{text-align:left}}</style>
</head><body><h1>FeedLab — deep analysis openEMS: {a['label']} @ {a['f0']:g} GHz</h1>
<p>Parabola {dish.kind}, D {dish.D_mm:.0f} mm, f/D {dish.fD:.3f}; mesh {a.get('cells_per_lambda')} celle/λ,
{(a['mesh'].get('cells') or 0) / 1e6:.2f} M celle; durata {(a['timing'].get('total_s') or 0) / 60:.1f} min.</p>
<h2>Avvisi</h2><ul>{warn}</ul>
<h2>Adattamento</h2><img src="data:image/png;base64,{figs['s11']}">
<table><tr><th class=k>S11 a f0</th><td>{f(s['s11_f0_db'], 1)} dB</td><th class=k>VSWR</th><td>{f(s['vswr_f0'])}</td></tr>
<tr><th class=k>S11 minimo</th><td>{f(s['s11_min_db'], 1)} dB a {s['f_min_ghz']:.3f} GHz</td><th class=k>S11 peggiore in banda</th><td>{f(s['s11_max_band_db'], 1)} dB</td></tr>
<tr><th class=k>Banda S11 &lt; −15 dB</th><td>{bw(s['bw15'])}</td><th class=k>Banda S11 &lt; −20 dB</th><td>{bw(s['bw20'])}</td></tr></table>
<h2>Lobo e fase</h2><img src="data:image/png;base64,{figs['pattern']}">
<table><tr><th>GHz</th><th>−10 dB E (°)</th><th>−10 dB H (°)</th><th>X-pol picco (dB)</th><th>D BOR (dBi)</th>
<th>Centro di fase (mm)</th><th>η (%)</th><th>G (dBi)</th><th>G/T (dB/K)</th></tr>{rows}</table>
<p>Centro di fase: + = davanti al piano d'apertura (verso il riflettore). Formula W1GHZ a −10 dB:
E {f(d0['phase_center'].get('d_E_mm'))} mm, H {f(d0['phase_center'].get('d_H_mm'))} mm.
Spostamento nella banda: {f(a['pc_spread_mm'])} mm.</p>
<p>Sfera completa: D {f(sph.get('D_dbi'))} dBi; P irr./P acc. {f(sph.get('rad_eff'))}; scostamento dall'ipotesi BOR1 {f(sph.get('bor_dev_db'))} dB RMS.</p>
<h2>Sulla parabola (f0)</h2><img src="data:image/png;base64,{figs['eff']}">
<table><tr><th class=k>Efficienza totale</th><td>{f(100 * d0['eta_total'], 1)} %</td><th class=k>Spillover</th><td>{f(100 * e['spillover'], 1)} %</td></tr>
<tr><th class=k>Illuminazione</th><td>{f(100 * e['illumination'], 1)} %</td><th class=k>Fase</th><td>{f(100 * e['phase'], 1)} %</td></tr>
<tr><th class=k>Polarizzazione</th><td>{f(100 * e['polarization'], 1)} %</td><th class=k>Bloccaggio</th><td>{f(100 * e['blockage'], 1)} %</td></tr>
<tr><th class=k>Taper al bordo</th><td>{f(e['edge_taper_db'], 1)} dB</td><th class=k>f/D ottimo</th><td>{f(d0['best_fD'])} (η {f(100 * d0['best_eta'], 1)} %)</td></tr>
<tr><th class=k>Guadagno</th><td>{f(d0['gain_dbi'])} dBi</td><th class=k>T antenna</th><td>{f(d0['t_ant'], 1)} K (cielo {f(d0['t_sky'], 1)} K)</td></tr>
<tr><th class=k>HPBW parabola (E / H)</th><td>{f(d0['hpbw_E_deg'], 3)}° / {f(d0['hpbw_H_deg'], 3)}°</td>
<th class=k>Primo lobo laterale</th><td>{f(d0['sidelobe_db'], 1)} dB</td></tr>
<tr><th class=k>T sistema</th><td>{f(d0['t_sys'], 1)} K</td><th class=k>G/T</th><td>{f(d0['g_over_t_db'])} dB/K</td></tr></table>
<p style="color:#777;font-size:12px">Generato da FeedLab. Simulazione FDTD openEMS; efficienza con il metodo
Kildal/W1GHZ sui tagli E/H (ipotesi BOR1).</p></body></html>"""
    from . import i18n
    html = i18n.tr(html).replace('<html lang="it">', f'<html lang="{i18n.get_lang()}">')
    path = Path(path)
    path.write_text(html, encoding="utf-8")
    return path
