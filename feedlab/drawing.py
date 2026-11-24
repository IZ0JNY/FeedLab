"""Mechanical drawing (PDF) of a feed: half-section with dimensions, dimension table, title block."""
from __future__ import annotations

import datetime as _dt
import math
import textwrap
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


TOLERANCE = {"general": None}    # general machining tolerance set by the user (None = OE2IGL value for the band)
HOLE_TOLERANCES = "filetti ISO 6H · fori spina H7 (pin m6) · fori passanti +0.1/0 · lamature +0.2/0"


def general_tolerance(f_ghz: float) -> float:
    """Tolerance printed on the drawings: the user's value, or the recommended one for the band."""
    return float(TOLERANCE.get("general") or tolerance_mm(f_ghz))


def _dim_h(ax, x0, x1, y, text, off=0.0):
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text((x0 + x1) / 2, y + off, text, ha="center", va="bottom", fontsize=6.5)


def _dim_v(ax, x, y0, y1, text):
    ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.6))
    ax.text(x, (y0 + y1) / 2, text, ha="right", va="center", fontsize=6.5, rotation=90)


_NOT_DIMS = ("wall", "outer_diam", "length", "rings")


def _param_for(geo, value: float, diameter: bool) -> str:
    """Name of the design dimension (geo.params) equal to `value` (mm), '' if none: lets the drawing say
    which callout is Di, las, D_aperture… For radii the parameter can be a diameter or a radius."""
    best = ""
    for k, v in geo.params.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool) or k in _NOT_DIMS or k.endswith(("_deg", "_pct")):
            continue
        if geo.kind == "axial_corrugated" and k[:1] == "d" and k[1:].isdigit():
            continue                                    # slot depths: dimensioned inside each step
        if abs(v - value) < 0.006:
            return k
    return best


def _corrugated_dims(ax, geo, half=True):
    """Axial Corrugated: depth d1…d8 inside each of the 8 steps, step width w, pitch and delta (upper half)."""
    p = geo.params
    a_s = max(p["Ds"], p["Di"]) / 2
    r_in = [a_s + p["delta"] + k * p["pitch"] for k in range(8)]
    z_open = [p.get("z_head", 0.0) + p["las"] + k * p["axi"] for k in range(8)]
    for k in range(8):
        dk = p[f"d{k + 1}"]
        y = r_in[k] + p["w"] / 2
        ax.annotate("", (z_open[k] - dk, y), (z_open[k], y), arrowprops=dict(arrowstyle="<->", lw=0.5, color="tab:blue"))
        ax.text(z_open[k] - dk / 2, y, f"d{k + 1}", ha="center", va="bottom", fontsize=6, color="tab:blue")
    zk = z_open[7] + 0.25 * p["axi"]                    # w across the last step, pitch between steps 7 and 8
    ax.annotate("", (zk, r_in[7]), (zk, r_in[7] + p["w"]), arrowprops=dict(arrowstyle="<->", lw=0.5, color="tab:blue"))
    ax.text(zk + 0.3, r_in[7] + p["w"] / 2, "w", ha="left", va="center", fontsize=6, color="tab:blue")
    zp = z_open[6] + 0.25 * p["axi"]
    ax.annotate("", (zp, r_in[6]), (zp, r_in[7]), arrowprops=dict(arrowstyle="<->", lw=0.5, color="tab:blue"))
    ax.text(zp + 0.3, (r_in[6] + r_in[7]) / 2, "pitch", ha="left", va="center", fontsize=6, color="tab:blue")
    if p["delta"] > 1e-6:
        zd = z_open[0] + 0.7 * p["axi"]
        ax.annotate("", (zd, a_s), (zd, r_in[0]), arrowprops=dict(arrowstyle="<->", lw=0.5, color="tab:blue"))
        ax.text(zd + 0.3, (a_s + r_in[0]) / 2, "delta", ha="left", va="center", fontsize=6, color="tab:blue")
    ax.text(0, -geo.outer_radius * (0.2 if half else 1.42) - 3, "d1…d8 = profondità degli 8 scalini (in blu); w, pitch, delta come in tabella",
            fontsize=6.5, color="tab:blue")


