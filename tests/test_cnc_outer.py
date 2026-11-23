"""Optional CNC options for the outside of every feed of revolution: simplified outer profile and outer
fillets. The inner (RF) surface never changes and the wall never gets thinner than 60% of its thickness."""
import pytest

from feedlab import geometry
from feedlab.geometry import _seg_dist

KINDS = [k for k in geometry.FEED_TYPES if k not in ("rect_horn", "axial_corrugated")]


def _build(kind, mode="wall", fillet=0.0):
    geometry.MOUNT.update({"wg": "WR-90", "system": "metric", "pol": "V"})
    geometry.OUTER_PROFILE.update(mode=mode, fillet=fillet)
    try:
        return geometry.build(kind, 10.368, fD=0.65, wall=1.5)
    finally:
        geometry.OUTER_PROFILE.update(mode="wall", fillet=0.0)
        geometry.MOUNT.update({"wg": None})


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("mode", ["wall", "cone1", "hull"])
@pytest.mark.parametrize("fillet", [0.0, 1.0, 5.0])
def test_inside_unchanged_and_wall_kept(kind, mode, fillet):
    g0, g1 = _build(kind), _build(kind, mode, fillet)
    n = len(g0.profile)
    inner0 = [tuple(p) for p in g0.polygons[0][:n - 1]]
    assert [tuple(p) for p in g1.polygons[0][:n - 1]] == inner0
    assert tuple(g1.polygons[0][n - 1]) == tuple(g0.polygons[0][n - 1])        # inner aperture edge stays sharp
    inner = [tuple(p) for p in g1.polygons[0][:n]]
    ft = g1.params["flange_thickness"]
    t = g1.params["wall"]
    outer = [tuple(p) for p in g1.polygons[0][n:] if p[1] > ft + 1e-6]
    d = min(_seg_dist(p, a, b) for p in outer for a, b in zip(inner[:-1], inner[1:]))
    assert d >= 0.6 * t - 1e-6


@pytest.mark.parametrize("kind", KINDS)
def test_fillet_rounds_the_outside(kind):
    g0, g1 = _build(kind), _build(kind, fillet=1.0)
    assert len(g1.polygons[0]) > len(g0.polygons[0])                          # arcs added
    assert g1.params["outer_fillet_R"] == 1.0
    assert any("raccordati R 1" in n for n in g1.notes)
    assert "outer_fillet_R" not in g0.params


def test_options_are_optional_by_default():
    assert geometry.OUTER_PROFILE == {"mode": "wall", "fillet": 0.0}
    g = geometry.build("w2imu", 10.368, fD=0.65)
    assert "outer_profile" not in g.params and "outer_fillet_R" not in g.params


def test_corrugated_never_changed():
    g0, g1 = _build("axial_corrugated"), _build("axial_corrugated", "hull", 2.0)
    assert [p.tolist() for p in g0.polygons] == [p.tolist() for p in g1.polygons]


@pytest.mark.parametrize("kind", ["w2imu", "pickett_potter", "iz0jny", "ve4ma"])
def test_filleted_3d_model_is_valid(kind):
    """The rounded outside goes into the 3D model / STEP: a valid solid, slightly different volume."""
    pytest.importorskip("cadquery")
    from feedlab import cad
    s0, s1 = cad.solid(_build(kind)).val(), cad.solid(_build(kind, "hull", 1.0)).val()
    assert s1.isValid()
    assert abs(s1.Volume() - s0.Volume()) > 1e-3
