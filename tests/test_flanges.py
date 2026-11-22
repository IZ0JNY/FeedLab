"""Fixing holes: standard flange patterns, plate counterbores/pocket, drilled feed flange, STEP and PDF."""
import math

import pytest

from feedlab import cad, credits, drawing, flanges, geometry, plate
from feedlab.waveguide import RECT_WG


@pytest.fixture(autouse=True)
def _no_mount():
    yield
    geometry.MOUNT.update(wg=None, system="metric", pol="V")


def test_flann_patterns():
    f = flanges.FLANGES["WR-90"]
    assert (f.A, f.E, f.F, f.hole) == (41.40, 16.26, 15.49, 4.255)          # UBR 100, Flann
    u = flanges.FLANGES["WR-12"]
    assert u.shape == "round" and u.pcd == pytest.approx(14.29) and u.imperial == "4-40 UNC"   # UG-387/U
    assert set(RECT_WG) <= set(flanges.FLANGES)


@pytest.mark.parametrize("wg", list(RECT_WG))
@pytest.mark.parametrize("system", ["metric", "imperial"])
def test_mount_every_waveguide(wg, system):
    d_circ = 1.1 * RECT_WG[wg].a_mm
    m = flanges.mount(wg, system, "V", d_circ)
    kinds = [h.kind for h in m.plate_holes]
    assert kinds.count("tap") == 4 and kinds.count("cbore") == 4                 # IZ0JNY scheme
    assert kinds.count("dowel") == (0 if flanges.FLANGES[wg].shape == "square" else 4)
    assert m.plate_screw.startswith("M") == (system == "metric")
    assert m.screw.startswith("M") == (system == "metric" and flanges.FLANGES[wg].shape == "square")
    # every plate hole keeps clear of the others and of the circular guide
    hs = m.plate_holes
    for i, a in enumerate(hs):
        ra = max(a.dia, a.cb_dia) / 2
        assert math.hypot(a.x, a.y) - ra > d_circ / 2
        for b in hs[i + 1:]:
            assert math.hypot(a.x - b.x, a.y - b.y) > ra + max(b.dia, b.cb_dia) / 2
    # screws of the standard pass through the standard's holes
    if flanges.FLANGES[wg].hole:
        assert flanges.SCREWS[m.screw][0] < flanges.FLANGES[wg].hole
    assert not [w for w in m.warnings if "troppo vicino" in w]


def test_horizontal_polarisation_rotates_pattern():
    v = flanges.mount("WR-42", "metric", "V", 12.0)
    h = flanges.mount("WR-42", "metric", "H", 12.0)
    pv = sorted((round(x.x, 3), round(x.y, 3)) for x in v.plate_holes if x.kind == "tap")
    ph = sorted((round(-x.y, 3), round(x.x, 3)) for x in h.plate_holes if x.kind == "tap")
    assert sorted(pv) == sorted(ph)


def test_plate_with_holes_counterbores_and_pocket(tmp_path):
    p0 = plate.design_plate(47.088, "WR-22", 6.5, "V")
    p1 = plate.design_plate(47.088, "WR-22", 6.5, "V", holes="metric")
    assert p1.thickness == pytest.approx(p0.thickness)                       # λ/4 section unchanged
    assert p1.body_t >= p1.mount.plate_body_min() and p1.pocket_depth > 0
    assert p1.outer >= flanges.FLANGES["WR-22"].A
    s = plate.plate_solid(p1).val()
    plain = p1.outer ** 2 * p1.body_t
    assert s.Volume() < plain - 10                                           # holes, counterbores, pocket cut
    assert plate.export_step(p1, tmp_path / "p.step").stat().st_size > 10000
    assert plate.drawing_pdf(p1, tmp_path / "p.pdf").stat().st_size > 5000


def test_feed_flange_drilled_in_step_and_pdf(tmp_path):
    g0 = geometry.build("pickett_potter", 47.088, fD=0.7)
    faces0 = len(cad.solid(g0).faces().vals())
    geometry.MOUNT.update(wg="WR-22", system="imperial", pol="V")
    g1 = geometry.build("pickett_potter", 47.088, fD=0.7)
    m = g1.mount
    d_need, t_need = m.feed_flange_min()
    assert g1.params["flange_diam"] >= d_need - 1e-9 and g1.params["flange_thickness"] >= t_need - 1e-9
    assert g1.z_aperture - g0.z_aperture == pytest.approx(g1.params["input_length"] - g0.params["input_length"])
    assert sum(h.kind == "tap" for h in m.feed_holes) == 4                   # the 4 plate → feed screws
    assert sum(h.kind == "pin" for h in m.feed_holes) == 2                   # 47 GHz: alignment pins
    sol = cad.solid(g1)
    assert len(sol.faces().vals()) > faces0                                  # hole walls
    pdf = drawing.drawing_pdf(g1, tmp_path / "f.pdf")
    from pypdf import PdfReader
    assert len(PdfReader(str(pdf)).pages) == 2


def test_issue_url():
    u = credits.issue_url("w2imu", 10.368)
    assert u.startswith(credits.REPO + "/issues/new?") and "FeedLab" in u


def test_iz0jny_24ghz_plate():
    """IZ0JNY's WR-42 plate for his 24 GHz W2IMU (iz0jny.it): circular guide Ø9.50, corner radius 2,
    thickness 3.59, M3 tapped flange holes at (±8.13, ±8.51), 4 M2.5 screws in Ø5.5 × 2.5 counterbores."""
    p = plate.design_plate(24.048, "WR-42", 9.5, "V", 2.0, True, holes="metric")
    assert p.thickness == pytest.approx(3.59, abs=0.02)
    assert p.mount.screw == "M3" and p.mount.plate_screw == "M2.5"
    cb = [h for h in p.mount.plate_holes if h.kind == "cbore"]
    assert len(cb) == 4 and all(h.cb_dia == 5.5 and h.cb_depth == 2.5 for h in cb)
    assert all(abs(math.hypot(h.x, h.y) - 9.0) < 0.5 for h in cb)            # IZ0JNY: on the axes at 9.00
    assert not [h for h in p.mount.plate_holes if h.kind == "pin"]           # below 47 GHz: no pins


def test_pins_from_47ghz():
    assert not [h for h in flanges.mount("WR-22", "metric", "V", 6.5, 46.9).plate_holes if h.kind == "pin"]
    for f, wg, d in [(47.0, "WR-22", 6.5), (76.0, "WR-12", 3.2), (122.25, "WR-8", 2.2)]:
        m = flanges.mount(wg, "metric", "V", d, f)
        assert sum(h.kind == "pin" for h in m.plate_holes) == 2 and sum(h.kind == "pin" for h in m.feed_holes) == 2
        assert not [w for w in m.warnings if "troppo vicino" in w or "nessuna" in w]


def test_pawlan_tm11_ratio_pickett_potter():
    from feedlab import explore
    r = explore.evaluate("pickett_potter", 24.048, explore.Scenario(D_mm=630, fD=0.79))
    q = explore.tm11_power_ratio(r.modes)
    assert explore.TM11_TARGET[0] <= q <= explore.TM11_TARGET[1]            # Pawlan WA6KBL: ≈ 15 %
