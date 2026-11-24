"""0.4.17: RX objective in the wizard, counterbores in the feed base for every flange."""
from feedlab import cad, flanges, geometry, wizard


def test_rx_objective_prefers_low_noise_feeds():
    d = wizard.dish_from_prime(2400, 0.6)
    rx = wizard.recommend(d, 24.048, priority="rx", quick_sim=False)
    assert rx and all(c.kind not in ("open_circular", "rect_horn") for c in rx[:3])
    assert any("RX" in r for c in rx for r in c.reasons)


def test_square_flange_feed_counterbores_adjustable():
    m = flanges.mount("WR-90", "metric", "V", 23.0, f_ghz=10.368, feed_cbore=True, cb_depth=6, cb_dia=9.5)
    assert m.feed_cbore and m.feed_holes
    h = m.feed_holes[0]
    assert h.kind == "cbore_back" and h.cb_depth == 6 and h.cb_dia == 9.5


def test_feed_base_mesh_has_counterbores():
    geometry.MOUNT.clear()
    geometry.MOUNT.update({"wg": "WR-42", "system": "metric", "polarization": "V", "feed_cbore": True})
    try:
        g = geometry.build("w2imu", 24.048, fD=0.6)
        assert any(h.kind == "cbore_back" for h in g.mount.feed_holes)
        v, f = cad.mesh_base(g)
        assert len(v) > 0 and v[:, 2].max() <= g.params["flange_thickness"] + 4.01
    finally:
        geometry.MOUNT.clear()
        geometry.MOUNT.update({"wg": None})