def _ring_dims(ax, geo):
    """VE4MA / Chaparral: ring_width, ring_depth and ring_setback on the first ring (upper half)."""
    p = geo.params
    t = float(p.get("wall", 0) or 0)
    L = geo.z_aperture
    r_in = p["horn_diam"] / 2 + t
    r_out = r_in + p["ring_width"]
    z_open = L - p["ring_setback"]
    z_bot = z_open - p["ring_depth"]
    kw = dict(arrowprops=dict(arrowstyle="<->", lw=0.5, color="tab:blue"))
    tx = dict(fontsize=6, color="tab:blue")
    zm = z_bot + 0.3 * p["ring_depth"]
    ax.annotate("", (zm, r_in), (zm, r_out), **kw)
    ax.text(zm + 0.3, (r_in + r_out) / 2, "ring_width", ha="left", va="center", **tx)
    rm = r_in + 0.7 * p["ring_width"]
    ax.annotate("", (z_bot, rm), (z_open, rm), **kw)
    ax.text((z_bot + z_open) / 2, rm, "ring_depth", ha="center", va="bottom", **tx)
    if p["ring_setback"] > 1e-6:
        ys = r_in + 0.25 * p["ring_width"]               # in front of the ring, above the horn wall
        ax.annotate("", (z_open, ys), (L, ys), **kw)
        ax.text(L + 0.3, ys, "ring_setback", ha="left", va="center", **tx)


def _title_block(fig, geo, title, material, sheet):
    """Title block: long texts (feed names, materials) wrap inside their cell and the row grows to fit."""
    from . import i18n
    rows = [("Titolo", title), ("Frequenza", f"{geo.f_ghz:g} GHz  (λ = {geo.lam:.3f} mm)"),
            ("Materiale", material), ("Tolleranze generali", f"±{general_tolerance(geo.f_ghz):g} mm  (Ø interni: precisione λ/100)"),
            ("Tolleranze fori", HOLE_TOLERANCES),
            ("Quote", "mm  —  z = 0 faccia flangia d'ingresso"),
            ("Data / Foglio", f"{_dt.date.today().isoformat()}  —  {sheet}"), ("Generato da", "FeedLab")]
    # translate whole texts first, then wrap (a wrapped line would no longer match the translation)
    cells = [(i18n.tr(k), textwrap.wrap(i18n.tr(str(v)), 52) or [""]) for k, v in rows]
    n_lines = sum(len(v) for _, v in cells)
    h = min(0.215, 0.17 * (n_lines + 0.6 * len(cells)) / (1.6 * len(cells)))   # stays below the dimension table
    ax = fig.add_axes([0.62, 0.03, 0.36, h]); ax.set_axis_off()
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0, 0), 1, 1, fill=False, lw=1.0))
    unit = 1.0 / (n_lines + 0.6 * len(cells))       # height of one text line in axes units
    y = 1.0
    for i, (k, v) in enumerate(cells):
        hr = unit * (len(v) + 0.6)
        y -= hr
        if i < len(cells) - 1:
            ax.plot([0, 1], [y, y], lw=0.4, color="k")
        ax.text(0.02, y + hr / 2, k, fontsize=6, color="0.3", va="center")
        ax.text(0.30, y + hr / 2, "\n".join(v), fontsize=7, va="center", linespacing=1.15)


