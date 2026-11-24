# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Feed synthesis: smooth-wall profiled horns found by global optimisation with the fast mode-matching solver.

Instead of starting from a published design, the inner wall is a free monotone profile (PCHIP spline through
a few control radii, everything in wavelengths) with an optional input step that launches TM11. The objective
is the EME figure for a given dish (gain + G/T, the own-echo SNR), with S11 kept low over the band.
Dimensions in λ make the result valid for every band with the same dish f/D.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from . import explore, geometry, modematch
from .waveguide import wavelength_mm

# parameter vector (all in wavelengths): Di, Ds, Ls, L, and K radius increments (fractions of the remaining growth)
K = 6
BOUNDS = [(0.70, 0.80),      # Di: input guide diameter (TE11 only)
          (0.80, 1.20),      # Ds: diameter after the input step (= Di: no step)
          (0.00, 0.60),      # Ls: length of the stepped section before the profile starts
          (1.5, 7.0),        # L: profiled length
          (1.0, 2.6)]        # Dap: aperture diameter
BOUNDS += [(0.0, 1.0)] * K   # shape: relative heights of the control points (made monotone)


@dataclass
class Profile:
    Di: float
    Ds: float
    Ls: float
    L: float
    Dap: float
    shape: tuple

    def points_lambda(self, n: int = 60):
        """Inner wall [(z, r)] in wavelengths: input guide, step, smooth profile to the aperture."""
        from scipy.interpolate import PchipInterpolator
        Ds = max(self.Ds, self.Di)
        Dap = max(self.Dap, Ds)
        w = np.cumsum(np.maximum(np.asarray(self.shape, float), 1e-3))
        w = w / w[-1]                                    # monotone 0…1 at the control points
        zc = np.linspace(0, self.L, len(w) + 1)
        rc = np.concatenate([[Ds / 2], Ds / 2 + (Dap - Ds) / 2 * w])
        sp = PchipInterpolator(zc, rc)
        zin = 0.6
        pts = [(0.0, self.Di / 2), (zin, self.Di / 2)]
        if Ds > self.Di + 1e-4:
            pts.append((zin, Ds / 2))
        z0 = zin + self.Ls
        if self.Ls > 1e-4:
            pts.append((z0, Ds / 2))
        for z in np.linspace(0, self.L, n)[1:]:
            pts.append((z0 + float(z), float(sp(z))))
        return pts


def vec_to_profile(x) -> Profile:
    return Profile(*[float(v) for v in x[:5]], tuple(float(v) for v in x[5:]))


def geometry_for(p: Profile, f_ghz: float, wall: float | None = None) -> geometry.FeedGeometry:
    lam = wavelength_mm(f_ghz)
    prof = [(z * lam, r * lam) for z, r in p.points_lambda()]
    t = wall if wall is not None else geometry.wall_default(f_ghz)
    params = {"Di_input": p.Di * lam, "Ds_step": max(p.Ds, p.Di) * lam, "Ls": p.Ls * lam, "L_profile": p.L * lam,
              "D_aperture": max(p.Dap, p.Ds, p.Di) * lam, "length": prof[-1][0], "wall": t}
    return geometry._finish("eme_profiled", f_ghz, params, prof, t, flange=False,
                            notes=["profilo liscio sintetizzato da FeedLab (ottimizzazione globale, mode matching)"])


def evaluate(p: Profile, f_ghz: float, sc: explore.Scenario, band: float = 0.01):
    """EME figure at f0 and S11 over f0·(1 ± band)."""
    geo = geometry_for(p, f_ghz)
    lam = wavelength_mm(f_ghz)
    secs = geo.staircase(lam / 20)
    fl = [f_ghz * (1 - band), f_ghz, f_ghz * (1 + band)]
    r = modematch.simulate(secs, fl, n_modes=10)
    pat = modematch.aperture_pattern(r, 1, f_ghz, n_rho=28, n_phi=32, n_theta=181)
    res = explore.performance("eme_profiled", f_ghz, sc, geo, pat, float(r.s11_db[1]), r.aperture_modes[1])
    return res, float(np.max(r.s11_db)), geo


S11_MAX = -25.0


def cost(x, f_ghz, sc_kw):
    sc = explore.Scenario(**sc_kw)
    try:
        res, s11w, geo = evaluate(vec_to_profile(x), f_ghz, sc)
    except Exception:
        return 1e3
    val = -(res.gain_dbi + res.g_over_t)
    if s11w > S11_MAX:
        val += 0.3 * (s11w - S11_MAX)
    if geo.length > 9 * wavelength_mm(f_ghz):                 # keep it machinable / not too long
        val += 0.2 * (geo.length / wavelength_mm(f_ghz) - 9)
    return val


# ------------------------------------------------------------------ search around a known family (IZ0JNY Dual-Flare)
DF_KEYS = ["Di", "Ds", "Ls", "Dm", "L1", "Lp", "Dap", "L2"]


