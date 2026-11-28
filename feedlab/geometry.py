"""Parametric feed geometry.

Rotationally symmetric feeds are described by
  * an *inner profile*: list of (z, r) points of the waveguide/horn wall (z = 0 at the input port,
    increasing toward the aperture), piecewise linear, vertical segments = steps;
  * a list of *metal polygons* in the (r, z) half-plane, to be revolved around the z axis
    (used for CAD/STEP, openEMS AddRotPoly, the 3D preview and the drawing).
Rectangular (pyramidal) horns are handled by `RectHornGeometry`.
All lengths in mm.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import horns
from .waveguide import wavelength_mm

DEG = math.pi / 180.0

FEED_TYPES = {
    "open_circular": "Guida circolare aperta (coffee-can)",
    "w2imu": "W2IMU dual-mode",
    "w2imu_oe2igl": "W2IMU Dual-Mode Feedhorn, parametric calculation OE2IGL",
    "large_w2imu": "Large W2IMU flare 30°, W1GHZ/W1FKF",
    "skobelev": "Dual-mode 'optimum' Skobelev, W1GHZ",
    "pickett_potter": "Pickett-Potter",
    "conical": "Horn conico",
    "ve4ma": "VE4MA / Super-VE4MA (choke)",
    "chaparral": "Chaparral 3 anelli",
    "axial_corrugated": "Axial Corrugated Feedhorn CT1DMK, parametric calculation OE2IGL",
    "rect_horn": "Tromba rettangolare, G3RPE",
    "iz0jny": "Dual-Flare, IZ0JNY",
    "fd04": "Feed 0.4 f/D",
}

# feeds built as axial-corrugated heads (8 axial slots on a stepped face): same drawing, editing and CAD rules
CORRUGATED_KINDS = {"axial_corrugated", "fd04"}

# amateur band names used in short titles: (low GHz, high GHz, label)
_BANDS = [(1.24, 1.30, "1.2"), (2.30, 2.45, "2.3"), (3.30, 3.50, "3.4"), (5.65, 5.925, "5.7"), (10.0, 10.5, "10"),
          (24.0, 24.25, "24"), (47.0, 47.2, "47"), (75.5, 81.0, "76"), (119.98, 123.0, "122"), (134.0, 141.0, "134"),
          (241.0, 250.0, "241")]


def band_label(f_ghz: float) -> str:
    """Short frequency for titles: the amateur band name (24.048 -> "24"), else rounded."""
    for lo, hi, lab in _BANDS:
        if lo <= f_ghz <= hi:
            return lab
    return f"{f_ghz:.0f}" if f_ghz >= 10 else f"{f_ghz:.1f}"


def short_title(feed_name: str, f_ghz: float | None = None) -> str:
    """Short title of a design: feed name without "Feedhorn", band in GHz ("W2IMU Dual-Mode, parametric
    calculation OE2IGL 24 GHz"). Tabs and tables keep the full name and the exact frequency."""
    name = feed_name.replace(" Feedhorn", "")
    return f"{name} {band_label(f_ghz)} GHz" if f_ghz else name


# feeds whose interior is a single circular guide with steps/cones -> mode-matching simulation possible
MODEMATCH_OK = {"open_circular", "w2imu", "w2imu_oe2igl", "large_w2imu", "skobelev", "pickett_potter", "conical", "iz0jny"}


@dataclass
class FeedGeometry:
    kind: str
    f_ghz: float
    params: dict                       # design parameters (mm / deg)
    profile: list                      # inner wall [(z, r)], z from input (0) to aperture (z_ap)
    polygons: list                     # metal cross-sections [(r, z) arrays] to revolve
    z_aperture: float
    r_aperture: float
    r_input: float
    outer_radius: float
    notes: list = field(default_factory=list)
    design: horns.Design | None = None

    @property
    def lam(self) -> float:
        return wavelength_mm(self.f_ghz)

    @property
    def length(self) -> float:
        return self.z_aperture

    def blockage_diameter(self) -> float:
        return 2 * self.outer_radius

    def staircase(self, max_step_mm: float | None = None) -> list[tuple[float, float]]:
        """Interior as a list of uniform sections (radius, length) for mode matching."""
        max_step = max_step_mm or self.lam / 40
        secs = []
        pts = self.profile
        for (z0, r0), (z1, r1) in zip(pts[:-1], pts[1:]):
            L = z1 - z0
            if L <= 1e-9:          # step: radius change at constant z -> handled by next section
                continue
            if abs(r1 - r0) < 1e-9:
                secs.append((r0, L))
            else:
                n = max(1, int(math.ceil(L / max_step)))
                for i in range(n):
                    rm = r0 + (r1 - r0) * (i + 0.5) / n
                    secs.append((rm, L / n))
        # merge consecutive equal radii
        out = []
        for r, L in secs:
            if out and abs(out[-1][0] - r) < 1e-9:
                out[-1] = (r, out[-1][1] + L)
            else:
                out.append((r, L))
        return out


def _offset_outer(inner, t):
    """Outer surface of a wall of constant thickness t (measured normal to the wall) around the inner
    profile [(r, z)] that runs from the input (z = 0) to the aperture. Each segment is moved by t along its
    outward normal and consecutive offset lines meet in a sharp (mitred) corner, so a radial step (a flat
    annulus at constant z) gets an annular wall t thick between the guide below and the one above —
    a purely radial offset gives that annulus zero thickness. The two ends stay on the input and aperture
    planes, so the rim and the flange face remain flat."""
    pts = [inner[0]]
    for q in inner[1:]:                                   # drop zero-length segments
        if math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) > 1e-9:
            pts.append(q)
    segs = []
    for (r0, z0), (r1, z1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(r1 - r0, z1 - z0)
        dr, dz = (r1 - r0) / L, (z1 - z0) / L
        nr, nz = dz, -dr                                  # outward normal (right of the direction of travel)
        segs.append(((r0 + t * nr, z0 + t * nz), (dr, dz)))
    merged = [segs[0]]                                    # collinear neighbours: one line
    for sg in segs[1:]:
        (_, d0), (_, d1) = merged[-1], sg
        if abs(d0[0] * d1[1] - d0[1] * d1[0]) < 1e-9 and d0[0] * d1[0] + d0[1] * d1[1] > 0:
            continue
        merged.append(sg)

    def cross(a, b):
        (p, d), (q, e) = a, b
        den = d[0] * e[1] - d[1] * e[0]
        k = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        return (p[0] + k * d[0], p[1] + k * d[1])

    def at_z(line, z):
        (p, d) = line
        if abs(d[1]) < 1e-12:                             # flat line: cannot reach the end plane
            return (p[0], z)
        k = (z - p[1]) / d[1]
        return (p[0] + k * d[0], z)

    z_in, z_ap = pts[0][1], pts[-1][1]
    out = [at_z(merged[0], z_in)]
    out += [cross(a, b) for a, b in zip(merged[:-1], merged[1:])]
    out.append(at_z(merged[-1], z_ap))
    return out


def wall_features(profile, tol: float = 1e-6) -> dict:
    """Radial steps and flares of an inner profile [(z, r)], for dimensioning drawings.
    steps: [(z, r_from, r_to)]; flares: [(z0, r0, z1, r1, half_angle_deg)] (taper segments)."""
    steps, flares = [], []
    for (z0, r0), (z1, r1) in zip(profile[:-1], profile[1:]):
        if abs(z1 - z0) < tol and abs(r1 - r0) > tol:
            steps.append((z0, r0, r1))
        elif abs(z1 - z0) > tol and abs(r1 - r0) > tol:
            flares.append((z0, r0, z1, r1, math.degrees(math.atan2(r1 - r0, z1 - z0))))
    return {"steps": steps, "flares": flares}


def _wall_polygon(profile, t, flange_r=None, flange_t=None):
    """Metal cross-section of a horn wall of thickness t following the inner profile (r, z).
    Outer surface: the inner profile offset by t normal to the wall (constant thickness, steps included).
    Optional input flange (disk) at z=0."""
    inner = [(r, z) for z, r in profile]
    outer = _offset_outer(inner, t)[::-1]
    # rim at aperture is flat; at input add flange if requested
    poly = inner + outer
    if flange_r and flange_t:
        r_in = profile[0][1]
        # outer wall down to one wall thickness above the flange, then straight onto it: a step or cone that
        # starts just above a thick flange is filled solid (no thin neck, no wall dipping into the flange)
        keep = []
        for p in outer[:-1]:
            if p[1] < flange_t + t - 1e-9:
                break
            keep.append(p)
        keep = keep or outer[:1]
        r_out0 = keep[-1][0]
        poly = inner + keep + [(r_out0, flange_t), (flange_r, flange_t), (flange_r, 0.0), (r_in, 0.0)]
    return np.array(poly)


def _upper_envelope(pts):
    """Upper concave envelope of (z, r) points: the smallest outline without dents that contains them."""
    h = []
    for p in sorted(set(pts)):
        while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) >= -1e-12:
            h.pop()
        h.append(p)
    return h


