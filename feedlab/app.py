"""FeedLab GUI — run with:  feedlab-gui   (or: streamlit run feedlab/app.py)"""
from __future__ import annotations

import io
import json
import math
import os
import tempfile
import time
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as _st

import feedlab
from feedlab import credits as _credits_mod

from feedlab import i18n

st = i18n.wrap(_st)

from feedlab import (app_openems, cad, dishes, drawing, efficiency, explore, materials, plate, geometry, modematch, noise, openems_local, openems_sim, patterns, tolerance,
                     reflector, wizard)
from feedlab.waveguide import HAM_BANDS_GHZ, wavelength_mm

S = st.session_state
if "lang" not in S:
    S.lang = i18n.default_lang()
i18n.set_lang(S.lang)
st.set_page_config(page_title="FeedLab — Laboratorio di Progettazione di feed/illuminatori a microonde", page_icon="📡", layout="wide")
WORK = Path(tempfile.gettempdir()) / "feedlab_work"
WORK.mkdir(exist_ok=True)

BANDS = {f"{v:g} GHz ({k})": v for k, v in HAM_BANDS_GHZ.items() if v <= 140}


# ---------------------------------------------------------------- helpers
def _defaults():
    S.setdefault("f_ghz", 47.088)
    S.setdefault("dish", None)
    S.setdefault("feed_kind", "pickett_potter")
    S.setdefault("overrides", {})
    S.setdefault("wall", None)
    S.setdefault("cands", None)
    S.setdefault("fullwave", None)


_defaults()


def current_geometry():
    dish = S.dish or wizard.dish_from_prime(600, 0.6)
    kind = S.feed_kind
    ov = dict(S.overrides.get(kind, {}))
    if kind == "rect_horn":
        return geometry.build_rect(S.f_ghz, dish.fD, wizard._wg_for(S.f_ghz), wall=S.wall, **ov)
    return geometry.build(kind, S.f_ghz, fD=dish.fD, wall=S.wall, **ov)


@st.cache_data(show_spinner=False)
def run_modematch(sections: tuple, f_list: tuple, n_modes: int):
    r = modematch.simulate(list(sections), np.array(f_list), n_modes=n_modes)
    return r


@st.cache_data(show_spinner=False)
def quick_pattern(kind: str, sections: tuple, f0: float, rect_params: tuple | None):
    if rect_params:
        a, b, AH, AE, L = rect_params
        lam = wavelength_mm(f0)
        RH = math.hypot(L, (AH - a) / 2) * AH / max(AH - a, 1e-6)
        RE = math.hypot(L, (AE - b) / 2) * AE / max(AE - b, 1e-6)
        return patterns.rectangular_aperture_pattern(AH / lam, AE / lam, RH / lam, RE / lam, n=80, n_theta=361), None
    r = modematch.simulate(list(sections), [f0], n_modes=16)
    return modematch.aperture_pattern(r, 0, f0, n_rho=48, n_phi=60, n_theta=361), r.aperture_modes[0]


def polar_fig(p: patterns.Pattern, title: str, floor: float = -40):
    e, h = p.db()
    fig = go.Figure()
    for name, v, col in (("Piano E (φ=0°)", e, "#d62728"), ("Piano H (φ=90°)", h, "#1f77b4")):
        th = np.concatenate([-p.theta_deg[::-1], p.theta_deg])
        vv = np.clip(np.concatenate([v[::-1], v]), floor, 0) - floor
        fig.add_trace(go.Scatterpolar(theta=th, r=vv, mode="lines", name=name, line=dict(color=col)))
    fig.update_layout(title=title, height=460, polar=dict(
        angularaxis=dict(rotation=90, direction="clockwise", tickmode="array",
                         tickvals=list(range(0, 360, 30))),
        radialaxis=dict(tickvals=[0, 10, 20, 30, 40], ticktext=[f"{floor}", f"{floor + 10}", f"{floor + 20}",
                                                                 f"{floor + 30}", "0 dB"])))
    return fig


def lobe3d_fig(p: patterns.Pattern, floor: float = -35):
    th = np.radians(p.theta_deg)
    ph = np.radians(np.arange(0, 361, 4))
    T, PH = np.meshgrid(th, ph, indexing="ij")
    n = p.normalized()
    P = np.abs(n.E)[:, None] ** 2 * np.cos(PH) ** 2 + np.abs(n.H)[:, None] ** 2 * np.sin(PH) ** 2
    db = 10 * np.log10(P + 1e-12)
    R = np.clip(db - floor, 0, None) / -floor
    X, Y, Z = R * np.sin(T) * np.cos(PH), R * np.sin(T) * np.sin(PH), R * np.cos(T)
    fig = go.Figure(go.Surface(x=X, y=Y, z=Z, surfacecolor=np.clip(db, floor, 0), colorscale="Turbo",
                               cmin=floor, cmax=0, colorbar=dict(title="dB")))
    fig.update_layout(height=560, scene=dict(aspectmode="data", xaxis_title="x (piano E)", yaxis_title="y (piano H)",
                                             zaxis_title="z (verso il riflettore)"),
                      title="Lobo di irradiazione 3D del feed (normalizzato)")
    return fig


def model3d_fig(geo, cut: bool):
    if isinstance(geo, geometry.RectHornGeometry):
        v, f = cad.mesh(geo)
    else:
        v, f = cad.profile_mesh(geo, n_phi=64, cut_deg=90 if cut else 0)
    fig = go.Figure(go.Mesh3d(x=v[:, 0], y=v[:, 1], z=v[:, 2], i=f[:, 0], j=f[:, 1], k=f[:, 2],
                              color="#c9a227", flatshading=False, lighting=dict(ambient=0.45, diffuse=0.8, specular=0.6),
                              opacity=1.0))
    fig.update_layout(height=600, scene=dict(aspectmode="data", xaxis_title="x mm", yaxis_title="y mm", zaxis_title="z mm"),
                      title="Modello 3D (ottone) — z = 0 flangia d'ingresso")
    return fig


def section_fig(geo):
    fig = go.Figure()
    if isinstance(geo, geometry.RectHornGeometry):
        return None
    for poly in geo.polygons:
        for s in (1, -1):
            P = np.vstack([poly, poly[:1]])
            fig.add_trace(go.Scatter(x=P[:, 1], y=s * P[:, 0], fill="toself", mode="lines",
                                     line=dict(color="black", width=1), fillcolor="rgba(201,162,39,0.6)", showlegend=False))
    fig.add_hline(y=0, line_dash="dashdot", line_color="gray")
    t = float(geo.params.get("wall", 0) or 0)
    feats = geometry.wall_features(geo.profile)
    ann = dict(showarrow=True, arrowhead=0, arrowwidth=1, ax=0, ay=-28, font=dict(size=11), bgcolor="rgba(255,255,255,0.8)")
    for z, ra, rb in feats["steps"]:
        z0 = z - t if rb > ra else z
        fig.add_annotation(x=z0 + t / 2, y=(min(ra, rb) + t + max(ra, rb)) / 2, text=f"gradino {t:.2f} mm", **ann)
    for z0, r0, z1, r1, a in feats["flares"]:
        fig.add_annotation(x=(z0 + z1) / 2, y=-(r0 + r1) / 2, text=f"flare α = {abs(a):.2f}°",
                           **{**ann, "ay": 28})
    fig.update_layout(height=330, yaxis=dict(scaleanchor="x"), xaxis_title="z (mm)", yaxis_title="r (mm)",
                      title=f"Sezione assiale · parete {t:.2f} mm", margin=dict(t=40, b=10))
    return fig


# ---------------------------------------------------------------- sidebar
def _set_lang():
    i18n.set_lang(S.lang)
    try:
        openems_local.save_settings(language=S.lang)
    except Exception:
        pass


@_st.dialog("ℹ️ Credits", width="large")
def _credits_dialog():
    from feedlab import credits as _cr
    _cr.render(st, header=False)


