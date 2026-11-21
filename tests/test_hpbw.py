"""Dish HPBW from the real feed illumination (aperture integration) vs the Baars beam factor."""
import numpy as np
import pytest

from feedlab import efficiency, patterns, reflector


def test_beam_factor_matches_numerical_pedestal():
    # numerical Hankel transform of a parabolic-on-pedestal illumination
    from scipy.special import j0
    r = np.linspace(0, 1, 3001)
    for te in (0, 10, 20):
        c = 10 ** (-te / 20)
        a = c + (1 - c) * (1 - r ** 2)
        u = np.linspace(1e-4, 3, 3000)
        F = np.array([np.trapezoid(a * j0(x * r) * r, r) for x in u])
        b = 2 * u[np.argmax((F / F[0]) ** 2 < 0.5)] / np.pi
        assert reflector.beam_factor(te) == pytest.approx(b, rel=0.005)


def test_dish_beam_follows_edge_taper():
    lam, D = 299.792458 / 10.368, 600.0
    b = efficiency.dish_beam(patterns.cosq_pattern(2), 0.6, D, lam)
    assert b.hpbw_E_deg == pytest.approx(b.hpbw_H_deg, rel=1e-3)          # symmetric feed
    assert b.beam_factor == pytest.approx(reflector.beam_factor(b.edge_taper_db), rel=0.02)
    # stronger taper -> wider beam, lower sidelobes
    w = efficiency.dish_beam(patterns.cosq_pattern(8), 0.6, D, lam)
    assert w.hpbw_deg > b.hpbw_deg and w.first_sidelobe_db < b.first_sidelobe_db
    # over-illumination (taper < 10 dB) gives a narrower beam than the fixed 10 dB estimate
    assert b.edge_taper_db < 10 and b.hpbw_deg < reflector.hpbw_deg(D, lam, 10)