def cnc_outer(poly, n_inner: int, flange_t: float, mode: str):
    """Outer surface simplified for CNC turning/milling, inner surface untouched (material only added):
    "cone1": solid from the base up to the end of the first cone (no step / neck next to the base);
    "hull": the whole outside without dents. Anything else: constant wall (unchanged)."""
    if mode not in ("cone1", "hull") or not flange_t:
        return poly
    P = [tuple(map(float, p)) for p in poly]
    inner, rest = P[:n_inner], P[n_inner:]
    k = next((i for i, (r, z) in enumerate(rest) if abs(z - flange_t) < 1e-9), None)
    if k is None:
        return poly
    outer, tail = rest[:k + 1], rest[k + 1:]
    zr = [(z, r) for r, z in outer][::-1]                     # from the base top to the aperture
    if mode == "hull":
        new = _upper_envelope(zr)
    else:
        i_end = None                                          # end of the first cone (slope drops after it)
        for i in range(1, len(zr) - 1):
            (z0, r0), (z1, r1), (z2, r2) = zr[i - 1], zr[i], zr[i + 1]
            if z1 > z0 + 1e-9 and r1 > r0 + 1e-9 and (z2 <= z1 + 1e-9 or (r2 - r1) / (z2 - z1) < (r1 - r0) / (z1 - z0) - 1e-6):
                i_end = i
                break
        if i_end is None:
            return poly
        new = _upper_envelope(zr[:i_end + 1]) + zr[i_end + 1:]
    return np.array(inner + [(r, z) for z, r in new[::-1]] + tail)


def _seg_dist(p, a, b) -> float:
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - u * dx, p[1] - ay - u * dy)


def _arc(a, b, c, r, step_deg=10.0):
    """Points of the fillet of radius r at corner b (a → b → c), or None if the corner is (almost) straight."""
    u1 = np.subtract(a, b, dtype=float); u2 = np.subtract(c, b, dtype=float)
    l1, l2 = np.linalg.norm(u1), np.linalg.norm(u2)
    if l1 < 1e-9 or l2 < 1e-9:
        return None
    u1, u2 = u1 / l1, u2 / l2
    alpha = math.acos(max(-1.0, min(1.0, float(u1 @ u2))))   # angle between the two edges at b
    if alpha > math.radians(178) or alpha < math.radians(2):
        return None
    d = r / math.tan(alpha / 2)                                # tangent length
    dmax = 0.5 * min(l1, l2)                                   # never past the middle of an edge
    if d > dmax:
        d, r = dmax, dmax * math.tan(alpha / 2)
    if r < 1e-3:
        return None
    w = (u1 + u2) / np.linalg.norm(u1 + u2)
    ctr = np.asarray(b, float) + w * (r / math.sin(alpha / 2))
    p1, p2 = np.asarray(b, float) + u1 * d, np.asarray(b, float) + u2 * d
    t1, t2 = math.atan2(*(p1 - ctr)[::-1]), math.atan2(*(p2 - ctr)[::-1])
    dt = (t2 - t1 + math.pi) % (2 * math.pi) - math.pi        # the short way round
    n = max(2, int(math.ceil(abs(math.degrees(dt)) / step_deg)) + 1)
    return [tuple(ctr + r * np.array([math.cos(t1 + dt * k / (n - 1)), math.sin(t1 + dt * k / (n - 1))]))
            for k in range(n)], r


