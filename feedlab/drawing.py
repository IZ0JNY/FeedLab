"""Mechanical drawing (PDF) of a feed: half-section with dimensions, dimension table, title block."""
from __future__ import annotations

import datetime as _dt
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon, Rectangle

from .geometry import FEED_TYPES, FeedGeometry, RectHornGeometry, wall_features


def tolerance_mm(f_ghz: float) -> float:
    """OE2IGL guide: ±0.1 mm < 30 GHz, ±0.05 < 55 GHz, ±0.02 above (≈ λ/100-λ/200)."""
    return 0.1 if f_ghz < 30 else 0.05 if f_ghz < 55 else 0.02 if f_ghz < 80 else 0.01


def _dim_h(ax, x0, x1, y, text, off=0.0):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom", fontsize=6.5)


def _dim_v(ax, x, y0, y1, text):
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text(x, (y0 + y1) / 2, text, ha="right", va="center", fontsize=6.5, rotation=90)


def _title_block(fig, geo, title, material, sheet):
    ax = fig.add_axes([0.62, 0.03, 0.36, 0.17]); ax.set_axis_off()
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, lw=1.0))
    rows = [("Titolo", title), ("Frequenza", f"{geo.f_ghz:g} GHz  (λ = {geo.lam:.3f} mm)"),
            ("Materiale", material), ("Tolleranze generali", f"±{tolerance_mm(geo.f_ghz)} mm  (Ø interni: precisione λ/100)"),
            ("Quote", "mm  —  z = 0 faccia flangia d'ingresso"),
            ("Data / Foglio", f"{_dt.date.today().isoformat()}  —  {sheet}"), ("Generato da", "FeedLab")]
    for i, (k, v) in enumerate(rows):
        y = 1 - (i + 1) / len(rows)
        ax.plot([0, 1], [y, y], lw=0.4, color="k")
        ax.text(0.02, y + 0.03, k, fontsize=6, color="0.3")
        ax.text(0.30, y + 0.03, v, fontsize=7)


def _section_axes(fig, geo: FeedGeometry):
    ax = fig.add_axes([0.05, 0.25, 0.55, 0.68])
    for poly in geo.polygons:
        for s in (1, -1):
            pts = [(z, s * r) for r, z in poly]
            ax.add_patch(Polygon(pts, closed=True, facecolor="0.85", edgecolor="k", lw=0.8, hatch="////"))
    ax.axhline(0, color="k", lw=0.5, ls="-.")
    L = geo.z_aperture
    Rmax = geo.outer_radius
    ax.set_xlim(-0.08 * L - 4, L * 1.08 + 4)
    ax.set_ylim(-Rmax * 1.5 - 5, Rmax * 1.35 + 3)
    ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("Sezione assiale (metà superiore = sezione, metà inferiore = specchio)", fontsize=8)
    # dimensions along the inner profile
    prof = geo.profile
    zs = sorted({round(z, 4) for z, _ in prof})
    ytop = Rmax * 1.15 + 1
    for i, (z0, z1) in enumerate(zip(zs[:-1], zs[1:])):
        _dim_h(ax, z0, z1, ytop + (i % 2) * 0.08 * Rmax, f"{z1 - z0:.2f}")
    _dim_h(ax, 0, L, ytop + 0.25 * Rmax, f"L = {L:.2f}")
    # diameters
    seen = set()
    for z, r in prof:
        key = round(r, 3)
        if key in seen:
            continue
        seen.add(key)
        _dim_v(ax, z + 0.01 * L, -r, r, f"Ø{2 * r:.3f}")
    ax.text(L, -Rmax * 1.3, f"Ø esterno max {2 * geo.outer_radius:.2f}", fontsize=6.5, ha="right")
    _wall_dims(ax, geo)
    return ax