def _section_axes(fig, geo: FeedGeometry, half: bool = False):
    """half=True: upper half only, at twice the scale (Axial Corrugated, sheet 1)."""
    ax = fig.add_axes([0.05, 0.25, 0.55, 0.68])
    for poly in geo.polygons:
        for s in ((1,) if half else (1, -1)):
            pts = [(z, s * r) for r, z in poly]
            ax.add_patch(Polygon(pts, closed=True, facecolor="0.85", edgecolor="k", lw=0.8, hatch="////"))
    ax.axhline(0, color="k", lw=0.5, ls="-.")
    L = geo.z_aperture
    Rmax = geo.outer_radius
    n_d = len({round(r, 3) for _, r in geo.profile})
    sp = 0.07 * Rmax                                  # half view: diameter callouts side by side, right of the part
    side = geo.kind == "axial_corrugated"             # many close diameters: callouts side by side, right of the part
    ax.set_xlim(-0.08 * L - 4, (L + (n_d + 1) * sp if side else L * 1.08) + 4)
    ax.set_ylim(-Rmax * (0.25 if half else 1.5) - 5, Rmax * (1.5 if side else 1.35) + 3)
    ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("Mezza sezione assiale, scala doppia (asse in basso)" if half else
                 "Sezione assiale (metà superiore = sezione, metà inferiore = specchio)", fontsize=8)
    # dimensions along the inner profile
    prof = geo.profile
    zs = sorted({round(z, 4) for z, _ in prof})
    ytop = Rmax * 1.15 + 1
    named = set()
    for i, (z0, z1) in enumerate(zip(zs[:-1], zs[1:])):
        k = _param_for(geo, z1 - z0, False)
        if geo.kind == "axial_corrugated" and (not k or k in named):              # corrugated: one callout per named length (las, axi)
            continue
        lab = f"{z1 - z0:.2f}" + (f" = {k}" if k and k not in named else "")
        named.add(k)
        _dim_h(ax, z0, z1, ytop + (i % 2) * 0.08 * Rmax, lab)
    _dim_h(ax, 0, L, ytop + 0.25 * Rmax, f"L = {L:.2f}")
    # diameters
    seen = set()
    for z, r in prof:
        key = round(r, 3)
        if key in seen:
            continue
        seen.add(key)
        k = _param_for(geo, 2 * r, True)
        x = z + 0.01 * L
        if side:
            x = L + len(seen) * sp
            ax.plot([z, x], [r, r], color="0.5", lw=0.3, ls=":")          # extension lines
            if not half:
                ax.plot([z, x], [-r, -r], color="0.5", lw=0.3, ls=":")
        _dim_v(ax, x, 0 if half else -r, r, f"Ø{2 * r:.3f}" + (f" = {k}" if k else ""))
    ax.text(L, -Rmax * (0.12 if half else 1.3), f"Ø esterno max {2 * geo.outer_radius:.2f}", fontsize=6.5, ha="right")
    _wall_dims(ax, geo)
    if geo.kind == "axial_corrugated":
        _corrugated_dims(ax, geo, half)
    if geo.kind in ("ve4ma", "chaparral"):
        _ring_dims(ax, geo)
    if geo.kind == "iz0jny":
        _step_dims(ax, geo)
    return ax


def _step_dims(ax, geo):
    """IZ0JNY: the inner step (upper half, inside the bore): height h = (Ds − Di)/2 and length Ls of the
    cylinder after it, with a leader to a readable label."""
    p = geo.params
    zs, ri, rs, ls = p["input_length"], p["Di_input"] / 2, p["Ds_step"] / 2, p["Ls"]
    c = "tab:red"
    ax.annotate("", (zs + 0.5 * ls, ri), (zs + 0.5 * ls, rs), arrowprops=dict(arrowstyle="<->", lw=0.6, color=c))
    ax.annotate("", (zs, rs - 0.25 * (rs - ri)), (zs + ls, rs - 0.25 * (rs - ri)),
                arrowprops=dict(arrowstyle="<->", lw=0.6, color=c))
    R = max(geo.outer_radius, rs)
    ax.annotate(f"scalino interno: h = {rs - ri:.3f} = (Ds_step − Di_input)/2\nLs = {ls:.3f}",
                xy=(zs + 0.5 * ls, 0.5 * (ri + rs)), xytext=(zs + 0.6 * R, 0.35 * ri),
                fontsize=6.5, color=c, arrowprops=dict(arrowstyle="-", lw=0.5, color=c))