def fillet_outer(poly, n_inner: int, flange_t, radius: float, wall: float):
    """Round the outer edges (aperture rim, steps, joint with the base) with radius `radius`; the inner (RF)
    surface keeps sharp edges. Where a convex fillet would leave less than 60% of the wall, its radius is
    reduced. Returns (polygon, smallest radius actually used or None)."""
    if not radius or radius <= 0:
        return poly, None
    P = [tuple(map(float, p)) for p in poly]
    inner, rest = P[:n_inner], P[n_inner:]
    k = next((i for i, (r, z) in enumerate(rest) if flange_t and abs(z - flange_t) < 1e-9), None)
    if k is not None and k + 1 < len(rest):
        chain_end = k + 1                     # up to the base top (outer edge of the base stays as it is)
    else:
        chain_end = len(rest) - 1             # no base: up to the outer edge of the input face
    chain = [inner[-1]] + rest[:chain_end + 1]
    min_wall = 0.6 * wall if wall else 0.0
    inner_segs = list(zip(inner[:-1], inner[1:]))
    out = [chain[0]]
    used = []
    for i in range(1, len(chain) - 1):
        a, b, c = chain[i - 1], chain[i], chain[i + 1]
        r_try = radius
        arc = None
        for _ in range(8):
            res = _arc(a, b, c, r_try)
            if res is None:
                break
            pts, r_eff = res
            if not min_wall or min(_seg_dist(p, s0, s1) for p in pts for s0, s1 in inner_segs) >= min_wall - 1e-9:
                arc = res
                break
            r_try *= 0.5
        if arc is None:
            out.append(b)
        else:
            out.extend(arc[0])
            used.append(arc[1])
    out.append(chain[-1])
    new = inner[:-1] + out + rest[chain_end + 1:]
    return np.array(new), (min(used) if used else None)


# outer profile of every feed of revolution: "wall" constant wall (default), "cone1" / "hull" simplified for CNC;
# "fillet": radius (mm) of the outer edges, 0 = sharp edges
OUTER_PROFILE = {"mode": "wall", "fillet": 0.0}

COLLAR = {"diam": None, "length": 25.0, "z0": 3.0}    # set COLLAR["diam"] = 40 for standard LNB holders
# bolted stack WR component | λ/4 plate | feed: set MOUNT["wg"] (e.g. "WR-28") to drill the feed flange
MOUNT = {"wg": None, "system": "metric", "pol": "V", "plate_screw": None, "plate_t": None}
# base of the feed: "round" (disc) or "square" = same size as the square flange of BASE["wg"] (WR-90, WR-75, WR-42…)
BASE = {"shape": "round", "wg": None, "thickness": None}     # thickness None = automatic


def square_base_side() -> float | None:
    """Side (mm) of the square base when chosen and the waveguide has a square standard flange, else None."""
    if BASE.get("shape") != "square":
        return None
    from .flanges import FLANGES
    fl = FLANGES.get(BASE.get("wg") or MOUNT.get("wg") or "")
    return fl.A if fl is not None and fl.shape == "square" else None


