"""Standard waveguide flange hole patterns and the bolted stack WR component | λ/4 plate | feed.

Hole patterns are Flann's "standard" flanges (Flann Microwave, *Waveguide and Flange Data*, pages
"Standard flange data"; MIL-DTL-3922/67C for the round doweled flanges). All dimensions in mm, waveguide
broad wall along x, narrow wall along y (vertical polarisation: E field along y).

Assembly (as in IZ0JNY's 24 GHz W2IMU feed, iz0jny.it):
  * the WR component is screwed into the PLATE: the standard flange pattern is tapped in the plate;
  * the plate is screwed to the FEED with 4 screws on the axes, heads sunk in counterbores on the WR side,
    so the face that mates with the waveguide stays flat; the feed flange has the 4 tapped holes;
  * round MIL flanges (UG-383/385/387): the component's two dowel pins need Ø1.65 holes through the plate
    (and clearance in the feed when they stick out of a thin plate). Square flanges have no dowels.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

SOURCE = "Flann Microwave, Waveguide and Flange Data (standard flanges); MIL-DTL-3922/67C"


@dataclass(frozen=True)
class Flange:
    wg: str
    name: str
    shape: str                    # "square" | "round"
    A: float                      # square side or round diameter
    E: float = 0.0                # square: half spacing along y (narrow wall)
    F: float = 0.0                # square: half spacing along x (broad wall)
    pcd: float = 0.0              # round: pitch circle diameter
    hole: float = 0.0             # published clearance diameter of the screw holes
    imperial: str = ""            # screw of the standard
    note: str = ""


FLANGES = {f.wg: f for f in [
    Flange("WR-90", "UBR 100", "square", 41.40, E=16.26, F=15.49, hole=4.255, imperial="8-32 UNC"),
    Flange("WR-75", "UBR 120", "square", 38.30, E=14.25, F=13.21, hole=4.085, imperial="6-32 UNC"),
    Flange("WR-62", "UBR 140", "square", 33.30, E=12.14, F=12.63, hole=4.085, imperial="6-32 UNC"),
    Flange("WR-51", "UBR 180", "square", 30.10, E=11.25, F=10.29, hole=4.085, imperial="6-32 UNC"),
    Flange("WR-42", "UBR 220 (UG-595/U)", "square", 22.41, E=8.51, F=8.13, hole=3.07, imperial="4-40 UNC"),
    Flange("WR-34", "UBR 260", "square", 22.10, E=7.90, F=7.50, hole=3.07, imperial="4-40 UNC"),
    Flange("WR-28", "UG-599/U", "square", 33.30, E=12.14, F=12.63, hole=4.085, imperial="6-32 UNC",
           note="Flann pubblica per il WR-28 gli stessi valori del WR-62: verifica sulla flangia reale prima di forare"),
    Flange("WR-22", "UG-383/U", "round", 28.55, pcd=23.81, imperial="4-40 UNC"),
    Flange("WR-19", "UG-383/U mod.", "round", 28.55, pcd=23.81, imperial="4-40 UNC"),
    Flange("WR-15", "UG-385/U", "round", 19.05, pcd=14.29, imperial="4-40 UNC"),
    Flange("WR-12", "UG-387/U", "round", 19.05, pcd=14.29, imperial="4-40 UNC"),
    Flange("WR-10", "UG-387/U mod.", "round", 19.05, pcd=14.29, imperial="4-40 UNC"),
    Flange("WR-8", "UG-387/U mod.", "round", 19.05, pcd=14.29, imperial="4-40 UNC"),
    Flange("WR-6", "UG-387/U mod.", "round", 19.05, pcd=14.29, imperial="4-40 UNC"),
    Flange("WR-5", "UG-387/U mod.", "round", 19.05, pcd=14.29, imperial="4-40 UNC"),
]}

# screws: major diameter, tap drill, clearance drill (normal fit)
SCREWS = {
    "M2": (2.0, 1.6, 2.4), "2-56 UNC": (2.184, 1.78, 2.6),
    "M2.5": (2.5, 2.05, 2.8), "3-48 UNC": (2.515, 1.99, 2.9), "M3": (3.0, 2.5, 3.2), "M4": (4.0, 3.3, 4.3),
    "4-40 UNC": (2.845, 2.26, 3.0), "6-32 UNC": (3.505, 2.70, 3.7), "8-32 UNC": (4.166, 3.45, 4.3),
}
PITCH = {"M2": 0.4, "M2.5": 0.45, "M3": 0.5, "M4": 0.7, "2-56 UNC": 25.4 / 56, "3-48 UNC": 25.4 / 48,
         "4-40 UNC": 25.4 / 40, "6-32 UNC": 25.4 / 32, "8-32 UNC": 25.4 / 32}

# ---- screws holding the λ/4 plate on the feed (user's choice, IZ0JNY) ----
PLATE_SCREWS_10GHZ = ["M3", "M4"]              # 10 GHz band
PLATE_SCREWS_HIGH = ["M2.5", "M3", "M2"]       # 24 GHz and up (first = default)
TEN_GHZ_MAX = 15.0                             # below this the 10 GHz choices apply
SCREW_FACTOR = 2.0                             # screw length = 2 × plate thickness, commercial (IZ0JNY)
# imperial equivalents (nearest UNC size): M2→#2-56 (Ø2.18), M2.5→#3-48 (Ø2.51, less common than 4-40),
# M3→#4-40 (Ø2.84), M4→#8-32 (Ø4.17)
UNC_FOR_METRIC = {"M2": "2-56 UNC", "M2.5": "3-48 UNC", "M3": "4-40 UNC", "M4": "8-32 UNC"}
# commercial lengths: metric (ISO 4762) and inch (ASME B18.3) socket head cap screws
LENGTHS_MM = [10, 12, 14, 16, 18, 20, 25]
LENGTHS_IN = [(3 / 8, '3/8"'), (1 / 2, '1/2"'), (5 / 8, '5/8"'), (3 / 4, '3/4"'), (7 / 8, '7/8"'), (1.0, '1"')]


def plate_screw_options(f_ghz: float | None) -> list[str]:
    """Metric sizes offered for the plate → feed screws at this frequency (first = default)."""
    return PLATE_SCREWS_10GHZ if f_ghz is not None and f_ghz < TEN_GHZ_MAX else PLATE_SCREWS_HIGH


def plate_screw_name(metric: str, system: str) -> str:
    return UNC_FOR_METRIC[metric] if system == "imperial" else metric


def screw_length(plate_t: float, system: str = "metric") -> tuple[float, str]:
    """Plate → feed screw length: SCREW_FACTOR × plate thickness rounded to the nearest commercial length
    (10, 12, 14, 16, 18, 20, 25 mm; inch screws 3/8 … 1 inch). Returns (mm, label)."""
    target = SCREW_FACTOR * plate_t
    if system == "imperial":
        v, lab = min(LENGTHS_IN, key=lambda x: (abs(x[0] * 25.4 - target), -x[0]))
        return v * 25.4, lab
    v = min(LENGTHS_MM, key=lambda x: (abs(x - target), -x))
    return float(v), f"{v} mm"
# counterbores for the plate → feed screws: socket head cap screws ISO 4762 / ASME B18.3 (head Ø, height)
# → counterbore Ø, depth. M2.5: Ø5.5 × 2.5 as in IZ0JNY's WR-42 plate. Check against the screws you buy.
HEADS = {"M2": (3.8, 2.0), "M2.5": (4.5, 2.5), "M3": (5.5, 3.0), "M4": (7.0, 4.0), "2-56 UNC": (3.56, 2.18),
         "3-48 UNC": (4.09, 2.51), "4-40 UNC": (4.65, 2.84), "8-32 UNC": (6.86, 4.17)}
CBORE = {"M2": (4.4, 2.1), "M2.5": (5.5, 2.5), "M3": (6.5, 3.1), "M4": (8.0, 4.4), "2-56 UNC": (4.2, 2.3),
         "3-48 UNC": (4.8, 2.7), "4-40 UNC": (5.3, 3.0), "8-32 UNC": (7.9, 4.4)}
METRIC_FOR = {"4-40 UNC": "M3", "6-32 UNC": "M3", "8-32 UNC": "M4"}   # passes the standard's clearance holes (M3 on UG-595 as IZ0JNY)
DOWEL_HOLE_ROUND = 1.65          # MIL round flanges, for Ø1.549/1.562 pins
DOWEL_PIN_SQUARE = 2.0           # alignment pins added by FeedLab on square flanges (Ø2 m6, holes Ø2 H7)


@dataclass
class Hole:
    x: float
    y: float
    dia: float                   # drilled diameter in the part
    kind: str                    # "tap" | "dowel" (guide pins) | "pin" (plate–feed pins) | "cbore" (counterbored)
    callout: str                 # text for the drawing
    depth: float | None = None   # None = through
    cb_dia: float = 0.0          # counterbore (kind "cbore")
    cb_depth: float = 0.0


@dataclass
class Mount:
    flange: Flange
    screw: str
    polarization: str            # "V" | "H" (H rotates the pattern 90°)
    plate_holes: list = field(default_factory=list)
    feed_holes: list = field(default_factory=list)
    engagement: float = 0.0      # thread length in the feed flange
    warnings: list = field(default_factory=list)
    plate_screw: str = ""        # screws holding the plate on the feed (heads in counterbores, WR side)
    screw_len: float = 0.0       # their length (mm), 0 = not set (plate thickness unknown)
    screw_len_label: str = ""
    tap_depth: float = 0.0       # threaded depth in the feed flange
    screw_in: float = 0.0        # length of screw inside the feed (screw length − grip in the plate)

    @property
    def plate_radius(self) -> float:
        return max(math.hypot(h.x, h.y) + max(h.dia, h.cb_dia) / 2 for h in self.plate_holes)

    def plate_body_min(self) -> float:
        """Plate thickness needed: counterbore + 0.8 mm seat, and ≥ 1·d of thread for the tapped flange screws."""
        cb = max((h.cb_depth + 0.8 for h in self.plate_holes if h.kind == "cbore"), default=0.0)
        return max(cb, SCREWS[self.screw][0] + 0.3)

    @property
    def radius(self) -> float:
        """Outermost hole edge from the axis (feed flange must cover it with margin)."""
        return max(math.hypot(h.x, h.y) + h.dia / 2 for h in self.feed_holes)

    def feed_flange_min(self) -> tuple[float, float]:
        """(diameter, thickness) the feed flange needs for these holes."""
        d_major = SCREWS[self.plate_screw or self.screw][0]
        drill = max((h.depth or 0.0 for h in self.feed_holes if h.kind == "tap"), default=0.0)
        return 2 * (self.radius + max(1.5, 0.75 * d_major)), max(self.engagement + 1.0, drill + 0.8, 3.0)


def screw_for(wg: str, system: str = "metric") -> str:
    """Thread in the plate for the waveguide's screws. Round MIL flanges come with captive 4-40 screws:
    the plate must be threaded 4-40 whatever the user's preference."""
    fl = FLANGES[wg]
    if fl.shape == "round" or system == "imperial":
        return fl.imperial
    return METRIC_FOR[fl.imperial]


