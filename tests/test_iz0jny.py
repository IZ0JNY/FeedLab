"""IZ0JNY Dual-Flare: step + cone 1 + phasing cylinder + cone 2, optimised with the fast solver for EME."""
import pytest

from feedlab import explore, geometry, i18n, openems_sim, wizard
from feedlab.waveguide import wavelength_mm


@pytest.mark.parametrize("f", [10.368, 24.048, 47.088])
@pytest.mark.parametrize("fD", [0.5, 0.6, 0.75, 0.9, 1.1])
def test_builds_and_is_monotone(f, fD):
    g = geometry.build("iz0jny", f, fD=fD)
    p = g.params
    assert p["Di_input"] <= p["Ds_step"] <= p["Dm"] <= p["D_aperture"]
    rs = [r for _, r in g.profile]
    assert rs == sorted(rs)
    assert 3 < g.length / g.lam < 7
    assert g.polygons


def test_fast_solver_close_to_the_limit_with_good_match():
    f = 10.368
    sc = explore.Scenario(dish_kind="offset", D_mm=1200, fD=0.8, elev_deg=30, t_rx_K=40, zenith_atten_db=0.05)
    w = geometry.wall_default(f)
    r = explore.evaluate("iz0jny", f, sc, {}, w, fast=False)
    ref = explore.evaluate("pickett_potter", f, sc, {}, w, fast=False)
    assert r.eta > 0.77
    assert r.s11_db < -28
    assert r.t_ant < ref.t_ant
    assert r.g_over_t > ref.g_over_t


def test_overrides_and_tunables():
    g = geometry.build("iz0jny", 24.048, fD=0.8, Dap=60.0, Lp=20.0)
    assert g.params["D_aperture"] == pytest.approx(60.0)
    assert g.params["Lp"] == pytest.approx(20.0)
    for k, _, _ in explore.TUNABLE["iz0jny"]:
        assert explore.PARAM_FROM_GEOM[k] in g.params


def test_in_wizard_and_translated():
    d = wizard.dish_from_prime(1200, 0.8)
    assert "iz0jny" in [c.kind for c in wizard.recommend(d, 10.368, quick_sim=False)]
    assert i18n.tr(geometry.FEED_TYPES["iz0jny"], "en") == "IZ0JNY Dual-Flare (step + double cone)"


def test_openems_script(tmp_path):
    g = geometry.build("iz0jny", 10.368, fD=0.8)
    p = openems_sim.make_deep_script(g, tmp_path)
    assert p.exists() and "feedlab-openems-config" in p.read_text()


@pytest.mark.parametrize("mode", ["cone1", "hull"])
def test_cnc_outer_profile_keeps_the_inside(mode):
    """Options 1/2 for CNC: only material added outside, inner profile identical, no step next to the base."""
    from feedlab import cad
    try:
        geometry.MOUNT.update({"wg": "WR-90", "system": "metric", "pol": "V"})
        geometry.OUTER_PROFILE["mode"] = "wall"
        g0 = geometry.build("iz0jny", 10.368, fD=0.65, wall=2.0)
        geometry.OUTER_PROFILE["mode"] = mode
        g1 = geometry.build("iz0jny", 10.368, fD=0.65, wall=2.0)
    finally:
        geometry.OUTER_PROFILE["mode"] = "wall"
        geometry.MOUNT.update({"wg": None})
    n = len(g0.profile)
    assert [tuple(p) for p in g1.polygons[0][:n]] == [tuple(p) for p in g0.polygons[0][:n]]
    assert cad.solid(g1).val().Volume() > cad.solid(g0).val().Volume()
    # outer radius never decreases going from the base top to the end of the first cone
    ft = g1.params["flange_thickness"]
    outer = [(z, r) for r, z in g1.polygons[0][n:] if z > ft + 1e-6][::-1]
    rs = [r for z, r in outer[:3]]
    assert rs == sorted(rs)
    # other feeds are never changed
    geometry.OUTER_PROFILE["mode"] = mode
    try:
        w = geometry.build("w2imu", 10.368, fD=0.65)
    finally:
        geometry.OUTER_PROFILE["mode"] = "wall"
    assert "outer_profile" not in w.params
