"""The metal wall has constant thickness normal to the profile: no zero-thickness annulus at a step."""
import math

import numpy as np
import pytest
from matplotlib.path import Path

from feedlab import geometry


def _self_intersections(P):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    n, bad = len(P), 0
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            a, b, c, d = P[i], P[(i + 1) % n], P[j], P[(j + 1) % n]
            if o(a, b, c) * o(a, b, d) < -1e-12 and o(c, d, a) * o(c, d, b) < -1e-12:
                bad += 1
    return bad


KINDS = [k for k in geometry.FEED_TYPES if k != "rect_horn"]


@pytest.mark.parametrize("kind", KINDS)
def test_wall_polygon_is_simple(kind):
    geo = geometry.build(kind, 10.368, fD=0.6)
    for p in geo.polygons:
        assert _self_intersections([tuple(map(float, x)) for x in p]) == 0


def test_pickett_potter_step_has_metal():
    geo = geometry.build("pickett_potter", 10.368, fD=0.6)
    t = geo.params["wall"]
    poly = Path(np.array([(float(r), float(z)) for r, z in geo.polygons[0]]))
    inner = [(float(r), float(z)) for r, z in geo.polygons[0]]
    # step: two consecutive inner points at the same z, radius increasing
    (r1, zs), (r2, _) = next((a, b) for a, b in zip(inner, inner[1:]) if abs(a[1] - b[1]) < 1e-9 and b[0] > a[0] + 0.1)
    for r in np.linspace(r1 + t + 0.05, r2 - 0.05, 5):
        assert poly.contains_point((r, zs - 0.5 * t)), "annular step wall missing"
    assert not poly.contains_point((0.5 * (r1 + r2), zs + 0.5 * t))       # waveguide above the step stays empty


def test_flare_thickness_is_normal():
    geo = geometry.build("conical", 10.368, fD=0.6)
    t = geo.params["wall"]
    P = [(float(r), float(z)) for r, z in geo.polygons[0]]
    # inner flare segment = the longest non-vertical, non-horizontal segment of the inner side
    segs = [(a, b) for a, b in zip(P, P[1:]) if abs(a[0] - b[0]) > 1e-6 and abs(a[1] - b[1]) > 1e-6]
    (a, b), (c, _) = segs[0], segs[1]
    d = (b[0] - a[0], b[1] - a[1])
    dist = abs((c[0] - a[0]) * d[1] - (c[1] - a[1]) * d[0]) / math.hypot(*d)
    assert dist == pytest.approx(t, rel=1e-6)