def _rot(x, y, pol):
    return (x, y) if pol == "V" else (-y, x)


PIN_FROM_GHZ = 47.0             # alignment pins plate ↔ feed from 47 GHz up (IZ0JNY)


def mount(wg: str, system: str = "metric", polarization: str = "V", feed_input_diam: float = 0.0,
          f_ghz: float | None = None, plate_screw: str | None = None, plate_t: float | None = None) -> Mount:
    """Hole patterns of the plate and of the feed flange for waveguide `wg` (see module docstring)."""
    if wg not in FLANGES:
        raise ValueError(f"nessuna flangia standard in tabella per {wg}")
    fl = FLANGES[wg]
    screw = screw_for(wg, system)
    d_major, tap, clear = SCREWS[screw]
    m = Mount(fl, screw, polarization)
    if fl.note:
        m.warnings.append(fl.note)
    if fl.shape == "round" and system != "imperial":
        m.warnings.append("flangia MIL rotonda: la guida ha viti imperdibili 4-40 UNC, la piastra è filettata 4-40 "
                          "(le viti piastra→feed restano metriche)")
    if fl.shape == "square":
        screw_xy = [(sx * fl.F, sy * fl.E) for sx in (1, -1) for sy in (1, -1)]
        dowel_xy = []
    else:
        r = fl.pcd / 2
        screw_xy = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (0, 90, 180, 270)]
        dowel_xy = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (45, 135, 225, 315)]
    for x, y in screw_xy:
        x, y = _rot(x, y, polarization)
        m.plate_holes.append(Hole(x, y, tap, "tap", f"{screw} filettato passante (preforo Ø{tap:g})"))
    for x, y in dowel_xy:
        x, y = _rot(x, y, polarization)
        m.plate_holes.append(Hole(x, y, DOWEL_HOLE_ROUND, "dowel", f"Ø{DOWEL_HOLE_ROUND:g} passante, spine guida Ø1.56"))
        m.feed_holes.append(Hole(x, y, DOWEL_HOLE_ROUND, "dowel", f"Ø{DOWEL_HOLE_ROUND:g} prof. 3, punte spine guida",
                                 depth=3.0))
    choices = plate_screw_options(f_ghz)
    metric = plate_screw if plate_screw in choices else choices[0]
    _plate_screws(m, system, feed_input_diam, wg, screw=plate_screw_name(metric, system), plate_t=plate_t)
    if f_ghz is not None and f_ghz >= PIN_FROM_GHZ - 1e-9:
        _alignment_pins(m, feed_input_diam, wg)
    # interference with the feed's circular input guide
    if feed_input_diam:
        for h in m.feed_holes:
            gap = math.hypot(h.x, h.y) - max(h.dia, h.cb_dia) / 2 - feed_input_diam / 2
            if gap < 0.8:
                m.warnings.append(f"foro {h.callout.split(' ')[0]} a {gap:.2f} mm dalla guida circolare Ø{feed_input_diam:.2f}: "
                                  "troppo vicino, usa una flangia più grande o una guida diversa")
                break
    return m


