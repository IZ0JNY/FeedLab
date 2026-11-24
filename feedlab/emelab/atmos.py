# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Atmospheric gaseous attenuation and sky noise from the surface weather.

Specific attenuation of dry air (oxygen) and water vapour with the approximate formulas of ITU-R P.676
(Annex 2, valid 1–350 GHz), equivalent heights for the zenith path, slant path with a curved-earth air-mass
for low elevations, and the sky brightness temperature with the mean radiating temperature of ITU-R P.618
(Tm ≈ 1.12·T − 50 K). At 24 GHz water vapour dominates (22.235 GHz line): humidity counts a lot.
Clouds and rain are not included (a liquid-water term can be added with cloud_lwc_kg_m2, ITU-R P.840).
"""
from __future__ import annotations

import math


def vapour_density(t_c: float, rh_pct: float) -> float:
    """Water vapour density ρ (g/m³) from temperature (°C) and relative humidity (%)."""
    es = 6.1121 * math.exp(17.502 * t_c / (240.97 + t_c))           # hPa (Buck)
    e = rh_pct / 100.0 * es
    return 216.7 * e / (t_c + 273.15)


def dew_point(t_c: float, rh_pct: float) -> float:
    a, b = 17.502, 240.97
    g = math.log(max(rh_pct, 0.1) / 100.0) + a * t_c / (b + t_c)
    return b * g / (a - g)


def _phi(rp, rt, a, b, c, d):
    return rp ** a * rt ** b * math.exp(c * (1 - rp) + d * (1 - rt))


def gamma_oxygen(f: float, p_hpa: float = 1013.25, t_c: float = 15.0) -> float:
    """Dry-air specific attenuation (dB/km), ITU-R P.676 Annex 2, f ≤ 54 GHz."""
    rp, rt = p_hpa / 1013.25, 288.0 / (273.15 + t_c)
    if f > 54:
        raise ValueError("f ≤ 54 GHz")
    x1 = _phi(rp, rt, 0.0717, -1.8132, 0.0156, -1.6515)
    x2 = _phi(rp, rt, 0.5146, -4.6368, -0.1921, -5.7416)
    x3 = _phi(rp, rt, 0.3414, -6.5851, 0.2130, -8.5854)
    return (7.2 * rt ** 2.8 / (f ** 2 + 0.34 * rp ** 2 * rt ** 1.6)
            + 0.62 * x3 / ((54 - f) ** (1.16 * x1) + 0.83 * x2)) * f ** 2 * rp ** 2 * 1e-3


def gamma_vapour(f: float, rho: float, p_hpa: float = 1013.25, t_c: float = 15.0) -> float:
    """Water-vapour specific attenuation (dB/km), ITU-R P.676 Annex 2."""
    rp, rt = p_hpa / 1013.25, 288.0 / (273.15 + t_c)
    n1 = 0.955 * rp * rt ** 0.68 + 0.006 * rho
    n2 = 0.735 * rp * rt ** 0.5 + 0.0353 * rt ** 4 * rho
    g = lambda fi: 1 + ((f - fi) / (f + fi)) ** 2
    s = (3.98 * n1 * math.exp(2.23 * (1 - rt)) / ((f - 22.235) ** 2 + 9.42 * n1 ** 2) * g(22.0)
         + 11.96 * n1 * math.exp(0.7 * (1 - rt)) / ((f - 183.31) ** 2 + 11.14 * n1 ** 2)
         + 0.081 * n1 * math.exp(6.44 * (1 - rt)) / ((f - 321.226) ** 2 + 6.29 * n1 ** 2)
         + 3.66 * n1 * math.exp(1.6 * (1 - rt)) / ((f - 325.153) ** 2 + 9.22 * n1 ** 2)
         + 25.37 * n1 * math.exp(1.09 * (1 - rt)) / (f - 380) ** 2
         + 17.4 * n1 * math.exp(1.46 * (1 - rt)) / (f - 448) ** 2
         + 844.6 * n1 * math.exp(0.17 * (1 - rt)) / (f - 557) ** 2 * g(557)
         + 290 * n1 * math.exp(0.41 * (1 - rt)) / (f - 752) ** 2 * g(752)
         + 8.3328e4 * n2 * math.exp(0.99 * (1 - rt)) / (f - 1780) ** 2 * g(1780))
    return s * f ** 2 * rt ** 2.5 * rho * 1e-4


def h_oxygen(f: float, p_hpa: float = 1013.25) -> float:
    """Equivalent height of dry air (km)."""
    rp = p_hpa / 1013.25
    t1 = 4.64 / (1 + 0.066 * rp ** -2.3) * math.exp(-((f - 59.7) / (2.87 + 12.4 * math.exp(-7.9 * rp))) ** 2)
    t2 = 0.14 * math.exp(2.12 * rp) / ((f - 118.75) ** 2 + 0.031 * math.exp(2.2 * rp))
    t3 = 0.0114 / (1 + 0.14 * rp ** -2.6) * f * (-0.0247 + 0.0001 * f + 1.61e-6 * f ** 2) / \
        (1 - 0.0169 * f + 4.1e-5 * f ** 2 + 3.2e-7 * f ** 3)
    return 6.1 / (1 + 0.17 * rp ** -1.1) * (1 + t1 + t2 + t3)


def h_vapour(f: float, p_hpa: float = 1013.25) -> float:
    """Equivalent height of water vapour (km)."""
    rp = p_hpa / 1013.25
    sw = 1.013 / (1 + math.exp(-8.6 * (rp - 0.57)))
    return 1.66 * (1 + 1.39 * sw / ((f - 22.235) ** 2 + 2.56 * sw) + 3.37 * sw / ((f - 183.31) ** 2 + 4.69 * sw)
                   + 1.58 * sw / ((f - 325.1) ** 2 + 2.89 * sw))


def cloud_specific(f: float, t_c: float = 0.0) -> float:
    """Liquid-water (cloud) specific attenuation coefficient K_l, (dB/km)/(g/m³), ITU-R P.840 (Rayleigh)."""
    th = 300.0 / (t_c + 273.15)
    e0 = 77.66 + 103.3 * (th - 1)
    e1, e2 = 0.0671 * e0, 3.52
    fp = 20.20 - 146 * (th - 1) + 316 * (th - 1) ** 2
    fs = 39.8 * fp
    ei = f * (e0 - e1) / (fp * (1 + (f / fp) ** 2)) + f * (e1 - e2) / (fs * (1 + (f / fs) ** 2))
    er = (e0 - e1) / (1 + (f / fp) ** 2) + (e1 - e2) / (1 + (f / fs) ** 2) + e2
    eta = (2 + er) / ei
    return 0.819 * f / (ei * (1 + eta ** 2))


def zenith_attenuation(f: float, t_c: float, rh_pct: float, p_hpa: float = 1013.25,
                       cloud_lwc_kg_m2: float = 0.0) -> dict:
    """Zenith attenuation (dB) split into oxygen, water vapour and clouds."""
    rho = vapour_density(t_c, rh_pct)
    ao = gamma_oxygen(f, p_hpa, t_c) * h_oxygen(f, p_hpa)
    aw = gamma_vapour(f, rho, p_hpa, t_c) * h_vapour(f, p_hpa)
    ac = cloud_lwc_kg_m2 * cloud_specific(f, 0.0)
    return {"oxygen": ao, "vapour": aw, "cloud": ac, "total": ao + aw + ac, "rho": rho}


def airmass(el_deg: float) -> float:
    """Relative path length through the atmosphere (curved earth, Kasten–Young form), 1 at zenith."""
    el = max(el_deg, 0.0)
    return 1.0 / (math.sin(math.radians(el)) + 0.50572 * (el + 6.07995) ** -1.6364)


def slant_attenuation(a_zenith_db: float, el_deg: float) -> float:
    return a_zenith_db * airmass(el_deg)


def sky_temperature(a_db: float, t_c: float, t_bg: float = 2.73) -> float:
    """Sky brightness temperature (K) along a path with attenuation a_db: Tm(1 − 1/L) + T_bg/L."""
    tm = 1.12 * (t_c + 273.15) - 50.0
    l = 10 ** (a_db / 10)
    return tm * (1 - 1 / l) + t_bg / l


def iwv_kg_m2(t_c: float, rh_pct: float, scale_height_km: float = 2.0) -> float:
    """Integrated water vapour (kg/m², = mm of precipitable water) from the surface density and a 2 km scale height."""
    return vapour_density(t_c, rh_pct) * scale_height_km