with st.sidebar:
    st.selectbox("Lingua / Language", list(i18n.LANGS), key="lang", format_func=lambda k: i18n.LANGS[k],
                 on_change=_set_lang)
    st.title("📡 FeedLab")
    st.subheader("Laboratorio di Progettazione di feed/illuminatori a microonde")
    st.caption("10–134 GHz · basato su W1GHZ Antenna Book, design guide OE2IGL e letteratura")
    band = st.selectbox("Banda", list(BANDS) + ["Altra frequenza…"],
                        index=list(BANDS.values()).index(S.f_ghz) if S.f_ghz in BANDS.values() else len(BANDS))
    if band == "Altra frequenza…":
        S.f_ghz = st.number_input("Frequenza (GHz)", 10.0, 140.0, float(S.f_ghz), 0.001, format="%.3f")
    else:
        S.f_ghz = BANDS[band]
    st.metric("λ", f"{wavelength_mm(S.f_ghz):.3f} mm")
    if S.dish:
        d = S.dish
        st.markdown(f"**Parabola:** {'offset' if d.kind == 'offset' else 'prime focus'} · D {d.D_mm:.0f} mm · "
                    f"f/D{' eq.' if d.kind == 'offset' else ''} {d.fD:.3f} · apertura {d.opening_deg:.1f}°")
    st.markdown(f"**Feed:** {geometry.FEED_TYPES[S.feed_kind]}")
    mats = list(materials.MATERIALS)
    S.material = st.selectbox("Materiale del feed", mats, index=mats.index(S.get("material", "Ottone CuZn39Pb3")),
                              help="conducibilità e rugosità → perdite ohmiche e rumore del feed")
    m_ = materials.MATERIALS[S.material]
    st.caption(f"σ = {m_.sigma / 1e7:.2f}·10⁷ S/m · δ = {materials.skin_depth_um(m_.sigma, S.f_ghz):.3f} µm · {m_.notes}")
    col_on = st.checkbox("Collare Ø40 mm per portaLNB commerciale", bool(geometry.COLLAR.get("diam")))
    geometry.COLLAR["diam"] = st.number_input("Ø collare (mm)", 20.0, 80.0, 40.0, 1.0) if col_on else None
    geometry.MOUNT.update(S.get("mount_cfg") or {"wg": None})
    st.divider()
    if os.environ.get("FEEDLAB_DESKTOP") == "browser":
        if st.button("⏻ Chiudi FeedLab", help="ferma il programma (le simulazioni openEMS in corso continuano)"):
            st.write("FeedLab chiuso: puoi chiudere questa scheda del browser.")
            os._exit(0)
    st.caption(f"Versione {feedlab.__version__} · © Ivan De Cesaris IZ0JNY")
    if st.button("ℹ️ Credits", key="credits_btn", help="Autore, versione e tutte le fonti"):
        _credits_dialog()
    _man = Path(feedlab.__file__).resolve().parent.parent / "docs" / "manual" / (
        "FeedLab_Manuale_IT.pdf" if i18n.get_lang() == "it" else "FeedLab_User_Manual_EN.pdf")
    if _man.exists():
        st.download_button("📖 Manuale", _man.read_bytes(), file_name=_man.name, mime="application/pdf",
                           help="manuale d'uso in PDF (italiano o inglese secondo la lingua scelta)")
    st.link_button("🐞 Segnala un problema", _credits_mod.issue_url(S.get("feed_kind", ""), S.get("f_ghz")),
                   help="apre la pagina GitHub delle segnalazioni (issue) con versione e progetto già compilati")
    st.caption("openEMS (opzionale): " + ("✅ pronto" if (S.get("oems_env") or {}).get("py") else
                                         "vedi scheda Full-wave openEMS"))

tabs = st.tabs(["🧭 Procedura guidata", "📐 Progetto feed", "🎛️ Laboratorio", "📈 Simulazione & S11", "🌐 Lobo 3D",
                "🧊 Modello 3D", "📄 Disegno & STEP", "🔌 Piastrina WR", "🖥️ Full-wave openEMS", "ℹ️ Credits"])

