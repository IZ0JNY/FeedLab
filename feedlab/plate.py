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

    def rotation_deg(self) -> float:
        """Rotation of the WR broad wall from horizontal (0 = H-wall horizontal → vertical polarisation)."""
        return 0.0 if self.polarization == "V" else 90.0


def _zte(k, kc):
    beta = math.sqrt(k * k - kc * kc)
    return ETA0 * k / beta


def design_plate(f_ghz: float, wg: str, circ_diam_mm: float, polarization: str = "V",
                 corner_r_mm: float | None = None, optimized: bool = True) -> MatchingPlate:
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
    return MatchingPlate(f_ghz, wg, circ_diam_mm, a_opt, b, r, t, lg / 200, z0, polarization, outer, basic)


def plate_solid(p: MatchingPlate):
    import cadquery as cq
    body = cq.Workplane("XY").rect(p.outer, p.outer).extrude(p.thickness)
    hole = cq.Workplane("XY").sketch().rect(p.a, p.b).vertices().fillet(max(p.corner_r, 0.01)).finalize().extrude(p.thickness)
    if p.polarization == "H":
        hole = hole.rotate((0, 0, 0), (0, 0, 1), 90)
    return body.cut(hole)


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
           f"Lato esterno        {p.outer:.1f} mm\n"
           f"Z0 intermedia       {p.z0:.1f} Ω\n\n"
           f"Versione base: a {p.basic['a']:.3f}, b {p.basic['b']:.3f}, t {p.basic['thickness']:.3f} mm\n\n"
           f"Materiale: {material}\nTolleranza generale ±{tolerance_mm(p.f_ghz)} mm\n"
           "Fori di fissaggio: secondo la flangia standard del WR\n"
           "e del feed (allineare con spine di centraggio).\n\n"
           "Metodo: design guide OE2IGL (openEMS), ottimizzazione HB9PZK.\n"
           "Verificare S11 con openEMS prima della produzione.")
    ax2.text(0, 1, txt, va="top", family="monospace", fontsize=9)
    from . import i18n
    i18n.translate_figure_mpl(fig)
    fig.savefig(path)
    plt.close(fig)
    return path
