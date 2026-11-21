"""Cassegrain sub-reflector design (W1GHZ 'Multiple reflector antennas' 2004 + Cassegrain_design.xls,
formulas re-derived and checked against the spreadsheet example; Kildal 1983 optimum sub size)."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .reflector import half_angle_from_fD

DEG = math.pi / 180.0


def kildal_optimum_taper_db(D_lambda: float) -> float:
    """Approximation of Kildal's curve: ~14 dB for small dishes → ~11 dB for very large ones.
    Anchored at W1GHZ example (84λ → 12.36 dB). Rough interpolation in log(D)."""
    pts = np.array([[20, 14.0], [84.26, 12.36], [300, 11.5], [1000, 11.0]])
    return float(np.interp(math.log10(D_lambda), np.log10(pts[:, 0]), pts[:, 1]))


def kildal_optimum_sub_ratio(D_lambda: float, psi_feed_deg: float, phi0_deg: float, taper_db: float) -> float:
    """(d/D)^5 = cos^4(psi/2) * E * lambda / ((4 pi)^2 sin(phi0) D), E = 10^(-T/10)."""
    E = 10 ** (-taper_db / 10)
    v = math.cos(psi_feed_deg * DEG / 2) ** 4 * E / ((4 * math.pi) ** 2 * math.sin(phi0_deg * DEG) * D_lambda)
    return v ** 0.2


@dataclass
class Cassegrain:
    D: float; fD: float; f: float
    d_sub: float
    psi_feed_deg: float
    phi0_deg: float
    M: float; e: float; a: float; b: float; c: float
    apex_to_focus: float      # c - a
    apex_to_feed_pc: float    # c + a
    feed_shadow_half_deg: float
    sub_shadow_half_deg: float
    rayleigh_ok: bool

    def profile(self, n: int = 101) -> np.ndarray:
        """Hyperbola profile: columns (r, z) with r radial from axis (0..d/2) and z sag measured from
        the sub apex toward the main reflector focus side (positive away from feed)."""
        r = np.linspace(0, self.d_sub / 2, n)
        # hyperbola: z'^2/a^2 - r^2/b^2 = 1 ; apex at z' = a
        z = self.a * np.sqrt(1 + (r / self.b) ** 2) - self.a
        return np.column_stack([r, z])

    def gcode(self, n: int = 101, feed_mm_min: float = 50) -> str:
        """Simple lathe G-code (X = radius*2 diameter mode off, Z = sag)."""
        lines = ["G21 G90 (FeedLab Cassegrain sub)", f"F{feed_mm_min}"]
        for r, z in self.profile(n):
            lines.append(f"G01 X{r:.4f} Z{-z:.4f}")
        lines.append("M30")
        return "\n".join(lines)


def design_cassegrain(D: float, fD: float, lam: float, feed_fD_equiv: float | None = None,
                      psi_feed_deg: float | None = None, feed_diam: float = 0.0, feed_pc: float = 0.0,
                      taper_db: float | None = None, d_sub: float | None = None) -> Cassegrain:
    """All lengths in the same unit (e.g. mm). feed_pc: phase-centre offset (negative = inside horn).
    Provide either psi_feed_deg (feed half-angle at the chosen taper, from its pattern) or feed_fD_equiv."""
    f = fD * D
    phi0 = half_angle_from_fD(fD)
    if psi_feed_deg is None:
        psi_feed_deg = half_angle_from_fD(feed_fD_equiv)
    if taper_db is None:
        taper_db = kildal_optimum_taper_db(D / lam)
    K = 0.5 * (1 / math.tan(phi0 * DEG) + 1 / math.tan(psi_feed_deg * DEG))
    if d_sub is None:
        d_opt = kildal_optimum_sub_ratio(D / lam, psi_feed_deg, phi0, taper_db) * D
        d_noblock = math.sqrt(feed_diam * f / K) if feed_diam > 0 else 0.0
        d_sub = max(d_opt, d_noblock, 10 * lam * 0)  # user may override
    two_c = d_sub * K
    c = two_c / 2
    M = math.tan(phi0 * DEG / 2) / math.tan(psi_feed_deg * DEG / 2)
    e = (M + 1) / (M - 1)
    a = c / e
    b = math.sqrt(c * c - a * a)
    feed_shadow = math.atan(feed_diam / (2 * (two_c + feed_pc))) / DEG if feed_diam else 0.0
    sub_shadow = math.asin(min(1.0, d_sub / (2 * f))) / DEG
    rayleigh_ok = (c + a) >= 0.5 * 2 * feed_diam ** 2 / lam if feed_diam else True
    return Cassegrain(D, fD, f, d_sub, psi_feed_deg, phi0, M, e, a, b, c, c - a, c + a,
                      feed_shadow, sub_shadow, rayleigh_ok)
