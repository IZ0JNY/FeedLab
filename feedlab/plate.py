"""λ/4 matching plate from the feed's circular input guide to standard rectangular waveguide (WR).

Method: OE2IGL 'quarter-waveguide-adapter' design guide (openEMS-verified, S11 < -25…-30 dB):
  Z0 = sqrt(Z_TE10(rect) * Z_TE11(circ)),   Z_TE = eta0 * k / beta
  intermediate rectangular aperture: a = pi / sqrt(k^2 - (k eta0 / Z0)^2), b = a/2 (basic)
  optimized (HB9PZK) with corner radius r: b = 0.97 sqrt(D * b_rect), a_opt = a + 0.808 r^2 / b,
  thickness = lambda_g/4 (basic) or 0.828 * lambda_g/4 (optimized), tolerance ± lambda_g/200.
The orientation of the WR sets the linear polarisation radiated by the (circularly symmetric) feed:
E-field is parallel to the narrow side 'b'. Vertical polarisation = WR broad wall horizontal.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .waveguide import RECT_WG, C0

ETA0 = 376.730313


@dataclass
class MatchingPlate:
    f_ghz: float
    wg: str
    circ_diam: float
    a: float               # aperture width (mm), along the WR broad wall
    b: float               # aperture height (mm)
    corner_r: float
    thickness: float
    tolerance: float
    z0: float
    polarization: str      # "V" | "H"
    outer: float           # plate outer side (mm)
    basic: dict
    mount: object = None   # flanges.Mount when the fixing holes are drilled
    body_t: float = 0.0    # total plate thickness (> thickness when a pocket makes room for counterbores)

    @property
    def pocket_depth(self) -> float:
        """Feed-side pocket of the circular guide diameter: extends the feed's circular guide."""
        return max(self.body_t - self.thickness, 0.0)

    @property
    def shape(self) -> str:
        """Outline of the plate = outline of the standard flange of the WR: square (WR-90, WR-75, WR-42…)
        or round (MIL UG-383/385/387: WR-22 and smaller). outer is the side or the diameter."""
        from .flanges import FLANGES
        fl = FLANGES.get(self.wg)
        return "round" if fl is not None and fl.shape == "round" else "square"

    def rotation_deg(self) -> float:
        """Rotation of the WR broad wall from horizontal (0 = H-wall horizontal → vertical polarisation)."""
        return 0.0 if self.polarization == "V" else 90.0


def _zte(k, kc):
    beta = math.sqrt(k * k - kc * kc)
    return ETA0 * k / beta