def _finish(kind, f, params, profile, t, extra_polys=None, notes=None, design=None, flange=True):
    lam = wavelength_mm(f)
    mnt = None
    if flange and MOUNT.get("wg"):
        from .flanges import mount
        mnt = mount(MOUNT["wg"], MOUNT.get("system", "metric"), MOUNT.get("pol", "V"), 2 * profile[0][1], f,
                    MOUNT.get("plate_screw"), MOUNT.get("plate_t"), MOUNT.get("base_holes") or "flange",
                    MOUNT.get("hole_dia"), MOUNT.get("thread"), bool(MOUNT.get("cbore")),
                    MOUNT.get("cb_depth"), MOUNT.get("cb_dia"), MOUNT.get("pins", True),
                    MOUNT.get("plate_head") or "allen", bool(MOUNT.get("plate_tap")), MOUNT.get("plate_hole_dia"),
                    MOUNT.get("plate_cb_dia"), MOUNT.get("plate_cb_depth"))
        d_need, t_need = mnt.feed_flange_min()
    # base (flange) thickness: chosen by the user (≥ 1 mm) or automatic (enough for the threaded holes)
    t_user = BASE.get("thickness")
    fl_t = (max(1.0, float(t_user)) if t_user else
            max(max(1.5, 0.12 * lam), t_need if mnt is not None else 0.0)) if flange else None
    if mnt is not None:
        if mnt.feed_cbore:                         # through holes: screws from the feed side, grip = base under the head
            cbk = max((h.cb_depth for h in mnt.feed_holes if h.kind == "cbore_back"), default=0.0)
            mnt.guide_in = max(fl_t - cbk, 0.0)
            notes = list(notes or []) + [f"viti {mnt.screw} dal lato del feed: lunghezza ≈ {max(fl_t - cbk, 0):.1f} mm (base sotto "
                                         "la testa) + spessore piastrina + ~4 mm nella flangia della guida"]
            if cbk and fl_t < cbk + 0.8:
                notes = list(notes) + [f"base {fl_t:.2f} mm troppo sottile per la lamatura ({cbk:g} mm): aumentala"]
            # horn body around the screw heads: close to the base (head + hex key, ~12 mm) it must leave them
            # free; higher up a flare may overhang them (an L hex key still reaches the screw)
            from .flanges import HEADS
            heads = [math.hypot(h.x, h.y) - (h.cb_dia or HEADS[mnt.screw][0]) / 2
                     for h in mnt.feed_holes if h.kind == "cbore_back"]
            r_low = max((r for z, r in profile if z <= fl_t + 12.0), default=profile[0][1]) + t + 0.3
            r_all = max(r for _, r in profile) + t + 0.3
            if any(d < r_low for d in heads):
                notes = list(notes) + ["le teste delle viti toccano il corpo del feed: allunga la guida d'ingresso "
                                       "o usa i fori filettati nella base"]
            elif any(d < r_all for d in heads):
                notes = list(notes) + ["la svasatura del feed sovrasta le viti: per serrarle serve una chiave a "
                                       "brugola a L (non un cacciavite dritto)"]
        else:                                      # threaded through: the thread is the whole base
            from .flanges import SCREWS
            mnt.guide_in = fl_t
            t_thr = max(3.0, 1.5 * SCREWS[mnt.thread][0])
            if fl_t < t_thr - 1e-9:
                notes = list(notes or []) + [f"base {fl_t:.2f} mm: filetto {mnt.thread} utile {fl_t:.2f} mm "
                                             f"(consigliati ≥ {t_thr:.1f} mm)"]
        if fl_t < t_need - 1e-9 and mnt.screw_len:
            # plate→feed screws: the longest commercial one whose tip stays inside the base
            from .flanges import CBORE, LENGTHS_IN, LENGTHS_MM
            grip = max((MOUNT.get("plate_t") or 0.0) - mnt.plate_grip_cut, 0.0)   # plate under the head
            short_in = [(1 / 8, '1/8"'), (3 / 16, '3/16"'), (1 / 4, '1/4"'), (5 / 16, '5/16"')]
            opts = ([(v * 25.4, lab) for v, lab in short_in + list(LENGTHS_IN)] if MOUNT.get("system") == "imperial"
                    else [(float(v), f"{v} mm") for v in [3, 4, 5, 6, 8] + list(LENGTHS_MM)])
            fit = [o for o in opts if o[0] <= grip + fl_t + 1e-9]
            if fit:
                mnt.screw_len, mnt.screw_len_label = fit[-1]
                mnt.screw_in = mnt.screw_len - grip
                notes = list(notes or []) + [f"viti piastrina→feed {mnt.plate_screw} × {mnt.screw_len_label}: "
                                             f"entrano {mnt.screw_in:.1f} mm nella base"]
        if fl_t < t_need - 1e-9 and mnt.plate_screw:
            # thinner than the tapped holes need: they go through; the thread length is the base thickness
            for h in mnt.feed_holes:
                if h.depth is not None and h.depth > fl_t:
                    h.depth = None
                    if h.kind == "tap":
                        h.callout = h.callout.split(" filetto")[0] + " filettato passante"
                    elif h.kind == "dowel":
                        h.callout = h.callout.split(" prof.")[0] + " passante"
            notes = list(notes or []) + [f"base {fl_t:.2f} mm: fori filettati passanti, filetto utile {fl_t:.2f} mm "
                                         f"(consigliati ≥ {t_need:.1f} mm)"]
        # the base must sit on the straight input guide: lengthen it if needed (electrically benign)
        r0 = profile[0][1]
        z_first = profile[1][0] if abs(profile[1][1] - r0) < 1e-9 else 0.0
        # the wall after the input guide (step, cone) is offset by t towards the input: keep it clear of the
        # flange top (t + 0.5 mm), otherwise the outer wall would dip into the flange
        if fl_t + t + 0.5 > z_first:
            d = fl_t + t + 0.5 - z_first
            rest = profile[2:] if z_first > 0 else profile[1:]
            profile = [(0.0, r0), (z_first + d, r0)] + [(z + d, r) for z, r in rest]
            if "input_length" in params:
                params = {**params, "input_length": params["input_length"] + d}
            notes = list(notes or []) + [f"guida d'ingresso allungata di {d:.2f} mm per la flangia forata"]
    if COLLAR.get("diam"):
        rc = COLLAR["diam"] / 2
        r_wall = profile[0][1] + t
        L = profile[-1][0]
        z0 = COLLAR.get("z0", 3.0)
        z1 = min(z0 + COLLAR.get("length", 25.0), L - 1.0)
        if rc > r_wall + 0.2 and z1 > z0 + 1:
            extra_polys = list(extra_polys or []) + [[(r_wall, z0), (rc, z0), (rc, z1), (r_wall, z1)]]
            # if the feed widens inside the collar, only fill where the horn is smaller (CAD union handles overlap)
            notes = list(notes or []) + [f"collare Ø{COLLAR['diam']} mm × {z1 - z0:.0f} mm per portaLNB standard"]
    r_ap = profile[-1][1]
    outer = max(r for _, r in profile) + t
    polys = []
    fl_r = profile[0][1] + t + max(2.0, 0.4 * lam) if flange else None
    if mnt is not None:
        if mnt.flange.shape == "round":           # round MIL flange: base as large as the flange (holes inside)
            from .flanges import HEADS
            head = HEADS[mnt.screw][0] if mnt.feed_cbore else 0.0       # through holes: the head rests on the base
            edge = max(math.hypot(h.x, h.y) + max(h.dia, h.cb_dia, head if h.kind == "cbore_back" else 0) / 2
                       for h in mnt.feed_holes)
            fl_r = max(fl_r, mnt.flange.A / 2, edge + 0.5)
        else:
            fl_r = max(fl_r, d_need / 2)
    side = square_base_side() if flange else None
    if side:
        # square base as large as the waveguide flange: in the axial section (cut along x or y) it is ±side/2;
        # the corners are added in the 3D model / STEP. Holes on the diagonals fall in the corners.
        if side / 2 < profile[0][1] + t + 1.0:
            notes = list(notes or []) + [f"base quadrata {side:.2f} mm troppo piccola per questo feed: base circolare"]
            side = None
        else:
            # holes and counterbores always inside the base, with at least 0.8 mm of wall: if the standard
            # flange is too small for them (e.g. WR-42 22.41 mm with M3 counterbores) the square grows
            from .flanges import HEADS
            head = HEADS[mnt.screw][0] if mnt is not None and mnt.feed_cbore else 0.0   # plain holes: head on the base
            need = 2 * (max((max(abs(h.x), abs(h.y)) + max(h.dia, h.cb_dia, head if h.kind == "cbore_back" else 0) / 2
                             for h in mnt.feed_holes), default=0.0) + 0.8) if mnt is not None else 0.0
            wg_name = BASE.get('wg') or MOUNT.get('wg')
            if need > side + 1e-9:
                notes = list(notes or []) + [f"base quadrata allargata a {math.ceil(need * 10) / 10:.2f} mm "
                                             f"per tenere fori e lamature all'interno (flangia {wg_name}: {side:.2f} mm)"]
                side = math.ceil(need * 10) / 10
            else:
                notes = list(notes or []) + [f"base quadrata {side:.2f} × {side:.2f} mm come la flangia {wg_name}"]
            fl_r = side / 2
    if mnt is not None:
        notes = list(notes or []) + [f"flangia forata per {mnt.flange.wg} {mnt.flange.name}: {mnt.screw}, "
                                     f"{sum(h.kind == 'dowel' for h in mnt.feed_holes)} fori spina"] + mnt.warnings
    wall_poly = _wall_polygon(profile, t, fl_r, fl_t)
    # optional CNC outer profile and outer fillets (every feed of revolution; the Axial Corrugated input tube is
    # joined to the corrugated head, where a fillet would leave a groove)
    cnc_ok = kind not in CORRUGATED_KINDS
    mode = OUTER_PROFILE.get("mode", "wall") if cnc_ok else "wall"
    if mode != "wall":
        simpler = cnc_outer(wall_poly, len(profile), fl_t, mode)
        if simpler is wall_poly or np.array_equal(simpler, wall_poly):
            notes = list(notes or []) + [{"cone1": "profilo esterno: nessun primo cono da riempire, parete costante",
                                          "hull": "profilo esterno: già senza rientranze"}.get(mode, "")]
        else:
            wall_poly = simpler
            params = {**params, "outer_profile": mode}
            notes = list(notes or []) + [{"cone1": "esterno pieno fino alla fine del 1° cono (interno invariato)",
                                          "hull": "esterno senza rientranze (interno invariato)"}[mode]]
    if OUTER_PROFILE.get("fillet") and cnc_ok:
        wall_poly, r_used = fillet_outer(wall_poly, len(profile), fl_t, float(OUTER_PROFILE["fillet"]), t)
        if r_used is not None:
            R = float(OUTER_PROFILE["fillet"])
            params = {**params, "outer_fillet_R": R}
            notes = list(notes or []) + [f"spigoli esterni raccordati R {R:g} mm" + (
                "" if r_used >= R - 1e-6 else
                f" (minimo R {r_used:.2f} mm sul bordo dell'apertura e dove la parete è sottile)") +
                "; interno a spigolo vivo"]
    polys.append(wall_poly)
    for p in extra_polys or []:
        polys.append(np.asarray(p))
        outer = max(outer, max(x for x, _ in p))
    if fl_r:
        outer = max(outer, fl_r) if fl_r > outer else outer
    if fl_r:
        params = {**params, "flange_diam": 2 * fl_r, "flange_thickness": fl_t}
    if side:
        params = {**params, "base_square": side}
        outer = max(outer, side / math.sqrt(math.pi))      # blockage: circle of the same area as the square
    g = FeedGeometry(kind, f, params, profile, polys, profile[-1][0], r_ap, profile[0][1],
                     max(outer, max(np.max(p[:, 0]) for p in polys)), notes or [], design)
    g.mount = mnt
    return g


