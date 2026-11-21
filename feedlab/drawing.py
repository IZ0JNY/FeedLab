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

from .geometry import FEED_TYPES, FeedGeometry, RectHornGeometry


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
            ("Data / Foglio", f"{_dt.date.today().isoformat()}  —  {sheet}"), ("Generato da", "FeedLab / mwFeedDesign")]
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
    ax.set_ylim(-Rmax * 1.35 - 3, Rmax * 1.35 + 3)
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
    return ax


def drawing_pdf(geo, path: str | Path, material: str = "Ottone CuZn39Pb3 / Al 6082", title: str | None = None) -> Path:
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
        _title_block(fig, geo, title, material, "1/1")
        from . import i18n
        i18n.translate_figure_mpl(fig)
        pdf.savefig(fig); plt.close(fig)
    return path


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
