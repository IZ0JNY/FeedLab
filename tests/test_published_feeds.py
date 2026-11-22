"""Axial Corrugated (base concept Luis CT1DMK, improved version Gerald OE2IGL, v1.4 spreadsheet) as a FeedLab feed type."""
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