# ---------------------------------------------------------------- 1 wizard
with tabs[0]:
    st.header("Scegli il feed migliore per la tua parabola")
    c1, c2, c3 = st.columns(3)
    with c1:
        src = st.radio("Parabola", ["Catalogo commerciale (datasheet)", "Parabola custom"], horizontal=True)
        dish = None
        if src.startswith("Catalogo"):
            cat = dishes.by_label()
            makers = sorted({d.maker for d in dishes.CATALOG})
            mk = st.selectbox("Costruttore", makers, index=makers.index("Gibertini"))
            labs = [l for l, d in cat.items() if d.maker == mk]
            dm = cat[st.selectbox("Modello", labs)]
            f_cat, f_src = dm.focal()
            st.caption(f"Fonte: {dm.source}" + (f" — {dm.notes}" if dm.notes else ""))
            info = {"Tipo": dm.kind, "Dimensioni esterne (mm)": f"{dm.width_mm:.0f} × {dm.height_mm:.0f}",
                    "Area attiva (mm)": f"{dm.active_w_mm:.0f} × {dm.active_h_mm:.0f}" if dm.active_w_mm and dm.active_h_mm else "—",
                    "F/D costruttore": dm.fD_maker or "—", "Focale (mm)": f"{f_cat:.0f} ({f_src})" if f_cat else f_src,
                    "Angolo offset": f"{dm.offset_deg}°" if dm.offset_deg else "—",
                    "Illuminazione richiesta": f"{dm.illum_deg}°" if dm.illum_deg else "—",
                    "Efficienza dichiarata": f"{dm.efficiency_pct}%" if dm.efficiency_pct else "—",
                    "Guadagni": ", ".join(f"{g} dBi @{f:g} GHz" for f, g in dm.gain.items()) or "—",
                    "Collare LNB": dm.collar_mm or "—", "Materiale": dm.material or "—"}
            st.table({"Dato": list(info), "Valore": [str(v) for v in info.values()]})
            if dm.opening_deg() is None or st.checkbox("Ho misurato la mia parabola (più preciso del datasheet)"):
                st.info("Misura: assi del bordo e profondità massima (righello teso sul bordo lungo l'asse lungo).")
                la = st.number_input("Asse lungo (mm)", 100.0, 5000.0, float(dm.height_mm))
                sa = st.number_input("Asse corto (mm)", 100.0, 5000.0, float(dm.width_mm))
                dp = st.number_input("Profondità massima (mm)", 1.0, 1000.0, float(round(sa * sa / (16 * (f_cat or 0.6 * sa)) * sa / la, 1)))
                dish = wizard.dish_from_offset_tv(la, sa, dp) if dm.kind == "offset" else wizard.dish_from_prime(sa, depth=dp)
            else:
                dish = wizard.dish_from_catalog(dm)
        else:
            dk = st.radio("Tipo di parabola", ["Offset (TV/sat)", "Prime focus"], horizontal=True)
            if dk.startswith("Offset"):
                mode = st.radio("Dati disponibili", ["Diametro + f/D (come nei datasheet)", "Misure del riflettore (assi + profondità)",
                                                     "Diametro + focale", "Diametro + angolo di illuminazione"])
                if mode.startswith("Diametro + f/D"):
                    D = st.number_input("Diametro / larghezza (mm)", 100.0, 10000.0, 800.0)
                    fdo = st.number_input("f/D offset (f / larghezza)", 0.3, 2.0, 0.66, 0.01,
                                          help="convenzione dei costruttori di parabole TV (es. Gibertini 0.66, Triax 0.6)")
                    dish = wizard.dish_from_offset_fD(D, fdo * D, 0.0)
                elif mode.endswith("illuminazione"):
                    D = st.number_input("Diametro proiettato (mm)", 100.0, 10000.0, 800.0)
                    ang = st.number_input("Angolo di illuminazione richiesto (° totali)", 20.0, 170.0, 70.0, 0.5)
                    dish = wizard.Dish("offset", D, reflector.fD_from_half_angle(ang / 2), None,
                                       note="parabola custom definita dall'angolo di illuminazione")
                elif mode.startswith("Misure"):
                    la = st.number_input("Asse lungo (mm)", 100.0, 5000.0, 676.0)
                    sa = st.number_input("Asse corto (mm)", 100.0, 5000.0, 630.0)
                    dp = st.number_input("Profondità massima (mm)", 1.0, 1000.0, 52.0)
                    dish = wizard.dish_from_offset_tv(la, sa, dp)
                else:
                    D = st.number_input("Diametro proiettato (mm)", 100.0, 5000.0, 600.0)
                    f = st.number_input("Focale del paraboloide madre (mm)", 50.0, 5000.0, 390.0)
                    h = st.number_input("Distanza asse → bordo inferiore (mm)", 0.0, 2000.0, 0.0)
                    dish = wizard.dish_from_offset_fD(D, f, h)
            else:
                D = st.number_input("Diametro (mm)", 100.0, 20000.0, 1200.0)
                mode = st.radio("Conosco", ["f/D", "Profondità al centro"], horizontal=True)
                if mode == "f/D":
                    fD = st.number_input("f/D", 0.2, 2.0, 0.38, 0.01)
                    dish = wizard.dish_from_prime(D, fD)
                else:
                    dp = st.number_input("Profondità (mm)", 1.0, 5000.0, 197.0)
                    dish = wizard.dish_from_prime(D, depth=dp)
    with c2:
        pol = st.radio("Polarizzazione", ["Lineare", "Circolare"], horizontal=True)
        prio = st.radio("Obiettivo", ["Massimo guadagno (TX/terrestre)", "Massimo G/T (RX, EME, sole)"])
        tools = st.radio("Mezzi di costruzione", ["Tornio / CNC", "Solo lamiera e saldatura"])
        quick = st.checkbox("Stima con simulazione rapida (mode matching, ~20 s)", True)
    with c3:
        st.subheader("Parabola")
        st.write(f"f/D {'equivalente vista dal feed' if dish.kind == 'offset' else ''}: **{dish.fD:.3f}**")
        st.write(f"Angolo di apertura (centro→bordo ×2): **{dish.opening_deg:.1f}°**")
        lam = wavelength_mm(S.f_ghz)
        st.write(f"Diametro: **{dish.D_mm / lam:.0f} λ** — HPBW ≈ **{reflector.hpbw_deg(dish.D_mm, lam, 10):.2f}°** "
                 f"(taper al bordo 10 dB; {reflector.hpbw_deg(dish.D_mm, lam, 0):.2f}° con illuminazione uniforme)")
        st.caption("L'HPBW reale dipende dall'illuminazione del feed: dopo la scelta del feed è calcolato dal suo lobo "
                   "nella scheda Simulazione & S11.")
        st.write(f"Guadagno a 60%: **{reflector.gain_dbi(dish.D_mm, lam, 0.6):.1f} dBi**")
        rms = st.number_input("Precisione superficie RMS (mm)", 0.0, 5.0, 0.2, 0.01)
        st.write(f"Perdita Ruze: **{reflector.ruze_loss_db(rms, lam):.2f} dB**")
        if dish.note:
            st.info(dish.note)
    if st.button("🔎 Trova il feed migliore", type="primary"):
        S.dish = dish
        with st.spinner("Valuto i candidati…"):
            S.cands = wizard.recommend(dish, S.f_ghz, "circular" if pol == "Circolare" else "linear",
                                       "gt" if "G/T" in prio else "gain", "sheet" if "lamiera" in tools else "lathe", quick)
    if S.cands:
        rows = []
        for i, c in enumerate(S.cands):
            rows.append({"#": i + 1, "Feed": c.label, "η stimata %": round(100 * c.eta_est, 1) if c.eta_est else None,
                         "f/D ottimo del feed": round(c.best_fD, 2) if c.best_fD else None,
                         "Ingombro Ø mm": round(c.blockage_diam_mm, 1) if c.blockage_diam_mm else "— (offset)",
                         "Perché": "; ".join(c.reasons), "Attenzione": "; ".join(c.warnings)})
        st.dataframe(rows, width="stretch", hide_index=True)
        st.caption("η = illuminazione × spillover × fase × cross-pol × blocking, calcolata (modello d'apertura o "
                   "design guide). Su parabole reali aspettarsi 12–15 punti in meno (W1GHZ, WD5AGO).")
        pick = st.selectbox("Feed da progettare", [c.label for c in S.cands])
        if st.button("➡️ Usa questo feed"):
            S.feed_kind = next(c.kind for c in S.cands if c.label == pick)
            S.overrides = {}
            st.success("Feed selezionato: apri la scheda 'Progetto feed'.")

# ---------------------------------------------------------------- 2 design
with tabs[1]:
    st.header("Progetto del feed")
    kinds = list(geometry.FEED_TYPES)
    S.feed_kind = st.selectbox("Tipo di feed", kinds, index=kinds.index(S.feed_kind),
                               format_func=lambda k: geometry.FEED_TYPES[k])
    geo = current_geometry()
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Quote (modificabili)")
        S.wall = st.number_input("Spessore parete (mm)", 0.2, 10.0, float(geo.params.get("wall", 1.0)), 0.05)
        editable = {k: v for k, v in geo.params.items() if isinstance(v, (int, float)) and k not in ("wall", "rings", "flange_diam", "flange_thickness")}
        newv = {}
        map_keys = {"A_input": "A", "B_aperture": "B", "flare_half_deg": "alpha", "C_phasing": "C",
                    "Di_input": "Di", "Ds_step": "Ds", "D_aperture": "Dap" if S.feed_kind in ("skobelev", "pickett_potter") else "D",
                    "d_input": "d_in", "diam": "diam", "length": "length", "input_length": "input_length",
                    "flare_length": "flare_length", "horn_diam": "horn_diam", "ring_width": "ring_width",
                    "ring_depth": "ring_depth", "ring_setback": "ring_setback", "ring_wall": "ring_wall",
                    "aperture_H": "aperture_H", "aperture_E": "aperture_E", "axial_length": "axial_length"}
        for k, v in editable.items():
            if k not in map_keys:
                continue
            if S.feed_kind in ("w2imu", "w2imu_oe2igl", "large_w2imu") and k == "flare_length":
                st.text(f"flare_length (calcolata) {v:.3f}")
                continue
            if S.feed_kind == "conical" and k == "flare_length":
                continue
            lab = f"{k} ({'°' if k.endswith('_deg') else 'mm'})"
            nv = st.number_input(lab, value=float(round(v, 4)), format="%.4f", key=f"in_{S.feed_kind}_{k}")
            if abs(nv - v) > 1e-6:
                newv[map_keys[k]] = nv
        cc1, cc2 = st.columns(2)
        if cc1.button("Applica modifiche"):
            ov = S.overrides.setdefault(S.feed_kind, {})
            # flare: angle and length are the same quantity seen two ways -> the one just edited wins
            if "alpha" in newv and "flare_length" in newv:
                newv.pop("flare_length")
            if "alpha" in newv:
                ov.pop("flare_length", None)
            if "flare_length" in newv:
                ov.pop("alpha", None)
            ov.update(newv)
            st.rerun()
        if cc2.button("Ripristina progetto"):
            S.overrides[S.feed_kind] = {}
            st.rerun()
    with c2:
        fig = section_fig(geo)
        if fig:
            st.plotly_chart(fig, width="stretch")
        lam = geo.lam
        st.write(f"Lunghezza totale **{geo.length:.2f} mm** ({geo.length / lam:.2f} λ) · "
                 f"Ø ingombro **{geo.blockage_diameter():.2f} mm** ({geo.blockage_diameter() / lam:.2f} λ) · "
                 f"tolleranza consigliata **±{drawing.tolerance_mm(S.f_ghz)} mm**")
        for n in getattr(geo, "notes", []) or []:
            st.caption("• " + n)
        if getattr(geo, "design", None) is not None:
            with st.expander("Dati della regola di progetto"):
                st.text(str(geo.design))