def _wall_dims(ax, geo):
    """On the lower (mirrored) half, outside the part: wall thickness, axial thickness of every step
    (dimension between extension lines) and flare half-angles (leader to the flare)."""
    t = float(geo.params.get("wall", 0) or 0)
    feats = wall_features(geo.profile)
    L = geo.z_aperture
    Rmax = geo.outer_radius
    y_dim = -Rmax * 1.12 - 1.0                           # dimension line below the part
    if t > 0:                                            # wall at the aperture rim
        r_ap = geo.profile[-1][1]
        ax.annotate("", (L + 0.02 * L, -r_ap), (L + 0.02 * L, -r_ap - t), arrowprops=dict(arrowstyle="<->", lw=0.6))
        ax.text(L + 0.035 * L, -r_ap - t / 2, f"parete {t:.2f}", fontsize=6.5, va="center", ha="left")
    for z, ra, rb in feats["steps"]:                     # annular step wall: t thick along z
        z0 = z - t if rb > ra else z
        y_top = -(max(ra, rb) + t)
        for zz in (z0, z0 + t):                          # extension lines
            ax.plot([zz, zz], [y_top - 0.3, y_dim - 0.8], color="k", lw=0.4)
        w = max(1.2 * t, 0.025 * L)
        ax.annotate("", (z0, y_dim), (z0 - w, y_dim), arrowprops=dict(arrowstyle="<-", lw=0.6))
        ax.annotate("", (z0 + t, y_dim), (z0 + t + w, y_dim), arrowprops=dict(arrowstyle="<-", lw=0.6))
        ax.text(z0 + t + w + 0.3, y_dim, f"{t:.2f} (gradino)", fontsize=6.5, ha="left", va="center")
    for i, (z0, r0, z1, r1, a) in enumerate(feats["flares"]):   # flare half-angle with leader
        zm, rm = z0 + 0.55 * (z1 - z0), r0 + 0.55 * (r1 - r0)
        rr = rm + t / math.cos(math.radians(a))          # outer surface of the wall at zm
        ax.annotate(f"semiangolo flare α = {abs(a):.2f}°", xy=(zm, -rr), xytext=(zm, y_dim - 0.09 * Rmax * (i + 1) - 2),
                    fontsize=6.5, ha="center", va="top", arrowprops=dict(arrowstyle="->", lw=0.6))


def drawing_pdf(geo, path: str | Path, material: str = "Ottone CuZn39Pb3 / Al 6082", title: str | None = None,
                tolerances: list | None = None) -> Path:
    """tolerances: rows from tolerance.analyse(...).critical — printed as a table of the tolerance each
    critical dimension needs (the general tolerance applies to all the others)."""
    path = Path(path)
    title = title or f"{FEED_TYPES.get(geo.kind, geo.kind)}"
    with PdfPages(path) as pdf:
        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
        if isinstance(geo, RectHornGeometry):
            _rect_views(fig, geo)
        else:
            _section_axes(fig, geo)
        # dimension table
        ax = fig.add_axes([0.62, 0.25, 0.36, 0.68]); ax.set_axis_off()
        ax.set_title("Quote di progetto", fontsize=9, loc="left")
        lines = []
        for k, v in geo.params.items():
            if isinstance(v, (int, float)):
                unit = "°" if k.endswith("_deg") else ("" if k in ("rings",) else " mm")
                lam = "" if (k.endswith("_deg") or k == "rings") else f"   ({v / geo.lam:.3f} λ)"
                lines.append(f"{k:<18s} {v:10.3f}{unit}{lam}")
            else:
                lines.append(f"{k:<18s} {v}")
        lines.append("")
        lines += [f"• {n}" for n in (geo.notes or [])][:8]
        ax.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=7)
        if tolerances:
            axt = fig.add_axes([0.05, 0.03, 0.55, 0.17]); axt.set_axis_off()
            rows = [f"{'Quota':<22s}{'Nominale':>12s}{'Tolleranza':>13s}{'Varianza':>10s}"]
            for c in tolerances:
                u = c.get("unit", "mm")
                rows.append(f"{c['label']:<22.22s}{c['nominal']:>10.3f} {u:<2s}{'±' + format(c['tol_ok'], 'g'):>10s} {u:<2s}"
                            f"{100 * c['share']:>8.0f}%")
            axt.text(0, 1, "TOLLERANZE PER QUOTA (analisi Monte Carlo FeedLab)\n" + "\n".join(rows),
                     va="top", family="monospace", fontsize=6.5)
        _title_block(fig, geo, title, material, "1/1")
        from . import i18n
        i18n.translate_figure_mpl(fig)
        pdf.savefig(fig); plt.close(fig)
        mnt = getattr(geo, "mount", None)
        if mnt is not None:
            fig = _flange_sheet(geo, mnt, title, material)
            i18n.translate_figure_mpl(fig)
            pdf.savefig(fig); plt.close(fig)
    return path