def _input_len(f, d_in):
    lam = wavelength_mm(f)
    lc = 1.706 * d_in
    lg = lam / math.sqrt(max(1 - (lam / lc) ** 2, 1e-6))
    return max(lg, lam)        # >= 1 guide wavelength (W1GHZ)


def wall_default(f):
    return round(max(1.0, 0.06 * wavelength_mm(f)), 2)


def build(kind: str, f_ghz: float, *, fD: float | None = None, opening_deg: float | None = None,
          wall: float | None = None, **kw) -> FeedGeometry:
    """Build a feed geometry. fD = prime-focus (or offset-equivalent) f/D; opening_deg = full dish
    opening angle (OE2IGL guides). Extra keyword arguments override design values."""
    lam = wavelength_mm(f_ghz)
    t = wall if wall is not None else wall_default(f_ghz)
    if opening_deg is None and fD is not None:
        opening_deg = 4 * math.degrees(math.atan(1 / (4 * fD)))
    if fD is None and opening_deg is not None:
        fD = 1 / (4 * math.tan(math.radians(opening_deg) / 4))

    if kind == "open_circular":
        d = kw.get("diam", lam * float(np.interp(fD or 0.35, [0.25, 0.4], [0.6, 0.9])))
        L = kw.get("length", _input_len(f_ghz, d) * 1.5)
        prof = [(0.0, d / 2), (L, d / 2)]
        return _finish(kind, f_ghz, {"diam": d, "length": L, "wall": t}, prof, t,
                       notes=["W1GHZ 6.3: 0.6-0.9λ → f/D 0.25-0.4; oltre 0.95λ squint"])

    if kind in ("w2imu", "w2imu_oe2igl", "large_w2imu"):
        if kind == "w2imu":
            des = horns.w2imu(f_ghz, B_lambda=kw.get("B_lambda"), fD=fD)
            A, B = des.dims_mm["input_diam"], des.dims_mm["aperture_diam_B"]
            alpha, C = des.dims_mm["flare_half_deg"], des.dims_mm["phasing_length_C"]
        elif kind == "w2imu_oe2igl":
            des = horns.w2imu_oe2igl(f_ghz, opening_deg)
            A, B = des.dims_mm["input_diam_A"], des.dims_mm["aperture_diam_B"]
            alpha, C = des.dims_mm["flare_half_deg"], des.dims_mm["length_C"]
        else:
            des = horns.large_w2imu_30deg(f_ghz, kw.get("B_lambda", 1.78))
            A, B = des.dims_mm["input_diam"], des.dims_mm["aperture_diam_B"]
            alpha, C = 30.0, des.dims_mm["length_C"]
        A = kw.get("A", A); B = kw.get("B", B); alpha = kw.get("alpha", alpha); C = kw.get("C", C)
        Lf = (B - A) / 2 / math.tan(alpha * DEG)
        Lin = kw.get("input_length", _input_len(f_ghz, A))
        prof = [(0.0, A / 2), (Lin, A / 2), (Lin + Lf, B / 2), (Lin + Lf + C, B / 2)]
        return _finish(kind, f_ghz, {"A_input": A, "B_aperture": B, "flare_half_deg": alpha, "flare_length": Lf,
                                     "C_phasing": C, "input_length": Lin, "wall": t}, prof, t,
                       notes=des.notes, design=des)

    if kind in ("skobelev", "pickett_potter"):
        if kind == "skobelev":
            des = horns.skobelev(f_ghz, fD=fD)
            Di, Ds, Dap, Lf = (des.dims_mm[k] for k in ("input_diam", "step_diam", "aperture_diam", "flare_length"))
        else:
            des = horns.pickett_potter_oe2igl(f_ghz, opening_deg)
            Di, Ds, Dap, Lf = (des.dims_mm[k] for k in ("input_diam_Di", "step_diam_Ds", "aperture_diam", "flare_length"))
        Di = kw.get("Di", Di); Ds = kw.get("Ds", Ds); Dap = kw.get("Dap", Dap); Lf = kw.get("flare_length", Lf)
        if kw.get("alpha") is not None:
            # flare given by its half-angle (aperture kept): length follows; a flat flare is not a horn
            a = min(max(float(kw["alpha"]), 0.5), 60.0)
            if Dap - Ds > 1e-6:
                Lf = (Dap - Ds) / 2 / math.tan(a * DEG)
        alpha = math.degrees(math.atan2((Dap - Ds) / 2, Lf)) if Lf > 0 else 90.0
        Lin = kw.get("input_length", lam)
        prof = [(0.0, Di / 2), (Lin, Di / 2), (Lin, Ds / 2), (Lin + Lf, Dap / 2)]
        return _finish(kind, f_ghz, {"Di_input": Di, "Ds_step": Ds, "D_aperture": Dap, "flare_length": Lf,
                                     "flare_half_deg": alpha, "input_length": Lin, "wall": t}, prof, t,
                       notes=des.notes + ["ingresso Ø≈1.02λ: propagano anche TM01/TE21, non eccitati dal TE11 in "
                                          "struttura simmetrica — raccordare con taper dolce dalla guida monomodo"], design=des)

    if kind == "conical":
        d_in = kw.get("d_in", 0.76 * lam)
        D = kw.get("D", lam * 1.3)
        alpha = kw.get("alpha", 15.0)
        Lf = (D - d_in) / 2 / math.tan(alpha * DEG)
        Lin = kw.get("input_length", _input_len(f_ghz, d_in))
        prof = [(0.0, d_in / 2), (Lin, d_in / 2), (Lin + Lf, D / 2)]
        return _finish(kind, f_ghz, {"d_input": d_in, "D_aperture": D, "flare_half_deg": alpha,
                                     "flare_length": Lf, "input_length": Lin, "wall": t}, prof, t,
                       notes=["conico liscio: E/H diversi, correnti sul bordo (W1GHZ 6.4.1)"])

    if kind in ("ve4ma", "chaparral"):
        if kind == "ve4ma":
            des = horns.ve4ma(f_ghz, kw.get("variant", "super"))
            n_rings = 1
        else:
            des = horns.chaparral(f_ghz, kw.get("variant", "best"))
            n_rings = int(des.dims_mm["rings"])
        d = kw.get("horn_diam", des.dims_mm["horn_diam"])
        w = kw.get("ring_width", des.dims_mm["ring_width"])
        dep = kw.get("ring_depth", des.dims_mm["ring_depth"])
        back = kw.get("ring_setback", des.dims_mm["ring_setback"])
        L = kw.get("length", _input_len(f_ghz, d) * 1.5)
        tr = kw.get("ring_wall", t if kind == "ve4ma" else max(0.3, 0.03 * lam))
        prof = [(0.0, d / 2), (L, d / 2)]
        z_open = L - back
        r0 = d / 2 + t
        polys = []
        r_in = r0
        for i in range(n_rings):
            r_out = r_in + w
            # cup: bottom from r_in to r_out+tr at depth, outer wall up to opening
            polys.append([(r_in, z_open - dep - t), (r_out + tr, z_open - dep - t), (r_out + tr, z_open),
                          (r_out, z_open), (r_out, z_open - dep), (r_in, z_open - dep)])
            r_in = r_out + tr
        geo = _finish(kind, f_ghz, {"horn_diam": d, "ring_width": w, "ring_depth": dep, "ring_setback": back,
                                    "rings": n_rings, "ring_wall": tr, "length": L, "wall": t},
                      prof, t, extra_polys=polys, notes=des.notes, design=des)
        return geo

    if kind == "axial_corrugated":
        return _axial_corrugated(f_ghz, opening_deg, t, kw)

    if kind == "iz0jny":
        return _iz0jny(f_ghz, fD, t, kw)

    if kind == "fd04":
        return _fd04(f_ghz, t, kw)

    raise ValueError(f"unknown feed type {kind}")