def design_plate(f_ghz: float, wg: str, circ_diam_mm: float, polarization: str = "V",
                 corner_r_mm: float | None = None, optimized: bool = True, holes: str | None = None,
                 plate_screw: str | None = None) -> MatchingPlate:
    """holes: None (plain plate) or "metric" / "imperial": drill the standard flange pattern of `wg`
    (feedlab.flanges) — clearance holes for the screws and dowel holes."""
    w = RECT_WG[wg]
    k = 2 * math.pi * f_ghz * 1e9 / C0                    # 1/m
    kc_r = math.pi / (w.a_mm * 1e-3)
    kc_c = 1.841 * 2 / (circ_diam_mm * 1e-3)
    if k <= kc_r or k <= kc_c:
        raise ValueError("frequenza sotto il cutoff di una delle guide")
    z0 = math.sqrt(_zte(k, kc_r) * _zte(k, kc_c))
    a = 1000 * math.pi / math.sqrt(k * k - (k * ETA0 / z0) ** 2)
    lg = 2 * math.pi / math.sqrt(k * k - (math.pi / a * 1000) ** 2) * 1000
    basic = {"a": a, "b": a / 2, "thickness": lg / 4}
    r = corner_r_mm if corner_r_mm is not None else round(min(2.0, 0.15 * a), 2)
    if optimized:
        b = math.sqrt(circ_diam_mm * w.b_mm) * 0.97
        a_opt = a + 0.808 / b * r * r
        t = lg / 4 * 0.828
    else:
        b, a_opt, t = a / 2, a, lg / 4
    outer = max(circ_diam_mm, w.a_mm, a_opt) + 2 * max(6.0, 0.5 * w.a_mm)
    mnt = None
    if holes:
        from .flanges import mount
        mnt = mount(wg, holes, polarization, circ_diam_mm, f_ghz, plate_screw)
        body_t = round(max(t, mnt.plate_body_min()), 2)
        # screw length depends on the plate thickness: drill again with it (same positions)
        mnt = mount(wg, holes, polarization, circ_diam_mm, f_ghz, plate_screw, plate_t=body_t)
        outer = max(outer, mnt.flange.A, 2 * mnt.plate_radius + 3.0)   # refined below, per flange shape
    from .flanges import FLANGES
    fl = FLANGES.get(wg)
    if fl is not None:
        # same outline and size as the waveguide's standard flange (square WR-90/75/42…, round MIL from WR-22),
        # larger only where the plate→feed screws do not fit inside it (0.5 mm of metal at the edge, as their placement)
        outer = fl.A
        if mnt is not None:
            if fl.shape == "round":
                need = max(math.hypot(h.x, h.y) + max(h.dia, h.cb_dia) / 2 for h in mnt.plate_holes)
            else:
                need = max(max(abs(h.x), abs(h.y)) + max(h.dia, h.cb_dia) / 2 for h in mnt.plate_holes)
            outer = max(outer, 2 * (need + 0.5))
            if outer > fl.A + 0.01:
                mnt.warnings.append(f"la piastrina misura {outer:.2f} mm invece di {fl.A:.2f} mm come la flangia {wg}: le lamature delle "
                                    "viti piastra→feed non ci stanno; con viti piastra→feed più piccole può restare "
                                    "uguale alla flangia")
    body_t = max(t, mnt.plate_body_min()) if mnt else t
    return MatchingPlate(f_ghz, wg, circ_diam_mm, a_opt, b, r, t, lg / 200, z0, polarization, outer, basic, mnt,
                         round(body_t, 2))


def plate_solid(p: MatchingPlate):
    """z = 0 feed side, z = body_t WR side. The λ/4 rectangular aperture occupies the last `thickness`
    on the WR side; a thicker body gets a feed-side pocket of the circular guide diameter."""
    import cadquery as cq
    T = p.body_t or p.thickness
    body = (cq.Workplane("XY").circle(p.outer / 2) if p.shape == "round" else
            cq.Workplane("XY").rect(p.outer, p.outer)).extrude(T)
    hole = (cq.Workplane("XY").workplane(offset=T - p.thickness).sketch().rect(p.a, p.b).vertices()
            .fillet(max(p.corner_r, 0.01)).finalize().extrude(p.thickness))
    if p.polarization == "H":
        hole = hole.rotate((0, 0, 0), (0, 0, 1), 90)
    body = body.cut(hole)
    if T - p.thickness > 1e-6:
        body = body.cut(cq.Workplane("XY").circle(p.circ_diam / 2).extrude(T - p.thickness))
    if p.mount is not None:
        for h in p.mount.plate_holes:
            body = body.cut(cq.Workplane("XY").center(h.x, h.y).circle(h.dia / 2).extrude(T))
            if h.kind == "cbore":
                body = body.cut(cq.Workplane("XY").workplane(offset=T - h.cb_depth).center(h.x, h.y)
                                .circle(h.cb_dia / 2).extrude(h.cb_depth))
    return body


def mesh(p: MatchingPlate, tol: float = 0.02):
    """Triangle mesh (vertices Nx3, faces Mx3) of the plate for the 3D preview."""
    import numpy as np
    shape = plate_solid(p).val()
    verts, tris = shape.tessellate(tol, 0.2)
    return np.array([(v.x, v.y, v.z) for v in verts]), np.array(tris, dtype=int)


def export_step(p: MatchingPlate, path):
    import cadquery as cq
    cq.exporters.export(plate_solid(p), str(path), exportType="STEP")
    return path