# ---------------------------------------------------------------- 3 simulation
with tabs[3]:
    st.header("Simulazione rapida: S11, contenuto modale, lobo, efficienza")
    geo = current_geometry()
    is_rect = isinstance(geo, geometry.RectHornGeometry)
    if not is_rect and geo.kind not in geometry.MODEMATCH_OK:
        st.warning("Per i feed con anelli/choke la simulazione rapida non è disponibile (regioni coassiali): "
                   "usa la scheda **Full-wave openEMS**. Sotto: efficienza attesa dalle simulazioni W1GHZ/WD5AGO.")
        st.text(str(geo.design))
    else:
        c1, c2, c3 = st.columns(3)
        bw = c1.slider("Banda di analisi ± %", 1, 20, 6)
        npts = c2.slider("Punti in frequenza", 5, 41, 15)
        nm = c3.select_slider("Modi (precisione)", [8, 12, 16, 24], 16)
        if not is_rect:
            secs = tuple(geo.staircase())
            fl = tuple(np.linspace(S.f_ghz * (1 - bw / 100), S.f_ghz * (1 + bw / 100), npts))
            with st.spinner("Mode matching…"):
                t0 = time.time()
                mm = run_modematch(secs, fl, nm)
            fig = go.Figure(go.Scatter(x=mm.f_ghz, y=mm.s11_db, mode="lines+markers", name="S11"))
            fig.add_vline(x=S.f_ghz, line_dash="dot")
            fig.update_layout(title="S11 ingresso TE11 (stima mode-matching)", xaxis_title="GHz", yaxis_title="dB",
                              height=330, yaxis_range=[min(-40, float(mm.s11_db.min()) - 3), 0])
            st.plotly_chart(fig, width="stretch")
            i0 = int(np.argmin(np.abs(mm.f_ghz - S.f_ghz)))
            st.caption(f"S11 a {S.f_ghz:g} GHz: **{mm.s11_db[i0]:.1f} dB** (RL {-mm.s11_db[i0]:.1f} dB) · "
                       f"bilancio di potenza {mm.power_balance[i0]:.4f} · {time.time() - t0:.1f} s. "
                       "Apertura modellata come flangia (stima ottimistica per aperture < 1λ); "
                       "transizione dalla guida WR esclusa. Per S11 di riferimento usa openEMS.")
            modes = mm.aperture_modes[i0]
            if "TE11" in modes:
                te = modes["TE11"]
                st.write("Contenuto modale all'apertura (rispetto a TE11): " + ", ".join(
                    f"{k}: {abs(v / te):.3f} ∠{math.degrees(np.angle(v / te)):.0f}°" for k, v in modes.items()))
                q_ = explore.tm11_power_ratio(modes)
                if geo.kind in explore.STEP_HORNS and q_ is not None:
                    st.caption(f"TM11/TE11 in potenza: {100 * q_:.1f}% — Pawlan WA6KBL indica ~15% per un Pickett-Potter "
                               f"({'nella norma' if explore.TM11_TARGET[0] <= q_ <= explore.TM11_TARGET[1] else 'da correggere'}).")
        pat, _ = quick_pattern(geo.kind, tuple(geo.staircase()) if not is_rect else (), S.f_ghz,
                               (geo.params["a"], geo.params["b"], geo.params["aperture_H"], geo.params["aperture_E"],
                                geo.params["axial_length"]) if is_rect else None)
        if S.fullwave is not None and st.checkbox("Usa il pattern full-wave openEMS caricato", True):
            pat = S.fullwave["pattern"]
        S["last_pattern"] = pat
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(polar_fig(pat, f"Lobo del feed @ {S.f_ghz:g} GHz"), width="stretch")
        with c2:
            e, h = pat.db()
            fig = go.Figure([go.Scatter(x=pat.theta_deg, y=e, name="E"), go.Scatter(x=pat.theta_deg, y=h, name="H")])
            ph_e = np.degrees(np.unwrap(np.angle(pat.E)) - np.angle(pat.E[0]))
            fig.add_trace(go.Scatter(x=pat.theta_deg, y=ph_e, name="fase E (°)", yaxis="y2", line=dict(dash="dot")))
            fig.update_layout(height=460, xaxis_title="θ (°)", yaxis_title="dB", yaxis_range=[-40, 1], xaxis_range=[0, 180],
                              yaxis2=dict(overlaying="y", side="right", title="fase °"), title="Pattern cartesiano")
            st.plotly_chart(fig, width="stretch")
        dish = S.dish or wizard.dish_from_prime(600, 0.6)
        blk = geo.blockage_diameter() / dish.D_mm if dish.kind == "prime" else 0.0
        fds = np.arange(0.25, 1.6, 0.01)
        effs = efficiency.efficiency_vs_fD(pat, fds, blk)
        fig = go.Figure()
        for key, name in (("total", "Totale"), ("spillover", "Spillover"), ("illumination", "Illuminazione"),
                          ("phase", "Fase"), ("polarization", "Cross-pol")):
            fig.add_trace(go.Scatter(x=fds, y=[100 * getattr(x, key) for x in effs], name=name,
                                     line=dict(width=3 if key == "total" else 1.5)))
        fig.add_vline(x=dish.fD, line_dash="dot", annotation_text="tua parabola")
        fig.update_layout(height=400, title="Efficienza della parabola vs f/D (prime focus o equivalente offset)",
                          xaxis_title="f/D", yaxis_title="%", yaxis_range=[0, 101])
        st.plotly_chart(fig, width="stretch")
        here = efficiency.dish_efficiency(pat, dish.fD, blk)
        best = max(effs, key=lambda x: x.total)
        pc, _ = efficiency.phase_center_by_efficiency(pat, dish.fD, span_lambda=1.5, step=0.01, block_diam_ratio=blk)
        lam = wavelength_mm(S.f_ghz)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("η sulla tua parabola", f"{100 * here.total:.1f} %")
        m2.metric("Taper al bordo", f"{here.edge_taper_db:.1f} dB")
        m3.metric("f/D ottimo del feed", f"{best.fD:.2f}", f"{100 * best.total:.1f} %")
        m4.metric("Centro di fase", f"{pc * lam:+.2f} mm", "davanti all'apertura" if pc > 0 else "dentro l'horn")
        beam = efficiency.dish_beam(pat.shifted(pc), dish.fD, dish.D_mm, lam, blk)
        b1, b2, b3 = st.columns(3)
        b1.metric("HPBW della parabola", f"{beam.hpbw_deg:.3f}°",
                  help="dal lobo reale del feed (integrazione sull'apertura, feed nel centro di fase)")
        b2.metric("HPBW piano E / H", f"{beam.hpbw_E_deg:.3f}° / {beam.hpbw_H_deg:.3f}°")
        b3.metric("Primo lobo laterale", f"{beam.first_sidelobe_db:.1f} dB",
                  f"taper al bordo {beam.edge_taper_db:.1f} dB", delta_color="off")
        G = reflector.gain_dbi(dish.D_mm, lam, max(here.total, 1e-3))
        st.write(f"Guadagno teorico con questo feed: **{G:.1f} dBi** (reale ≈ {reflector.gain_dbi(dish.D_mm, lam, max(here.total - 0.13, 0.01)):.1f} dBi, −13 punti)")
        with st.expander("G/T (prime focus, modello W1GHZ 2014)"):
            el = st.slider("Elevazione (°)", 5, 90, 30)
            nf = st.number_input("NF ricevitore (dB)", 0.2, 15.0, 1.0)
            azen = st.number_input("Attenuazione zenitale atmosfera (dB)", 0.0, 5.0, 0.3 if S.f_ghz < 60 else 1.0)
            tsky = noise.sky_temp(el, azen, f_ghz=S.f_ghz)
            ta = noise.antenna_temp_prime_focus(pat, dish.fD, el, tsky)
            st.write(f"T_cielo {tsky:.1f} K · T_antenna {ta:.1f} K · T_rx {noise.receiver_temp(nf):.0f} K → "
                     f"**G/T = {noise.g_over_t_db(G, ta, noise.receiver_temp(nf)):.1f} dB/K**")

