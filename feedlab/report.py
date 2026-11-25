# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Project outputs of FeedLab: PDF documents (simulations, feed, dish, plate, feed + plate, data table, openEMS,
complete report) built from the project dictionary (feedlab.project), plus CSV and ZIP."""
from __future__ import annotations

import csv
import io
import math
import zipfile
from pathlib import Path

import numpy as np

A4 = (8.27, 11.69)


def _tr(s):
    from . import i18n
    return i18n.tr(s)


def _fig():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt.figure(figsize=A4, dpi=100)


def _header(fig, proj, title):
    i = proj["inputs"]
    fig.text(0.06, 0.965, "FeedLab — " + _tr(title), fontsize=13, weight="bold")
    fig.text(0.06, 0.945, f"{i.get('feed_name', '')} · {i.get('f_ghz', 0):.3f} GHz · "
             f"{_tr('parabola')} {i['dish']['kind']} D {i['dish']['D_mm']:.0f} mm f/D {i['dish']['fD']:.3f} · "
             f"{_tr(i.get('material') or '')}", fontsize=8, color="0.3")
    fig.text(0.06, 0.02, f"FeedLab {proj.get('app_version', '')} · {proj.get('created_utc', '')} UTC · © Ivan De Cesaris IZ0JNY",
             fontsize=6.5, color="0.45")


def _table(ax, rows, col_w=(0.55, 0.45), fs=8):
    ax.axis("off")
    if not rows:
        return
    t = ax.table(cellText=[[_tr(str(a)), b] for a, b in rows], colWidths=list(col_w), loc="upper left", cellLoc="left")
    t.auto_set_font_size(False)
    t.set_fontsize(fs)
    t.scale(1, 1.25)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("0.85")
        if c == 0:
            cell.set_facecolor("#f3f5f8")


def _fmt(v, nd=3):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return _tr("sì") if v else _tr("no")
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    if isinstance(v, (list, tuple)):
        return ", ".join(_fmt(x, nd) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}={_fmt(x, nd)}" for k, x in v.items() if x is not None)
    return str(v)


def results_rows(proj):
    r = proj.get("results") or {}
    sc = proj["inputs"].get("scenario") or {}
    ts = r.get("tsys") or {}
    rows = [("Guadagno della parabola (dBi)", _fmt(r.get("gain_dbi"), 2)), ("G/T (dB/K)", _fmt(r.get("g_over_t"), 2)),
            ("Efficienza totale (%)", _fmt(100 * r["eta"], 1) if r.get("eta") is not None else "—"),
            ("Spillover (%)", _fmt(100 * r["spill"], 1) if r.get("spill") is not None else "—"),
            ("Illuminazione (%)", _fmt(100 * r["illum"], 1) if r.get("illum") is not None else "—"),
            ("Fase (%)", _fmt(100 * r["phase"], 2) if r.get("phase") is not None else "—"),
            ("Polarizzazione (%)", _fmt(100 * r["pol"], 2) if r.get("pol") is not None else "—"),
            ("Taper al bordo (dB)", _fmt(r.get("edge_taper_db"), 1)), ("S11 a f0 (dB)", _fmt(r.get("s11_db"), 1)),
            ("Centro di fase (mm, + davanti all'apertura)", _fmt(r.get("phase_center_mm"), 2)),
            ("Perdite ohmiche del feed (dB)", _fmt(r.get("ohmic_db"), 3)),
            ("Temperatura d'antenna (K)", _fmt(r.get("t_ant_K"), 1)), ("Tsys (K)", _fmt(ts.get("sys"), 1)),
            ("Elevazione (°)", _fmt(sc.get("elev_deg"), 0)), ("NF del preamplificatore (dB)", _fmt(sc.get("nf_db"), 2)),
            ("Perdite feed → LNA (dB)", _fmt(sc.get("line_loss_db"), 2)), ("Superficie RMS (mm)", _fmt(sc.get("rms_mm"), 2)),
            ("Attenuazione allo zenit (dB)", _fmt(sc.get("zenith_db"), 2))]
    return rows


def _sim_pages(pdf, proj):
    """Fast-simulation pages: results, S11 over the band, E/H pattern with the dish edge."""
    from . import reflector
    fig = _fig()
    _header(fig, proj, "Simulazioni veloci (mode matching)")
    _table(fig.add_axes([0.06, 0.52, 0.88, 0.40]), results_rows(proj))
    sw = proj.get("s11_sweep")
    ax = fig.add_axes([0.10, 0.08, 0.38, 0.30])
    if sw:
        ax.plot(sw["f_ghz"], sw["s11_db"], lw=1.6)
        ax.axhline(-20, ls=":", color="0.5")
        ax.set_xlabel("GHz"); ax.set_ylabel("S11 (dB)"); ax.set_title(_tr("Adattamento S11"), fontsize=9)
        ax.grid(alpha=0.3)
    else:
        ax.axis("off")
    pat = (proj.get("results") or {}).get("pattern")
    ax = fig.add_axes([0.58, 0.08, 0.38, 0.30])
    if pat:
        ax.plot(pat["theta_deg"], pat["E_db"], label=_tr("piano E"))
        ax.plot(pat["theta_deg"], pat["H_db"], label=_tr("piano H"), ls="--")
        edge = reflector.half_angle_from_fD(proj["inputs"]["dish"]["fD"])
        ax.axvline(edge, color="r", ls=":", lw=1)
        ax.text(edge + 1, -3, _tr("bordo"), color="r", fontsize=7)
        ax.set_xlim(0, 120); ax.set_ylim(-40, 1); ax.grid(alpha=0.3)
        ax.set_xlabel("θ (°)"); ax.set_ylabel("dB"); ax.set_title(_tr("Lobo del feed"), fontsize=9); ax.legend(fontsize=7)
    else:
        ax.axis("off")
    pdf.savefig(fig)


def _dish_pages(pdf, proj):
    from . import reflector
    i = proj["inputs"]
    d = i["dish"]
    r = proj.get("results") or {}
    fig = _fig()
    _header(fig, proj, "Parabola")
    half = reflector.half_angle_from_fD(d["fD"])
    rows = [("Tipo", "offset" if d["kind"] == "offset" else "prime focus"), ("Diametro (mm)", _fmt(d["D_mm"], 0)),
            ("f/D (equivalente per offset)", _fmt(d["fD"], 3)), ("Focale (mm)", _fmt(d.get("f_mm"), 1)),
            ("Angolo di apertura visto dal feed (°)", _fmt(2 * half, 1)),
            ("f/D di progetto del feed", _fmt(i.get("fd_design_used"), 3)),
            ("Illuminazione", _fmt(i.get("ill_mode"))), ("Taper al bordo scelto (dB)", _fmt(i.get("ill_taper"), 1)),
            ("Note", (d.get("note") or "")[:110])]
    _table(fig.add_axes([0.06, 0.60, 0.88, 0.32]), rows, (0.42, 0.58))
    ax = fig.add_axes([0.36, 0.12, 0.56, 0.38])
    parts = [("spill", "Spillover"), ("illum", "Illuminazione"), ("phase", "Fase"), ("pol", "Polarizzazione")]
    vals = [100 * (r.get(k) or 0) for k, _ in parts] + [100 * (r.get("eta") or 0)]
    labs = [_tr(l) for _, l in parts] + [_tr("Totale (con superficie e perdite)")]
    ax.barh(labs, vals, color=["#4c78a8"] * 4 + ["#f58518"])
    for y, v in enumerate(vals):
        ax.text(v + 0.5, y, f"{v:.1f} %", va="center", fontsize=8)
    ax.set_xlim(0, 110); ax.invert_yaxis(); ax.set_title(_tr("Efficienza della parabola con questo feed"), fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    pdf.savefig(fig)


def _rows_flat(d, prefix=""):
    rows = []
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            rows += _rows_flat(v, f"{prefix}{k}.")
        elif isinstance(v, list) and len(v) > 8:
            continue
        else:
            rows.append((f"{prefix}{k}", _fmt(v, 4) if isinstance(v, float) else _fmt(v)))
    return rows


def data_rows(proj):
    """Every value of the project as (name, value) rows: inputs, feed dimensions, plate, results."""
    rows = [("— " + _tr("Dati inseriti") + " —", "")]
    inp = {k: v for k, v in proj["inputs"].items() if k not in ("mount_ui",)}
    rows += _rows_flat(inp)
    rows += [("— " + _tr("Quote del feed (mm, °)") + " —", "")] + _rows_flat(proj.get("geometry", {}).get("params"))
    g = proj.get("geometry", {})
    rows += [("length_mm", _fmt(g.get("length_mm"), 3)), ("aperture_diam_mm", _fmt(g.get("aperture_diam_mm"), 3)),
             ("outer_diam_mm", _fmt(g.get("outer_diam_mm"), 3))]
    if proj.get("plate"):
        rows += [("— " + _tr("Piastrina λ/4") + " —", "")] + _rows_flat(proj["plate"])
    rows += [("— " + _tr("Risultati (simulatore veloce)") + " —", "")] + _rows_flat(
        {k: v for k, v in (proj.get("results") or {}).items() if k != "pattern"})
    for n, o in enumerate(proj.get("openems") or []):
        rows += [("— openEMS " + str(o.get("label") or n + 1) + " —", "")] + _rows_flat(
            {k: v for k, v in o.items() if k not in ("dir", "label")})
    return rows


def _data_pages(pdf, proj):
    rows = data_rows(proj)
    per = 46
    for k in range(0, len(rows), per):
        fig = _fig()
        _header(fig, proj, "Tabella di tutte le quote e i dati del progetto")
        _table(fig.add_axes([0.06, 0.05, 0.88, 0.87]), rows[k:k + per], (0.45, 0.55), fs=7)
        pdf.savefig(fig)


def _openems_pages(pdf, proj):
    from . import deep_analysis
    runs = proj.get("openems") or []
    if not runs:
        fig = _fig()
        _header(fig, proj, "Simulazioni openEMS")
        fig.text(0.06, 0.85, _tr("Nessuna simulazione openEMS completata per questo feed e questa banda."), fontsize=10)
        pdf.savefig(fig)
        return
    for o in runs:
        fig = _fig()
        _header(fig, proj, "Simulazioni openEMS")
        fig.text(0.06, 0.915, str(o.get("label") or ""), fontsize=10, weight="bold")
        rows = [("Guadagno della parabola (dBi)", _fmt(o.get("gain_dbi"), 2)), ("G/T (dB/K)", _fmt(o.get("g_over_t"), 2)),
                ("Efficienza totale (%)", _fmt(100 * o["eta"], 1) if o.get("eta") is not None else "—"),
                ("Centro di fase (mm, + davanti all'apertura)", _fmt(o.get("phase_center_mm"), 2)),
                ("Fascio a −3 dB (°)", _fmt(o.get("hpbw_deg"), 3)), ("Tsys (K)", _fmt(o.get("t_sys"), 1)),
                ("Celle per λ", _fmt(o.get("cells_per_lambda"))), ("S11", _fmt(o.get("s11"), 2))]
        _table(fig.add_axes([0.06, 0.58, 0.88, 0.32]), rows, (0.45, 0.55))
        try:
            r = deep_analysis.load(Path(o["dir"]) / "results.json")
            ax = fig.add_axes([0.10, 0.10, 0.38, 0.36])
            ax.plot(r.freq_ghz, r.s11_db); ax.set_xlabel("GHz"); ax.set_ylabel("S11 (dB)"); ax.grid(alpha=0.3)
            ax.set_title(_tr("Adattamento S11"), fontsize=9)
            ff = r.ff_at(r.f0).pattern()
            ax = fig.add_axes([0.58, 0.10, 0.38, 0.36])
            for arr, lab, ls in ((ff.E, _tr("piano E"), "-"), (ff.H, _tr("piano H"), "--")):
                ax.plot(ff.theta_deg, 20 * np.log10(np.abs(arr) / np.max(np.abs(arr)) + 1e-12), ls=ls, label=lab)
            ax.set_xlim(0, 120); ax.set_ylim(-40, 1); ax.grid(alpha=0.3); ax.legend(fontsize=7)
            ax.set_title(_tr("Lobo del feed (openEMS)"), fontsize=9)
        except Exception:
            pass
        pdf.savefig(fig)


def _assembly_pages(pdf, proj, S):
    from . import mounting
    fig = _fig()
    _header(fig, proj, "Feed + piastrina (montaggio)")
    mu = S.get("mount_ui") or {}
    scheme = mu.get("scheme") or "none"
    rows = [("Schema di montaggio", _tr(mounting.SCHEMES.get(scheme, ("—",))[0])),
            ("Guida d'onda rettangolare", _fmt(proj["inputs"].get("wr_wg"))),
            ("Viti della flangia", _fmt((proj["inputs"].get("mount_cfg") or {}).get("thread") or mu.get("screw"))),
            ("Viti piastrina → feed", _fmt(mu.get("plate_screw"))), ("Spessore della piastrina (mm)", _fmt((proj.get("plate") or {}).get("body_t"), 3)),
            ("Spessore della base del feed (mm)", _fmt(proj["geometry"]["params"].get("flange_thickness"), 3)),
            ("Lunghezza del feed (mm)", _fmt(proj["geometry"].get("length_mm"), 2))]
    _table(fig.add_axes([0.06, 0.66, 0.88, 0.26]), rows, (0.45, 0.55))
    try:
        sf = mounting.section_fig(scheme, _tr, mu.get("screw", ""), mu.get("plate_screw") or "")
        buf = io.BytesIO()
        sf.savefig(buf, format="png", dpi=160)
        import matplotlib.image as mpimg
        buf.seek(0)
        ax = fig.add_axes([0.08, 0.08, 0.84, 0.55])
        ax.imshow(mpimg.imread(buf)); ax.axis("off")
    except Exception:
        pass
    pdf.savefig(fig)


def _pages_pdf(proj, builders) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        for b in builders:
            b(pdf)
    plt.close("all")
    return buf.getvalue()


def _merge(parts: list[bytes]) -> bytes:
    from pypdf import PdfWriter, PdfReader
    w = PdfWriter()
    for p in parts:
        if p:
            for page in PdfReader(io.BytesIO(p)).pages:
                w.add_page(page)
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


def _cover(pdf, proj):
    i = proj["inputs"]
    r = proj.get("results") or {}
    fig = _fig()
    fig.text(0.5, 0.80, "FeedLab", ha="center", fontsize=30, weight="bold", color="#12324f")
    fig.text(0.5, 0.75, _tr("Report di progetto"), ha="center", fontsize=18)
    fig.text(0.5, 0.68, i.get("feed_name", ""), ha="center", fontsize=14)
    fig.text(0.5, 0.645, f"{i.get('f_ghz', 0):.3f} GHz · {_tr(i.get('material') or '')}", ha="center", fontsize=11)
    d = i["dish"]
    fig.text(0.5, 0.61, f"{_tr('parabola')} {d['kind']} D {d['D_mm']:.0f} mm f/D {d['fD']:.3f}", ha="center", fontsize=11)
    if r.get("gain_dbi") is not None:
        fig.text(0.5, 0.54, f"G {r['gain_dbi']:.2f} dBi · G/T {r['g_over_t']:.2f} dB/K · η {100 * r['eta']:.1f} % · "
                 f"{_tr('taper al bordo')} {r['edge_taper_db']:.1f} dB", ha="center", fontsize=10)
    fig.text(0.5, 0.20, f"FeedLab {proj.get('app_version', '')} · {proj.get('created_utc', '')} UTC", ha="center", fontsize=9, color="0.4")
    fig.text(0.5, 0.17, "© Ivan De Cesaris IZ0JNY · GPL-3.0-or-later", ha="center", fontsize=9, color="0.4")
    pdf.savefig(fig)


# ------------------------------------------------------------------ public builders
def sims_pdf(proj) -> bytes:
    return _pages_pdf(proj, [lambda p: _sim_pages(p, proj)])


def dish_pdf(proj) -> bytes:
    return _pages_pdf(proj, [lambda p: _dish_pages(p, proj)])


def data_pdf(proj) -> bytes:
    return _pages_pdf(proj, [lambda p: _data_pages(p, proj)])


def openems_pdf(proj) -> bytes:
    return _pages_pdf(proj, [lambda p: _openems_pages(p, proj)])


def assembly_pdf(proj, S) -> bytes:
    return _pages_pdf(proj, [lambda p: _assembly_pages(p, proj, S)])


def feed_pdf(proj, geo, work: Path) -> bytes:
    """Feed drawing (the PDF of the Drawing tab) followed by its simulation pages."""
    from . import drawing
    path = drawing.drawing_pdf(geo, work / "feed_drawing.pdf", proj["inputs"].get("material") or "", None)
    return _merge([Path(path).read_bytes(), sims_pdf(proj)])


def plate_pdf(S, proj, work: Path) -> bytes | None:
    from . import plate, project
    pl = project.plate_obj(S, proj["inputs"]["f_ghz"])
    if pl is None:
        return None
    return Path(plate.drawing_pdf(pl, work / "plate.pdf", proj["inputs"].get("material") or "")).read_bytes()


def data_csv(proj) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow([_tr("Voce"), _tr("Valore")])
    for a, b in data_rows(proj):
        w.writerow([a, b])
    return buf.getvalue()


def full_pdf(proj, S, geo, work: Path) -> bytes:
    parts = [_pages_pdf(proj, [lambda p: _cover(p, proj), lambda p: _sim_pages(p, proj), lambda p: _dish_pages(p, proj)])]
    try:                                              # feed drawing (the simulation pages are already above)
        from . import drawing
        parts.append(Path(drawing.drawing_pdf(geo, work / "feed_drawing_full.pdf",
                                              proj["inputs"].get("material") or "", None)).read_bytes())
    except Exception:
        pass
    try:
        parts.append(plate_pdf(S, proj, work))
    except Exception:
        pass
    parts += [assembly_pdf(proj, S), openems_pdf(proj), data_pdf(proj)]
    return _merge(parts)


def zip_all(files: dict[str, bytes | str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            if data:
                z.writestr(name, data)
    return buf.getvalue()
