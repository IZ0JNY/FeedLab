"""Closed-form antenna relations from C. A. Balanis, *Antenna Theory: Analysis and Design*
(Wiley, 4th ed. 2016), used as independent checks of FeedLab's numerical engines.

  * fundamentals (ch. 2): VSWR / return loss / mismatch loss, polarisation loss factor, Friis equation,
    aperture efficiency from gain;
  * horn antennas (ch. 13): E-plane and H-plane sectoral and pyramidal horn directivity with Fresnel
    integrals; conical horn directivity with the quadratic-phase loss L(s);
  * reflector antennas (ch. 15): aperture efficiency of a paraboloid fed by G_f = 2(n+1)·cos^n θ,
    general integral and the closed form for n = 2.

Fresnel integrals: C(x) = ∫0^x cos(πτ²/2) dτ, S(x) = ∫0^x sin(πτ²/2) dτ (scipy.special.fresnel returns S, C).
Lengths in any consistent unit (λ, a, b, ρ the same).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import fresnel

C0 = 299_792_458.0


# ---------------------------------------------------------------- fundamentals (ch. 2)
def reflection_from_s11_db(s11_db: float) -> float:
    return 10 ** (s11_db / 20)


def vswr_from_s11_db(s11_db: float) -> float:
    g = reflection_from_s11_db(s11_db)
    return (1 + g) / (1 - g)


def s11_db_from_vswr(vswr: float) -> float:
    return 20 * math.log10((vswr - 1) / (vswr + 1))


def mismatch_loss_db(s11_db: float) -> float:
    """Power lost by reflection: −10·log10(1 − |Γ|²)."""
    return -10 * math.log10(1 - reflection_from_s11_db(s11_db) ** 2)


def plf_linear(angle_deg: float) -> float:
    """Polarisation loss factor between two linear polarisations at an angle ψ: cos²ψ."""
    return math.cos(math.radians(angle_deg)) ** 2


PLF_LINEAR_CIRCULAR = 0.5          # linear ↔ circular: −3.01 dB; opposite circular senses: 0 (−∞ dB)


def friis_received_dbm(pt_dbm: float, gt_dbi: float, gr_dbi: float, f_ghz: float, d_m: float,
                       plf: float = 1.0, s11_tx_db: float | None = None, s11_rx_db: float | None = None) -> float:
    """Friis transmission equation with polarisation and impedance mismatch."""
    lam = C0 / (f_ghz * 1e9)
    p = pt_dbm + gt_dbi + gr_dbi + 20 * math.log10(lam / (4 * math.pi * d_m)) + 10 * math.log10(plf)
    for s in (s11_tx_db, s11_rx_db):
        if s is not None:
            p -= mismatch_loss_db(s)
    return p


def aperture_efficiency_from_gain(gain_dbi: float, diameter_m: float, f_ghz: float) -> float:
    lam = C0 / (f_ghz * 1e9)
    return 10 ** (gain_dbi / 10) / (math.pi * diameter_m / lam) ** 2


# ---------------------------------------------------------------- horns (ch. 13)
def _CS(x: float) -> tuple[float, float]:
    S, C = fresnel(x)
    return float(C), float(S)


def e_plane_sectoral_directivity(a: float, b1: float, rho1: float, lam: float) -> float:
    """D_E = 64 a ρ1 / (π λ b1) · [C²(q) + S²(q)], q = b1/√(2λρ1). a: waveguide broad wall, b1: E-plane
    aperture, ρ1: E-plane apex-to-aperture distance."""
    C, S = _CS(b1 / math.sqrt(2 * lam * rho1))
    return 64 * a * rho1 / (math.pi * lam * b1) * (C * C + S * S)


def h_plane_sectoral_directivity(a1: float, b: float, rho2: float, lam: float) -> float:
    """D_H = 4π b ρ2 / (λ a1) · {[C(u) − C(v)]² + [S(u) − S(v)]²},
    u, v = (1/√2)(√(λρ2)/a1 ± a1/√(λρ2)). a1: H-plane aperture, b: waveguide narrow wall."""
    t = math.sqrt(lam * rho2)
    u = (t / a1 + a1 / t) / math.sqrt(2)
    v = (t / a1 - a1 / t) / math.sqrt(2)
    Cu, Su = _CS(u)
    Cv, Sv = _CS(v)
    return 4 * math.pi * b * rho2 / (lam * a1) * ((Cu - Cv) ** 2 + (Su - Sv) ** 2)


def pyramidal_directivity(a: float, b: float, a1: float, b1: float, rho1: float, rho2: float, lam: float) -> float:
    """D_P = π λ² / (32 a b) · D_E · D_H (waveguide a×b, aperture a1 (H) × b1 (E))."""
    return math.pi * lam ** 2 / (32 * a * b) * e_plane_sectoral_directivity(a, b1, rho1, lam) * \
        h_plane_sectoral_directivity(a1, b, rho2, lam)


def conical_phase_loss_db(s: float) -> float:
    """L(s) ≈ 0.8 − 1.71 s + 26.25 s² − 17.79 s³ (dB), s = d²/(8λl): loss from the quadratic aperture phase
    of a conical horn relative to a uniform aperture of the same circumference."""
    return 0.8 - 1.71 * s + 26.25 * s * s - 17.79 * s ** 3


def conical_directivity_db(d: float, slant: float, lam: float) -> float:
    """D_c(dB) = 10·log10[(C/λ)²] − L(s), C = π d (aperture circumference), s = d²/(8 λ l)."""
    s = d * d / (8 * lam * slant)
    return 10 * math.log10((math.pi * d / lam) ** 2) - conical_phase_loss_db(s)


# ---------------------------------------------------------------- reflectors (ch. 15)
def reflector_aperture_efficiency_cosn(n: float, theta0_deg: float, num: int = 4001) -> float:
    """ε_ap = cot²(θ0/2) · |∫0^θ0 √G_f(θ) tan(θ/2) dθ|², G_f = 2(n+1) cos^n θ (spillover × taper)."""
    t0 = math.radians(theta0_deg)
    t = np.linspace(0.0, t0, num)
    y = np.sqrt(2 * (n + 1) * np.cos(t) ** n) * np.tan(t / 2)
    integral = float(np.sum((y[1:] + y[:-1]) * np.diff(t)) / 2)
    return integral ** 2 / math.tan(t0 / 2) ** 2


def reflector_aperture_efficiency_cos2(theta0_deg: float) -> float:
    """Closed form for n = 2: ε_ap = 24 {sin²(θ0/2) + ln[cos(θ0/2)]}² cot²(θ0/2)."""
    h = math.radians(theta0_deg) / 2
    return 24 * (math.sin(h) ** 2 + math.log(math.cos(h))) ** 2 / math.tan(h) ** 2