# ---------------------------------------------------------------- 4 lobe 3D
with tabs[4]:
    st.header("Lobo di irradiazione 3D")
    pat = S.get("last_pattern")
    if pat is None:
        st.info("Esegui prima la simulazione nella scheda 'Simulazione & S11'.")
    else:
        floor = st.slider("Dinamica (dB)", -60, -15, -35)
        st.plotly_chart(lobe3d_fig(pat, floor), width="stretch")

# ---------------------------------------------------------------- 5 model 3D
with tabs[5]:
    st.header("Modello 3D del feed")
    geo = current_geometry()
    cut = st.checkbox("Sezione a quarto (vedi l'interno)", True)
    st.plotly_chart(model3d_fig(geo, cut), width="stretch")

# ---------------------------------------------------------------- 6 export
with tabs[6]:
    st.header("Disegno meccanico (PDF) e file per la produzione")
    geo = current_geometry()
    mat = st.text_input("Materiale", f"{S.material}, interno lucidato Ra ≤ {materials.MATERIALS[S.material].rq_um} µm")
    name = st.text_input("Titolo", f"{geometry.FEED_TYPES[geo.kind]} {S.f_ghz:g} GHz")
    base = WORK / f"{geo.kind}_{S.f_ghz:g}GHz".replace(".", "p")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("📄 Genera PDF"):
        tt = S.get("tol_table")
        pth = drawing.drawing_pdf(geo, base.with_suffix(".pdf"), mat, name,
                                  tolerances=tt[1] if tt and tt[0] == geo.kind else None)
        S["pdf"] = pth.read_bytes()
    if S.get("pdf"):
        c1.download_button("Scarica disegno PDF", S["pdf"], file_name=base.name + ".pdf", mime="application/pdf")
    if c2.button("🧊 Genera STEP"):
        with st.spinner("OpenCascade…"):
            S["step"] = cad.export_step(geo, base.with_suffix(".step")).read_bytes()
    if S.get("step"):
        c2.download_button("Scarica .stp", S["step"], file_name=base.name + ".stp")
    if c3.button("🖨️ Genera STL"):
        S["stl"] = cad.export_stl(geo, base.with_suffix(".stl")).read_bytes()
    if S.get("stl"):
        c3.download_button("Scarica .stl", S["stl"], file_name=base.name + ".stl")
    rep = {"feed": geo.kind, "f_ghz": S.f_ghz, "params_mm": geo.params,
           "dish": None if S.dish is None else S.dish.__dict__}
    c4.download_button("🧾 Parametri JSON", json.dumps(rep, indent=2, default=float), file_name=base.name + ".json")
    if S.get("pdf"):
        import base64
        b64 = base64.b64encode(S["pdf"]).decode()
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="620"></iframe>',
                    unsafe_allow_html=True)

# ---------------------------------------------------------------- 7 openEMS (optional deep analysis)
with tabs[8]:
    app_openems.render(S, current_geometry(), polar_fig)


# ---------------------------------------------------------------- 3 laboratory
@st.cache_data(show_spinner=False, max_entries=500)
def lab_eval(kind, f, sc_tuple, over_tuple, wall):
    sc = explore.Scenario(*sc_tuple)
    return explore.evaluate(kind, f, sc, dict(over_tuple), wall)


