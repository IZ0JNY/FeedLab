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


def slant_atten_db(elev_deg: float, zenith_atten_db: float) -> float:
    """Gas attenuation along the slant path, A = A_zenith / sin(el) (ITU-R P.676 for el ≥ 5°).
    Checked against VK3UM 'Atmosphere' 1.18 at 24 GHz (W5LUA 2012): its slant values at 45°, 20° and 5°
    all follow A_zen/sin(el) with one A_zen (0.378 dB) to 0.01%."""
    return zenith_atten_db / math.sin(elev_deg * DEG)


def sky_temp(elev_deg: float, zenith_atten_db: float, t_amb_c: float = 15.0, t_cmb: float = 2.725,
             f_ghz: float | None = None, t_atm: float | None = None) -> float:
    """T_sky = (1-L) * T_atm + T_cmb * L, L = 10^(-A_slant/10), T_atm = 0.81*T_amb + 37.4 (or given).
    VK3UM uses T_atm = 280 K (W5LUA 2012: 32.43/62.92/176.9 K at 45/20/5° elevation, 24 GHz)."""
    L = 10 ** (-slant_atten_db(elev_deg, zenith_atten_db) / 10)
    tcmb = planck_temp(t_cmb, f_ghz) if f_ghz else t_cmb
    ta = t_atm if t_atm is not None else 0.81 * (273.15 + t_amb_c) + 37.4
    return (1 - L) * ta + tcmb * L


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


def beam_fill_factor(source_diam_deg: float, hpbw_deg: float) -> float:
    """Correction K for a uniform disc source seen by a Gaussian beam: K = x²/(1-exp(-x²)),
    x² = ln2·(θ_source/θ_beam)². The antenna sees ΔT = S·Ae/(2k)/K.
    VK3UM (W5LUA 2012, 24 GHz, beam 0.36°): Moon 0.559° → 2.06, Sun → 1.98."""
    x2 = math.log(2) * (source_diam_deg / hpbw_deg) ** 2
    return x2 / -math.expm1(-x2)


def sun_noise_expected_db(flux_sfu: float, D_m: float, eta: float, f_ghz: float, t_sys: float,
                          beam_correction: float = 1.0, hpbw_deg: float | None = None,
                          sun_diam_deg: float = 0.54) -> float:
    """Expected sun-to-cold-sky Y (dB): ΔT = S·Ae/(2k)/K, S in SFU (1e-22 W/m²/Hz) at the working
    frequency. With hpbw_deg, K = beam_fill_factor(sun_diam_deg, hpbw_deg); otherwise ΔT is multiplied
    by beam_correction. VK3UM check (W5LUA 2012): 732 SFU, 2.4 m, η 66%, Tsys 221.1 K, 0.36° → 12.8 dB."""
    Ae = eta * math.pi * D_m ** 2 / 4
    dT = flux_sfu * 1e-22 * Ae / (2 * K_B) * beam_correction
    if hpbw_deg:
        dT /= beam_fill_factor(sun_diam_deg, hpbw_deg)
    return 10 * math.log10((t_sys + dT) / t_sys)


def moon_noise_expected_db(t_moon: float, D_m: float, eta: float, f_ghz: float, t_sys: float,
                           hpbw_deg: float, moon_diam_deg: float = 0.52) -> float:
    """Expected moon-to-cold-sky Y (dB): ΔT = T_moon·Ω_moon·Ae/(λ²·K), Ω_moon = π(θ/2)².
    T_moon ≈ 200–280 K at 1.25 cm depending on phase (Kraus, Radio Astronomy, fig. 8-28).
    VK3UM check (W5LUA 2012): 213 K, Moon 0.559°, 2.4 m, η 66%, Tsys 221.1 K → 2.23 dB."""
    lam = 299_792_458.0 / (f_ghz * 1e9)
    Ae = eta * math.pi * D_m ** 2 / 4
    omega = math.pi * (moon_diam_deg * DEG / 2) ** 2
    dT = t_moon * omega * Ae / lam ** 2 / beam_fill_factor(moon_diam_deg, hpbw_deg)
    return 10 * math.log10((t_sys + dT) / t_sys)


