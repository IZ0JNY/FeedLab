# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""EME link budget: path loss with the actual Moon distance, the part of the Moon the beam illuminates,
two-way atmosphere and the own-echo signal-to-noise ratio."""
from __future__ import annotations

import math

from . import sky

R_MOON_M = 1737.4e3
REFLECTIVITY = 0.065            # radar cross-section σ = 0.065·π·a² (microwave value, ARRL/VK3UM)


def path_loss_db(f_ghz: float, dist_km: float, reflectivity: float = REFLECTIVITY) -> float:
    """Isotropic two-way path loss (dB) via the Moon: (4π)³R⁴ / (σλ²)."""
    lam = sky.C / (f_ghz * 1e9)
    sigma = reflectivity * math.pi * R_MOON_M ** 2
    R = dist_km * 1e3
    return 10 * math.log10((4 * math.pi) ** 3 * R ** 4 / (sigma * lam ** 2))


def beam_moon_factor(moon_diam_deg: float, hpbw: float, n: int = 60) -> float:
    """Fraction of the full-Moon echo kept when the beam is narrower than the Moon (24/47 GHz on big dishes).

    Echo ∝ ∫ G_tx·G_rx·σ0 dA over the disk: two-way Gaussian beam, scattering weighted by cos^1.5 of the
    incidence angle (mostly diffuse Moon at cm/mm waves). 1.0 when the beam is much wider than the Moon."""
    a = moon_diam_deg / 2
    num = den = 0.0
    for i in range(n):
        r = (i + 0.5) / n                      # fraction of the Moon radius
        w = (1 - r ** 2) ** 0.75 * r           # cos^1.5(i)·ring area
        rho = r * a
        num += w * math.exp(-4 * math.log(2) * 2 * rho ** 2 / hpbw ** 2)
        den += w
    return num / den


def echo_power_dbm(p_tx_w: float, gain_dbi: float, f_ghz: float, dist_km: float, moon_diam_deg: float,
                   hpbw: float, atm_oneway_db: float) -> float:
    return (10 * math.log10(p_tx_w * 1000) + 2 * gain_dbi - path_loss_db(f_ghz, dist_km)
            + 10 * math.log10(beam_moon_factor(moon_diam_deg, hpbw)) - 2 * atm_oneway_db)


def noise_dbm(t_sys: float, bw_hz: float) -> float:
    return 10 * math.log10(sky.K_B * t_sys * bw_hz * 1000)


def echo_snr(p_tx_w, gain_dbi, f_ghz, dist_km, moon_diam_deg, hpbw, atm_oneway_db, t_sys_on_moon,
             spread_hz: float) -> dict:
    """Own-echo SNR in 1 Hz and in the libration-spread bandwidth (the useful one at 24/47 GHz)."""
    pe = echo_power_dbm(p_tx_w, gain_dbi, f_ghz, dist_km, moon_diam_deg, hpbw, atm_oneway_db)
    n1 = noise_dbm(t_sys_on_moon, 1.0)
    bw = max(spread_hz, 1.0)
    return {"echo_dbm": pe, "noise_1hz_dbm": n1, "snr_1hz_db": pe - n1, "snr_spread_db": pe - noise_dbm(t_sys_on_moon, bw),
            "spread_hz": bw, "path_loss_db": path_loss_db(f_ghz, dist_km),
            "beam_moon_db": 10 * math.log10(beam_moon_factor(moon_diam_deg, hpbw))}
