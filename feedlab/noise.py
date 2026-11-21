"""Antenna noise temperature and G/T (OE2IGL 'Antenna Basics', W1GHZ 'Feedhorn analysis for G/T' 2014)."""
from __future__ import annotations

import math

import numpy as np

from .efficiency import _normalise, _trap
from .patterns import Pattern
from .reflector import half_angle_from_fD

H_PLANCK = 6.62607015e-34
K_B = 1.380649e-23
DEG = math.pi / 180


def planck_temp(T: float, f_ghz: float) -> float:
    """Brightness temperature corrected for Planck (Rayleigh-Jeans not valid at mm-waves)."""
    x = H_PLANCK * f_ghz * 1e9 / (K_B * T)
    return H_PLANCK * f_ghz * 1e9 / (K_B * math.expm1(x))


def sky_temp(elev_deg: float, zenith_atten_db: float, t_amb_c: float = 15.0, t_cmb: float = 2.725,
             f_ghz: float | None = None) -> float:
    """T_sky = (1-L) * (0.81*T_amb + 37.4) + T_cmb * L, L = 10^(-A_zen/(10 sin el))."""
    L = 10 ** (-zenith_atten_db / (10 * math.sin(elev_deg * DEG)))
    tcmb = planck_temp(t_cmb, f_ghz) if f_ghz else t_cmb
    return (1 - L) * (0.81 * (273.15 + t_amb_c) + 37.4) + tcmb * L


def receiver_temp(nf_db: float) -> float:
    return 290.0 * (10 ** (nf_db / 10) - 1)


def spillover_temp_simple(eta_s: float, fD: float, elev_deg: float, t_ground: float = 290.0,
                          t_sky: float = 10.0, offset_deg: float = 0.0) -> float:
    """OE2IGL approximation: fraction of the spillover cone seeing ground vs sky."""
    psi0 = half_angle_from_fD(fD) * DEG
    arg = max(-1.0, min(1.0, math.sin((elev_deg - offset_deg) * DEG) / math.sin(psi0)))
    f_sky = math.acos(arg) / math.pi
    return (1 - f_sky) * t_ground * (1 - eta_s) + f_sky * t_sky * (1 - eta_s)


def antenna_temp_prime_focus(p: Pattern, fD: float, elev_deg: float, t_sky: float, t_ground: float = 290.0,
                             n_phi: int = 180, mesh_leakage: float = 0.0) -> float:
    """Pattern-integrated antenna temperature of a prime-focus dish (W1GHZ 2014 approximations):
    power intercepted by the dish sees the sky (plus mesh leakage of ground); spillover past the rim
    sees ground or sky depending on direction relative to the horizon. No edge diffraction."""
    t, A, B = _normalise(p)
    psi0 = half_angle_from_fD(fD) * DEG
    phi = np.linspace(0, 2 * math.pi, n_phi, endpoint=False)
    TT, PP = np.meshgrid(t, phi, indexing="ij")
    P = (np.abs(A)[:, None] ** 2 * np.cos(PP) ** 2 + np.abs(B)[:, None] ** 2 * np.sin(PP) ** 2)
    # feed looks back toward the dish along -z; dish axis at elevation el. Direction of feed ray:
    el = elev_deg * DEG
    # unit vector of ray in feed frame (feed boresight = toward dish = opposite to dish beam)
    x = np.sin(TT) * np.cos(PP); y = np.sin(TT) * np.sin(PP); z = np.cos(TT)
    # dish beam points to elevation el: feed boresight points to -el (downwards); vertical component:
    vert = -(z * math.sin(el)) + x * math.cos(el)
    T_dir = np.where(vert > 0, t_sky, t_ground)
    on_dish = TT <= psi0
    T_eff = np.where(on_dish, t_sky * (1 - mesh_leakage) + t_ground * mesh_leakage, T_dir)
    w = np.sin(TT)
    return float(np.sum(P * T_eff * w) / np.sum(P * w))


def g_over_t_db(gain_dbi: float, t_ant: float, t_rx: float) -> float:
    return gain_dbi - 10 * math.log10(t_ant + t_rx)


def sun_noise_expected_db(flux_sfu: float, D_m: float, eta: float, f_ghz: float, t_sys: float,
                          beam_correction: float = 1.0) -> float:
    """Expected sun-to-cold-sky Y (dB): T_sun_ant = S*Ae/(2k) with S in SFU (1e-22 W/m²/Hz)."""
    Ae = eta * math.pi * D_m ** 2 / 4
    dT = flux_sfu * 1e-22 * Ae / (2 * K_B) * beam_correction
    return 10 * math.log10((t_sys + dT) / t_sys)