def drawing_pdf(p: MatchingPlate, path, material: str = "Ottone / Alluminio"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
    from .drawing import tolerance_mm
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.05, 0.12, 0.5, 0.8]); ax.set_aspect("equal"); ax.set_axis_off()
    h = p.outer / 2
    if p.shape == "round":
        ax.add_patch(Circle((0, 0), h, fill=False, lw=1.2))
    else:
        ax.add_patch(Rectangle((-h, -h), p.outer, p.outer, fill=False, lw=1.2))
    aa, bb = (p.a, p.b) if p.polarization == "V" else (p.b, p.a)
    ax.add_patch(FancyBboxPatch((-aa / 2 + p.corner_r, -bb / 2 + p.corner_r), aa - 2 * p.corner_r, bb - 2 * p.corner_r,
                                boxstyle=f"round,pad={p.corner_r}", fill=True, fc="0.85", ec="k", lw=1))
    ax.add_patch(Circle((0, 0), p.circ_diam / 2, fill=False, ls="--", lw=0.8))
    w = RECT_WG[p.wg]
    wa, wb = (w.a_mm, w.b_mm) if p.polarization == "V" else (w.b_mm, w.a_mm)
    ax.add_patch(Rectangle((-wa / 2, -wb / 2), wa, wb, fill=False, ls=":", lw=0.8, ec="b"))
    ax.annotate("", (-aa / 2, -h - 2), (aa / 2, -h - 2), arrowprops=dict(arrowstyle="<->"))
    ax.text(0, -h - 1.5, f"{aa:.3f}", ha="center", fontsize=8)
    ax.annotate("", (h + 2, -bb / 2), (h + 2, bb / 2), arrowprops=dict(arrowstyle="<->"))
    ax.text(h + 3, 0, f"{bb:.3f}", va="center", rotation=90, fontsize=8)
    ax.arrow(0, -bb / 2 * 0.6, 0, bb * 0.5, width=0.05 * bb, color="r") if p.polarization == "V" else \
        ax.arrow(-aa * 0.3, 0, aa * 0.5, 0, width=0.05 * aa, color="r")
    if p.mount is not None:
        for hl in p.mount.plate_holes:
            ax.add_patch(Circle((hl.x, hl.y), hl.dia / 2, fill=False, lw=0.9, ec="g" if hl.kind in ("dowel", "pin") else "k"))
            if hl.kind == "tap":
                from .flanges import SCREWS
                from matplotlib.patches import Arc
                dM = SCREWS[p.mount.screw][0]
                ax.add_patch(Arc((hl.x, hl.y), dM, dM, theta1=0, theta2=270, lw=0.6))
            if hl.kind == "cbore":
                ax.add_patch(Circle((hl.x, hl.y), hl.cb_dia / 2, fill=False, lw=0.7, ec="m"))
            ax.plot([hl.x - hl.dia * 0.7, hl.x + hl.dia * 0.7], [hl.y, hl.y], lw=0.3, color="0.4")
            ax.plot([hl.x, hl.x], [hl.y - hl.dia * 0.7, hl.y + hl.dia * 0.7], lw=0.3, color="0.4")
    ax.set_xlim(-h - 6, h + 8); ax.set_ylim(-h - 6, h + 6)
    ax.set_title("Piastrina λ/4 — vista frontale (rosso = campo E)\n"
                 "tratteggio: Ø guida circolare del feed · punteggiato blu: WR", fontsize=9)
    ax2 = fig.add_axes([0.6, 0.12, 0.38, 0.8]); ax2.set_axis_off()
    txt = (f"PIASTRINA DI ADATTAMENTO λ/4\n\n"
           f"Frequenza           {p.f_ghz:g} GHz\n"
           f"Guida rettangolare  {p.wg} ({w.a_mm} × {w.b_mm} mm)\n"
           f"Guida circolare     Ø {p.circ_diam:.3f} mm\n"
           f"Polarizzazione      {'VERTICALE' if p.polarization == 'V' else 'ORIZZONTALE'}\n\n"
           f"Apertura a × b      {p.a:.3f} × {p.b:.3f} mm\n"
           f"Raggio angoli       {p.corner_r:.2f} mm\n"
           f"Spessore            {p.thickness:.3f} mm  (± {p.tolerance:.3f})\n"
           + (f"Spessore corpo      {p.body_t:.2f} mm: tasca lato feed Ø{p.circ_diam:.3f}\n"
              f"                    prof. {p.pocket_depth:.2f} mm (prolunga la guida circolare)\n"
              if p.pocket_depth > 1e-6 else "") +
           (f"Ø esterno           {p.outer:.2f} mm (flangia rotonda)\n" if p.shape == "round" else
              f"Lato esterno        {p.outer:.1f} mm\n") +
           f"Z0 intermedia       {p.z0:.1f} Ω\n\n"
           f"Versione base: a {p.basic['a']:.3f}, b {p.basic['b']:.3f}, t {p.basic['thickness']:.3f} mm\n\n"
           f"Materiale: {material}\nTolleranza generale ±{tolerance_mm(p.f_ghz)} mm\n"
           + (_holes_text(p) if p.mount is not None else
              "Fori di fissaggio: secondo la flangia standard del WR\n"
              "e del feed (allineare con spine di centraggio).\n\n") +
           "Metodo: design guide OE2IGL (openEMS), ottimizzazione HB9PZK.\n"
           "Verificare S11 con openEMS prima della produzione.")
    ax2.text(0, 1, txt, va="top", family="monospace", fontsize=6.8 if p.mount is not None else 9)
    from . import i18n
    i18n.translate_figure_mpl(fig)
    fig.savefig(path)
    plt.close(fig)
    return path


