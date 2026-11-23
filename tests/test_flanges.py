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
    if flanges.FLANGES[wg].shape == "square":                                    # IZ0JNY scheme, 10/24 GHz
        assert kinds.count("tap") == 4 and kinds.count("cbore") == 4 and kinds.count("dowel") == 0
        assert m.plate_screw.startswith("M") == (system == "metric")
        assert m.screw.startswith("M") == (system == "metric")
    else:                                                                       # round MIL: stack, no plate screws
        assert m.stack and not m.plate_screw
        assert kinds.count("clear") == 4 and kinds.count("dowel") == 4 and kinds.count("cbore") == 0
        assert sum(h.kind == "tap" for h in m.feed_holes) == 4 and m.screw == "4-40 UNC"
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
    p0 = plate.design_plate(24.048, "WR-42", 9.47, "V")
    p1 = plate.design_plate(24.048, "WR-42", 9.47, "V", holes="metric")
    assert p1.thickness == pytest.approx(p0.thickness)                       # λ/4 section unchanged
    assert p1.body_t >= p1.mount.plate_body_min() and p1.pocket_depth >= 0
    assert p1.outer >= flanges.FLANGES["WR-42"].A
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
    assert g1.params["flange_diam"] >= flanges.FLANGES["WR-22"].A - 1e-9      # base as large as the round flange
    assert g1.params["flange_thickness"] >= t_need - 1e-9
    assert g1.z_aperture - g0.z_aperture == pytest.approx(g1.params["input_length"] - g0.params["input_length"])
    assert sum(h.kind == "tap" for h in m.feed_holes) == 4                   # the guide screws, tapped through
    assert sum(h.kind == "dowel" for h in m.feed_holes) == 4                 # standard dowels align the stack
    sol = cad.solid(g1)
    assert len(sol.faces().vals()) > faces0                                  # hole walls
    pdf = drawing.drawing_pdf(g1, tmp_path / "f.pdf")
    import re
    assert len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes())) == 2       # two sheets


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


def test_from_47ghz_the_flange_dowels_align_the_stack():
    """Round MIL flanges: the 4 standard dowel holes go through the plate into the feed base and align the
    whole stack; no extra plate–feed pins and no plate screws."""
    for f, wg, d in [(47.0, "WR-22", 6.5), (76.0, "WR-12", 3.2), (122.25, "WR-8", 2.2)]:
        m = flanges.mount(wg, "metric", "V", d, f)
        assert not [h for h in m.plate_holes + m.feed_holes if h.kind == "pin"]
        assert sum(h.kind == "dowel" for h in m.plate_holes) == 4 and sum(h.kind == "dowel" for h in m.feed_holes) == 4
        assert not [w for w in m.warnings if "troppo vicino" in w or "nessuna" in w]


def test_pawlan_tm11_ratio_pickett_potter():
    from feedlab import explore
    r = explore.evaluate("pickett_potter", 24.048, explore.Scenario(D_mm=630, fD=0.79))
    q = explore.tm11_power_ratio(r.modes)
    assert explore.TM11_TARGET[0] <= q <= explore.TM11_TARGET[1]            # Pawlan WA6KBL: ≈ 15 %


def test_plate_screw_choices_and_length():
    from feedlab import flanges, plate
    assert flanges.plate_screw_options(10.368) == ["M3", "M4"]
    assert flanges.plate_screw_options(24.048) == ["M2.5", "M3", "M2"]
    assert flanges.screw_length(3.67) == (10.0, "10 mm")          # 7.3 -> 10 (shortest)
    assert flanges.screw_length(7.5)[0] == 16.0                   # 15 -> 16 (tie 14/16 goes up)
    assert flanges.screw_length(8.85)[0] == 18.0                  # 17.7 -> 18
    assert flanges.screw_length(14.0)[0] == 25.0                  # beyond the list: 25
    assert flanges.screw_length(6.0, "imperial")[1] == '1/2"'
    for f, wg, d in ((10.368, "WR-90", 21.0), (24.048, "WR-42", 9.2)):
        for sc in flanges.plate_screw_options(f):
            for system in ("metric", "imperial"):
                p = plate.design_plate(f, wg, d, "V", None, True, holes=system, plate_screw=sc)
                m = p.mount
                assert m.plate_screw == (sc if system == "metric" else flanges.UNC_FOR_METRIC[sc])
                assert m.screw_len == pytest.approx(flanges.screw_length(p.body_t, system)[0])
                # the screw reaches the end of the thread minus margin: length = grip + thread
                cb = flanges.CBORE[m.plate_screw][1]
                assert m.screw_in == pytest.approx(m.screw_len - (p.body_t - cb), abs=1e-6)
                taps = [h for h in m.feed_holes if h.kind == "tap" and m.plate_screw in h.callout]
                assert len(taps) == 4
                for h in taps:          # blind hole: even whole millimetres, thread reaches the screw end
                    assert h.depth % 2 == 0 and m.screw_in <= m.tap_depth < h.depth
                    assert h.depth - m.screw_in < 2 + max(1.0, 3 * flanges.PITCH[m.plate_screw]) + 1e-9


