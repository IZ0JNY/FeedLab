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
    "w2imu": "W2IMU dual-mode (Turrin/W1GHZ)",
    "w2imu_oe2igl": "W2IMU ottimizzato (OE2IGL)",
    "large_w2imu": "Large W2IMU flare 30° (W1GHZ/W1FKF)",
    "skobelev": "Dual-mode 'optimum' Skobelev (W1GHZ)",
    "pickett_potter": "Pickett-Potter (OE2IGL)",
    "conical": "Horn conico",
    "ve4ma": "VE4MA / Super-VE4MA (choke)",
    "chaparral": "Chaparral 3 anelli",
    "rect_horn": "Horn rettangolare (G3RPE)",
}

# feeds whose interior is a single circular guide with steps/cones -> mode-matching simulation possible
MODEMATCH_OK = {"open_circular", "w2imu", "w2imu_oe2igl", "large_w2imu", "skobelev", "pickett_potter", "conical"}


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


def _wall_polygon(profile, t, flange_r=None, flange_t=None):
    """Metal cross-section of a horn wall of thickness t following the inner profile (r, z).
    Outer surface is the inner profile offset radially by t (simple, machinable).
    Optional input flange (disk) at z=0."""
    inner = [(r, z) for z, r in profile]
    outer = [(r + t, z) for z, r in profile][::-1]
    # rim at aperture is flat; at input add flange if requested
    poly = inner + outer
    if flange_r and flange_t:
        r_in = profile[0][1]
        poly = inner + outer[:-1] + [(profile[0][1] + t, flange_t), (flange_r, flange_t), (flange_r, 0.0), (r_in, 0.0)]
    return np.array(poly)


COLLAR = {"diam": None, "length": 25.0, "z0": 3.0}    # set COLLAR["diam"] = 40 for standard LNB holders


def _finish(kind, f, params, profile, t, extra_polys=None, notes=None, design=None, flange=True):
    lam = wavelength_mm(f)
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
    fl_t = max(1.5, 0.12 * lam) if flange else None
    polys.append(_wall_polygon(profile, t, fl_r, fl_t))
    for p in extra_polys or []:
        polys.append(np.asarray(p))
        outer = max(outer, max(x for x, _ in p))
    if fl_r:
        outer = max(outer, fl_r) if fl_r > outer else outer
    if fl_r:
        params = {**params, "flange_diam": 2 * fl_r, "flange_thickness": fl_t}
    return FeedGeometry(kind, f, params, profile, polys, profile[-1][0], r_ap, profile[0][1],
                        max(outer, max(np.max(p[:, 0]) for p in polys)), notes or [], design)


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
                       notes=["W1GHZ 6.3: 0.6-0.9λ → f/D 0.25-0.4; >0.95λ squint"])

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
        Lin = kw.get("input_length", lam)
        prof = [(0.0, Di / 2), (Lin, Di / 2), (Lin, Ds / 2), (Lin + Lf, Dap / 2)]
        return _finish(kind, f_ghz, {"Di_input": Di, "Ds_step": Ds, "D_aperture": Dap, "flare_length": Lf,
                                     "input_length": Lin, "wall": t}, prof, t,
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
                       notes=["smooth conical: unequal E/H, edge currents (W1GHZ 6.4.1)"])

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

    raise ValueError(f"unknown feed type {kind}")


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
