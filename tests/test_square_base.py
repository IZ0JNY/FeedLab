"""Square feed base as large as the square flange of WR-90 / WR-75 / WR-42 (10 and 24 GHz feeds)."""
import pytest

from feedlab import cad, drawing, geometry, i18n


@pytest.fixture(autouse=True)
def _reset():
    yield
    geometry.BASE.update({"shape": "round", "wg": None})
    geometry.MOUNT.update({"wg": None, "plate_screw": None, "plate_t": None})


@pytest.mark.parametrize("wg,f,side", [("WR-90", 10.368, 41.40), ("WR-75", 10.368, 38.30), ("WR-42", 24.048, 22.41)])
def test_square_base_side_and_model(wg, f, side, tmp_path):
    geometry.BASE.update({"shape": "square", "wg": wg})
    g = geometry.build("iz0jny", f, fD=0.65)
    assert g.params["base_square"] == pytest.approx(side)
    assert g.params["flange_diam"] == pytest.approx(side)          # axial section: ± side/2
    v, _ = cad.profile_mesh(g)
    z0 = v[:, 2] < 1e-6
    assert abs(v[z0, 0]).max() == pytest.approx(side / 2, abs=1e-6)   # square, not a disc of radius side/√2
    corner = (abs(abs(v[z0, 0]) - side / 2) < 1e-6) & (abs(abs(v[z0, 1]) - side / 2) < 1e-6)
    assert corner.any()
    bb = cad.solid(g).val().BoundingBox()
    assert bb.xlen == pytest.approx(side, abs=0.01) or bb.xlen > side    # horn may be wider than the base
    assert any("square base" in i18n.tr(n, "en") for n in g.notes)


def test_square_base_with_holes_and_drawing(tmp_path):
    geometry.BASE.update({"shape": "square", "wg": "WR-90"})
    geometry.MOUNT.update({"wg": "WR-90", "system": "metric", "pol": "V"})
    g = geometry.build("w2imu", 10.368, fD=0.65)
    assert g.mount is not None and g.params["base_square"] == pytest.approx(41.40)
    for h in g.mount.feed_holes:
        assert max(abs(h.x), abs(h.y)) + h.dia / 2 < 41.40 / 2
    drawing.drawing_pdf(g, tmp_path / "d.pdf")
    cad.export_step(g, tmp_path / "f.step")
    assert (tmp_path / "f.step").stat().st_size > 1000


def test_round_is_default_and_round_flange_guides_ignored():
    g = geometry.build("iz0jny", 10.368, fD=0.8)
    assert "base_square" not in g.params
    geometry.BASE.update({"shape": "square", "wg": "WR-15"})      # MIL round flange: no square base
    assert "base_square" not in geometry.build("pickett_potter", 76.032, fD=0.8).params


def _self_intersects(poly):
    pts = [tuple(p) for p in poly]
    segs = list(zip(pts, pts[1:] + pts[:1]))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    for i, (a, b) in enumerate(segs):
        for j, (c, d) in enumerate(segs):
            if abs(i - j) <= 1 or {i, j} == {0, len(segs) - 1}:
                continue
            d1, d2, d3, d4 = cross(c, d, a), cross(c, d, b), cross(a, b, c), cross(a, b, d)
            if d1 * d2 < -1e-9 and d3 * d4 < -1e-9:
                return True
    return False


@pytest.mark.parametrize("kind", ["iz0jny", "pickett_potter", "w2imu", "skobelev", "conical"])
@pytest.mark.parametrize("wg,f", [("WR-90", 10.368), ("WR-75", 10.368), ("WR-42", 24.048)])
def test_thick_drilled_flange_does_not_overlap_the_wall(kind, wg, f):
    """IZ0JNY 24 GHz on WR-42: the 8.8 mm drilled flange used to overlap the outer wall of the step."""
    geometry.BASE.update({"shape": "square", "wg": wg})
    geometry.MOUNT.update({"wg": wg, "system": "metric", "pol": "V"})
    g = geometry.build(kind, f, fD=0.65)
    assert not _self_intersects(g.polygons[0])