@pytest.mark.parametrize("wg,d", [("WR-90", 22.0), ("WR-90", 15.0), ("WR-75", 22.0), ("WR-62", 16.0)])
def test_plate_screws_symmetric(wg, d):
    """The 4 plate→feed screws sit on the axes or on the diagonals (WR-90 used to get a crooked 40° pattern)."""
    import math
    for pol in "VH":
        m = flanges.mount(wg, "metric", pol, d, 10.368, plate_t=4.0)
        cb = [h for h in m.plate_holes if h.kind == "cbore"]
        ang = math.degrees(math.atan2(cb[0].y, cb[0].x)) % 90
        assert min(abs(ang), abs(ang - 45), abs(ang - 90)) < 1e-6, (wg, pol, ang)


@pytest.mark.parametrize("f,wg,shape,side", [(10.368, "WR-90", "square", 41.40), (10.368, "WR-75", "square", 38.30),
                                             (24.048, "WR-42", "square", 22.41), (47.088, "WR-22", "round", 28.55),
                                             (47.088, "WR-19", "round", 28.55), (76.032, "WR-12", "round", 19.05)])
def test_plate_has_the_shape_and_size_of_the_flange(f, wg, shape, side):
    """Square WR-90/75/42 flanges → square plate; from 47 GHz the MIL flanges are round → round plate,
    as large as the flange (without holes; with holes larger only if the counterbores do not fit)."""
    from feedlab import plate
    d = 0.76 * 299.792458 / f
    p = plate.design_plate(f, wg, d, "V")
    assert p.shape == shape and p.outer == pytest.approx(side)
    ph = plate.design_plate(f, wg, d, "V", holes="metric", plate_screw="M2")
    assert ph.shape == shape and ph.outer >= side - 1e-9
    if ph.outer > side + 0.01:
        assert any("invece di" in w for w in ph.mount.warnings)


def test_round_flange_stack_no_plate_screws():
    """From 47 GHz (round MIL flanges): the plate rests on the feed base, the guide's 4-40 screws pass through
    the plate and are tapped through the base; no plate→feed screws, no counterbores."""
    from feedlab import geometry, plate
    p = plate.design_plate(47.088, "WR-22", 4.84, "V", holes="metric")
    m = p.mount
    assert m.stack and not m.plate_screw and p.shape == "round" and p.outer == pytest.approx(28.55)
    assert {h.kind for h in m.plate_holes} == {"clear", "dowel"}
    assert all(h.depth is None for h in m.feed_holes if h.kind == "tap")
    assert p.body_t == pytest.approx(p.thickness, abs=0.01)
    try:
        geometry.MOUNT.update({"wg": "WR-22", "system": "metric", "pol": "V"})
        for th, expect in ((None, 4.3), (2.0, 2.0), (0.4, 1.0)):
            geometry.BASE.update({"shape": "round", "wg": None, "thickness": th})
            g = geometry.build("iz0jny", 47.088, fD=0.65)
            assert g.params["flange_thickness"] == pytest.approx(expect)
            assert g.params["flange_diam"] == pytest.approx(28.55)
            assert g.mount.screw_in == pytest.approx(expect)        # thread = base thickness
    finally:
        geometry.BASE.update({"shape": "round", "wg": None, "thickness": None})
        geometry.MOUNT.update({"wg": None})


def test_iz0jny_cone_angles_in_lab():
    from feedlab import explore, geometry
    assert {"a1", "a2"} <= {k for k, _, _ in explore.TUNABLE["iz0jny"]}
    g = geometry.build("iz0jny", 24.048, fD=0.65, a1=20, a2=6)
    assert g.params["cone1_half_deg"] == pytest.approx(20) and g.params["cone2_half_deg"] == pytest.approx(6)
