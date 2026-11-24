"""Feed synthesis helpers: profiled, Dual-Flare family and corrugated geometries are valid and simulate."""
from feedlab import explore, synth

SC = dict(dish_kind="offset", D_mm=2400, fD=0.6905, elev_deg=30, t_rx_K=90, surface_rms_mm=0.4)


def test_profiles_are_monotone_and_simulate():
    p = synth.vec_to_profile([0.76, 0.95, 0.15, 3.5, 1.9] + [0.5] * synth.K)
    pts = p.points_lambda()
    assert all(b[0] >= a[0] for a, b in zip(pts, pts[1:]))
    assert synth.cost([0.76, 0.95, 0.15, 3.5, 1.9] + [0.5] * synth.K, 24.048, SC) < 0


def test_dual_flare_family_reproduces_iz0jny():
    x0 = [0.76, 0.9543, 0.0777, 1.6342, 0.5776, 1.763, 1.8316, 1.3452]
    res, s11, geo = synth.df_evaluate(x0, 24.048, explore.Scenario(**SC), 0.6905)
    ref = explore.evaluate("iz0jny", 24.048, explore.Scenario(**SC), {}, fD_design=0.6905)
    assert abs((res.gain_dbi + res.g_over_t) - (ref.gain_dbi + ref.g_over_t)) < 0.02 and s11 < -25


def test_corrugated_horn_has_slots_and_good_match():
    x = [1.83, 7.2, 0.182, 0.214, 0.315, 6, 0.78]
    pts = synth.corrugated_profile(x)
    assert len(pts) > 40
    res, s11, geo = synth.cg_evaluate(x, 24.048, explore.Scenario(**SC))
    assert s11 < -30 and res.edge_taper_db > 10
