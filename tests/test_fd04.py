"""Feed 0.4 f/D: corrugated head optimised with openEMS (fdtd/), as a FeedLab feed type."""
import pytest

from feedlab import drawing, geometry, i18n, wizard
from feedlab.waveguide import wavelength_mm


def test_in_catalogue_with_neutral_name():
    assert geometry.FEED_TYPES["fd04"] == "Feed 0.4 f/D"
    assert i18n.tr(geometry.FEED_TYPES["fd04"], "en") == "Feed 0.4 f/D"
    assert "fd04" in geometry.CORRUGATED_KINDS


@pytest.mark.parametrize("f", [10.368, 24.048])
def test_dimensions_scale_with_wavelength(f):
    g = geometry.build("fd04", f)
    lam = wavelength_mm(f)
    x = geometry.FD04_LAMBDA
    assert g.kind == "fd04"
    assert g.params["pitch"] == pytest.approx(x["pitch"] * lam)
    assert g.params["w"] == pytest.approx(x["w_frac"] * x["pitch"] * lam)
    assert g.params["Di"] == pytest.approx(x["Di"] * lam)
    assert g.params["d1"] == pytest.approx(x["d1"] * lam)
    assert all(g.params[f"d{k}"] == pytest.approx(x["dk"] * lam) for k in range(2, 9))
    assert g.params["pitch"] > g.params["w"]                      # walls between the slots
    assert g.r_input * 2 / lam > 0.586                            # TE11 above cutoff
    assert g.params["eta_guide_pct"] == pytest.approx(100 * geometry.FD04_ETA)
    assert any("openEMS" in n for n in g.notes)


def test_user_edits_win():
    g = geometry.build("fd04", 10.368, d1=5.0)
    assert g.params["d1"] == pytest.approx(5.0)


def test_drawing(tmp_path):
    g = geometry.build("fd04", 24.048)
    p = tmp_path / "fd04.pdf"
    drawing.drawing_pdf(g, p)
    assert p.exists() and p.stat().st_size > 10000


def test_wizard_offers_it_at_fd04_on_10_and_24_ghz_only():
    d = wizard.dish_from_prime(1200, 0.4)
    for f in (10.368, 24.048):
        assert "fd04" in [c.kind for c in wizard.recommend(d, f, quick_sim=False)]
    assert "fd04" not in [c.kind for c in wizard.recommend(d, 47.088, quick_sim=False)]
    assert "fd04" not in [c.kind for c in wizard.recommend(wizard.dish_from_prime(1200, 0.7), 10.368, quick_sim=False)]