# IZ0JNY Dual-Flare: optimised with FeedLab's mode-matching solver for EME (global search, ΔG + ΔG/T with a small
# length penalty; 0.4.24: compact version, same G/T within 0.01 dB, +0.02 dB gain, 2–18 % shorter; S11 ≤ −25 dB
# over ±1 %; checked with openEMS at 24 and 47 GHz on a 2.4 m offset dish), offset-equivalent f/D 0.6…0.9.
# Per f/D, in wavelengths: Ø after the step, step section length, Ø of the phasing cylinder, cone-1 length,
# phasing length, aperture Ø, cone-2 length. Input guide Ø 0.76 λ (TE11 only).
IZ0JNY_TABLE = {
    0.6: (1.0922, 0.0769, 1.6074, 0.4733, 1.0722, 1.5275, 1.5843),
    0.7: (1.0694, 0.0875, 1.5579, 0.4763, 1.3769, 1.8103, 1.1274),
    0.8: (1.0646, 0.2672, 1.6423, 0.4415, 1.6571, 2.0266, 1.8022),
    0.9: (1.0300, 0.3149, 1.6931, 0.4985, 1.7514, 2.2507, 2.2170),
}


def _iz0jny(f_ghz, fD, t, kw):
    lam = wavelength_mm(f_ghz)
    fds = sorted(IZ0JNY_TABLE)
    x = float(min(max(fD or 0.8, fds[0]), fds[-1]))
    v = [float(np.interp(x, fds, [IZ0JNY_TABLE[k][i] for k in fds])) * lam for i in range(7)]
    ds, ls, dm, l1, lp, dap, l2 = v
    Di = kw.get("Di", 0.76 * lam); Ds = kw.get("Ds", ds); Ls = kw.get("Ls", ls); Dm = kw.get("Dm", dm)
    L1 = kw.get("L1", l1); Lp = kw.get("Lp", lp); Dap = kw.get("Dap", dap); L2 = kw.get("L2", l2)
    Lin = kw.get("input_length", 0.6 * lam)
    Ds = max(Ds, Di); Dm = max(Dm, Ds); Dap = max(Dap, Dm)
    # cones given by their half-angle (diameters kept): the length follows (Laboratory, optimiser)
    if kw.get("a1") is not None and Dm - Ds > 1e-6:
        L1 = (Dm - Ds) / 2 / math.tan(min(max(float(kw["a1"]), 1.0), 80.0) * DEG)
    if kw.get("a2") is not None and Dap - Dm > 1e-6:
        L2 = (Dap - Dm) / 2 / math.tan(min(max(float(kw["a2"]), 0.3), 60.0) * DEG)
    z = [Lin, Lin + Ls, Lin + Ls + L1, Lin + Ls + L1 + Lp, Lin + Ls + L1 + Lp + L2]
    prof = [(0.0, Di / 2), (z[0], Di / 2), (z[0], Ds / 2), (z[1], Ds / 2), (z[2], Dm / 2), (z[3], Dm / 2), (z[4], Dap / 2)]
    a1 = math.degrees(math.atan2((Dm - Ds) / 2, L1)) if L1 > 0 else 90.0
    a2 = math.degrees(math.atan2((Dap - Dm) / 2, L2)) if L2 > 0 else 90.0
    notes = ["scalino + cono 1 generano il TM11; il cilindro Dm lo rimette in fase col TE11",
             "il cono 2 forma l'apertura: bordo ≈ -12 dB, centro di fase vicino all'apertura",
             "ottimizzato per EME col solutore rapido (ΔG + ΔG/T, lunghezza minima) e verificato con openEMS a 24 e 47 GHz"]
    return _finish("iz0jny", f_ghz, {"Di_input": Di, "Ds_step": Ds, "Ls": Ls, "Dm": Dm, "L1": L1, "Lp": Lp, "D_aperture": Dap, "L2": L2,
                                     "input_length": Lin, "cone1_half_deg": a1, "cone2_half_deg": a2, "wall": t},
                   prof, t, notes=notes)