def _holes_text(p: MatchingPlate) -> str:
    from . import i18n
    import textwrap

    def T(tpl, **kw):
        return i18n.tr(tpl).format(**kw)
    m = p.mount
    lines = ["", T("FORATURA flangia {wg} {name}", wg=m.flange.wg, name=m.flange.name)]
    if m.stack:
        lines += textwrap.wrap(T("(viti guida {screw} passanti, avvitate nella base del feed; coordinate dal centro)",
                                 screw=m.screw), 58)
    else:
        lines += textwrap.wrap(T("(viti guida {screw} nella piastra, viti piastra→feed {ps}; coordinate dal centro)",
                                 screw=m.screw, ps=m.plate_screw), 58)
    for h in m.plate_holes:
        lines.append(f"  x {h.x:+7.2f}  y {h.y:+7.2f}  {i18n.tr(h.callout)}")
    if m.stack:
        lines += ["  " + x for x in textwrap.wrap(T("viti della guida: lunghezza = flangia guida + {t:.1f} mm + {s:.1f} nel feed",
                                                    t=p.body_t, s=m.screw_in), 58)]
    else:
        lines += ["  " + x for x in textwrap.wrap(T("viti della guida: lunghezza ≤ flangia guida + {t:.1f} mm", t=p.body_t), 58)]
    if m.screw_len and not m.stack:
        drill = max(h.depth or 0.0 for h in m.feed_holes if h.kind == "tap" and m.plate_screw in h.callout)
        for x in (T("viti piastra→feed: 4 × {ps} × {ln} a testa cilindrica", ps=m.plate_screw, ln=m.screw_len_label),
                  T("(2 × spessore {t:.2f} → {ln}); nel feed: vite {s:.1f}, foro prof. {d:.0f} (pari), filetto prof. {tp:.1f}",
                    t=p.body_t, ln=m.screw_len_label, s=m.screw_in, d=drill, tp=m.tap_depth)):
            lines += ["  " + y for y in textwrap.wrap(x, 58)]
    for w in m.warnings:
        lines += ["  " + x for x in textwrap.wrap(i18n.tr(w), 58)]
    return "\n".join(lines) + "\n\n"
