"""Axial Corrugated Feedhorn CT1DMK (parametric calculation OE2IGL), v1.4 spreadsheet, as a FeedLab feed type."""
import pytest

from feedlab import geometry, wizard


def test_axial_corrugated_matches_spreadsheet_47ghz():
    g = geometry.build("axial_corrugated", 47.088, opening_deg=137)
    p = g.params
    assert p["pitch"] == pytest.approx(2.7, abs=0.05)
    assert p["w"] == pytest.approx(1.875, abs=0.05)
    assert p["d1"] == pytest.approx(3.125, abs=0.05)
    assert 80 < p["eta_guide_pct"] < 87
    assert g.mount is None


def test_axial_corrugated_in_wizard_list():
    assert "axial_corrugated" in geometry.FEED_TYPES
    d = wizard.dish_from_prime(1200, 0.4)
    c = wizard.recommend(d, 24.048, quick_sim=False)
    kinds = [x.kind for x in c]
    assert "axial_corrugated" in kinds
    best = c[kinds.index("axial_corrugated")]
    assert 0.75 < best.eta_est < 0.88
    # out of range: 1296 MHz feeds are not FeedLab's business, and above 76 GHz no corrugated
    assert "axial_corrugated" not in [x.kind for x in wizard.recommend(d, 122.25, quick_sim=False)]


def test_axial_corrugated_circular_guide_section_and_base():
    """The head is turned together with a circular guide section (L_guide, default 1 λ) and its base; L_guide = 0
    gives the head alone, as before."""
    g0 = geometry.build("axial_corrugated", 10.368, opening_deg=137, L_guide=0)
    g1 = geometry.build("axial_corrugated", 10.368, opening_deg=137, L_guide=40)
    assert len(g0.polygons) == 1 and g0.params["L_guide"] == 0
    assert len(g1.polygons) == 2 and g1.params["L_guide"] == pytest.approx(40)
    assert g1.length == pytest.approx(g0.length + 40)
    assert g1.profile[0] == (0.0, g0.profile[0][1]) and "flange_diam" in g1.params
    try:
        geometry.BASE.update({"shape": "square", "wg": "WR-90"})
        geometry.MOUNT.update({"wg": "WR-90", "system": "metric", "pol": "V"})
        g2 = geometry.build("axial_corrugated", 10.368, opening_deg=137, L_guide=40)
        assert g2.params["base_square"] == pytest.approx(41.40) and g2.mount is not None
    finally:
        geometry.BASE.update({"shape": "round", "wg": None})
        geometry.MOUNT.update({"wg": None})