def _plate_screws(m: Mount, system: str, feed_input_diam: float, wg: str, n_ang: int = 36,
                  screw: str | None = None, plate_t: float | None = None) -> None:
    """Four screws holding the plate on the feed (θ + k·90°), heads sunk in counterbores on the WR side.
    Smallest radius whose counterbores keep ≥ 0.6 mm from every other hole, from the circular guide
    and from the WR aperture. Symmetric positions come first: on the axes (θ = 0, as in IZ0JNY's plate) or on the
    diagonals (θ = 45°), as long as they fit on the flange; other angles only as a last resort."""
    from .waveguide import RECT_WG
    screw = screw or ("M2.5" if system != "imperial" else "2-56 UNC")
    d_major, tap, clear = SCREWS[screw]
    cb_d, cb_k = CBORE[screw]
    w = RECT_WG.get(wg)
    a, b = (w.a_mm, w.b_mm) if w else (0.0, 0.0)
    if m.polarization == "H":
        a, b = b, a
    others = [(h.x, h.y, max(h.dia, h.cb_dia)) for h in m.plate_holes]

    def ok(x, y):
        if math.hypot(x, y) - cb_d / 2 < feed_input_diam / 2 + 0.6:
            return False
        if abs(x) < a / 2 + cb_d / 2 + 0.6 and abs(y) < b / 2 + cb_d / 2 + 0.6:
            return False
        return all(math.hypot(x - ox, y - oy) > (cb_d + od) / 2 + 0.6 for ox, oy, od in others)

    r = feed_input_diam / 2 + cb_d / 2 + 0.6
    eng = max(2.0 * d_major, 4.0)
    L, L_lab = 0.0, ""
    if plate_t:
        # screw length = 2 × plate thickness, commercial; it clamps the plate under the head (plate_t − counterbore)
        L, L_lab = screw_length(plate_t, system)
        eng = L - max(plate_t - cb_k, 0.0)
        if eng < 1.5 * d_major:
            m.warnings.append(f"vite {screw} × {L_lab}: solo {eng:.1f} mm di filetto nel feed (< 1.5 d)")
    # hole in the feed (IZ0JNY): even whole millimetres; the thread must reach the screw end and stops
    # 3 pitches (≥ 1 mm) before the bottom of the blind hole (tap lead)
    lead = max(1.0, 3 * PITCH.get(screw, 0.5))
    drill_d = float(2 * math.ceil((eng + lead) / 2 - 1e-9))
    tap_d = drill_d - lead
    # symmetric pattern first: screws on the axes (0°) or on the diagonals (45°), at the smallest radius that
    # still fits on the flange; only if neither fits, any angle (10° steps) at the smallest free radius
    r_max = m.flange.A / 2 - cb_d / 2 - 0.5
    cands = [(rr, th) for th in (0.0, math.pi / 4) for rr in (r + 0.1 * j for j in range(600)) if rr <= r_max]
    cands += [(r + 0.1 * j, 0.5 * math.pi * i / (n_ang // 4)) for j in range(600) for i in range(n_ang // 4)]
    for r, th in cands:
        if True:
            pts = [(r * math.cos(th + k * math.pi / 2), r * math.sin(th + k * math.pi / 2)) for k in range(4)]
            if all(ok(x, y) for x, y in pts):
                for x, y in pts:
                    m.plate_holes.append(Hole(x, y, clear, "cbore",
                                              f"Ø{clear:g} passante, lamatura Ø{cb_d:g} prof. {cb_k:g} ({screw}"
                                              + (f" × {L_lab}" if L_lab else "") + ")",
                                              cb_dia=cb_d, cb_depth=cb_k))
                    m.feed_holes.append(Hole(x, y, tap, "tap", f"{screw} filetto prof. {tap_d:.1f} "
                                             f"(preforo Ø{tap:g} prof. {drill_d:.0f})", depth=drill_d))
                m.plate_screw = screw
                m.engagement = eng
                m.tap_depth = tap_d
                m.screw_in = eng
                m.screw_len, m.screw_len_label = L, L_lab
                return
    m.warnings.append("nessuna posizione libera per le viti piastrina→feed")


def _alignment_pins(m: Mount, feed_input_diam: float, wg: str, n_ang: int = 72) -> None:
    """Two dowel pins between plate and feed (needed from 47 GHz up): pressed in the feed (Ø H7, m6 pin),
    sliding fit through the plate (Ø H7). Placed at θ and θ+180° at the smallest free radius."""
    from .waveguide import RECT_WG
    d = 1.5 if m.flange.A < 25 else 2.0
    w = RECT_WG.get(wg)
    a, b = (w.a_mm, w.b_mm) if w else (0.0, 0.0)
    if m.polarization == "H":
        a, b = b, a
    others = [(h.x, h.y, max(h.dia, h.cb_dia)) for h in m.plate_holes]

    def ok(x, y):
        if math.hypot(x, y) - d / 2 < feed_input_diam / 2 + 1.0:
            return False
        if abs(x) < a / 2 + d / 2 + 1.0 and abs(y) < b / 2 + d / 2 + 1.0:
            return False
        return all(math.hypot(x - ox, y - oy) > (d + od) / 2 + 0.6 for ox, oy, od in others)

    r = max(feed_input_diam / 2, math.hypot(a, b) / 2) + d / 2 + 1.0
    for _ in range(600):
        for i in range(n_ang // 2):
            th = math.pi / 4 + math.pi * i / (n_ang // 2)        # start on the diagonal
            x, y = r * math.cos(th), r * math.sin(th)
            if ok(x, y) and ok(-x, -y):
                for sx in (1, -1):
                    m.plate_holes.append(Hole(sx * x, sx * y, d, "pin", f"Ø{d:g} H7 passante, spina Ø{d:g} m6 (centraggio)"))
                    m.feed_holes.append(Hole(sx * x, sx * y, d, "pin", f"Ø{d:g} H7 prof. {2 * d + 1:g}, spina Ø{d:g} m6 piantata",
                                             depth=2 * d + 1))
                return
        r += 0.1
    m.warnings.append("nessuna posizione libera per le spine di centraggio piastra–feed")