def _wall_dims(ax, geo):
    """On the lower (mirrored) half, outside the part: wall thickness, axial thickness of every step
    (dimension between extension lines) and flare half-angles (leader to the flare)."""
    t = float(geo.params.get("wall", 0) or 0)
    feats = wall_features(geo.profile)
    L = geo.z_aperture
    Rmax = geo.outer_radius
    y_dim = -Rmax * 1.12 - 1.0                           # dimension line below the part
    if geo.kind == "axial_corrugated":   # slots: no smooth-horn step/flare callouts
        feats = {**feats, "steps": [], "flares": []}
        t = 0
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
    from . import i18n
    # Axial Corrugated: sheet 1 = half-section at double scale, sheet 2 = whole section
    views = [True, False] if geo.kind == "axial_corrugated" else [False]
    mnt = getattr(geo, "mount", None)
    n_sheets = len(views) + (mnt is not None)
    with PdfPages(path) as pdf:
      for i_view, half in enumerate(views):
        fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
        if isinstance(geo, RectHornGeometry):
            _rect_views(fig, geo)
        else:
            _section_axes(fig, geo, half)
        # dimension table
        ax = fig.add_axes([0.62, 0.25, 0.36, 0.68]); ax.set_axis_off()
        ax.set_title("Quote di progetto", fontsize=9, loc="left")
        lines = []
        for k, v in geo.params.items():
            if isinstance(v, (int, float)):
                unit = "°" if k.endswith("_deg") else ("%" if k.endswith("_pct") else ("" if k in ("rings",) else " mm"))
                lam = "" if (k.endswith(("_deg", "_pct")) or k == "rings") else f"   ({v / geo.lam:.3f} λ)"
                lines.append(f"{k:<18s} {v:10.3f}{unit}{lam}")
            else:
                lines.append(f"{k:<18s} {v}")
        lines.append("")
        for n in (geo.notes or [])[:8]:           # translated first, then wrapped to the column width
            lines += textwrap.wrap("• " + i18n.tr(n), 56, subsequent_indent="  ")
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
        _title_block(fig, geo, title, material, f"{i_view + 1}/{n_sheets}")
        i18n.translate_figure_mpl(fig)
        pdf.savefig(fig); plt.close(fig)
      if mnt is not None:
            fig = _flange_sheet(geo, mnt, title, material, f"{n_sheets}/{n_sheets}")
            i18n.translate_figure_mpl(fig)
            pdf.savefig(fig); plt.close(fig)
    return path


