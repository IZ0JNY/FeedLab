"""Gerald OE2IGL's axial corrugated feed (v1.4) and Mirek OK2AQ's 24 GHz feeds as FeedLab feed types."""
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


@pytest.mark.parametrize("kind", ["ok2aq_conical", "ok2aq_corrugated"])
def test_ok2aq_scales_with_wavelength(kind):
    g24 = geometry.build(kind, 24.048)
    g10 = geometry.build(kind, 10.368)
    assert kind in geometry.FEED_TYPES and "OK2AQ" in geometry.FEED_TYPES[kind]
    assert any("radio.feec.vutbr.cz" in n for n in g24.notes)
    L24, L10 = g24.length, g10.length
    assert L10 / L24 == pytest.approx(24.048 / 10.368, rel=0.02)


def test_ok2aq_corrugated_flagged_as_interpreted():
    g = geometry.build("ok2aq_corrugated", 24.048)
    assert any("ATTENZIONE" in n for n in g.notes)
    assert "ok2aq_corrugated" not in geometry.MODEMATCH_OK
