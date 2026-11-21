"""Tests for v0.2 modules: mode matching, plate (OE2IGL), dish catalogue, materials, geometry/CAD."""
import numpy as np
import pytest

from feedlab import dishes, geometry, materials, modematch, plate, explore


def test_modematch_energy_conservation():
    g = geometry.build("large_w2imu", 47.088, fD=0.7)
    r = modematch.simulate(g.staircase(), [45.0, 47.088, 49.0], n_modes=12)
    assert np.allclose(r.power_balance, 1.0, atol=3e-3)
    assert np.all(r.s11_db < -15)


def test_modematch_uniform_guide_no_reflection():
    r = modematch.simulate([(10.0, 30.0)], [10.368], aperture="matched")
    assert abs(r.s11[0]) < 1e-9


def test_large_w2imu_mode_mix_and_peak():
    g = geometry.build("large_w2imu", 10.368, fD=0.8)
    r = modematch.simulate(g.staircase(), [10.368], n_modes=12)
    m = r.aperture_modes[0]
    ratio = abs(m["TM11"] / m["TE11"])
    assert 0.15 < ratio < 0.4          # dual-mode action present


def test_plate_matches_oe2igl_sheet():
    p = plate.design_plate(24.048, "WR-42", 13.35, corner_r_mm=2)
    assert p.basic["a"] == pytest.approx(11.006, abs=2e-3)
    assert p.basic["thickness"] == pytest.approx(3.7815, abs=2e-3)
    assert p.a == pytest.approx(11.4449, abs=2e-3)
    assert p.b == pytest.approx(7.3647, abs=2e-3)
    assert p.thickness == pytest.approx(3.1311, abs=2e-3)


def test_catalogue_gibertini_consistency():
    d = {x.model: x for x in dishes.CATALOG}["OP 65 XP"]
    f, _ = d.focal()
    assert f == pytest.approx(445, abs=10)     # OE2IGL measured 445 mm
    assert d.opening_deg() == 70


def test_material_ordering():
    L = {m: materials.feed_ohmic_loss_db([(4.0, 50.0)], 24.0, materials.MATERIALS[m])
         for m in ("Rame argentato (Ag ≥ 3 µm)", "Rame OFHC (Cu-ETP)", "Ottone CuZn39Pb3", "Acciaio inox AISI 304")}
    v = list(L.values())
    assert v == sorted(v)


def test_step_export_and_evaluate(tmp_path):
    from feedlab import cad
    g = geometry.build("pickett_potter", 76.032, fD=0.7)
    p = cad.export_step(g, tmp_path / "pp.step")
    assert p.read_text()[:13] == "ISO-10303-21;"
    sc = explore.Scenario("offset", 630, 0.79)
    r = explore.evaluate("pickett_potter", 76.032, sc)
    assert 0.6 < r.eta < 0.85 and r.ohmic_db > 0