def _flange_sheet(geo, mnt, title, material):
    """Sheet 2: front view of the drilled input flange and the hole table."""
    from matplotlib.patches import Circle
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.05, 0.25, 0.5, 0.68]); ax.set_aspect("equal"); ax.set_axis_off()
    R = geo.params["flange_diam"] / 2
    ax.add_patch(Circle((0, 0), R, fill=False, lw=1.2))
    ax.add_patch(Circle((0, 0), geo.r_input, fill=False, lw=1.0))
    ax.plot([-R * 1.1, R * 1.1], [0, 0], lw=0.4, ls="-.", color="0.4")
    ax.plot([0, 0], [-R * 1.1, R * 1.1], lw=0.4, ls="-.", color="0.4")
    for i, h in enumerate(mnt.feed_holes, 1):
        ax.add_patch(Circle((h.x, h.y), h.dia / 2, fill=False, lw=0.9, ec="k" if h.kind == "tap" else "g"))  # dowel/pin in green
        if h.kind == "tap":                      # thread: 3/4 circle at the major diameter (drawing convention)
            from matplotlib.patches import Arc
            ax.add_patch(Arc((h.x, h.y), SCREW_MAJOR(mnt.screw), SCREW_MAJOR(mnt.screw), theta1=0, theta2=270, lw=0.6))
        ax.text(h.x + h.dia * 0.8, h.y + h.dia * 0.8, str(i), fontsize=7, color="b")
    ax.set_xlim(-R * 1.25, R * 1.25); ax.set_ylim(-R * 1.25, R * 1.25)
    ax.set_title(f"Flangia d'ingresso: vista dalla faccia z = 0 (Ø{2 * R:.2f}, spessore "
                 f"{geo.params['flange_thickness']:.2f} mm)\nlato largo della guida {mnt.flange.wg} lungo x "
                 f"(polarizzazione {'verticale' if mnt.polarization == 'V' else 'orizzontale'})", fontsize=9)
    ax2 = fig.add_axes([0.58, 0.25, 0.4, 0.68]); ax2.set_axis_off()
    lines = [f"FORATURA per flangia {mnt.flange.wg} {mnt.flange.name}",
             f"Viti piastra → feed: {mnt.plate_screw} (testa nella lamatura della piastra)",
             f"Le viti della guida ({mnt.screw}) si avvitano nella piastra.", "",
             f"{'#':>2s} {'x':>8s} {'y':>8s}  lavorazione"]
    for i, h in enumerate(mnt.feed_holes, 1):
        depth = ""
        lines.append(f"{i:>2d} {h.x:>8.2f} {h.y:>8.2f}  {h.callout}{depth}")
    lines += ["", "Coordinate in mm dal centro della guida.",
              "Fori filettati nella flangia; nel file STEP sono", "modellati al diametro di preforo.",
              "Allineare piastrina e guida con le spine prima di serrare."]
    import textwrap
    for w in mnt.warnings:
        lines += textwrap.wrap(f"ATTENZIONE: {w}", 70)
    lines += ["", f"Fonte foratura: Flann, Waveguide and Flange Data; MIL-DTL-3922/67C"]
    ax2.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=7.5)
    _title_block(fig, geo, title, material, "2/2")
    return fig


def SCREW_MAJOR(screw: str) -> float:
    from .flanges import SCREWS
    return SCREWS[screw][0]


def _rect_views(fig, geo: RectHornGeometry):
    p = geo.params
    L0, L = p["input_length"], p["axial_length"]
    for j, (lab, w0, w1) in enumerate((("Piano H (vista dall'alto)", p["a"], p["aperture_H"]),
                                        ("Piano E (vista laterale)", p["b"], p["aperture_E"]))):
        ax = fig.add_axes([0.05, 0.6 - j * 0.34, 0.55, 0.32]); ax.set_axis_off(); ax.set_aspect("equal")
        t = p["wall"]
        for s in (1, -1):
            pts = [(0, s * w0 / 2), (L0, s * w0 / 2), (L0 + L, s * w1 / 2), (L0 + L, s * (w1 / 2 + t)),
                   (L0, s * (w0 / 2 + t)), (0, s * (w0 / 2 + t))]
            ax.add_patch(Polygon(pts, closed=True, facecolor="0.85", edgecolor="k", hatch="////", lw=0.8))
        ax.set_xlim(-5, L0 + L + 5); ax.set_ylim(-w1 / 2 - 3 * t - 6, w1 / 2 + 3 * t + 6)
        ax.set_title(lab, fontsize=8)
        _dim_h(ax, 0, L0, w1 / 2 + t + 2, f"{L0:.2f}")
        _dim_h(ax, L0, L0 + L, w1 / 2 + t + 2, f"{L:.2f}")
        _dim_v(ax, L0 + L + 2, -w1 / 2, w1 / 2, f"{w1:.2f}")
        _dim_v(ax, -1, -w0 / 2, w0 / 2, f"{w0:.2f}")
