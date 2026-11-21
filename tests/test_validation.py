"""Validation against published numbers (W1GHZ book/papers/spreadsheets, OE2IGL guides, classic theory)."""
import math
import numpy as np
import pytest
from scipy.integrate import quad

from feedlab import patterns as P, efficiency as E, horns as H, cassegrain as C, reflector as R, noise as N
from feedlab.waveguide import wavelength_mm, circular_cutoff_wavelength


def test_waveguide_cutoffs():
    assert circular_cutoff_wavelength(1.0, "TE11") == pytest.approx(1.706, rel=1e-3)
    assert circular_cutoff_wavelength(1.0, "TM11") == pytest.approx(0.820, rel=1e-3)
    assert circular_cutoff_wavelength(1.0, "TM01") == pytest.approx(1.306, rel=1e-3)


def test_space_attenuation_book():
    # W1GHZ ch.6.0: f/D 0.35 -> 3.6 dB, 142 deg; f/D 0.25 -> 6 dB, 180 deg
    assert R.space_attenuation_db(0.35) == pytest.approx(3.6, abs=0.05)
    assert 2 * R.half_angle_from_fD(0.35) == pytest.approx(142, abs=1)
    assert R.space_attenuation_db(0.25) == pytest.approx(6.02, abs=0.01)


@pytest.mark.parametrize("n", [2, 4, 8])
def test_cos_n_against_analytic(n):
    G = lambda t: 2 * (n + 1) * math.cos(t) ** n
    def eta(psi):
        num = quad(lambda t: math.sqrt(G(t)) * math.tan(t / 2), 0, psi)[0]
        return (2 * math.pi * num) ** 2 / (4 * math.pi ** 2 * math.tan(psi / 2) ** 2)
    ref = max(eta(p * math.pi / 180) for p in np.arange(30, 90, 0.1))
    got = E.best_fD(P.cosq_pattern(n / 2, 1441)).total
    assert got == pytest.approx(ref, abs=0.003)


def test_gaussian_closed_forms():
    t, s = R.gaussian_taper_spill(10)
    assert t == pytest.approx(0.902, abs=0.001) and s == pytest.approx(0.90, abs=0.001)


def test_ruze_oe2igl():
    lam = wavelength_mm(122.25)
    assert R.ruze_loss_db(0.1, lam) == pytest.approx(-1.1, abs=0.1)
    assert R.ruze_loss_db(0.1, wavelength_mm(241.92)) == pytest.approx(-4.4, abs=0.2)


def test_w2imu_w1ghz_examples():
    d = H.w2imu(10.368, B_lambda=1.63)          # book 6.5.2: 27.4 deg, 2.8 lambda
    assert d.dims_mm["flare_half_deg"] == pytest.approx(27.4, abs=0.1)
    assert d.in_lambda()["phasing_length_C"] == pytest.approx(2.8, abs=0.03)
    d = H.w2imu(10.368, B_lambda=1.79)          # 24.9 deg, 3.52 lambda
    assert d.dims_mm["flare_half_deg"] == pytest.approx(24.9, abs=0.1)
    assert d.in_lambda()["phasing_length_C"] == pytest.approx(3.52, abs=0.02)


def test_pickett_potter_oe2igl_example():
    d = H.pickett_potter_oe2igl(47.048, 69.2).dims_mm
    assert d["aperture_diam"] == pytest.approx(11.9924, abs=1e-3)
    assert d["flare_length"] == pytest.approx(18.2927, abs=1e-3)
    assert d["input_diam_Di"] == pytest.approx(6.4995, abs=1e-3)


def test_cassegrain_w1ghz_spreadsheet():
    lam = 299.792458 / 10.368
    c = C.design_cassegrain(2438, 0.359, lam, psi_feed_deg=36.545731604625935, feed_diam=59,
                            feed_pc=-0.11 * lam, taper_db=12.36, d_sub=14.3 * lam)
    assert c.M == pytest.approx(2.109, abs=0.001)
    assert c.e == pytest.approx(2.8034, abs=0.001)
    assert c.apex_to_focus == pytest.approx(114.39, rel=0.003)
    assert c.apex_to_feed_pc == pytest.approx(241.25, rel=0.003)
    r = C.kildal_optimum_sub_ratio(2438 / lam, 36.545731604625935, R.half_angle_from_fD(0.359), 12.36)
    assert r == pytest.approx(0.08234, abs=2e-4)


def test_offset_gibertini_illumination():
    g = R.offset_geometry(445, 630, 0)        # OE2IGL: OP65, illumination ~70 deg
    assert g.psi_U == pytest.approx(70.6, abs=0.5)


def test_open_circular_guide_matches_book():
    p = P.circular_aperture_pattern(0.76, {"TE11": 1})
    b = E.best_fD(p)                          # W1GHZ 6.3: ~67% at f/D 0.35-0.4
    assert 0.33 <= b.fD <= 0.42 and 0.62 <= b.total <= 0.72


def test_w2imu_mode_mix_peak_fD():
    p = P.circular_aperture_pattern(1.31, {"TE11": 1, "TM11": 0.15}, n_rho=30, n_phi=36, n_theta=181)
    b = E.best_fD(p, np.arange(0.3, 1.0, 0.02))
    assert 0.5 <= b.fD <= 0.62 and b.total > 0.72


def test_phase_center_shift_recovered():
    p = P.gaussian_pattern(12, 40).shifted(0.37)
    d, _ = E.phase_center_by_efficiency(p, 0.6, span_lambda=1.0, step=0.01)
    assert d == pytest.approx(-0.37, abs=0.02)


def test_planck_correction_oe2igl():
    assert N.planck_temp(23, 47) == pytest.approx(21.9, abs=0.6)