def df_params(x, lam):
    return {k: float(v) * lam for k, v in zip(DF_KEYS, x)}


def df_evaluate(x, f_ghz, sc: explore.Scenario, fD_design: float, band: float = 0.01):
    lam = wavelength_mm(f_ghz)
    geo = geometry.build("iz0jny", f_ghz, fD=fD_design, **df_params(x, lam))
    secs = geo.staircase(lam / 20)
    r = modematch.simulate(secs, [f_ghz * (1 - band), f_ghz, f_ghz * (1 + band)], n_modes=10)
    pat = modematch.aperture_pattern(r, 1, f_ghz, n_rho=28, n_phi=32, n_theta=181)
    res = explore.performance("iz0jny", f_ghz, sc, geo, pat, float(r.s11_db[1]), r.aperture_modes[1])
    return res, float(np.max(r.s11_db)), geo


def df_cost(x, f_ghz, sc_kw, fD_design, w_gt: float = 1.0, w_g: float = 1.0):
    try:
        res, s11w, geo = df_evaluate(x, f_ghz, explore.Scenario(**sc_kw), fD_design)
    except Exception:
        return 1e3
    val = -(w_g * res.gain_dbi + w_gt * res.g_over_t)
    if s11w > S11_MAX:
        val += 0.3 * (s11w - S11_MAX)
    return val


# ------------------------------------------------------------------ conical corrugated horn (radial slots)
# x = [Dap, half-angle (deg), pitch, tooth fraction, slot depth in the flare, n converter slots, Di]  (λ units)
CG_BOUNDS = [(1.6, 3.2), (6.0, 30.0), (0.18, 0.33), (0.15, 0.45), (0.22, 0.32), (3, 7), (0.72, 0.80)]


def corrugated_profile(x):
    """Inner wall [(z, r)] in λ: input guide Di, a mode converter whose slot depth goes from ~λ/2 to the flare
    depth (TE11 → HE11), then a conical flare with constant-depth slots up to the aperture Dap."""
    Dap, half, p, tf, depth, nconv, Di = x
    nconv = int(round(nconv))
    t = tf * p                                   # tooth width
    w = p - t                                    # slot width
    r_in = Di / 2
    ta = math.tan(math.radians(half))
    L = max((Dap / 2 - r_in) / ta, p * (nconv + 2))
    nslots = max(int(L / p), nconv + 2)
    pts = [(0.0, r_in), (0.6, r_in)]
    z = 0.6
    for k in range(nslots):
        r = r_in + ta * (k * p)                   # inner (tooth) radius along the flare
        d = 0.5 - (0.5 - depth) * k / nconv if k < nconv else depth
        r_slot = r + d
        pts += [(z, r), (z + t, r), (z + t, r_slot), (z + t + w, r_slot), (z + t + w, r + ta * p)]
        z += p
    pts.append((z, r_in + ta * nslots * p))
    return pts


def cg_geometry(x, f_ghz):
    lam = wavelength_mm(f_ghz)
    prof = [(z * lam, r * lam) for z, r in corrugated_profile(x)]
    t = geometry.wall_default(f_ghz)
    params = {"D_aperture": 2 * prof[-1][1], "Di_input": x[6] * lam, "flare_half_deg": x[1], "pitch": x[2] * lam,
              "tooth": x[3] * x[2] * lam, "depth": x[4] * lam, "n_conv": int(round(x[5])), "length": prof[-1][0], "wall": t}
    return geometry._finish("eme_corrugated", f_ghz, params, prof, t, flange=False,
                            notes=["horn corrugato conico sintetizzato da FeedLab (mode matching)"])


def cg_evaluate(x, f_ghz, sc, band: float = 0.01, n_modes: int = 14):
    geo = cg_geometry(x, f_ghz)
    lam = wavelength_mm(f_ghz)
    secs = geo.staircase(lam / 20)
    r = modematch.simulate(secs, [f_ghz * (1 - band), f_ghz, f_ghz * (1 + band)], n_modes=n_modes)
    pat = modematch.aperture_pattern(r, 1, f_ghz, n_rho=28, n_phi=32, n_theta=181)
    res = explore.performance("eme_corrugated", f_ghz, sc, geo, pat, float(r.s11_db[1]), r.aperture_modes[1])
    return res, float(np.max(r.s11_db)), geo


def cg_cost(x, f_ghz, sc_kw):
    try:
        res, s11w, geo = cg_evaluate(x, f_ghz, explore.Scenario(**sc_kw))
    except Exception:
        return 1e3
    val = -(res.gain_dbi + res.g_over_t)
    if s11w > S11_MAX:
        val += 0.3 * (s11w - S11_MAX)
    lam = wavelength_mm(f_ghz)
    if geo.length > 12 * lam:
        val += 0.2 * (geo.length / lam - 12)
    return val