# Feed 0.4 f/D: axial-corrugated head found with openEMS (fdtd/optimize.py, family axial_corrugated, 200 FDTD
# runs) for a dish of f/D 0.4 (prime focus, or offset-equivalent): illuminator efficiency x (1 - |S11|^2), mean over
# f0 +/- 2 %, with S11 <= -20 dB; confirmed at lambda/24 and at 10.368 and 24.048 GHz (fdtd/RISULTATI_fD040.md).
# In wavelengths: pitch, slot width / pitch, axial advance per slot, delta, Di, Ds, depth of slot 1, depth of 2...8.
FD04_LAMBDA = {"pitch": 0.4441, "w_frac": 0.5862, "axi": 0.0599, "delta": 0.2214, "Di": 0.7233, "Ds": 0.7233,
               "d1": 0.4775, "dk": 0.2689}
FD04_ETA = 0.835          # openEMS, f/D 0.4, mean over f0 +/- 2 %, S11 included
FD04_FD = 0.4


def _fd04(f_ghz, t, kw):
    lam = wavelength_mm(f_ghz)
    x = FD04_LAMBDA
    dims = {"pitch": x["pitch"] * lam, "w": x["w_frac"] * x["pitch"] * lam, "axi": x["axi"] * lam,
            "delta": x["delta"] * lam, "Di": x["Di"] * lam, "Ds": x["Ds"] * lam, "d1": x["d1"] * lam,
            **{f"d{k}": x["dk"] * lam for k in range(2, 9)}}
    dims.update(kw)                      # the user's edits win
    opening = 4 * math.degrees(math.atan(1 / (4 * FD04_FD)))
    g = _axial_corrugated(f_ghz, opening, t, dims)
    g.kind = "fd04"
    g.params["eta_guide_pct"] = 100 * FD04_ETA
    g.params["opening_deg"] = opening
    g.notes = ["ottimizzato con openEMS per f/D 0.4: 83.5 % con S11 ≤ −21 dB (f0 ± 2 %), verificato a 10.368 e 24.048 GHz",
               "8 scanalature assiali sul fronte a gradini (stessa struttura dell'Axial Corrugated)",
               "simulazione rapida non disponibile: verificato con openEMS a 10 e 24 GHz"] + \
              [n for n in g.notes if not n.startswith(("efficienza secondo", "usa l'angolo", "simulazione rapida",
                                                       "valido 10", "tolleranza", "ATTENZIONE"))]
    g.design = None
    return g


