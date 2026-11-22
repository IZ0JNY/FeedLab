"""Reflector geometry and closed-form loss models (prime focus and offset).

Sources: W1GHZ Antenna Book ch.4/5/6, OE2IGL 'Antenna Basics' (Baars, Milligan, Stutzman).
Angles in degrees unless the name ends with _rad.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

DEG = math.pi / 180.0


# ---------------- prime focus ----------------
def half_angle_from_fD(fD: float) -> float:
    """Illumination half-angle psi0 (deg) of a prime-focus dish."""
    return 2.0 * math.atan(1.0 / (4.0 * fD)) / DEG


def fD_from_half_angle(psi_deg: float) -> float:
    return 1.0 / (4.0 * math.tan(psi_deg * DEG / 2.0))


def focal_length_from_depth(D: float, depth: float) -> float:
    return D * D / (16.0 * depth)


def space_attenuation_db(fD: float) -> float:
    """Free-space (spherical spreading) taper at the rim, dB (positive)."""
    psi = half_angle_from_fD(fD) * DEG
    return -20.0 * math.log10(math.cos(psi / 2.0) ** 2)


def feed_taper_for_edge(fD: float, edge_taper_db: float = 10.0) -> float:
    """Feed pattern level (dB below peak) needed at the rim for a given total edge taper."""
    return edge_taper_db - space_attenuation_db(fD)


def kelleher_bw3(psi_deg: float, feed_taper_db: float) -> float:
    """Kelleher universal horn: half-power beamwidth (full, deg) giving feed_taper at +-psi."""
    return 2.0 * psi_deg * math.sqrt(3.0 / feed_taper_db)


def gain_dbi(D: float, lam: float, eta: float) -> float:
    return 10.0 * math.log10(eta * (math.pi * D / lam) ** 2)


# ---------------- closed-form efficiency models ----------------
def gaussian_taper_spill(edge_taper_db: float) -> tuple[float, float]:
    """Gaussian illumination (Baars/Milligan): (taper eff, spillover eff)."""
    a = edge_taper_db * math.log(10) / 20.0
    eta_t = 2.0 * (1 - math.exp(-a)) ** 2 / (a * (1 - math.exp(-2 * a)))
    eta_s = 1.0 - math.exp(-2 * a)
    return eta_t, eta_s


def cos2n_taper_spill(N: float, fD: float) -> tuple[float, float]:
    """cos^(2N)(psi/2) feed (Milligan): (taper eff, spillover eff)."""
    psi0 = half_angle_from_fD(fD) * DEG
    u = math.cos(psi0 / 2)
    eta_t = 4 * (N + 1) * (1 - u ** N) ** 2 / (N ** 2 * (1 - u ** (2 * (N + 1))) * math.tan(psi0 / 2) ** 2)
    eta_s = 1 - u ** (2 * (N + 1))
    return eta_t, eta_s


def ruze(rms: float, lam: float) -> float:
    return math.exp(-(4 * math.pi * rms / lam) ** 2)


def ruze_loss_db(rms: float, lam: float) -> float:
    """Ruze in dB: −685.8·(rms/λ)². Sergei RW3BP: 0.31 mm rms at 77 GHz (λ 3.9 mm) → −4.3 dB."""
    return -685.8 * (rms / lam) ** 2


def lens_thickness_mm(deviation_mm: float, phi_deg: float, eps_r: float) -> float:
    """Dielectric correcting lens in front of the feed (Sergei RW3BP, 77 GHz): a surface deviation d along
    the axis changes the path by d·(cos φ + 1); a dielectric slab of thickness h adds h·(√ε − 1), so
    h = d·(cos φ + 1)/(√ε − 1). φ: angle of the ray from the focus. PTFE: ε ≈ 2.1."""
    return deviation_mm * (math.cos(math.radians(phi_deg)) + 1) / (math.sqrt(eps_r) - 1)


def blocking_efficiency(d_block: float, D: float, eta_illum: float = 1.0) -> float:
    """Baars: (1 - (1/eta_i)(dB/D)^2)^2."""
    return (1 - (d_block / D) ** 2 / eta_illum) ** 2


def defocus_efficiency_gaussian(z_lambda: float, fD: float, edge_taper_db: float) -> float:
    """Axial defocus with gaussian illumination (Milligan). z in wavelengths."""
    a = edge_taper_db / 8.686
    s = z_lambda * (1 - math.cos(half_angle_from_fD(fD) * DEG))
    x = 2 * math.pi * s
    return a * a * (1 - 2 * math.exp(-a) * math.cos(x) + math.exp(-2 * a)) / ((a * a + x * x) * (1 - math.exp(-a)) ** 2)


def beam_factor(edge_taper_db: float) -> float:
    """Baars beam factor b (HPBW = b*lambda/D rad) for parabolic-on-pedestal taper."""
    tau = 10 ** (-edge_taper_db / 20)
    return 1.269 - 0.566 * tau + 0.534 * tau ** 2 - 0.208 * tau ** 3


def hpbw_deg(D: float, lam: float, edge_taper_db: float = 10.0) -> float:
    return beam_factor(edge_taper_db) * lam / D / DEG


# ---------------- offset ----------------
@dataclass
class OffsetGeometry:
    F: float          # focal length
    D: float          # projected aperture diameter
    H: float          # height of aperture centre above axis (h + D/2)
    psi_L: float      # lower rim angle (deg)
    psi_U: float      # upper rim angle (deg)
    psi_S: float      # half subtended angle (deg)
    psi_B: float      # bisector (deg)
    psi_C: float      # direction to aperture centre (deg)
    fD_equiv: float   # prime-focus f/D with same subtended half-angle

    def feed_pointing(self, edge_taper_db: float = 10.0) -> float:
        """OE2IGL/Stutzman: feed axis angle psi_F balancing the two rim tapers (gaussian feed)."""
        dft = 40 * math.log10(math.cos(self.psi_L * DEG / 2) / math.cos(self.psi_U * DEG / 2))
        bw = 2 * self.psi_S
        psi_p = dft * bw / (4.01 * (2 * edge_taper_db - dft)) + self.psi_S
        return self.psi_L + psi_p


def offset_geometry(F: float, D: float, h: float = 0.0) -> OffsetGeometry:
    """Offset paraboloid (Stutzman/Milligan). h = clearance from axis to lower rim
    (0 for TV dishes whose lower rim is the parent vertex)."""
    H = h + D / 2
    # rim angles from the focus (exact): tan(psi/2) = y/(2F)
    psi_L = 2 * math.atan(h / (2 * F)) / DEG
    psi_U = 2 * math.atan((h + D) / (2 * F)) / DEG
    psi_S = (psi_U - psi_L) / 2
    psi_B = (psi_U + psi_L) / 2
    psi_C = 2 * math.atan(H / (2 * F)) / DEG
    return OffsetGeometry(F, D, H, psi_L, psi_U, psi_S, psi_B, psi_C, fD_from_half_angle(psi_S))


def offset_from_tv_measurements(long_axis: float, short_axis: float, depth: float) -> dict:
    """OE2IGL/Legon quick formula for TV offset dishes (lower rim at vertex):
    f = short^3/(16*long*depth); tilt = arccos(short/long)."""
    f = short_axis ** 3 / (16 * long_axis * depth)
    tilt = math.acos(short_axis / long_axis) / DEG
    geo = offset_geometry(f, short_axis, 0.0)
    # string lengths: bottom rim = f (vertex), top rim distance from focus
    y_top = short_axis
    x_top = y_top ** 2 / (4 * f)
    top_string = math.hypot(f - x_top, y_top)
    return {"f": f, "tilt_from_vertical_deg": tilt, "bottom_string": f, "top_string": top_string, "geometry": geo}


def fit_offset_parabola(points_xy: np.ndarray, f_range=(0.2, 3.0), steps: int = 2000) -> dict:
    """Least-squares fit of profile points (x along beam axis depth, y along long axis, measured in the
    dish's own frame) to a rotated parabola with vertex at the lower rim (W1GHZ HDL_ANT v3 approach).
    Returns f, tilt and rms error. points_xy[:,0]=depth, [:,1]=position from lower rim."""
    pts = np.asarray(points_xy, float)
    best = None
    for tilt in np.linspace(-45, 45, int(steps) * 5 + 1):
        t = tilt * DEG
        # rotate measured frame into parabola frame; for fixed tilt, 1/(4f) is a linear LSQ
        xr = pts[:, 0] * math.cos(t) + pts[:, 1] * math.sin(t)
        yr = -pts[:, 0] * math.sin(t) + pts[:, 1] * math.cos(t)
        g = float(np.sum(xr * yr ** 2) / np.sum(yr ** 4))
        if g <= 0:
            continue
        e = float(np.sqrt(np.mean((xr - g * yr ** 2) ** 2)))
        if best is None or e < best[0]:
            best = (e, 1.0 / (4 * g), tilt)
    return {"f": best[1], "tilt_deg": best[2], "rms": best[0]}