with tabs[2]:
    st.header("Laboratorio: varia le quote e guarda cosa cambia")
    kind = S.feed_kind
    if kind not in explore.TUNABLE:
        st.warning("Il laboratorio interattivo usa il simulatore rapido: disponibile per guida aperta, W2IMU, "
                   "Large W2IMU, Skobelev, Pickett-Potter, conico e horn rettangolare. Per VE4MA/Chaparral usa openEMS.")
    else:
        dish = S.dish or wizard.dish_from_prime(600, 0.6)
        lam = wavelength_mm(S.f_ghz)
        with st.expander("Scenario d'uso (parabola, ricevitore, cielo)", expanded=True):
            c = st.columns(6)
            objective = c[0].selectbox("Obiettivo", list(explore.OBJECTIVES), format_func=lambda k: explore.OBJECTIVES[k],
                                       index=1)
            elev = c[1].slider("Elevazione °", 0, 90, 30 if objective != "tx" else 5)
            nf = c[2].number_input("NF LNA (dB)", 0.1, 20.0, 1.0 if S.f_ghz < 30 else 3.0 if S.f_ghz < 80 else 8.0, 0.1)
            line = c[3].number_input("Perdita linea feed→LNA/PA (dB)", 0.0, 10.0, 0.1, 0.05)
            rms = c[4].number_input("RMS superficie (mm)", 0.0, 3.0, 0.1, 0.01)
            azen = c[5].number_input("Att. zenitale (dB)", 0.0, 10.0, 0.1 if S.f_ghz < 20 else 0.3 if S.f_ghz < 60 else 1.0, 0.05)
        sc = explore.Scenario(dish.kind, dish.D_mm, dish.fD, max(elev, 1), noise.receiver_temp(nf), azen, 290.0, rms, line,
                              material=S.material)
        sc_t = tuple(sc.__dict__.values())
        base_vals = explore.base_values(kind, S.f_ghz, dish.fD, S.wall)
        cur_over = dict(S.overrides.get(kind, {}))
        start = {**base_vals, **cur_over}
        st.subheader("Quote del feed")
        cols = st.columns(len(explore.TUNABLE[kind]))
        lab_over = {}
        for col, (key, label, span) in zip(cols, explore.TUNABLE[kind]):
            x0 = base_vals[key]
            unit = "°" if key == "alpha" else "mm"
            v = col.slider(f"{label} ({unit})", float(x0 * (1 - span)), float(x0 * (1 + span)),
                           float(np.clip(start[key], x0 * (1 - span), x0 * (1 + span))), float(x0 * span / 50),
                           format="%.3f", key=f"lab_{kind}_{key}",
                           help=f"progetto: {x0:.3f} {unit} = {x0 / lam:.3f} λ" if unit == "mm" else f"progetto: {x0:.2f}°")
            col.caption(f"{v / lam:.3f} λ · {100 * (v / x0 - 1):+.1f}%" if unit == "mm" else f"{100 * (v / x0 - 1):+.1f}%")
            if abs(v - x0) > 1e-9:
                lab_over[key] = v
        if any(k == "alpha" for k, _, _ in explore.TUNABLE[kind]):
            g_lab = geometry.build(kind, S.f_ghz, fD=dish.fD, wall=S.wall, **lab_over)
            p_lab = g_lab.params
            st.caption(f"Flare: semiangolo {p_lab['flare_half_deg']:.2f}° → lunghezza flare {p_lab['flare_length']:.3f} mm "
                       f"({p_lab['flare_length'] / lam:.3f} λ), lunghezza totale {g_lab.z_aperture:.2f} mm")
        with st.spinner("Calcolo…"):
            base = lab_eval(kind, S.f_ghz, sc_t, tuple(sorted({}.items())), S.wall)
            cur = lab_eval(kind, S.f_ghz, sc_t, tuple(sorted(lab_over.items())), S.wall)
        st.subheader("Risultato rispetto al progetto di partenza")
        m = st.columns(7)
        def met(col, lab, v, b, fmt, unit, better_up=True):
            d = v - b
            col.metric(lab, f"{fmt.format(v)} {unit}", None if abs(d) < 1e-9 else f"{d:+.2f}",
                       delta_color="normal" if better_up else "inverse")
        snr = cur.snr_delta(base, objective)
        st.caption(f"Perdita ohmica del feed ({S.material}): {cur.ohmic_db:.3f} dB → +{materials.noise_from_loss(cur.ohmic_db):.1f} K di rumore")
        m[0].metric("Δ S/N", f"{snr:+.2f} dB", help="TX: ΔG · RX: Δ(G/T) · EME: ΔG+Δ(G/T)")
        met(m[1], "Efficienza", 100 * cur.eta, 100 * base.eta, "{:.1f}", "%")
        met(m[2], "Guadagno", cur.gain_dbi, base.gain_dbi, "{:.2f}", "dBi")
        met(m[3], "G/T", cur.g_over_t, base.g_over_t, "{:.2f}", "dB/K")
        met(m[4], "T antenna", cur.t_ant, base.t_ant, "{:.1f}", "K", better_up=False)
        if cur.s11_db is not None:
            met(m[5], "S11", cur.s11_db, base.s11_db, "{:.1f}", "dB", better_up=False)
        met(m[6], "Taper bordo", cur.edge_taper_db, base.edge_taper_db, "{:.1f}", "dB")
        st.caption(f"Spillover {100 * cur.spill:.1f}% · illuminazione {100 * cur.illum:.1f}% · fase {100 * cur.phase:.1f}% · "
                   f"pol {100 * cur.pol:.1f}% · blocking {100 * cur.block:.1f}% · centro di fase {cur.pc_mm:+.2f} mm "
                   f"({'davanti' if cur.pc_mm > 0 else 'dentro'} all'apertura). Valori calcolati: sulla parabola reale "
                   "aspettarsi 12–15 punti di efficienza in meno, ma le DIFFERENZE tra varianti sono significative.")
        c1, c2 = st.columns(2)
        with c1:
            fig = polar_fig(cur.pattern, "Lobo: variante (pieno) vs progetto (tratteggio)")
            eb, hb = base.pattern.db()
            for v, col in ((eb, "#d62728"), (hb, "#1f77b4")):
                th = np.concatenate([-base.pattern.theta_deg[::-1], base.pattern.theta_deg])
                fig.add_trace(go.Scatterpolar(theta=th, r=np.clip(np.concatenate([v[::-1], v]), -40, 0) + 40,
                                              mode="lines", line=dict(color=col, dash="dash", width=1), showlegend=False))
            psi = reflector.half_angle_from_fD(dish.fD)
            fig.add_trace(go.Scatterpolar(theta=[psi, psi, None, -psi, -psi], r=[0, 40, None, 0, 40], mode="lines",
                                          line=dict(color="green", dash="dot"), name="bordo parabola"))
            st.plotly_chart(fig, width="stretch")
        with c2:
            fds = np.arange(0.3, 1.4, 0.02)
            blk = 0.0
            fig = go.Figure()
            for res, name, dash in ((base, "progetto", "dash"), (cur, "variante", "solid")):
                ef = efficiency.efficiency_vs_fD(res.pattern, fds, blk)
                fig.add_trace(go.Scatter(x=fds, y=[100 * e.total for e in ef], name=f"η {name}", line=dict(dash=dash, width=3)))
                fig.add_trace(go.Scatter(x=fds, y=[100 * e.spillover for e in ef], name=f"spillover {name}",
                                         line=dict(dash=dash, width=1)))
            fig.add_vline(x=dish.fD, line_dash="dot", annotation_text="tua parabola")
            fig.update_layout(height=460, title="Efficienza vs f/D", xaxis_title="f/D", yaxis_title="%", yaxis_range=[30, 101])
            st.plotly_chart(fig, width="stretch")
        st.subheader("💡 Consigli")
        for t in explore.advice(cur, base, sc, objective, kind, S.f_ghz):
            st.markdown("- " + t)
        b1, b2, b3 = st.columns(3)
        if b1.button("✅ Applica queste quote al progetto", type="primary"):
            S.overrides[kind] = {**lab_over}
            st.success("Quote applicate: disegno, STEP e openEMS useranno la variante.")
        st.divider()
        st.subheader("🔬 Sensibilità: cosa succede variando ogni quota")
        if st.button("Calcola sensibilità (≈ 7 punti per quota)"):
            with st.spinner("Scansione…"):
                S["sens"] = (objective, explore.sensitivity(kind, S.f_ghz, sc, lab_over, objective, 7, S.wall))
        if S.get("sens") and S["sens"][0] == objective:
            sens = S["sens"][1]
            cols = st.columns(len(sens))
            for col, (key, d) in zip(cols, sens.items()):
                R = d["rows"]
                fig = go.Figure()
                ylab = {"tx": "G (dBi)", "rx": "G/T (dB/K)", "eme": "G + G/T"}[objective]
                fig.add_trace(go.Scatter(x=R[:, 0], y=R[:, 1] - np.nanmax(R[:, 1]), name=ylab, mode="lines+markers"))
                if not np.all(np.isnan(R[:, 5])):
                    fig.add_trace(go.Scatter(x=R[:, 0], y=R[:, 5], name="S11 dB", yaxis="y2", line=dict(dash="dot")))
                fig.add_vline(x=d["x0"], line_dash="dot")
                fig.update_layout(height=300, title=d["label"], xaxis_title="mm" if key != "alpha" else "°",
                                  yaxis_title="dB dal max", yaxis2=dict(overlaying="y", side="right", title="S11"),
                                  showlegend=False, margin=dict(t=40, b=30))
                col.plotly_chart(fig, width="stretch")
                ib = int(np.nanargmax(R[:, 1]))
                gain = R[ib, 1] - R[len(R) // 2, 1]
                col.caption(f"Migliore a {R[ib, 0]:.3f} ({100 * (R[ib, 0] / d['x0'] - 1):+.0f}%): {gain:+.2f} dB. "
                            f"Pendenza ≈ {np.nanmax(np.abs(np.diff(R[:, 1]) / np.diff(R[:, 0]))):.2f} dB/{'mm' if key != 'alpha' else '°'} "
                            f"→ tolleranza utile.")
        st.divider()
        st.subheader("🤖 Ottimizzazione automatica")
        keys = st.multiselect("Quote da ottimizzare", [k for k, _, _ in explore.TUNABLE[kind]],
                              default=[k for k, _, _ in explore.TUNABLE[kind]][:2],
                              format_func=lambda k: dict((a, b) for a, b, _ in explore.TUNABLE[kind])[k])
        c1, c2 = st.columns(2)
        nev = c1.slider("Valutazioni massime", 10, 120, 40)
        s11lim = c2.slider("S11 massimo accettato (dB)", -30, -10, -18)
        if st.button(f"Ottimizza per: {explore.OBJECTIVES[objective]}") and keys:
            bar = st.progress(0.0, "ottimizzazione…")
            over, res = explore.optimize(kind, S.f_ghz, sc, lab_over, objective, keys, nev, S.wall,
                                         s11_limit_db=s11lim,
                                         progress=lambda i, n, v: bar.progress(min(i / n, 1.0), f"valutazione {i}/{n}"))
            S["opt"] = (over, res)
        if S.get("opt"):
            over, res = S["opt"]
            st.success(f"Ottimo trovato: Δ S/N {res.snr_delta(base, objective):+.2f} dB · η {100 * res.eta:.1f}% · "
                       f"G {res.gain_dbi:.2f} dBi · G/T {res.g_over_t:.2f} dB/K · S11 {res.s11_db if res.s11_db is None else round(res.s11_db, 1)} dB")
            st.write({k: f"{v:.3f} ({100 * (v / base_vals[k] - 1):+.1f}%)" for k, v in over.items()})
            if st.button("Applica l'ottimo al progetto"):
                S.overrides[kind] = {**over}
                for k, v in over.items():
                    S[f"lab_{kind}_{k}"] = float(v)
                st.rerun()

        # ------------------------------------------------ fabrication tolerances
        st.divider()
        st.subheader("🎯 Tolleranze di lavorazione e resa")
        if kind not in tolerance.TOL_KEYS:
            st.info("L'analisi di tolleranza usa il simulatore rapido a guida circolare: non disponibile per l'horn rettangolare.")
        else:
            st.caption("Ogni quota lavorata varia dentro la sua tolleranza: FeedLab stima come si distribuiscono efficienza, "
                       "guadagno, G/T e S11 dei pezzi prodotti (Monte Carlo), quali quote sono critiche e quale tolleranza "
                       "serve davvero a ciascuna. Si analizza il progetto con le quote attuali del laboratorio.")
            c = st.columns(4)
            tol_in = c[0].number_input("Tolleranza di lavorazione ± (mm)", 0.001, 0.5, float(drawing.tolerance_mm(S.f_ghz)),
                                       0.005, format="%.3f", key="tol_mm")
            dist = c[1].selectbox("Distribuzione delle quote", ["uniform", "normal"], key="tol_dist",
                                  format_func=lambda d: {"uniform": "Uniforme in ±t (prudente)",
                                                         "normal": "Normale, ±t = 3σ (CNC capace)"}[d])
            budget = c[2].number_input("Perdita ammessa (dB)", 0.01, 1.0, 0.1, 0.01, key="tol_budget",
                                       help="un pezzo è 'buono' se perde al massimo questo rispetto al nominale")
            s11t = c[3].slider("S11 massimo (dB)", -30, -10, -18, key="tol_s11")
            if st.button("🎲 Analizza tolleranze (≈ 20 simulazioni rapide)", key="tol_go"):
                bar = st.progress(0.0, "modello delle tolleranze…")
                rep = tolerance.analyse(kind, S.f_ghz, sc, lab_over, objective, tol_in, dist, 5000, 6, budget, s11t, S.wall,
                                        progress=lambda i, n: bar.progress(min(i / n, 1.0), f"simulazione {i}/{n}"))
                bar.empty()
                S["tol"] = (kind, objective, rep)
            if S.get("tol") and S["tol"][0] == kind:
                rep = S["tol"][2]
                ylab = {"tx": "G", "rx": "G/T", "eme": "G + G/T"}[S["tol"][1]]
                so, se, ss = rep.stats["objective"], rep.stats["eta"], rep.stats["s11_db"]
                m = st.columns(4)
                m[0].metric("Resa", f"{100 * rep.yield_frac:.1f} %",
                            help=f"pezzi con perdita ≤ {rep.spec['loss_budget_db']} dB e S11 ≤ {rep.spec['s11_limit_db']} dB")
                m[1].metric(f"Perdita media di {ylab}", f"{rep.nominal['objective'] - so['mean']:.3f} dB",
                            help=f"dispersione σ = {so['std']:.3f} dB")
                m[2].metric("Efficienza (5–95%)", f"{100 * se['p05']:.1f}–{100 * se['p95']:.1f} %")
                if not math.isnan(ss["p95"]):
                    m[3].metric("S11 peggiore (95%)", f"{ss['p95']:.1f} dB")
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=rep.samples["objective"] - rep.nominal["objective"], nbinsx=60,
                                           name=f"Δ {ylab} (dB)"))
                fig.add_vline(x=-rep.spec["loss_budget_db"], line_dash="dot")
                fig.update_layout(height=260, xaxis_title=f"Δ {ylab} rispetto al nominale (dB)", yaxis_title="pezzi",
                                  margin=dict(t=20, b=30), showlegend=False)
                st.plotly_chart(fig, width="stretch")
                st.markdown("**Quote critiche** (in ordine di importanza)")
                st.dataframe([{"Quota": cr["label"], "Nominale": f"{cr['nominal']:.3f} {cr['unit']}",
                               "Tolleranza analizzata": f"±{cr['tol_now']:.3f} {cr['unit']}",
                               "Quota di varianza": f"{100 * cr['share']:.0f} %",
                               f"Perdita a ±t (dB)": f"{cr['d_obj']:.3f}",
                               "ΔS11 a ±t (dB)": "" if math.isnan(cr["d_s11"]) else f"{cr['d_s11']:+.2f}",
                               "Tolleranza consigliata": f"±{cr['tol_ok']:g} {cr['unit']}"} for cr in rep.critical],
                             hide_index=True, width="stretch")
                ver = ", ".join(f"{m_} {v:.3g}" for m_, v in rep.verify)
                st.caption(f"{rep.n_runs} simulazioni rapide (modello quadratico + verifica diretta: scarto massimo {ver}). "
                           "Tolleranza consigliata: la più larga classe d'officina che mantiene la perdita di quella quota "
                           f"entro la sua parte del budget di {rep.spec['loss_budget_db']} dB. Il modello rapido non vede "
                           "parete esterna e bordo: per le quote critiche verifica con openEMS.")
                if st.button("📄 Usa queste tolleranze nel disegno PDF", key="tol_pdf"):
                    S["tol_table"] = (kind, rep.critical)
                    st.success("Le trovi nella tabella delle tolleranze del disegno (scheda Disegno & STEP).")
            st.markdown("**Ottimizzazione robusta**: cerca le quote che danno il miglior risultato *medio meno k·σ* dentro "
                        "le tolleranze, invece del picco nominale più stretto.")
            c = st.columns(3)
            rkeys = c[0].multiselect("Quote da ottimizzare", [k for k, _, _ in explore.TUNABLE[kind]],
                                     default=[k for k, _, _ in explore.TUNABLE[kind]][:2], key="rob_keys",
                                     format_func=lambda k: dict((a, b) for a, b, _ in explore.TUNABLE[kind])[k])
            ks = c[1].slider("k (σ)", 0.0, 3.0, 2.0, 0.5, key="rob_k", help="2 ≈ il 97% dei pezzi fa almeno così")
            rnev = c[2].slider("Valutazioni robuste", 6, 40, 16, key="rob_nev",
                               help="ognuna costa 2N+1 simulazioni rapide (≈ 0.5 s l'una)")
            if st.button("🛡️ Ottimizzazione robusta", key="rob_go") and rkeys:
                bar = st.progress(0.0, "ottimo nominale, poi ricerca robusta…")
                over_r, info = tolerance.robust_optimize(kind, S.f_ghz, sc, lab_over, objective, rkeys, tol_in, ks, rnev,
                                                         s11t, S.wall,
                                                         progress=lambda i, n, v: bar.progress(min(i / n, 1.0), f"valutazione {i}/{n}"))
                bar.empty()
                S["ropt"] = (kind, over_r, info)
            if S.get("ropt") and S["ropt"][0] == kind:
                _, over_r, info = S["ropt"]
                ylab_r = {"tx": "G", "rx": "G/T", "eme": "G + G/T"}[objective]
                st.success(f"Progetto robusto: {ylab_r} nominale {info['objective']:.2f} · medio {info['mean']:.2f} ± {info['sd']:.3f} dB · "
                           f"garantito (media − k·σ) {info['score']:.2f} · η {100 * info['eta']:.1f}% · S11 {info['s11_db']:.1f} dB")
                st.write({k: f"{v:.3f} ({100 * (v / base_vals[k] - 1):+.1f}%)" for k, v in over_r.items() if k in base_vals})
                if st.button("Applica il progetto robusto", key="rob_apply"):
                    S.overrides[kind] = {k: v for k, v in over_r.items() if k in base_vals}
                    for k, v in S.overrides[kind].items():
                        S[f"lab_{kind}_{k}"] = float(v)
                    st.rerun()


