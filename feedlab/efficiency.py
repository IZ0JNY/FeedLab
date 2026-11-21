"""Reflector efficiency from a feed pattern (W1GHZ FEEDPATT/PHASEPAT method generalised, Kildal form).

For a BOR1 feed with co-polar cuts A(theta) (E-plane) and B(theta) (H-plane), normalised so that the
total radiated power integrates to 4*pi (directivity units):
    eta_ap = | pi * int_{theta_b}^{psi0} (A + B) tan(theta/2) dtheta |^2 / (4 pi^2 tan^2(psi0/2))
which includes illumination, spillover, phase, cross-polar (Ludwig-3) and central blockage losses.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .patterns import Pattern
from .reflector import half_angle_from_fD, fD_from_half_angle

DEG = math.pi / 180.0


def _trap(y, x):
    return np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x)


@dataclass
class Efficiency:
    fD: float
    psi0_deg: float
    total: float
    spillover: float
    illumination: float      # amplitude taper only
    phase: float
    polarization: float
    blockage: float
    edge_taper_db: float     # feed level + space attenuation at the rim

    def as_dict(self):
        return self.__dict__.copy()


def _normalise(p: Pattern):
    t = p.theta_deg * DEG
    A, B = p.E, p.H
    ptot = math.pi * _trap((np.abs(A) ** 2 + np.abs(B) ** 2) * np.sin(t), t)
    s = math.sqrt(4 * math.pi / ptot)
    return t, A * s, B * s


def dish_efficiency(p: Pattern, fD: float, block_diam_ratio: float = 0.0) -> Efficiency:
    """Efficiency of a prime-focus (or equivalent offset) reflector of given f/D.
    block_diam_ratio = blocking diameter / dish diameter (0 for offset)."""
    t, A, B = _normalise(p)
    psi0 = half_angle_from_fD(fD) * DEG
    th_b = 2 * math.atan(block_diam_ratio / (4 * fD)) if block_diam_ratio > 0 else 0.0
    m = t <= psi0 + 1e-12
    tt, AA, BB = t[m], A[m], B[m]
    co = AA + BB                                  # pi*(A+B) = phi-integral of co-pol
    w = np.tan(tt / 2)
    num_full = math.pi * _trap(co * w, tt)
    mb = tt >= th_b
    num_blk = math.pi * _trap((co * w)[mb], tt[mb]) if th_b > 0 else num_full
    tan2 = math.tan(psi0 / 2) ** 2
    total = abs(num_blk) ** 2 / (4 * math.pi ** 2 * tan2)
    # decomposition
    p_in = math.pi * _trap((np.abs(AA) ** 2 + np.abs(BB) ** 2) * np.sin(tt), tt)      # power on dish
    spill = p_in / (4 * math.pi)
    # co-pol and x-pol (Ludwig-3) power on dish, phi-integrated:
    # co = pi/4*(3|A|^2+3|B|^2+2Re(AB*)), x = pi/4*|A-B|^2
    cop = (math.pi / 4) * _trap((3 * np.abs(AA) ** 2 + 3 * np.abs(BB) ** 2 + 2 * np.real(AA * np.conj(BB))) * np.sin(tt), tt)
    xp = (math.pi / 4) * _trap(np.abs(AA - BB) ** 2 * np.sin(tt), tt)
    pol = cop / (cop + xp) if cop + xp > 0 else 1.0
    num_amp = math.pi * _trap(np.abs(co) * w, tt)
    phase = abs(num_full) ** 2 / num_amp ** 2 if num_amp > 0 else 1.0
    illum = (num_amp ** 2 / (4 * math.pi ** 2 * tan2)) / (spill * pol) if spill * pol > 0 else 0.0
    block = abs(num_blk) ** 2 / abs(num_full) ** 2 if abs(num_full) > 0 else 1.0
    # edge taper (feed level at rim, average of planes) + space attenuation
    pe = np.interp(psi0, t, np.abs(A) ** 2); ph = np.interp(psi0, t, np.abs(B) ** 2)
    p0 = 0.5 * (abs(A[0]) ** 2 + abs(B[0]) ** 2)
    feed_lvl = -10 * math.log10(max(0.5 * (pe + ph), 1e-30) / p0)
    space = -20 * math.log10(math.cos(psi0 / 2) ** 2)
    return Efficiency(fD, psi0 / DEG, total, spill, illum, phase, pol, block, feed_lvl + space)


def efficiency_vs_fD(p: Pattern, fDs=None, block_diam_ratio: float = 0.0) -> list[Efficiency]:
    fDs = np.arange(0.25, 2.01, 0.01) if fDs is None else fDs
    return [dish_efficiency(p, float(f), block_diam_ratio) for f in fDs]


def best_fD(p: Pattern, fDs=None, block_diam_ratio: float = 0.0) -> Efficiency:
    return max(efficiency_vs_fD(p, fDs, block_diam_ratio), key=lambda e: e.total)


def phase_center_by_efficiency(p: Pattern, fD: float, span_lambda: float = 3.0, step: float = 0.005,
                               block_diam_ratio: float = 0.0) -> tuple[float, float]:
    """PHASEPAT method: scan the reference point along the axis and keep the best efficiency.
    Returns (d, eta) with d in wavelengths, positive = in front of the original reference (toward dish)."""
    best = (0.0, -1.0)
    for d in np.arange(-span_lambda, span_lambda + 1e-12, step):
        e = dish_efficiency(p.shifted(d), fD, block_diam_ratio).total
        if e > best[1]:
            best = (float(d), e)
    return best


def phase_center_at_angle(p: Pattern, theta_deg: float, plane: str = "E") -> float:
    """W1GHZ formula d = dphi * lambda / (2 pi (1 - cos theta)); returns wavelengths (+ = toward dish)."""
    v = p.E if plane == "E" else p.H
    ph = np.unwrap(np.angle(v))
    dphi = np.interp(theta_deg, p.theta_deg, ph) - ph[0]
    return float(dphi / (2 * math.pi * (1 - math.cos(theta_deg * DEG))))


def defocus_curve(p: Pattern, fD: float, offsets_lambda=None) -> list[tuple[float, float]]:
    offsets_lambda = np.arange(-3, 3.001, 0.05) if offsets_lambda is None else offsets_lambda
    return [(float(d), dish_efficiency(p.shifted(d), fD).total) for d in offsets_lambda]


def feedpatt_classic(p: Pattern, fD: float, dish_diam_lambda: float = 10.0, feed_diam_lambda: float = 1.0) -> dict:
    """Exact re-implementation of the W1GHZ FEEDPATT integration (amplitude only, 1 deg steps,
    power-averaged E/H) for cross-checking against published curves."""
    e_db, h_db = p.db()
    ang = np.arange(0, 181)
    Ep = np.interp(ang, p.theta_deg, 10 ** (e_db / 10))
    Hp = np.interp(ang, p.theta_deg, 10 ** (h_db / 10))
    v = np.sqrt(0.5 * (Ep + Hp))
    i = np.arange(1, 181)
    u = 0.5 * (v[i - 1] + v[i])
    th = (i - 0.5) * DEG
    in1 = u * np.tan(th / 2); in2 = u * u * np.sin(th)
    denom = in2.sum() / (180 / math.pi)
    psi = round(half_angle_from_fD(fD))
    tmp = math.tan(psi * DEG / 2)
    K = 2 / tmp ** 2
    blk = int(math.atan2(feed_diam_lambda, 2 * dish_diam_lambda * fD_from_half_angle(psi)) / DEG)
    num = in1[:psi].sum() / (180 / math.pi); deni = in2[:psi].sum() / (180 / math.pi)
    numb = in1[blk:psi].sum() / (180 / math.pi)
    unbl = K * num ** 2 / denom
    ill = K * num ** 2 / deni
    return {"total": K * numb ** 2 / denom, "illumination": ill, "spillover": unbl / ill,
            "blockage": (K * numb ** 2 / denom) / unbl, "psi": psi}


@dataclass
class DishBeam:
    hpbw_E_deg: float
    hpbw_H_deg: float
    edge_taper_db: float          # feed + space attenuation at the rim (average of E and H)
    beam_factor: float            # HPBW = b * lambda / D (mean of the two planes)
    first_sidelobe_db: float

    @property
    def hpbw_deg(self) -> float:
        return 0.5 * (self.hpbw_E_deg + self.hpbw_H_deg)


def dish_beam(p: Pattern, fD: float, D_mm: float, lam_mm: float, block_diam_ratio: float = 0.0,
              n_u: int = 900) -> DishBeam:
    """Secondary (dish) beam from the real illumination of the feed, by aperture integration.

    Feed at the focus of a paraboloid (prime focus, or the equivalent paraboloid of an offset dish).
    Aperture field at radius rho = 2 f tan(psi/2):  F(psi) / r(psi), r = 2f / (1 + cos psi) (space attenuation),
    with the feed phase. For a BOR1 feed the co-polar aperture field is (A+B)/2 + (A-B)/2 cos 2phi, so the
    far field in the E (phi=0) and H (phi=90°) planes is the Hankel transform
        E(u) = int [ (A+B)/2 J0(u rho) -/+ (A-B)/2 J2(u rho) ] rho drho,   u = k sin(theta).
    Central blockage (prime focus) removes rho < block/2. Replaces the fixed-taper Baars estimate.
    """
    from scipy.special import jv
    psi0 = half_angle_from_fD(fD) * DEG
    f = fD * D_mm
    t = p.theta_deg * DEG
    m = t <= psi0 + 1e-12
    psi = np.linspace(0.0, psi0, 1201)
    A = np.interp(psi, t[m], p.E[m].real) + 1j * np.interp(psi, t[m], p.E[m].imag)
    B = np.interp(psi, t[m], p.H[m].real) + 1j * np.interp(psi, t[m], p.H[m].imag)
    rho = 2 * f * np.tan(psi / 2)
    r = 2 * f / (1 + np.cos(psi))
    S = 0.5 * (A + B) / r
    Dd = 0.5 * (A - B) / r
    if block_diam_ratio > 0:
        keep = rho >= 0.5 * block_diam_ratio * D_mm
        S, Dd = S * keep, Dd * keep
    k = 2 * math.pi / lam_mm
    # search well past the main beam: u D/2 up to ~ 4 pi
    u = np.linspace(0.0, 8 * math.pi / D_mm, n_u)
    ur = np.outer(u, rho)
    J0, J2 = jv(0, ur), jv(2, ur)
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    IE = trap((S[None, :] * J0 - Dd[None, :] * J2) * rho[None, :], rho, axis=1)
    IH = trap((S[None, :] * J0 + Dd[None, :] * J2) * rho[None, :], rho, axis=1)

    def hp(I):
        P = np.abs(I) ** 2
        P = P / P[0]
        i = int(np.argmax(P < 0.5))
        u_h = np.interp(0.5, [P[i], P[i - 1]], [u[i], u[i - 1]])
        # first null / sidelobe
        rising = np.nonzero(np.diff(P[i:]) > 0)[0]
        sl = 10 * math.log10(max(P[i + rising[0]:].max(), 1e-12)) if len(rising) else float("nan")
        return 2 * math.degrees(math.asin(min(1.0, u_h / k))), sl

    hE, slE = hp(IE)
    hH, slH = hp(IH)
    edge = []
    for F in (A, B):
        e = abs(F[-1]) / abs(F[0]) * (2 * f / (1 + 1.0)) / r[-1]
        edge.append(-20 * math.log10(max(e, 1e-9)))
    hmean = 0.5 * (hE + hH)
    return DishBeam(hE, hH, 0.5 * (edge[0] + edge[1]), math.radians(hmean) * D_mm / lam_mm, max(slE, slH))
