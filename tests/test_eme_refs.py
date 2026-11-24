"""Checks against Sergei RW3BP (77 GHz EME antenna, EME 2014), Luis CT1DMK (EME and radio astronomy) and
Luis CT1DMK / Willi LX1DB (circularly polarised feed for 5.7/10 GHz EME)."""
import math

import pytest

from feedlab import balanis as B
from feedlab import noise, reflector


def test_rw3bp_ruze_and_lens():
    assert reflector.ruze_loss_db(0.31, 3.9) == pytest.approx(-4.3, abs=0.05)
    # 0.3 mm deviation seen at 60° from the focus, PTFE: ≈ 1 mm (RW3BP used 1 mm PTFE layers)
    assert reflector.lens_thickness_mm(0.3, 60, 2.1) == pytest.approx(1.0, abs=0.05)


def test_rw3bp_main_beam_efficiency_from_sun():
    y_db = 10 * math.log10(4.3)
    eps = noise.main_beam_efficiency_from_sun(y_db, 1030, 70, 0.77, 7250)
    assert eps == pytest.approx(0.65, abs=0.005)
    assert noise.sun_y_from_main_beam(eps, 1030, 70, 0.77, 7250) == pytest.approx(y_db, abs=1e-9)


def test_rw3bp_jupiter_and_dish():
    assert noise.small_source_y_db(0.33, 44, 400) == pytest.approx(0.004, abs=0.0005)
    # 62.5 dBi on 2.4 m at 77 GHz ↔ aperture efficiency ≈ 0.47
    assert B.aperture_efficiency_from_gain(62.5, 2.4, 77.0) == pytest.approx(0.47, abs=0.01)


def test_ct1dmk_radiometer_and_g_over_t():
    assert noise.dicke_tmin(100.0, 5e6, 1.0) == pytest.approx(0.0447, abs=1e-4)
    # consistency: the Y produced by a source with the antenna's own Ae gives back the same G/T
    f, D, eta, tsys, flux = 1.296, 5.6, 0.6, 50.0, noise.RADIO_SOURCES_1G4["Cassiopeia A (3C461)"]
    lam = 299_792_458.0 / (f * 1e9)
    ae = eta * math.pi * D ** 2 / 4
    dT = 0.5 * flux * noise.JY * ae / noise.K_B
    y_db = 10 * math.log10(1 + dT / tsys)
    g_db = 10 * math.log10(4 * math.pi * ae / lam ** 2)
    assert noise.g_over_t_from_source(y_db, flux, f) == pytest.approx(g_db - 10 * math.log10(tsys), abs=1e-6)


def test_ct1dmk_lx1db_circular_polarisation():
    assert B.xpd_from_axial_ratio_db(1.5) == pytest.approx(21.3, abs=0.1)     # isolation measured: 23 dB
    assert 10 * math.log10(B.plf_elliptical(100, 0)) == pytest.approx(-3.01, abs=0.01)   # linear ↔ CP
    assert B.plf_elliptical(0, 0) == pytest.approx(1.0) and B.plf_elliptical(0, 0, same_sense=False) == pytest.approx(0.0, abs=1e-12)
    assert B.plf_elliptical(100, 100, 90) == pytest.approx(0.0, abs=1e-12)