# ---------------------------------------------------------------- matching plate
with tabs[7]:
    st.header("Piastrina λ/4 di adattamento: guida circolare del feed → guida rettangolare WR")
    st.caption("Il feed a simmetria circolare irradia la polarizzazione lineare imposta dall'orientamento della guida WR: "
               "il campo E è parallelo al lato corto 'b'. Metodo: design guide OE2IGL (openEMS), ottimizzazione HB9PZK.")
    geo = current_geometry()
    from feedlab.waveguide import RECT_WG, suggest_rect_wg
    if isinstance(geo, geometry.RectHornGeometry):
        st.info("L'horn rettangolare si collega direttamente alla guida WR: piastrina non necessaria.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        sugg = suggest_rect_wg(S.f_ghz) or list(RECT_WG)
        wg = c1.selectbox("Guida rettangolare", list(RECT_WG), index=list(RECT_WG).index(sugg[0]))
        pol_ = c2.radio("Polarizzazione", ["Verticale", "Orizzontale"], horizontal=True)
        dcirc = c3.number_input("Ø guida circolare del feed (mm)", 0.5, 100.0, float(round(2 * geo.r_input, 3)), 0.001,
                                format="%.3f")
        rr = c4.number_input("Raggio angoli apertura (mm)", 0.0, 5.0, float(round(min(2.0, 0.08 * RECT_WG[wg].a_mm), 2)), 0.05,
                             help="raggio della fresa: angoli arrotondati compensati sulla larghezza (HB9PZK)")
        opt = st.checkbox("Versione ottimizzata (b e spessore corretti con openEMS)", True)
        from feedlab import flanges
        c1, c2 = st.columns(2)
        holes_on = c1.checkbox("Fori di fissaggio guida → piastrina → feed", bool((S.get("mount_cfg") or {}).get("wg")),
                               disabled=wg not in flanges.FLANGES, key="mount_on",
                               help="foratura della flangia standard della guida, viti piastrina→feed con la testa nella "
                                    "lamatura e spine di centraggio: nel PDF e nello STEP di piastrina e feed")
        system = c2.radio("Viti", ["metric", "imperial"], horizontal=True, key="mount_sys",
                          format_func=lambda x: {"metric": "Metriche (M)", "imperial": "Pollici (UNC)"}[x])
        opts = flanges.plate_screw_options(S.f_ghz)
        pscrew = st.selectbox("Viti piastrina → feed", opts, key=f"plate_screw_{opts[0]}", disabled=not holes_on,
                              format_func=lambda m_: m_ if system == "metric" else f"{flanges.UNC_FOR_METRIC[m_]} (≈ {m_})",
                              help="lunghezza = 3 × spessore della piastrina, arrotondata alla misura commerciale "
                                   "(10, 12, 14, 16, 18, 20, 25 mm; in pollici 3/8\" … 1\"); i fori filettati nel feed "
                                   "seguono la lunghezza della vite")
        pol_c = "V" if pol_ == "Verticale" else "H"
        try:
            pl = plate.design_plate(S.f_ghz, wg, dcirc, pol_c, rr, opt, holes=system if holes_on else None,
                                    plate_screw=pscrew)
            new_cfg = {"wg": wg if holes_on else None, "system": system, "pol": pol_c, "plate_screw": pscrew,
                       "plate_t": pl.body_t if holes_on else None}
            if new_cfg != (S.get("mount_cfg") or {"wg": None}) and (holes_on or (S.get("mount_cfg") or {}).get("wg")):
                S["mount_cfg"] = new_cfg
                geometry.MOUNT.update(new_cfg)
                for k in ("pdf", "step", "stl", "plate_pdf", "plate_step"):
                    S.pop(k, None)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Apertura a", f"{pl.a:.3f} mm"); m2.metric("Apertura b", f"{pl.b:.3f} mm")
            m3.metric("Spessore", f"{pl.thickness:.3f} mm", f"± {pl.tolerance:.3f}", delta_color="off")
            m4.metric("Z0 intermedia", f"{pl.z0:.0f} Ω")
            w = RECT_WG[wg]
            st.write(f"{wg}: {w.a_mm} × {w.b_mm} mm (fc TE10 {w.fc_te10_ghz:.2f} GHz) · guida circolare Ø{dcirc:.3f} mm "
                     f"(fc TE11 {299.792458 / (1.706 * dcirc):.2f} GHz)")
            if pl.mount is not None:
                mm_ = pl.mount
                st.info(f"Flangia {mm_.flange.wg} {mm_.flange.name}: le viti della guida ({mm_.screw}) si avvitano nella "
                        f"piastra; 4 viti piastra→feed {mm_.plate_screw} × {mm_.screw_len_label} con testa nella lamatura "
                        f"(lato guida), filetto nel feed prof. {mm_.tap_depth:.1f} mm"
                        + (", 2 spine di centraggio" if any(h.kind == "pin" for h in mm_.plate_holes) else "") + ". "
                        + (f"Corpo piastrina {pl.body_t:.2f} mm con tasca Ø{pl.circ_diam:.3f} × {pl.pocket_depth:.2f} mm sul lato "
                           "feed (prolunga la guida circolare; la parte λ/4 resta invariata). " if pl.pocket_depth > 1e-6 else "")
                        + "La foratura è applicata anche al feed (PDF foglio 2 e STEP nella scheda Disegno & STEP).")
                for w_ in mm_.warnings:
                    st.warning(w_)
            base = WORK / f"plate_{wg}_{S.f_ghz:g}GHz_{pl.polarization}".replace(".", "p")
            b1, b2 = st.columns(2)
            if b1.button("📄 Disegno PDF piastrina"):
                S["plate_pdf"] = Path(plate.drawing_pdf(pl, base.with_suffix(".pdf"), S.material)).read_bytes()
            if S.get("plate_pdf"):
                b1.download_button("Scarica PDF", S["plate_pdf"], file_name=base.name + ".pdf", mime="application/pdf")
            if b2.button("🧊 STEP piastrina"):
                S["plate_step"] = Path(plate.export_step(pl, base.with_suffix(".step"))).read_bytes()
            if S.get("plate_step"):
                b2.download_button("Scarica .stp", S["plate_step"], file_name=base.name + ".stp")
            # front view preview
            fig = go.Figure()
            h = pl.outer / 2
            fig.add_shape(type="rect", x0=-h, y0=-h, x1=h, y1=h, line=dict(color="black"), fillcolor="rgba(201,162,39,0.5)")
            aa, bb = (pl.a, pl.b) if pl.polarization == "V" else (pl.b, pl.a)
            fig.add_shape(type="rect", x0=-aa / 2, y0=-bb / 2, x1=aa / 2, y1=bb / 2, line=dict(color="black"), fillcolor="white")
            fig.add_shape(type="circle", x0=-dcirc / 2, y0=-dcirc / 2, x1=dcirc / 2, y1=dcirc / 2, line=dict(dash="dash", color="gray"))
            wa, wb = (w.a_mm, w.b_mm) if pl.polarization == "V" else (w.b_mm, w.a_mm)
            fig.add_shape(type="rect", x0=-wa / 2, y0=-wb / 2, x1=wa / 2, y1=wb / 2, line=dict(dash="dot", color="blue"))
            if pl.mount is not None:
                for hl in pl.mount.plate_holes:
                    col_ = {"tap": "black", "dowel": "green", "pin": "green", "cbore": "black"}.get(hl.kind, "black")
                    fig.add_shape(type="circle", x0=hl.x - hl.dia / 2, y0=hl.y - hl.dia / 2, x1=hl.x + hl.dia / 2,
                                  y1=hl.y + hl.dia / 2, line=dict(color=col_))
                    if hl.kind == "cbore":
                        fig.add_shape(type="circle", x0=hl.x - hl.cb_dia / 2, y0=hl.y - hl.cb_dia / 2, x1=hl.x + hl.cb_dia / 2,
                                      y1=hl.y + hl.cb_dia / 2, line=dict(color="magenta"))
            fig.add_annotation(x=0, y=0, ax=0 if pl.polarization == "V" else -40, ay=40 if pl.polarization == "V" else 0,
                               text="E", showarrow=True, arrowcolor="red", arrowhead=2, arrowwidth=2)
            fig.update_layout(height=420, xaxis=dict(range=[-h - 3, h + 3], title="mm"),
                              yaxis=dict(range=[-h - 3, h + 3], scaleanchor="x"), title="Vista frontale (lato feed)")
            st.plotly_chart(fig, width="stretch")
        except ValueError as ex:
            st.error(str(ex))


# ---------------------------------------------------------------- credits
with tabs[9]:
    from feedlab import credits as _credits
    _credits.render(st)