def free_space_loss_db(f_ghz: float, d_km: float) -> float:
    lam = 299_792_458.0 / (f_ghz * 1e9)
    return 20 * math.log10(4 * math.pi * d_km * 1e3 / lam)


def eme_path_loss_db(f_ghz: float, d_km: float = 384_400.0, reflectivity: float = 0.065) -> float:
    """Earth-Moon-Earth path loss: L = 10·log10((4π)³ d⁴ / (σ λ²)), σ = ρ·π·R_moon².
    VK3UM / W5LUA 2012: 295.24 dB at 24.048 GHz and 356 400 km; apogee-perigee ≈ 2.3 dB."""
    lam = 299_792_458.0 / (f_ghz * 1e9)
    sigma = reflectivity * math.pi * 1_737_400.0 ** 2
    return 10 * math.log10((4 * math.pi) ** 3 * (d_km * 1e3) ** 4 / (sigma * lam ** 2))



# ---------------------------------------------------------------- radio astronomy / EME station checks
# Luis CT1DMK, "EME and Radio Astronomy"; Sergei RW3BP, "EME antenna and Jupiter noise on 77 GHz" (EME 2014)
JY = 1e-26                         # W m^-2 Hz^-1

# total flux at 1.4 GHz (Jy), from Luis CT1DMK's table; a single-polarisation receiver sees half of it
RADIO_SOURCES_1G4 = {
    "Cassiopeia A (3C461)": 2480, "Cygnus A (3C405)": 1495, "M17 (W38)": 1060, "Taurus A (3C144)": 875,
    "W51 (3C400)": 710, "Orion A (3C145)": 520, "Virgo A (M87)": 198, "3C273": 46,
}


def dicke_tmin(t_sys: float, bandwidth_hz: float, tau_s: float) -> float:
    """Smallest detectable temperature change of a total-power radiometer: T_sys / sqrt(B·τ) (Dicke)."""
    return t_sys / math.sqrt(bandwidth_hz * tau_s)


def g_over_t_from_source(y_db: float, flux_jy: float, f_ghz: float, single_pol: bool = True) -> float:
    """G/T (dB/K) from the Y factor measured on a radio source of known total flux.
    ΔT = S·Ae/(2k) for a single-polarisation receiver (it gets half of the unpolarised flux), Ae = Gλ²/4π
    → G/T = 8πk(Y−1)/(λ²S). Luis CT1DMK writes G/T = 4πk(Y−1)/(λ²S) with S already halved."""
    lam = 299_792_458.0 / (f_ghz * 1e9)
    y = 10 ** (y_db / 10)
    s = flux_jy * JY * (0.5 if single_pol else 1.0)
    return 10 * math.log10(4 * math.pi * K_B * (y - 1) / (lam ** 2 * s))


def main_beam_efficiency_from_sun(y_sun_db: float, t_rx: float, t_atm: float, l_atm: float, t_sun: float) -> float:
    """Sergei RW3BP: ε_M = (T_atm + T_rx)(Y_sun − 1) / (T_sun·L_atm), the Sun filling the main beam.
    His 77 GHz example: Y 6.3 dB, T_rx 1030 K, T_atm 70 K, L_atm 0.77, T_sun 7250 K → ε_M = 0.65."""
    y = 10 ** (y_sun_db / 10)
    return (t_atm + t_rx) * (y - 1) / (t_sun * l_atm)


def sun_y_from_main_beam(eps_m: float, t_rx: float, t_atm: float, l_atm: float, t_sun: float) -> float:
    """Inverse of main_beam_efficiency_from_sun: expected sun Y (dB)."""
    return 10 * math.log10(1 + t_sun * l_atm * eps_m / (t_atm + t_rx))


def small_source_y_db(y_ref_db: float, source_size: float, reference_size: float) -> float:
    """Sergei RW3BP: a source much smaller than the beam, at the same brightness temperature as a reference
    filling the beam, gives Y ≈ Y_ref·(θ_source/θ_ref)² (Jupiter 44" with a 400" beam vs new Moon 0.33 dB
    → 0.004 dB). Valid for small Y (linear in dB)."""
    return y_ref_db * (source_size / reference_size) ** 2
