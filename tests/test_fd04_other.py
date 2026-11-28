"""Feed 0.4 f/D Chaparral / VE4MA / W2IMU: other feeds optimised with openEMS for f/D 0.4 (fdtd/RISULTATI_fD040.md)."""
import pytest

from feedlab import cad, drawing, geometry, i18n, wizard
from feedlab.waveguide import wavelength_mm

KINDS = ("fd04_chaparral", "fd04_ve4ma", "fd04_w2imu")
# outer diameter and main dimensions in mm at 10.368 GHz, from fdtd/RISULTATI_fD040.md
MM_10G = {"fd04_chaparral": ("horn_diam", 21.31, 111.0), "fd04_ve4ma": ("horn_diam", 22.67, 61.6),
          "fd04_w2imu": ("B_aperture", 26.16, 47.1)}


@pytest.mark.parametrize("k", KINDS)
def test_catalogue_names(k):
    assert geometry.FEED_TYPES[k].startswith("Feed 0.4 f/D ")
    assert i18n.tr(geometry.FEED_TYPES[k], "en") == geometry.FEED_TYPES[k]
    assert all(i18n.tr(n, "en") != n for n in geometry.build(k, 10.368).notes)


@pytest.mark.parametrize("k", KINDS)
def test_dimensions_match_openems_results(k):
    key, v, outer = MM_10G[k]
    g = geometry.build(k, 10.368)
    assert g.kind == k
    assert g.params[key] == pytest.approx(v, abs=0.02)
    assert 2 * g.outer_radius == pytest.approx(outer, abs=0.2)
    g24 = geometry.build(k, 24.048)
    assert g24.params[key] == pytest.approx(v * wavelength_mm(24.048) / wavelength_mm(10.368), rel=1e-3)


def test_user_edits_win():
    assert geometry.build("fd04_chaparral", 10.368, ring_depth=10.0).params["ring_depth"] == pytest.approx(10.0)
    assert geometry.build("fd04_w2imu", 10.368, B=27.0).params["B_aperture"] == pytest.approx(27.0)


@pytest.mark.parametrize("k", KINDS)
def test_drawing_and_step(k, tmp_path):
    g = geometry.build(k, 24.048)
    p = tmp_path / f"{k}.pdf"
    drawing.drawing_pdf(g, p)
    assert p.exists() and p.stat().st_size > 10000
    v, f = cad.mesh(g)
    assert len(v) and len(f)


def test_wizard_offers_them_on_prime_fd04_at_10_and_24_ghz():
    d = wizard.dish_from_prime(3000, 0.4)
    for f in (10.368, 24.048):
        kinds = [c.kind for c in wizard.recommend(d, f, quick_sim=False)]
        assert set(KINDS) <= set(kinds)
    assert not set(KINDS) & {c.kind for c in wizard.recommend(d, 47.088, quick_sim=False)}
    assert not set(KINDS) & {c.kind for c in wizard.recommend(wizard.dish_from_prime(3000, 0.7), 10.368, quick_sim=False)}
