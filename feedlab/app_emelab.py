# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Tab "📡 EMELab" of FeedLab (optional, enabled from the sidebar): EME station, measurement log with Sun/Moon
positions and weather (UTC), expected vs measured, pointing model, Moon planner and measurement guide.
All data stay in a local SQLite file (settings folder); the personal weather-station address is saved only
in the local settings."""
from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta, timezone

import numpy as np
import plotly.graph_objects as go
import streamlit as _st

from feedlab import i18n, openems_local
from feedlab.emelab import analysis, astro, atmos, db as edb, planner, weather

st = i18n.wrap(_st)
BANDS = {"10.368 GHz": 10.368, "24.048 GHz": 24.048, "47.088 GHz": 47.088}


def _db():
    """A fresh connection at every run (Streamlit reruns on other threads; opening SQLite costs ~1 ms)."""
    return edb.DB()


def _fmt(v, f="{:.2f}"):
    return "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f.format(v)


# ------------------------------------------------------------------ station and setups
def _station(D):
    stn = D.station()
    st.subheader("Stazione")
    c = st.columns(4)
    call = c[0].text_input("Nominativo", stn.get("callsign") or "", key="em_call")
    loc = c[1].text_input("Locator", stn.get("locator") or "", key="em_loc", help="es. JN61fs: calcola latitudine e longitudine")
    lat0, lon0 = stn.get("lat"), stn.get("lon")
    if loc and len(loc.strip()) >= 4 and (lat0 is None or loc.strip().upper() != (stn.get("locator") or "").upper()):
        try:
            lat0, lon0 = astro.locator_to_latlon(loc)
        except Exception:
            pass
    lat = c[2].number_input("Latitudine (°, nord +)", -90.0, 90.0, float(lat0 or 0.0), 0.0001, format="%.4f", key="em_lat")
    lon = c[3].number_input("Longitudine (°, est +)", -180.0, 180.0, float(lon0 or 0.0), 0.0001, format="%.4f", key="em_lon")
    c = st.columns(4)
    h = c[0].number_input("Quota (m s.l.m.)", -100.0, 5000.0, float(stn.get("height_m") or 0.0), 1.0, key="em_h")
    sets = openems_local.load_settings()
    url = c[1].text_input("Stazione meteo personale (facoltativa)", sets.get("emelab_wx_url", ""), key="em_wxurl",
                          help="indirizzo del tuo sito Meteotemplate / Cumulus / Weather Display, oppure del file dati. "
                               "Resta salvato solo su questo PC")
    flux = c[2].number_input("Flusso solare a 15.4 GHz (SFU)", 300.0, 3000.0, float(sets.get("emelab_flux", 550.0)), 10.0,
                             key="em_flux", help="valore del giorno dagli osservatori RSTN (San Vito, Learmonth, Sagamore "
                                                 "Hill, Palehua) pubblicato da NOAA SWPC; serve per il rumore solare atteso")
    if c[3].button("💾 Salva stazione", key="em_save_st"):
        D.save_station(callsign=call.strip().upper(), locator=loc.strip(), lat=lat, lon=lon, height_m=h)
        openems_local.save_settings(emelab_wx_url=url.strip(), emelab_flux=flux)
        st.success("Stazione salvata (solo su questo PC).")
    st.caption("Tutti i dati di EMELab (stazione, setup, misure, indirizzo della stazione meteo) restano in un file sul "
               "tuo PC e non vengono mai inviati: il meteo da internet riceve solo coordinate e ora.")


def _setup_from_feedlab(S, current_geometry, name, band, extra) -> dict | None:
    """Gain, efficiency, spillover and edge taper of the FeedLab design at this band, on the chosen dish."""
    from feedlab import explore
    if not (S.get("dish") and S.get("feed_kind")):
        return None
    d = S.dish
    sc = explore.Scenario(dish_kind=d.kind, D_mm=d.D_mm, fD=d.fD, elev_deg=30, t_rx_K=analysis.t_rx(extra["nf_db"]),
                          surface_rms_mm=extra.get("rms_mm", 0.3), feedline_loss_db=0.0,
                          material=S.get("material") or "Ottone CuZn39Pb3")
    r = explore.evaluate(S.feed_kind, band, sc, dict((S.get("overrides") or {}).get(S.feed_kind, {})),
                         fD_design=S.get("fd_design"))
    return {"band_ghz": band, "D_m": d.D_mm / 1000, "eta_ap": r.eta, "gain_dbi": r.gain_dbi, "edge_taper_db": r.edge_taper_db,
            "spill": r.spill, "ground_frac": 0.25 if d.kind == "offset" else 0.5, "feed": S.feed_kind,
            "dish": f"{d.kind} D {d.D_mm:.0f} mm f/D {d.fD:.3f}", "material": S.get("material"),
            "pc_mm": r.pc_mm, "source": "FeedLab", **extra}


def _setups(D, S, current_geometry):
    st.subheader("Setup per banda")
    st.caption("Un setup per ogni banda: parabola, feed, perdite, preamplificatore/transverter e potenza. Il pulsante "
               "«Da FeedLab» prende guadagno, efficienza, spillover e taper dal progetto aperto in FeedLab.")
    c = st.columns(4)
    band_l = c[0].selectbox("Banda", list(BANDS), key="em_setup_band")
    band = BANDS[band_l]
    name = c[1].text_input("Nome del setup", f"{band_l} — 2.4 m", key="em_setup_name")
    nf = c[2].number_input("NF preamplificatore / transverter (dB)", 0.2, 10.0, 1.5 if band < 30 else 3.0, 0.1, key="em_nf")
    line = c[3].number_input("Perdite feed → LNA (dB)", 0.0, 5.0, 0.2, 0.05, key="em_line",
                             help="relè, guida, adattatori tra il feed e l'ingresso del preamplificatore")
    c = st.columns(4)
    txw = c[0].number_input("Potenza TX al feed (W)", 0.0, 2000.0, 20.0, 1.0, key="em_txw")
    rms = c[1].number_input("Superficie della parabola, errore RMS (mm)", 0.0, 3.0, 0.3, 0.05, key="em_rms",
                            help="perdita di Ruze: a 47 GHz 0.3 mm RMS costano circa 1.2 dB")
    hp = c[2].number_input("Larghezza del fascio misurata (°, 0 = calcolata)", 0.0, 5.0, 0.0, 0.01, key="em_hpbw",
                           help="dal transito del sole: durata a −3 dB × 0.25°/min × cos(dec)")
    extra = {"nf_db": nf, "line_loss_db": line, "tx_w": txw, "rms_mm": rms, "hpbw_deg": hp or None}
    b = st.columns(3)
    if b[0].button("📐 Da FeedLab", key="em_from_fl", help="usa parabola, feed e materiale del progetto aperto"):
        stp = _setup_from_feedlab(S, current_geometry, name, band, extra)
        if stp is None:
            st.warning("Scegli prima parabola e feed in FeedLab (procedura guidata).")
        else:
            D.save_setup(name, band, stp)
            st.success("Setup salvato da FeedLab.")
    with b[1].popover("✍️ Inserisci a mano"):
        Dm = st.number_input("Diametro della parabola (m)", 0.3, 20.0, 2.4, 0.05, key="em_m_D")
        eta = st.number_input("Efficienza d'apertura (%)", 20.0, 90.0, 60.0, 1.0, key="em_m_eta")
        et = st.number_input("Taper al bordo (dB)", 5.0, 25.0, 12.0, 0.5, key="em_m_et")
        if st.button("💾 Salva setup", key="em_m_save"):
            lam = 299.792458 / band
            g = 10 * math.log10(eta / 100 * (math.pi * Dm * 1000 / lam) ** 2)
            D.save_setup(name, band, {"band_ghz": band, "D_m": Dm, "eta_ap": eta / 100, "gain_dbi": g, "edge_taper_db": et,
                                      "spill": 0.9, "ground_frac": 0.25, "source": "manuale", **extra})
            st.success("Setup salvato.")
    rows = D.setups()
    if rows:
        st.dataframe([{"ID": r["id"], "Nome": r["name"], "Banda (GHz)": r["band_ghz"], "Parabola (m)": r.get("D_m"),
                       "Guadagno (dBi)": round(r.get("gain_dbi", 0), 2), "Efficienza (%)": round(100 * r.get("eta_ap", 0), 1),
                       "Taper (dB)": round(r.get("edge_taper_db", 0), 1), "NF (dB)": r.get("nf_db"),
                       "Perdite (dB)": r.get("line_loss_db"), "TX (W)": r.get("tx_w"), "Origine": r.get("source")}
                      for r in rows], hide_index=True, use_container_width=True)
        dl = st.selectbox("Elimina setup", [None] + [r["id"] for r in rows], key="em_del_setup",
                          format_func=lambda i: "—" if i is None else next(r["name"] for r in rows if r["id"] == i))
        if dl and st.button("🗑️ Elimina", key="em_del_setup_btn"):
            D.delete_setup(dl)
            st.rerun()


# ------------------------------------------------------------------ new measurement
def _wx_fetch(src, stn, dt):
    url = openems_local.load_settings().get("emelab_wx_url", "")
    try:
        if src == "station":
            if not url:
                st.warning("Inserisci l'indirizzo della tua stazione meteo nella sezione Stazione.")
                return
            w = weather.station_now(url)
        else:
            w = weather.open_meteo(stn["lat"], stn["lon"], dt)
        for k in ("t_c", "rh", "p_hpa", "wind_ms", "rain_mmh", "cloud_pct"):
            if w.get(k) is not None:
                _st.session_state[f"em_wx_{k}"] = float(w[k])
        _st.session_state["em_wx_src"] = w.get("wx_source")
        _st.session_state["em_wx_utc"] = w.get("wx_utc")
    except Exception as e:
        st.error(i18n.tr("Meteo non disponibile") + f": {e}")


def _new(D):
    stn = D.station()
    sets = D.setups()
    if not stn.get("lat") and not stn.get("lon"):
        st.info("Inserisci e salva prima la stazione (posizione) nella sezione Stazione e setup.")
        return
    if not sets:
        st.info("Crea prima un setup per la banda (sezione Stazione e setup).")
        return
    now = datetime.now(timezone.utc)
    c = st.columns(4)
    sid = c[0].selectbox("Setup", [s["id"] for s in sets], key="em_n_setup",
                         format_func=lambda i: next(s["name"] for s in sets if s["id"] == i))
    setup = next(s for s in sets if s["id"] == sid)
    d0 = c[1].date_input("Data (UTC)", now.date(), key="em_n_date")
    t0 = c[2].time_input("Ora (UTC)", now.time().replace(second=0, microsecond=0), key="em_n_time", step=60)
    if "em_n_kind" not in _st.session_state:          # by night the Moon is the natural default
        _now = astro.sky(now, stn["lat"], stn["lon"], stn.get("height_m") or 0.0)
        _st.session_state["em_n_kind"] = "sun" if _now.sun.el > 3 else "moon" if _now.moon.el > 3 else "cold_sky"
    kind = c[3].selectbox("Tipo di misura", list(edb.KINDS), key="em_n_kind", format_func=lambda k: edb.KINDS[k])
    dt = datetime.combine(d0, t0).replace(tzinfo=timezone.utc)
    st.caption(f"⏱️ {edb.iso_utc(dt)} UTC")
    c = st.columns(4)
    y = c[0].number_input("Y misurato (dB)", -5.0, 40.0, None, 0.05, key="em_n_y",
                          help="sole/luna/terra: rapporto tra rumore sulla sorgente e cielo freddo")
    snr = c[1].number_input("SNR (dB)", -40.0, 60.0, None, 0.1, key="em_n_snr", help="eco o segnale: SNR letto dal programma")
    val = c[2].number_input("Altro valore", value=None, key="em_n_val", help="es. livello in dBm, spostamento del feed in mm")
    unit = c[3].text_input("Unità", "", key="em_n_unit")
    c = st.columns(5)
    azr = c[0].number_input("AZ letto (°)", 0.0, 360.0, None, 0.01, key="em_n_azr")
    elr = c[1].number_input("EL letto (°)", -5.0, 95.0, None, 0.01, key="em_n_elr")
    azo = c[2].number_input("Offset AZ al picco (°)", -10.0, 10.0, None, 0.005, key="em_n_azo",
                            help="correzione che hai dovuto dare rispetto alla posizione calcolata per avere il massimo")
    elo = c[3].number_input("Offset EL al picco (°)", -10.0, 10.0, None, 0.005, key="em_n_elo")
    partner = c[4].text_input("Stazione corrispondente", "", key="em_n_partner", help="nominativo e locator, per eco/QSO")
    st.markdown("**Meteo al momento della misura**")
    b = st.columns(3)
    if b[0].button("🌡️ Dalla mia stazione", key="em_wx_st"):
        _wx_fetch("station", stn, dt)
    if b[1].button("🌍 Da Open-Meteo", key="em_wx_om"):
        _wx_fetch("om", stn, dt)
    b[2].caption((i18n.tr("Fonte") + f": {_st.session_state.get('em_wx_src') or i18n.tr('manuale')} · "
                  f"{_st.session_state.get('em_wx_utc') or '—'} UTC"))
    c = st.columns(6)
    t_c = c[0].number_input("Temperatura (°C)", -40.0, 50.0, None, 0.1, key="em_wx_t_c")
    rh = c[1].number_input("Umidità (%)", 0.0, 100.0, None, 1.0, key="em_wx_rh")
    p = c[2].number_input("Pressione (hPa)", 800.0, 1100.0, None, 0.1, key="em_wx_p_hpa")
    wind = c[3].number_input("Vento (m/s)", 0.0, 60.0, None, 0.1, key="em_wx_wind_ms")
    rain = c[4].number_input("Pioggia (mm/h)", 0.0, 200.0, None, 0.1, key="em_wx_rain_mmh")
    cloud = c[5].number_input("Nuvole (%)", 0.0, 100.0, None, 1.0, key="em_wx_cloud_pct")
    notes = st.text_area("Note", "", key="em_n_notes", height=70)
    wx = {"t_c": t_c, "rh": rh, "p_hpa": p}
    calc = analysis.snapshot(stn, setup, dt, wx, openems_local.load_settings().get("emelab_flux"))
    _show_snapshot(calc, kind)
    if st.button("💾 Registra misura", type="primary", key="em_n_save"):
        D.add(utc=dt, setup_id=sid, band_ghz=setup["band_ghz"], kind=kind, y_db=y, snr_db=snr, value=val, unit=unit or None,
              az_read=azr, el_read=elr, az_off=azo, el_off=elo, partner=partner or None, notes=notes or None,
              t_c=t_c, rh=rh, p_hpa=p, wind_ms=wind, rain_mmh=rain, cloud_pct=cloud,
              wx_utc=_st.session_state.get("em_wx_utc"), wx_source=_st.session_state.get("em_wx_src") or "manuale",
              calc=_clean(calc))
        st.success("Misura registrata.")


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, float) and math.isnan(o):
        return None
    return o


def _show_snapshot(c, kind):
    s, m = c["sun"], c["moon"]
    cols = st.columns(4)
    cols[0].metric("Sole AZ / EL", f"{s['az']:.2f}° / {s['el']:.2f}°")
    cols[1].metric("Luna AZ / EL", f"{m['az']:.2f}° / {m['el']:.2f}°")
    cols[2].metric("Distanza Luna", f"{m['dist_km']:.0f} km")
    cols[3].metric("Angolo Sole–Luna", f"{c['sun_moon_deg']:.1f}°")
    cols = st.columns(4)
    cols[0].metric("Attenuazione allo zenit", f"{c['a_zen_db']:.2f} dB", help=f"O₂ {c['a_zen_o2']:.2f} + H₂O {c['a_zen_h2o']:.2f} dB, "
                   f"vapore {c['rho']:.1f} g/m³")
    src = s if kind == "sun" else m
    if src["el"] < 0:
        st.warning(("Il Sole" if kind == "sun" else "La Luna") + " " + i18n.tr("è sotto l'orizzonte in questo momento") +
                   f" (EL {src['el']:.1f}°).")
    cols[1].metric("Attenuazione sul percorso", _fmt(src["a_slant_db"], "{:.2f} dB"))
    cols[2].metric("Temperatura di cielo", _fmt(src["t_sky"], "{:.0f} K"))
    cols[3].metric("Tsys (cielo freddo)", _fmt(src["tsys"], "{:.0f} K"))
    cols = st.columns(4)
    cols[0].metric("Y sole atteso", _fmt(s["y_db"], "{:.2f} dB"))
    cols[1].metric("Y luna atteso", _fmt(m["y_db"], "{:.2f} dB"))
    cols[2].metric("Fascio a −3 dB", f"{c['hpbw_deg']:.3f}°")
    e = c.get("echo")
    cols[3].metric("Eco attesa (SNR in 1 Hz)", _fmt(e["snr_1hz_db"], "{:.1f} dB") if e else "—",
                   help=(i18n.tr("in banda di spreading") + f" {e['spread_hz']:.0f} Hz: {e['snr_spread_db']:.1f} dB · "
                         + i18n.tr("perdita di tratta") + f" {e['path_loss_db']:.2f} dB · " + i18n.tr("fascio più stretto della Luna")
                         + f" {e['beam_moon_db']:.1f} dB") if e else None)
    st.caption(i18n.tr("Doppler eco") + f" {c['doppler_hz']:+.0f} Hz · " + i18n.tr("spreading") + f" {c['spread_hz']:.0f} Hz · "
               + i18n.tr("fase lunare") + f" {c['moon_phase_deg']:+.0f}° ({100 * c['moon_illum']:.0f} %)")


# ------------------------------------------------------------------ log
def _log(D):
    sets = {s["id"]: s for s in D.setups()}
    c = st.columns(2)
    fb = c[0].selectbox("Banda", [None] + list(BANDS), key="em_l_band", format_func=lambda b: i18n.tr("tutte") if b is None else b)
    fk = c[1].selectbox("Tipo", [None] + list(edb.KINDS), key="em_l_kind",
                        format_func=lambda k: i18n.tr("tutti") if k is None else edb.KINDS[k])
    rows = D.measurements(BANDS.get(fb) if fb else None, fk)
    if not rows:
        st.info("Nessuna misura registrata.")
    else:
        tab = []
        for r in rows:
            ev = analysis.evaluate_measurement(r, sets[r["setup_id"]]) if r.get("setup_id") in sets else {}
            c = r.get("calc") or {}
            src = c.get("moon" if r["kind"] in ("moon", "echo", "qso") else "sun") or {}
            tab.append({"ID": r["id"], "UTC": r["utc"].replace("T", " ").replace("Z", ""), "GHz": r["band_ghz"], "Tipo": edb.KINDS.get(r["kind"], r["kind"]),
                        "Y (dB)": r["y_db"], "Y atteso": _r(ev.get("y_expected")), "ΔY": _r(ev.get("y_delta")),
                        "G/T misurato": _r(ev.get("gt_measured")), "ΔG/T": _r(ev.get("gt_delta")), "SNR": r["snr_db"],
                        "SNR atteso": _r(ev.get("snr_expected")), "EL": _r(src.get("el")), "AZ": _r(src.get("az")),
                        "°C": r["t_c"], "UR %": r["rh"], "hPa": r["p_hpa"], "Meteo": r["wx_source"], "Note": r["notes"]})
        import pandas as pd
        st.dataframe(pd.DataFrame(tab), hide_index=True, use_container_width=True)
        c = st.columns(3)
        dl = c[0].selectbox("Elimina misura (ID)", [None] + [r["id"] for r in rows], key="em_del_m",
                            format_func=lambda i: "—" if i is None else str(i))
        if dl and c[0].button("🗑️ Elimina", key="em_del_m_btn"):
            D.delete(dl)
            st.rerun()
        c[1].download_button("⬇️ Esporta CSV", D.export_csv(), file_name="emelab_misure.csv", mime="text/csv")
    up = st.file_uploader("Importa CSV", type=["csv"], key="em_imp")
    if up is not None and st.button("📥 Importa", key="em_imp_btn"):
        n = D.import_csv(up.getvalue().decode("utf-8"))
        st.success(i18n.tr("Misure importate") + f": {n}")


def _r(v, n=2):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else round(v, n)


# ------------------------------------------------------------------ analysis
def _analysis(D):
    sets = D.setups()
    if not sets:
        st.info("Nessun setup.")
        return
    sid = st.selectbox("Setup", [s["id"] for s in sets], key="em_a_setup",
                       format_func=lambda i: next(s["name"] for s in sets if s["id"] == i))
    setup = next(s for s in sets if s["id"] == sid)
    rows = [r for r in D.measurements() if r.get("setup_id") == sid]
    for t in analysis.advice(rows, setup):
        st.markdown("- " + i18n.tr(t))
    with st.expander("📊 Dove guadagnare dB con questo setup", expanded=not rows):
        st.caption("Quanto cambiano G/T (ricezione) e SNR delle eco con miglioramenti realistici, a 30° di elevazione e "
                   "UR 60 %, con lo stesso modello usato per i valori attesi.")
        st.dataframe([{"Miglioramento": i18n.tr(r["label"]), "ΔG/T (dB)": round(r["d_gt"], 2), "ΔEco (dB)": round(r["d_echo"], 2)}
                      for r in sorted(analysis.improvements(setup), key=lambda r: -abs(r["d_echo"]))],
                     hide_index=True, use_container_width=True)
    ev = [(r, analysis.evaluate_measurement(r, setup)) for r in rows]
    sun = [(r, e) for r, e in ev if "gt_delta" in e]
    if sun:
        c = st.columns(2)
        fig = go.Figure(go.Scatter(x=[r["calc"]["sun"]["el"] for r, _ in sun], y=[e["gt_delta"] for _, e in sun],
                                   mode="markers", marker=dict(size=9, color=[r.get("rh") for r, _ in sun],
                                   colorscale="Viridis", showscale=True, colorbar=dict(title="UR %"))))
        fig.add_hline(y=0, line_dash="dot")
        fig.update_layout(title="G/T misurato − atteso vs elevazione del sole", xaxis_title="Elevazione (°)",
                          yaxis_title="ΔG/T (dB)", height=360, margin=dict(l=10, r=10, t=40, b=10))
        c[0].plotly_chart(fig, use_container_width=True)
        fig = go.Figure(go.Scatter(x=[r["utc"] for r, _ in sun], y=[e["gt_measured"] for _, e in sun], mode="markers",
                                   name="misurato"))
        fig.add_trace(go.Scatter(x=[r["utc"] for r, _ in sun], y=[e["gt_expected"] for _, e in sun], mode="lines",
                                 name="atteso", line=dict(dash="dot")))
        fig.update_layout(title="G/T dal sole nel tempo", yaxis_title="G/T (dB/K)", height=360,
                          margin=dict(l=10, r=10, t=40, b=10))
        c[1].plotly_chart(fig, use_container_width=True)
    ff = analysis.focus_fit(rows)
    if ff:
        fig = go.Figure(go.Scatter(x=ff["x"], y=ff["y"], mode="markers", name="misurato"))
        xs = np.linspace(min(ff["x"]), max(ff["x"]), 60)
        a, b, c0 = ff["coef"]
        fig.add_trace(go.Scatter(x=xs, y=a * xs ** 2 + b * xs + c0, mode="lines", name="curva interpolata"))
        fig.update_layout(title="Messa a fuoco: Y in funzione dello spostamento del feed", xaxis_title="Spostamento (mm)",
                          yaxis_title="Y (dB)", height=340, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
        if ff["best_mm"] is not None:
            st.success(i18n.tr("Fuoco migliore a") + f" {ff['best_mm']:+.1f} mm " + i18n.tr("dalla posizione di partenza") +
                       f" ({ff['gain_db']:+.2f} dB " + i18n.tr("di Y in più") + ").")
    pm = [r for r in rows if r.get("az_off") is not None and r.get("el_off") is not None and r["kind"] in ("sun", "moon")]
    if pm:
        fig = go.Figure(go.Scatter(x=[r["az_off"] for r in pm], y=[r["el_off"] for r in pm], mode="markers",
                                   text=[r["utc"] for r in pm], marker=dict(size=9, color=[r["calc"][r["kind"]]["el"] for r in pm],
                                   colorscale="Plasma", showscale=True, colorbar=dict(title="EL"))))
        hp = analysis.hpbw_of(setup)
        fig.add_shape(type="circle", x0=-hp / 2, x1=hp / 2, y0=-hp / 2, y1=hp / 2, line=dict(dash="dot"))
        fig.update_layout(title="Offset di puntamento al picco (cerchio = fascio a −3 dB)", xaxis_title="Offset AZ (°)",
                          yaxis_title="Offset EL (°)", height=380, margin=dict(l=10, r=10, t=40, b=10))
        fig.update_yaxes(scaleanchor="x")
        st.plotly_chart(fig, use_container_width=True)


# ------------------------------------------------------------------ planner
def _planner(D):
    stn = D.station()
    sets = D.setups()
    if not sets or (not stn.get("lat") and not stn.get("lon")):
        st.info("Servono stazione e setup.")
        return
    c = st.columns(5)
    sid = c[0].selectbox("Setup", [s["id"] for s in sets], key="em_p_setup",
                         format_func=lambda i: next(s["name"] for s in sets if s["id"] == i))
    setup = next(s for s in sets if s["id"] == sid)
    days = c[1].number_input("Giorni", 1, 60, 14, key="em_p_days")
    min_el = c[2].number_input("Elevazione minima (°)", 0.0, 60.0, 10.0, 1.0, key="em_p_minel",
                               help="sotto i 10–15° a 24/47 GHz l'atmosfera e il rumore di terra pesano molto")
    ploc = c[3].text_input("Locator della stazione corrispondente", "", key="em_p_ploc",
                           help="facoltativo: mostra solo le finestre in cui la Luna è visibile da entrambi")
    use_fc = c[4].checkbox("Usa le previsioni meteo", False, key="em_p_fc",
                           help="umidità prevista da Open-Meteo (16 giorni): a 24 GHz cambia l'attenuazione")
    if st.button("🗓️ Calcola", type="primary", key="em_p_go"):
        partner = None
        if ploc.strip():
            try:
                partner = astro.locator_to_latlon(ploc)
            except Exception:
                st.warning("Locator non valido.")
        series = None
        if use_fc:
            try:
                series = weather.open_meteo_series(stn["lat"], stn["lon"], datetime.now(timezone.utc), min(int(days), 16))
            except Exception as e:
                st.warning(i18n.tr("Previsioni non disponibili") + f": {e}")
        with st.spinner("Calcolo delle finestre…"):
            smp = planner.windows(stn, setup, datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0),
                                  int(days), 15, min_el, partner, series)
        _st.session_state["em_plan"] = (smp, planner.daily(smp))
    if _st.session_state.get("em_plan"):
        smp, rows = _st.session_state["em_plan"]
        if not rows:
            st.info("Nessuna finestra nel periodo con questi limiti.")
            return
        st.dataframe([{"Inizio (UTC)": r["start"].strftime("%Y-%m-%d %H:%M"), "Fine (UTC)": r["end"].strftime("%Y-%m-%d %H:%M"),
                       "Ore": round(r["hours"], 1), "Momento migliore (UTC)": r["best_utc"].strftime("%Y-%m-%d %H:%M"),
                       "EL max (°)": round(r["best_el"], 1), "Distanza (km)": round(r["dist_km"]),
                       "Eco SNR 1 Hz (dB)": _r(r["snr_1hz"], 1), "Eco SNR nello spreading (dB)": _r(r["snr_spread"], 1),
                       "Spreading (Hz)": round(r["spread_hz"]), "Attenuazione (dB)": round(r["a_slant_db"], 2),
                       "Sole–Luna min (°)": round(r["sun_moon_deg"], 1)} for r in rows], hide_index=True, use_container_width=True)
        fig = go.Figure(go.Scatter(x=[s["utc"] for s in smp], y=[s["snr_1hz"] for s in smp], mode="markers",
                                   marker=dict(size=4, color=[s["el"] for s in smp], colorscale="Viridis", showscale=True,
                                               colorbar=dict(title="EL"))))
        fig.update_layout(title="SNR atteso delle eco (1 Hz) nelle finestre", yaxis_title="dB", height=360,
                          margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("🌡️ Mesi più favorevoli (clima dell'ultimo anno nel tuo luogo)"):
        st.caption("Medie mensili di temperatura e umidità dall'archivio Open-Meteo: vapore acqueo, attenuazione, "
                   "temperatura di cielo a 30° e quanto perdi rispetto al mese migliore (G/T e eco).")
        if st.button("Calcola dal clima", key="em_p_clim"):
            try:
                _st.session_state["em_clim"] = planner.monthly_climate(stn["lat"], stn["lon"], setup)
            except Exception as e:
                st.warning(i18n.tr("Archivio meteo non disponibile") + f": {e}")
        cl = _st.session_state.get("em_clim")
        if cl:
            st.dataframe([{"Mese": i18n.tr(planner.MONTHS_IT[r["month"] - 1]), "°C": round(r["t_c"], 1), "UR %": round(r["rh"]),
                           "Vapore (g/m³)": round(r["rho"], 1), "Attenuazione zenit (dB)": round(r["a_zen_db"], 2),
                           "Cielo a 30° (K)": round(r["t_sky"]), "ΔG/T (dB)": round(r["d_gt_db"], 2),
                           "ΔEco (dB)": round(r["d_echo_db"], 2)} for r in cl], hide_index=True, use_container_width=True)
    with st.expander("📅 Perigei e apogei dei prossimi mesi"):
        if st.button("Calcola perigei", key="em_p_peri"):
            pts = planner.perigees(datetime.now(timezone.utc), 200)
            st.dataframe([{"UTC": t.strftime("%Y-%m-%d %H:%M"), "Tipo": k, "Distanza (km)": round(d),
                           "Eco rispetto al perigeo (dB)": round(-40 * math.log10(d / min(x[1] for x in pts)), 2)}
                          for t, d, k in pts], hide_index=True, use_container_width=True)
        st.caption("Al perigeo le eco sono fino a 2.2 dB più forti che all'apogeo (la perdita di tratta va con R⁴).")


# ------------------------------------------------------------------ guide
def _guide():
    from pathlib import Path
    lang = i18n.get_lang()
    p = Path(__file__).resolve().parent / "emelab" / f"guida_misure_{'it' if lang == 'it' else 'en'}.md"
    if p.exists():
        _st.markdown(p.read_text(encoding="utf-8"))


def render(S, current_geometry):
    D = _db()
    st.header("📡 EMELab — stazione EME, misure e pianificazione")
    st.caption("Registra misure di sole, luna, cielo freddo, terra ed eco con posizione di sole e luna, distanza, "
               "meteo e attenuazione atmosferica (tutto in UTC); EMELab le confronta con quanto il tuo setup dovrebbe "
               "dare e ti dice dove migliorare.")
    t = st.tabs(["① Stazione e setup", "② Nuova misura", "③ Diario", "④ Analisi", "⑤ Pianificatore", "⑥ Guida alle misure"])
    with t[0]:
        _station(D)
        st.divider()
        _setups(D, S, current_geometry)
    with t[1]:
        _new(D)
    with t[2]:
        _log(D)
    with t[3]:
        _analysis(D)
    with t[4]:
        _planner(D)
    with t[5]:
        _guide()
