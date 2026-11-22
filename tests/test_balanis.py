"""Independent checks against the closed forms of C. A. Balanis, Antenna Theory (Wiley)."""
import math

import numpy as np
import pytest

from feedlab import balanis as B
from feedlab import efficiency, horns, patterns, reflector


@pytest.mark.parametrize("n", [2, 4, 6, 8])
@pytest.mark.parametrize("theta0", [40, 55, 66, 80])
def test_reflector_cosn_efficiency_equals_feedlab_engine(n, theta0):
    p = patterns.cosq_pattern(n / 2, 1441)
    e = efficiency.dish_efficiency(p, reflector.fD_from_half_angle(theta0), 0.0)
    assert e.total == pytest.approx(B.reflector_aperture_efficiency_cosn(n, theta0), abs=2e-4)


def test_reflector_cos2_closed_form_and_optimum():
    t = np.arange(20, 90, 0.5)
    eff = [B.reflector_aperture_efficiency_cos2(x) for x in t]
    assert B.reflector_aperture_efficiency_cos2(66) == pytest.approx(B.reflector_aperture_efficiency_cosn(2, 66), abs=1e-5)
    i = int(np.argmax(eff))
    assert 64 <= t[i] <= 68 and eff[i] == pytest.approx(0.83, abs=0.005)        # Balanis: ~83 % at ~66°


def _aperture_directivity(a1, b1, rho1, rho2, lam, n=801):
    k = 2 * math.pi / lam
    x = np.linspace(-a1 / 2, a1 / 2, n)
    y = np.linspace(-b1 / 2, b1 / 2, n)
    X, Y = np.meshgrid(x, y)
    E = np.cos(math.pi * X / a1) * np.exp(-1j * k * (X ** 2 / (2 * rho2) + Y ** 2 / (2 * rho1)))
    return 4 * math.pi / lam ** 2 * abs(E.sum()) ** 2 / (np.abs(E) ** 2).sum() * (x[1] - x[0]) * (y[1] - y[0])


@pytest.mark.parametrize("AH, AE, L", [(80, 60, 120), (120, 90, 250), (60, 45, 60)])
def test_pyramidal_directivity_fresnel_vs_aperture_integral(AH, AE, L):
    f, a, b = 10.368, 22.86, 10.16
    lam = 299.792458 / f
    rho1, rho2 = L * AE / (AE - b), L * AH / (AH - a)
    d_ref = 10 * math.log10(_aperture_directivity(AH, AE, rho1, rho2, lam))
    assert 10 * math.log10(B.pyramidal_directivity(a, b, AH, AE, rho1, rho2, lam)) == pytest.approx(d_ref, abs=0.02)
    assert horns.pyramidal_gain_dbi(AE, AH, L, a, b, f) == pytest.approx(d_ref, abs=0.02)


def test_pyramidal_long_horn_limit_is_uniform_cosine_aperture():
    lam, a, b, a1, b1 = 28.9, 22.86, 10.16, 80.0, 60.0
    d = B.pyramidal_directivity(a, b, a1, b1, 1e8, 1e8, lam)
    assert d == pytest.approx(4 * math.pi / lam ** 2 * 8 / math.pi ** 2 * a1 * b1, rel=1e-6)


def test_conical_optimum_matches_balanis_phase_loss():
    assert B.conical_phase_loss_db(3 / 8) == pytest.approx(2.91, abs=0.01)
    f, g = 10.368, 20.0
    d = horns.conical_optimum(f, g, 20.0).dims_mm
    lam = 299.792458 / f
    assert B.conical_directivity_db(d["aperture_diam"], d["slant_length"], lam) == pytest.approx(g, abs=0.1)


def test_fundamentals():
    assert B.vswr_from_s11_db(-20) == pytest.approx(1.222, abs=1e-3)
    assert B.s11_db_from_vswr(1.5) == pytest.approx(-13.98, abs=0.01)
    assert B.mismatch_loss_db(-10) == pytest.approx(0.458, abs=1e-3)
    assert 10 * math.log10(B.PLF_LINEAR_CIRCULAR) == pytest.approx(-3.01, abs=0.01)
    assert B.plf_linear(90) == pytest.approx(0, abs=1e-12)
    # Friis: 0 dBm, 0 dBi both ends, 1 km at 10 GHz → −112.4 dBm
    assert B.friis_received_dbm(0, 0, 0, 10.0, 1000.0) == pytest.approx(-112.4, abs=0.05)
    # W5LUA/VK3UM: 53.83 dBi on 2.4 m at 24.048 GHz is 66 % aperture efficiency
    assert B.aperture_efficiency_from_gain(53.83, 2.4, 24.048) == pytest.approx(0.66, abs=0.002)
