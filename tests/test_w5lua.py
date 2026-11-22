"""Validation against W5LUA, 'The Excitement & Challenges of 24 GHz EME' (2012).

The numbers come from the VK3UM 'EME Performance Calculator' 7.04 and 'Atmosphere' 1.18 screens and
from the drawing of W5LUA's modified W2IMU feed (24.048 GHz, 2.4 m offset dish, f/D 0.7).
"""
import math

import numpy as np
import pytest

from feedlab import efficiency, modematch, noise

F = 24.048
LAM = 299.792458 / F            # mm


def test_eme_path_and_free_space_loss():
    assert noise.eme_path_loss_db(F, 356_400) == pytest.approx(295.24, abs=0.01)
    assert noise.free_space_loss_db(F, 356_400) == pytest.approx(231.11, abs=0.01)
    # "nearly 2 dB difference in path loss between apogee and perigee"
    d = noise.eme_path_loss_db(F, 406_700) - noise.eme_path_loss_db(F, 356_400)
    assert 2.0 < d < 2.4


def test_dish_gain_and_aperture():
    D, eta = 2.4, 0.66
    g = 10 * math.log10(eta * (math.pi * D / (LAM * 1e-3)) ** 2)
    assert g == pytest.approx(53.83, abs=0.01)
    assert eta * math.pi * D ** 2 / 4 == pytest.approx(2.99, abs=0.01)


def test_beam_fill_moon_and_sun_noise():
    assert noise.beam_fill_factor(0.559, 0.36) == pytest.approx(2.06, abs=0.01)
    assert noise.beam_fill_factor(0.54, 0.36) == pytest.approx(1.98, abs=0.01)
    y_moon = noise.moon_noise_expected_db(213.0, 2.4, 0.66, F, 221.1, 0.36, moon_diam_deg=0.559)
    assert y_moon == pytest.approx(2.23, abs=0.02)
    y_sun = noise.sun_noise_expected_db(732, 2.4, 0.66, F, 221.1, hpbw_deg=0.36)
    assert y_sun == pytest.approx(12.8, abs=0.05)


@pytest.mark.parametrize("el, slant, t_sky", [(45, 0.5346, 32.43), (20, 1.1053, 62.92), (5, 4.3376, 176.90)])
def test_atmosphere_cosec_law_and_sky_noise(el, slant, t_sky):
    a_zen = 0.37802                       # VK3UM's slant values follow one zenith value
    assert noise.slant_atten_db(el, a_zen) == pytest.approx(slant, rel=2e-4)
    t = noise.sky_temp(el, a_zen, t_cmb=0.0, t_atm=280.0)
    assert t == pytest.approx(t_sky, abs=0.05)


def _stair(profile, step):
    secs = []
    for (z0, r0), (z1, r1) in zip(profile[:-1], profile[1:]):
        n = max(1, math.ceil((z1 - z0) / step))
        secs += [(r0 + (r1 - r0) * (i + 0.5) / n, (z1 - z0) / n) for i in range(n)]
    return secs


def test_w5lua_modified_w2imu_feed():
    """Ø11.1 → cone 23° to Ø23.6 (15.62 mm) → cylinder 48.3 mm → flare to Ø76.2 (40.6 mm axial).
    W5LUA: phase centre '~0.1 in (2.54 mm) behind the face of the horn' (end of the cylinder);
    used on a 2.4 m offset dish, f/D 0.7 (equivalent prime-focus f/D ≈ 0.78)."""
    prof = [(0, 5.55), (20, 5.55), (35.62, 11.8), (83.92, 11.8), (124.52, 38.1)]
    r = modematch.simulate(_stair(prof, LAM / 40), [F], n_modes=16)
    assert r.power_balance[0] == pytest.approx(1.0, abs=1e-3)
    assert r.s11_db[0] < -25
    p = modematch.aperture_pattern(r, 0, F, n_rho=40, n_phi=48, n_theta=361)
    d, eta = efficiency.phase_center_by_efficiency(p, 0.78, span_lambda=5.0, step=0.01)
    behind_cylinder_end = -(d * LAM + 40.6)       # mm, + = behind the end of the cylinder
    assert 0.0 < behind_cylinder_end < 5.0
    assert 0.65 < eta < 0.78