def _flange_sheet(geo, mnt, title, material, sheet="2/2"):
    """Sheet 2: front view of the drilled input flange and the hole table."""
    from matplotlib.patches import Circle
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0.05, 0.25, 0.5, 0.68]); ax.set_aspect("equal"); ax.set_axis_off()
    R = geo.params["flange_diam"] / 2
    side = geo.params.get("base_square")
    if side:
        from matplotlib.patches import Rectangle as _Rect
        ax.add_patch(_Rect((-side / 2, -side / 2), side, side, fill=False, lw=1.2))
        R = side / 2 * 1.15
    else:
        ax.add_patch(Circle((0, 0), R, fill=False, lw=1.2))
    ax.add_patch(Circle((0, 0), geo.r_input, fill=False, lw=1.0))
    ax.plot([-R * 1.1, R * 1.1], [0, 0], lw=0.4, ls="-.", color="0.4")
    ax.plot([0, 0], [-R * 1.1, R * 1.1], lw=0.4, ls="-.", color="0.4")
    for i, h in enumerate(mnt.feed_holes, 1):
        ax.add_patch(Circle((h.x, h.y), h.dia / 2, fill=False, lw=0.9, ec="k" if h.kind == "tap" else "g"))  # dowel/pin in green
        if h.kind == "tap":                      # thread: 3/4 circle at the major diameter (drawing convention)
            from matplotlib.patches import Arc
            dM = SCREW_MAJOR((mnt.plate_screw if h.depth else mnt.thread) or mnt.screw)
            ax.add_patch(Arc((h.x, h.y), dM, dM, theta1=0, theta2=270, lw=0.6))
        if h.cb_dia:                             # counterbore on the horn side (hidden from this face): dashed
            ax.add_patch(Circle((h.x, h.y), h.cb_dia / 2, fill=False, lw=0.7, ec="m", ls="--"))
        ax.text(h.x + h.dia * 0.8, h.y + h.dia * 0.8, str(i), fontsize=7, color="b")
    hole_labels(ax, mnt.feed_holes, R)
    ax.set_xlim(-R * 2.6, R * 1.25); ax.set_ylim(-R * 1.3, R * 1.3)
    from . import i18n

    def T(tpl, **kw):                          # whole sentences translated first (then wrapped), numbers after
        return i18n.tr(tpl).format(**kw)
    size = f"□ {side:.2f} × {side:.2f}" if side else f"Ø{2 * R:.2f}"
    pol = T("verticale" if mnt.polarization == "V" else "orizzontale")
    ax.set_title(T("Flangia d'ingresso: vista dalla faccia z = 0 ({size}, spessore {t:.2f} mm)", size=size,
                   t=geo.params["flange_thickness"]) + "\n" +
                 T("lato largo della guida {wg} lungo x (polarizzazione {pol})", wg=mnt.flange.wg, pol=pol), fontsize=9)
    ax2 = fig.add_axes([0.58, 0.25, 0.4, 0.68]); ax2.set_axis_off()
    import textwrap
    if mnt.base_holes == "tap":
        head = [T("Fori della flangia filettati {th} passanti: le viti entrano dal lato della guida, attraversano "
                  "flangia e piastrina e si avvitano in questa base.", th=mnt.thread)]
    elif any(h.cb_dia for h in mnt.feed_holes):
        head = [T("Viti {screw} inserite dal lato del feed, con la testa nella lamatura (tratteggio magenta, lato horn): "
                  "attraversano base e piastrina e si avvitano nella flangia della guida.", screw=mnt.screw)]
    else:
        head = [T("Fori della flangia passanti: viti {screw} inserite dal lato del feed con la testa appoggiata sulla "
                  "base; attraversano base e piastrina e si avvitano nella flangia della guida.", screw=mnt.screw)]
    if mnt.plate_screw:
        head.append(T("Viti piastra → feed: {ps} (testa nella lamatura della piastra).", ps=mnt.plate_screw))
    lines = [T("FORATURA per flangia {wg} {name}", wg=mnt.flange.wg, name=mnt.flange.name)]
    for h_ in head:
        lines += textwrap.wrap(h_, 62)
    lines += ["", f"{'#':>2s} {'x':>8s} {'y':>8s}  " + T("lavorazione")]
    for i, h in enumerate(mnt.feed_holes, 1):
        lines.append(f"{i:>2d} {h.x:>8.2f} {h.y:>8.2f}  {i18n.tr(h.callout)}")
    lines.append("")
    for n_ in (T("Coordinate in mm dal centro della guida."),
               T("Fori filettati nella flangia; nel file STEP sono modellati al diametro di preforo."),
               T("Allineare piastrina e guida con le spine prima di serrare.")):
        lines += textwrap.wrap(n_, 62)
    for w in mnt.warnings:
        lines += textwrap.wrap(T("ATTENZIONE:") + " " + i18n.tr(w), 70)
    lines += ["", T("Fonte foratura:") + " Flann, Waveguide and Flange Data; MIL-DTL-3922/67C"]
    ax2.text(0, 1, "\n".join(lines), va="top", family="monospace", fontsize=7.5)
    _title_block(fig, geo, title, material, sheet)
    return fig


def hole_labels(ax, holes, R, fontsize=6.5):
    """Callouts on the view: one leader per group of identical holes ('4× M3 filettato passante …'), stacked on the
    left of the part so they never run into the text on the right (translated, then wrapped)."""
    import textwrap as _tw
    from collections import OrderedDict
    from . import i18n
    groups = OrderedDict()
    for h in holes:
        groups.setdefault(h.callout, []).append(h)
    n = len(groups)
    for i, (callout, hs) in enumerate(groups.items()):
        h = min(hs, key=lambda q: (q.x, -q.y))                  # left-most hole of the group
        ty = R * (1.15 - 2.3 * (i + 0.5) / max(n, 1))
        txt = "\n".join(_tw.wrap(f"{len(hs)}× {i18n.tr(callout)}", 30))
        ax.annotate(txt, xy=(h.x, h.y), xytext=(-1.3 * R, ty), fontsize=fontsize, color="navy", ha="right", va="center",
                    arrowprops=dict(arrowstyle="-", lw=0.5, color="navy", shrinkA=1, shrinkB=2))


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
