"""Standard waveguide flange hole patterns and the bolted stack WR component | λ/4 plate | feed.

Hole patterns are Flann's "standard" flanges (Flann Microwave, *Waveguide and Flange Data*, pages
"Standard flange data"; MIL-DTL-3922/67C for the round doweled flanges). All dimensions in mm, waveguide
broad wall along x, narrow wall along y (vertical polarisation: E field along y).

Assembly (as in IZ0JNY's 24 GHz W2IMU feed, iz0jny.it):
  * the WR component is screwed into the PLATE: the standard flange pattern is tapped in the plate;
  * the plate is screwed to the FEED with 4 screws on the axes, heads sunk in counterbores on the WR side,
    so the face that mates with the waveguide stays flat; the feed flange has the 4 tapped holes;
  * round MIL flanges (UG-383/385/387, from 47 GHz, IZ0JNY): NO plate→feed screws. The plate is a thin
    disc as large as the flange that simply sits on the feed base; the waveguide's 4-40 screws pass through
    clearance holes in the plate and are screwed into the feed base, where the standard pattern is tapped.
    The flange's dowel holes go through the plate and into the base and align the whole stack.
    Square flanges have no dowels.
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
PLATE_SCREWS_HIGH = ["M2.5", "M2"]             # 24 GHz and up (first = default); M3 is too big on WR-42
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
         "3-48 UNC": (4.09, 2.51), "4-40 UNC": (4.65, 2.84), "6-32 UNC": (5.46, 3.51), "8-32 UNC": (6.86, 4.17)}
CBORE = {"M2": (4.4, 2.1), "M2.5": (5.5, 2.5), "M3": (6.5, 3.1), "M4": (8.0, 4.4), "2-56 UNC": (4.2, 2.3),
         "3-48 UNC": (4.8, 2.7), "4-40 UNC": (5.3, 3.0), "6-32 UNC": (6.1, 3.7), "8-32 UNC": (7.9, 4.4)}
# plate → feed screws: Phillips FLAT (countersunk) head, flush in the plate (IZ0JNY, 0.4.19).
# ISO 7046-1 (90°): head Ø dk, height k; UNC flat head 82° (ASME B18.6.3). Countersink Ø = dk + 0.2 mm.
CSK = {"M2": (3.8, 1.2, 90), "M2.5": (4.7, 1.5, 90), "M3": (5.5, 1.65, 90), "M4": (8.4, 2.7, 90),
       "2-56 UNC": (4.37, 1.3, 82), "3-48 UNC": (5.05, 1.5, 82), "4-40 UNC": (5.72, 1.7, 82), "8-32 UNC": (8.43, 2.5, 82)}
METRIC_FOR = {"4-40 UNC": "M3", "6-32 UNC": "M3", "8-32 UNC": "M4"}   # passes the standard's clearance holes (M3 on UG-595 as IZ0JNY)
DOWEL_HOLE_ROUND = 1.65          # MIL round flanges, for Ø1.549/1.562 pins
DOWEL_PIN_SQUARE = 2.0           # alignment pins added by FeedLab on square flanges (Ø2 m6, holes Ø2 H7)


def hole_role(h) -> str:
    """'flange' (holes of the waveguide flange), 'plate' (plate → feed fixing), 'pin' (alignment)."""
    c = h.callout or ""
    return "plate" if c.startswith("FISSAGGIO") else "pin" if (c.startswith("PIN") or h.kind in ("dowel", "pin")) else "flange"


ROLE_COLOR = {"flange": "k", "plate": "m", "pin": "g"}
ROLE_LEGEND = {"flange": "nero = fori della flangia della guida", "plate": "magenta = fissaggio piastrina → base del feed",
               "pin": "verde = pin di allineamento"}


def role_legend(holes, tr=lambda x: x) -> str:
    """Legend of the hole colours actually present in the view (translated with `tr`)."""
    roles = [r for r in ("flange", "plate", "pin") if any(hole_role(h) == r for h in holes)]
    return " · ".join(tr(ROLE_LEGEND[r]) for r in roles)


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
    stack: bool = False          # round MIL flange: guide screws through the plate into the feed, no plate screws
    feed_cbore: bool = False     # through holes in the base: screws from the feed side (head in a counterbore or on the base)
    base_holes: str = "flange"   # "flange" | "clear" | "tap" (see mount)
    thread: str = ""             # thread of the base holes (base_holes "tap")
    guide_in: float = 0.0        # length of the flange screw inside / through the feed base
    plate_head: str = ""         # plate→feed screws: "allen" (counterbore) | "flat" (countersink)
    plate_grip_cut: float = 0.0  # depth of their counterbore (the grip is the plate under the head)

    @property
    def plate_radius(self) -> float:
        return max(math.hypot(h.x, h.y) + max(h.dia, h.cb_dia) / 2 for h in self.plate_holes)

    def plate_body_min(self) -> float:
        """The plate keeps its λ/4 thickness (flush countersunk screws): nothing to add."""
        return 0.0

    @property
    def radius(self) -> float:
        """Outermost hole edge from the axis (feed flange must cover it with margin)."""
        return max(math.hypot(h.x, h.y) + max(h.dia, h.cb_dia) / 2 for h in self.feed_holes)

    def feed_flange_min(self) -> tuple[float, float]:
        """(diameter, thickness) the feed base needs for these holes."""
        d_major = SCREWS[self.thread or self.screw][0]
        guide = [h for h in self.feed_holes if h.kind in ("tap", "cbore_back") and h.depth is None]
        r_need = self.radius
        t_need = 3.0
        if self.feed_cbore:                       # through holes: counterbore + 1.5 mm seat, or head on the base
            cb = max((h.cb_depth for h in guide if h.kind == "cbore_back"), default=0.0)
            if not cb:
                head = HEADS.get(self.screw, (2 * d_major, 0))[0] / 2
                r_need = max(r_need, max(math.hypot(h.x, h.y) for h in guide) + head)
            t_need = max(t_need, cb + 1.5)
        elif self.base_holes == "tap":            # threaded through: the thread engagement is the base
            t_need = max(t_need, self.guide_in)
        if self.plate_screw:                      # blind tapped holes of the plate→feed screws
            drill = max((h.depth or 0.0 for h in self.feed_holes if h.kind == "tap" and h.depth), default=0.0)
            t_need = max(t_need, self.engagement + 1.0, drill + 0.8)
        return 2 * (r_need + max(1.5, 0.75 * d_major)), t_need


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


# feed-base holes at the positions of the waveguide flange (IZ0JNY, 0.4.19)
BASE_HOLE_MODES = ("flange", "clear", "tap")
# through holes "maggiorati": medium-fit clearance (ISO 273 / ASME B18.2.8) for the flange screw
CLEAR_MEDIUM = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4, "M4": 4.5, "2-56 UNC": 2.6, "3-48 UNC": 2.9, "4-40 UNC": 3.4,
                "6-32 UNC": 3.9, "8-32 UNC": 4.5}
BASE_THREADS_10GHZ = ["M4", "M3"]
BASE_THREADS_HIGH = ["M3", "M2.5", "M2"]
MIL_HOLE = 3.05                  # clearance holes of the round MIL flanges (4-40, Ø0.120")


def flange_hole(wg: str) -> float:
    """Through-hole diameter of the standard flange, rounded UP to the tenth of a millimetre
    (3.07 → 3.1, 4.255 → 4.3, 4.085 → 4.1, MIL 3.05 → 3.1)."""
    fl = FLANGES[wg]
    return math.ceil((fl.hole or MIL_HOLE) * 10 - 1e-6) / 10


def max_hole_dia(wg: str, feed_input_diam: float = 0.0, edge: float = 1.0) -> float:
    """Largest through hole at the flange positions that keeps `edge` mm of metal to the nearest edge:
    outline of the plate/base (flange size), the circular guide and the neighbouring holes."""
    fl = FLANGES[wg]
    if fl.shape == "square":
        to_out = min(fl.A / 2 - fl.F, fl.A / 2 - fl.E)
        r = math.hypot(fl.E, fl.F)
        neighbour = 2 * min(fl.E, fl.F)
    else:
        to_out = fl.A / 2 - fl.pcd / 2
        r = fl.pcd / 2
        neighbour = 2 * r * math.sin(math.pi / 8)        # dowel hole at 45°
    lim = [to_out - edge, neighbour / 2 - edge]
    if feed_input_diam:
        lim.append(r - feed_input_diam / 2 - edge)
    # never below the standard flange hole (the round MIL flanges leave only ~0.8 mm outside it)
    return max(math.floor(2 * max(min(lim), 0.5) * 10) / 10, flange_hole(wg))


def clear_hole(wg: str, system: str = "metric") -> float:
    """Proposed diameter of the enlarged through holes (medium clearance of the flange screw)."""
    return round(min(max(CLEAR_MEDIUM.get(screw_for(wg, system), flange_hole(wg) + 0.3), flange_hole(wg) + 0.2),
                     max_hole_dia(wg)), 2)


def base_thread_options(wg: str, f_ghz: float | None, system: str = "metric") -> list[str]:
    """Threads offered for the feed-base holes: 10 GHz M4/M3, 24 GHz M3/M2.5/M2 (or the UNC equivalents);
    round MIL flanges: 4-40 UNC (their captive screws)."""
    if FLANGES[wg].shape == "round":
        return ["4-40 UNC"]
    met = BASE_THREADS_10GHZ if f_ghz is not None and f_ghz < TEN_GHZ_MAX else BASE_THREADS_HIGH
    return [plate_screw_name(x, system) for x in met]


def mount(wg: str, system: str = "metric", polarization: str = "V", feed_input_diam: float = 0.0,
          f_ghz: float | None = None, plate_screw: str | None = None, plate_t: float | None = None,
          base_holes: str = "flange", hole_dia: float | None = None, thread: str | None = None,
          cbore: bool = False, cb_depth: float | None = None, cb_dia: float | None = None,
          pins: bool = True, plate_head: str = "allen", plate_tap: bool = False) -> Mount:
    """Holes of the plate and of the feed base for waveguide `wg`.

    The 4 holes of the standard flange are reproduced, at the same positions, in the plate and in the feed base:
      base_holes "flange": through, same diameter as the flange holes;
                 "clear":  through, enlarged (hole_dia, proposed = medium clearance) — also in the plate: the feed
                           is screwed onto the external waveguide (relay, LNA) with screws from the feed side;
                 "tap":    threaded through in the base (thread; 10 GHz M4/M3, 24 GHz M3/M2.5/M2, UNC equivalents),
                           the plate keeps the flange-size holes.
      cbore: through holes only — counterbore for the screw head on the horn side of the base.
      plate_screw: square flanges — 4 extra screws plate→feed in the free spots, heads in counterbores of the
                   plate (WR side), blind tapped holes in the feed. None = no plate screws.
      pins: round MIL flanges — the 4 dowel holes of the flange, through the plate and into the base.
      plate_head: plate→feed screws "allen" (socket head in a counterbore) or "flat" (Phillips countersunk).
      plate_tap: the flange holes are threaded in the plate (the waveguide screws into the plate)."""
    if wg not in FLANGES:
        raise ValueError(f"nessuna flangia standard in tabella per {wg}")
    if base_holes not in BASE_HOLE_MODES:
        raise ValueError(f"fori della base: {base_holes}?")
    fl = FLANGES[wg]
    screw = screw_for(wg, system)                     # the waveguide flange screw
    m = Mount(fl, screw, polarization)
    m.stack = True                                    # the flange screws always go through the plate
    m.base_holes = base_holes
    if fl.note:
        m.warnings.append(fl.note)
    if fl.shape == "square":
        screw_xy = [(sx * fl.F, sy * fl.E) for sx in (1, -1) for sy in (1, -1)]
        dowel_xy = []
    else:
        r = fl.pcd / 2
        screw_xy = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (0, 90, 180, 270)]
        dowel_xy = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in (45, 135, 225, 315)]
    d_fl = flange_hole(wg)
    if base_holes == "tap":
        opts = base_thread_options(wg, f_ghz, system)
        thread = thread if thread in opts else opts[0]
        m.thread = thread
        d_major, tap, _ = SCREWS[thread]
        d_plate = d_fl
        m.engagement = m.tap_depth = m.guide_in = round(max(1.5 * d_major, 3.0), 1)
    else:
        d_max = max_hole_dia(wg, feed_input_diam)
        d_min = round(SCREWS[screw][0] + 0.1, 1)
        d_def = d_fl if base_holes == "flange" else clear_hole(wg, system)
        d_hole = round(min(max(float(hole_dia or d_def), d_min), d_max), 2)
        d_plate = d_hole
        m.feed_cbore = True                           # screws from the feed side, through base and plate
        cb_d, cb_k = (CBORE.get(screw, (round(HEADS.get(screw, (d_hole * 1.8, 0))[0] + 0.6, 1), 3.0))
                      if cbore else (0.0, 0.0))
        if cbore and cb_depth:
            cb_k = round(max(0.5, float(cb_depth)), 2)
        if cbore and cb_dia:
            cb_d = round(max(float(cb_dia), d_hole + 0.2), 2)
    for x, y in screw_xy:
        x, y = _rot(x, y, polarization)
        if plate_tap:
            _, p_tap, _ = SCREWS[screw]
            m.plate_holes.append(Hole(x, y, p_tap, "tap", f"FLANGIA GUIDA: {screw} filettato passante 6H (preforo Ø{p_tap:g})"))
        else:
            m.plate_holes.append(Hole(x, y, d_plate, "clear", f"FLANGIA GUIDA: Ø{d_plate:g} passante"))
        if base_holes == "tap":
            m.feed_holes.append(Hole(x, y, tap, "tap", f"FLANGIA GUIDA: {thread} filettato passante (preforo Ø{tap:g})"))
        else:
            m.feed_holes.append(Hole(x, y, d_hole, "cbore_back",
                                     f"FLANGIA GUIDA: Ø{d_hole:g} passante, lamatura Ø{cb_d:g} prof. {cb_k:g} lato horn"
                                     if cbore else f"FLANGIA GUIDA: Ø{d_hole:g} passante", cb_dia=cb_d, cb_depth=cb_k))
    if pins and dowel_xy:
        for x, y in dowel_xy:
            x, y = _rot(x, y, polarization)
            m.plate_holes.append(Hole(x, y, DOWEL_HOLE_ROUND, "dowel", f"PIN ALLINEAMENTO: Ø{DOWEL_HOLE_ROUND:g} passante (pin Ø1.56)"))
            m.feed_holes.append(Hole(x, y, DOWEL_HOLE_ROUND, "dowel", f"PIN ALLINEAMENTO: Ø{DOWEL_HOLE_ROUND:g} prof. 3 (pin Ø1.56)",
                                     depth=3.0))
    if plate_screw and fl.shape == "square":
        choices = plate_screw_options(f_ghz)
        metric = plate_screw if plate_screw in choices else (
            next((k for k, v in UNC_FOR_METRIC.items() if v == plate_screw), choices[0]))
        _plate_screws(m, system, feed_input_diam, wg, screw=plate_screw_name(metric, system), plate_t=plate_t,
                      head=plate_head)
    # interference with the feed's circular input guide
    if feed_input_diam:
        for h in m.feed_holes:
            gap = math.hypot(h.x, h.y) - max(h.dia, h.cb_dia) / 2 - feed_input_diam / 2
            if gap < 0.8:
                m.warnings.append(f"foro Ø{h.dia:g} a {gap:.2f} mm dalla guida circolare Ø{feed_input_diam:.2f}: "
                                  "troppo vicino, usa una flangia più grande o una guida diversa")
                break
    return m


def _plate_screws(m: Mount, system: str, feed_input_diam: float, wg: str, n_ang: int = 36,
                  screw: str | None = None, plate_t: float | None = None, head: str = "allen") -> None:
    """Four Phillips flat-head (countersunk) screws holding the plate on the feed (θ + k·90°), heads flush in
    countersinks on the WR side: the plate keeps its thickness. Smallest radius whose countersinks keep ≥ 0.6 mm
    from every other hole, from the circular guide and from the WR aperture, and ≥ 1 mm from the outline of the
    plate (the flange size). Symmetric positions first (axes, diagonals); other angles only as a last resort."""
    from .waveguide import RECT_WG
    screw = screw or ("M2.5" if system != "imperial" else "2-56 UNC")
    d_major, tap, clear = SCREWS[screw]
    dk, k, ang = CSK[screw]
    if head == "flat":
        cs_d = round(dk + 0.2, 1)                             # countersink diameter at the surface
        cs_k = round((cs_d - clear) / 2 / math.tan(math.radians(ang / 2)), 2)   # countersink depth
        grip_cut = 0.0                                        # flush: the whole plate is the grip
    else:                                                     # socket head cap screw in a counterbore
        cs_d, cs_k = CBORE[screw]
        grip_cut = cs_k
    w = RECT_WG.get(wg)
    a, b = (w.a_mm, w.b_mm) if w else (0.0, 0.0)
    if m.polarization == "H":
        a, b = b, a
    others = [(h.x, h.y, max(h.dia, h.cb_dia)) for h in m.plate_holes]
    def ok(x, y):
        if math.hypot(x, y) - cs_d / 2 < feed_input_diam / 2 + 0.6:
            return False
        if abs(x) < a / 2 + cs_d / 2 + 0.6 and abs(y) < b / 2 + cs_d / 2 + 0.6:
            return False
        return all(math.hypot(x - ox, y - oy) > (cs_d + od) / 2 + 0.6 for ox, oy, od in others)

    r = feed_input_diam / 2 + cs_d / 2 + 0.6
    eng = max(2.0 * d_major, 4.0)
    L, L_lab = 0.0, ""
    if plate_t:
        # screw length = 2 × plate thickness, commercial; grip = plate under the head
        L, L_lab = screw_length(plate_t, system)
        eng = L - (plate_t - grip_cut)
        if eng < 1.5 * d_major:
            m.warnings.append(f"vite {screw} × {L_lab}: solo {eng:.1f} mm di filetto nel feed (< 1.5 d)")
        if cs_k > plate_t - (0.5 if head == "flat" else 0.8):
            m.warnings.append(f"{'svasatura' if head == 'flat' else 'lamatura'} {screw} profonda {cs_k:.2f} mm in una "
                              f"piastrina di {plate_t:.2f} mm: usa viti più piccole o aumenta lo spessore della piastrina")
    # hole in the feed (IZ0JNY): even whole millimetres; the thread must reach the screw end and stops
    # 3 pitches (≥ 1 mm) before the bottom of the blind hole (tap lead)
    lead = max(1.0, 3 * PITCH.get(screw, 0.5))
    drill_d = float(2 * math.ceil((eng + lead) / 2 - 1e-9))
    tap_d = drill_d - lead
    r = math.ceil(r * 2 - 1e-9) / 2                          # radius on a 0.5 mm grid (9.0 on WR-42, as IZ0JNY)
    cands = [(r + 0.5 * j, th) for th in (0.0, math.pi / 4) for j in range(120)]
    cands += [(r + 0.1 * j, 0.5 * math.pi * i / (n_ang // 4)) for j in range(600) for i in range(n_ang // 4)]
    std = "ISO 7046" if ang == 90 else "UNC 82°"
    for r, th in cands:
        pts = [(r * math.cos(th + q * math.pi / 2), r * math.sin(th + q * math.pi / 2)) for q in range(4)]
        if all(ok(x, y) for x, y in pts):
            for x, y in pts:
                lab = f" × {L_lab}" if L_lab else ""
                m.plate_holes.append(
                    Hole(x, y, clear, "csk", f"FISSAGGIO PIASTRINA: Ø{clear:g} passante, svasatura {ang}° Ø{cs_d:g} lato guida "
                                             f"({screw}{lab} testa piana Phillips {std})", cb_dia=cs_d, cb_depth=cs_k)
                    if head == "flat" else
                    Hole(x, y, clear, "cbore", f"FISSAGGIO PIASTRINA: Ø{clear:g} passante, lamatura Ø{cs_d:g} prof. {cs_k:g} "
                                               f"lato guida ({screw}{lab} a brugola ISO 4762)", cb_dia=cs_d, cb_depth=cs_k))
                m.feed_holes.append(Hole(x, y, tap, "tap", f"FISSAGGIO PIASTRINA: {screw} filetto prof. {tap_d:.1f} "
                                         f"(preforo Ø{tap:g} prof. {drill_d:.0f})", depth=drill_d))
            m.plate_screw = screw
            m.engagement = eng
            m.tap_depth = tap_d
            m.screw_in = eng
            m.screw_len, m.screw_len_label = L, L_lab
            m.plate_head, m.plate_grip_cut = head, grip_cut
            return
    m.warnings.append(f"nessuna posizione libera per le viti piastrina→feed {screw}")


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