def _axial_corrugated(f_ghz, opening_deg, t, kw):
    """Gerald OE2IGL high-performance axial-corrugated feed v1.4 (from Luis CT1DMK's concept): 8 concentric
    axial slots on a stepped face, dimensions from OE2IGL's design guide (polynomials of the half opening
    angle). Geometry as in OE2IGL's cross-section: input guide Ø Di (length las), step to Ø Ds, slot k of
    radial width w starts at radius Ds/2 + delta + (k−1)·pitch, its opening plane is (k−1)·axi further
    forward, depth d_k (axial, d2…d8 = λ/4). The body is a solid of revolution (machined from a bar)."""
    if opening_deg is None:
        raise ValueError("serve l'angolo di apertura della parabola")
    des = horns.axial_corrugated_oe2igl(f_ghz, opening_deg)
    d = des.dims_mm
    pitch = kw.get("pitch", d["pitch"]); w = kw.get("w", d["w"]); axi = kw.get("axi", d["axi"])
    delta = kw.get("delta", d["delta"]); Di = kw.get("Di", d["Di"]); Ds = kw.get("Ds", d["Ds"])
    depths = [kw.get("d1", d["d1"])] + [kw.get(f"d{k}", d["d2_to_d8"]) for k in range(2, 9)]
    ai, a_s = Di / 2, max(Ds / 2, Di / 2)
    t_out = kw.get("outer_wall", max(t, 0.5 * pitch))
    # the input guide must be long enough for the deepest slot bottom to stay inside the body
    las = kw.get("las", d["las"])
    z_f = max(las, max(dk - k * axi for k, dk in enumerate(depths)) + t)
    r_in = [a_s + delta + k * pitch for k in range(8)]
    r_out = [r + w for r in r_in]
    z_open = [z_f + k * axi for k in range(8)]
    z_top = z_f + 8 * axi
    R = r_out[-1] + t_out
    # "skyline" of the metal in (r, z): radial bands from the bore to the outer wall
    bands = [(ai, a_s, z_f)]                                   # step face (Ds > Di) or nothing
    if delta > 1e-9:
        bands.append((a_s, r_in[0], z_open[0]))                # lip before the first slot
    for k in range(8):
        bands.append((r_in[k], r_out[k], z_open[k] - depths[k]))                    # slot bottom
        nxt = r_in[k + 1] if k < 7 else R
        bands.append((r_out[k], nxt, z_open[k + 1] if k < 7 else z_top))            # wall / outer rim
    poly = [(ai, 0.0)]
    for r0, r1, h in bands:
        if r1 - r0 < 1e-9:
            continue
        poly += [(r0, h), (r1, h)]
    poly += [(R, 0.0)]
    clean = [poly[0]]
    for pt in poly[1:]:
        if abs(pt[0] - clean[-1][0]) > 1e-9 or abs(pt[1] - clean[-1][1]) > 1e-9:
            clean.append(pt)
    profile = [(0.0, ai), (z_f, ai), (z_f, a_s)] + [(z_open[k], r_in[k]) for k in range(8)] + [(z_top, R)]
    params = {"pitch": pitch, "w": w, "axi": axi, "delta": delta, "Di": Di, "Ds": Ds, "las": z_f,
              **{f"d{k + 1}": depths[k] for k in range(8)}, "outer_diam": 2 * R, "length": z_top,
              "opening_deg": opening_deg, "eta_guide_pct": d["eta_pct"], "wall": t}
    notes = [f"efficienza secondo la design guide OE2IGL: {d['eta_pct']:.1f}% (spillover {d['spill_pct']:.1f}%, "
             f"illuminazione {d['illum_pct']:.1f}%)", *des.notes,
             "usa l'angolo di apertura della parabola, non l'f/D (OE2IGL)",
             "simulazione rapida non disponibile (scalini assiali): verifica con openEMS"]
    if not z_f == las:
        notes.append(f"guida d'ingresso portata a {z_f:.2f} mm per contenere lo scalino più profondo")
    # circular waveguide section behind the head, with the base (round, or square like the WR flange) and the
    # flange drilling, turned in the same piece as the head. L_guide = 0: head only.
    L_g = float(kw.get("L_guide", wavelength_mm(f_ghz)))
    if L_g > 1e-6:
        tube = _finish("axial_corrugated", f_ghz, {"wall": t}, [(0.0, ai), (L_g, ai)], t)
        L_g = tube.profile[-1][0]                     # lengthened if the drilled base needs it
        head = np.array([(r, z + L_g) for r, z in clean])
        profile = [(0.0, ai)] + [(z + L_g, r) for z, r in profile]
        params = {**params, "L_guide": L_g, "z_head": L_g, "length": z_top + L_g,
                  **{k: tube.params[k] for k in ("flange_diam", "flange_thickness", "base_square") if k in tube.params}}
        notes = notes + [n for n in tube.notes if n not in notes]
        g = FeedGeometry("axial_corrugated", f_ghz, params, profile, [tube.polygons[0], head], z_top + L_g,
                         r_out[-1], ai, R, notes, des)
        g.mount = tube.mount
        return g
    params = {**params, "L_guide": 0.0}
    g = FeedGeometry("axial_corrugated", f_ghz, params, profile, [np.array(clean)], z_top, r_out[-1], ai, R,
                     notes, des)
    g.mount = None
    return g


@dataclass
class RectHornGeometry:
    kind: str
    f_ghz: float
    params: dict
    notes: list = field(default_factory=list)

    @property
    def lam(self):
        return wavelength_mm(self.f_ghz)

    @property
    def length(self):
        return self.params["input_length"] + self.params["axial_length"]

    def blockage_diameter(self):
        p = self.params
        return math.hypot(p["aperture_H"], p["aperture_E"]) + 2 * p["wall"]


def build_rect(f_ghz: float, fD: float, wg: str = "WR-90", wall: float | None = None, **kw) -> RectHornGeometry:
    from .waveguide import RECT_WG
    w = RECT_WG[wg]
    des = horns.rect_feedhorn_g3rpe(f_ghz, fD, w.a_mm, w.b_mm)
    t = wall if wall is not None else wall_default(f_ghz)
    p = {"wg": wg, "a": w.a_mm, "b": w.b_mm, "aperture_H": kw.get("aperture_H", max(des.dims_mm["aperture_H"], w.a_mm)),
         "aperture_E": kw.get("aperture_E", max(des.dims_mm["aperture_E"], w.b_mm)),
         "axial_length": kw.get("axial_length", max(des.dims_mm["axial_length"], 0.5 * wavelength_mm(f_ghz))),
         "input_length": kw.get("input_length", wavelength_mm(f_ghz)), "wall": t}
    return RectHornGeometry("rect_horn", f_ghz, p, des.notes)
