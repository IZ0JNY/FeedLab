# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Sun and Moon as noise sources, and the Y-factors a station should measure.

Sun: brightness temperature of the disk from the measured solar flux at 15.4 GHz (USAF RSTN: San Vito,
Learmonth, Sagamore Hill, Palehua; NOAA SWPC), scaled to the band with the quiet-Sun spectrum Tb ∝ f^-0.3
(cm–mm range: ~12 000 K at 10 GHz, ~9 700 K at 24 GHz, ~7 900 K at 47 GHz).
Moon: Tb = T0 + T1·cos(Φ − ξ) (Krotikov & Troitskii; Linsky 1973), Φ = lunar phase from full Moon
(negative while waxing): the warm-up lags the illumination and the swing grows at shorter wavelengths.
Beam filling: Gaussian main beam of half-power width θb on a uniform disk of diameter θs.
"""
from __future__ import annotations

import math

K_B = 1.380649e-23
C = 299792458.0
SUN_RADIO_DIAM_FACTOR = 1.05        # the cm/mm radio Sun is a few % larger than the optical disk

# Moon model per band: (T0 K, T1 K, lag ξ deg)
MOON_TB = {10: (211.0, 18.0, 45.0), 24: (207.0, 36.0, 40.0), 47: (204.0, 60.0, 30.0)}


def band_key(f_ghz: float) -> int:
    return min(MOON_TB, key=lambda b: abs(b - f_ghz))


def sun_tb_from_flux(flux_sfu_15g4: float, f_ghz: float, diam_deg: float = 0.533) -> float:
    """Disk brightness temperature (K) at f from the 15.4 GHz flux (solar flux units, 1 SFU = 1e-22 W/m²/Hz)."""
    th = math.radians(diam_deg * SUN_RADIO_DIAM_FACTOR) / 2
    omega = 2 * math.pi * (1 - math.cos(th))
    f0 = 15.4e9
    tb0 = flux_sfu_15g4 * 1e-22 * C ** 2 / (2 * K_B * omega * f0 ** 2)
    return tb0 * (f_ghz / 15.4) ** -0.3


def moon_tb(f_ghz: float, phase_signed_deg: float) -> float:
    t0, t1, lag = MOON_TB[band_key(f_ghz)]
    return t0 + t1 * math.cos(math.radians(phase_signed_deg - lag))


def hpbw_deg(f_ghz: float, D_m: float, edge_taper_db: float = 12.0) -> float:
    """Half-power beamwidth of a dish: (1.02 + 0.0135·taper) λ/D."""
    lam = C / (f_ghz * 1e9)
    return math.degrees((1.02 + 0.0135 * edge_taper_db) * lam / D_m)


def disk_fill(source_diam_deg: float, hpbw: float) -> float:
    """Fraction of a Gaussian beam's main-lobe response collected from a uniform disk."""
    return 1 - math.exp(-math.log(2) * (source_diam_deg / hpbw) ** 2)


def antenna_temp_disk(tb: float, source_diam_deg: float, f_ghz: float, D_m: float, eta_ap: float,
                      hpbw: float) -> float:
    """Antenna temperature (K) from a uniform disk: Tb·(Ae/λ²)·Ω_gauss·fill. For a small source this is S·Ae/2k."""
    lam = C / (f_ghz * 1e9)
    ae = eta_ap * math.pi * D_m ** 2 / 4
    om = 1.133 * math.radians(hpbw) ** 2
    return tb * ae / lam ** 2 * om * disk_fill(source_diam_deg, hpbw)


def y_db(t_source: float, t_sys_cold: float) -> float:
    return 10 * math.log10((t_source + t_sys_cold) / t_sys_cold)


def t_from_y(y: float, t_sys_cold: float) -> float:
    """Source antenna temperature from a measured Y (dB)."""
    return (10 ** (y / 10) - 1) * t_sys_cold


def tsys_from_sun(y: float, t_sun_ant: float) -> float:
    """System temperature (K, cold sky) from a measured sun Y and the expected sun antenna temperature."""
    return t_sun_ant / (10 ** (y / 10) - 1)
