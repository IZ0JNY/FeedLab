"""CAD export (STEP / STL) and 3D mesh for preview, using CadQuery (OpenCascade)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from .geometry import FeedGeometry, RectHornGeometry


def _cq():
    import cadquery as cq  # heavy import, keep lazy
    return cq


def solid(geo) -> "object":
    """CadQuery Workplane with the metal body of the feed (z = 0 at input flange face)."""
    cq = _cq()
    if isinstance(geo, RectHornGeometry):
        return _rect_solid(geo)
    body = None
    for poly in geo.polygons:
        pts = [(float(r), float(z)) for r, z in poly]
        # sketch in XZ plane (x = radius, z = axis) and revolve about the Z axis
        wp = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0))
        body = wp if body is None else body.union(wp)
    mnt = getattr(geo, "mount", None)
    if mnt is not None:                    # holes in the input flange (z = 0 face, axis = Z)
        t = float(geo.params.get("flange_thickness", 3.0))
        for h in mnt.feed_holes:
            depth = t if h.kind == "tap" else min(t, h.depth or t)
            body = body.cut(cq.Workplane("XY").center(h.x, h.y).circle(h.dia / 2).extrude(depth))
    return body


def _rect_solid(geo: RectHornGeometry):
    cq = _cq()
    p = geo.params
    a, b, t = p["a"], p["b"], p["wall"]
    Lin, L = p["input_length"], p["axial_length"]
    AH, AE = p["aperture_H"], p["aperture_E"]
    outer_wg = cq.Workplane("XY").rect(a + 2 * t, b + 2 * t).extrude(Lin)
    inner_wg = cq.Workplane("XY").rect(a, b).extrude(Lin)
    outer_h = (cq.Workplane("XY").workplane(offset=Lin).rect(a + 2 * t, b + 2 * t)
               .workplane(offset=L).rect(AH + 2 * t, AE + 2 * t).loft())
    inner_h = (cq.Workplane("XY").workplane(offset=Lin).rect(a, b)
               .workplane(offset=L).rect(AH, AE).loft())
    flange = cq.Workplane("XY").rect(a + 2 * t + 2 * max(8.0, 0.3 * geo.lam), b + 2 * t + 2 * max(8.0, 0.3 * geo.lam)).extrude(max(2.0, 0.1 * geo.lam))
    body = outer_wg.union(outer_h).union(flange).cut(inner_wg).cut(inner_h)
    return body


def export_step(geo, path: str | Path) -> Path:
    cq = _cq()
    path = Path(path)
    cq.exporters.export(solid(geo), str(path), exportType="STEP")
    return path


def export_stl(geo, path: str | Path, tol: float | None = None) -> Path:
    cq = _cq()
    path = Path(path)
    tol = tol or max(0.01, geo.lam / 200)
    cq.exporters.export(solid(geo), str(path), exportType="STL", tolerance=tol, angularTolerance=0.1)
    return path


def mesh(geo, tol: float | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Triangle mesh (vertices Nx3, faces Mx3) for 3D preview."""
    tol = tol or max(0.02, geo.lam / 60)
    shape = solid(geo).val()
    verts, tris = shape.tessellate(tol, 0.2)
    v = np.array([(p.x, p.y, p.z) for p in verts])
    f = np.array(tris, dtype=int)
    return v, f


def profile_mesh(geo: FeedGeometry, n_phi: int = 72, cut_deg: float = 0.0):
    """Lightweight surface-of-revolution mesh straight from the polygons (no OpenCascade).
    cut_deg > 0 removes a wedge to show the interior."""
    V, F = [], []
    phi0 = math.radians(cut_deg)
    phis = np.linspace(phi0, 2 * math.pi, n_phi)
    for poly in geo.polygons:
        P = np.vstack([poly, poly[:1]])
        base = len(V)
        for ph in phis:
            for r, z in P:
                V.append((r * math.cos(ph), r * math.sin(ph), z))
        n = len(P)
        for i in range(len(phis) - 1):
            for j in range(n - 1):
                a = base + i * n + j; b = a + n
                F.append((a, b, a + 1)); F.append((a + 1, b, b + 1))
    return np.array(V), np.array(F)
