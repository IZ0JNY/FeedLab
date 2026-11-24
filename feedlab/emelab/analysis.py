# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""What the station should measure (from the setup, the sky and the weather) and what the measurements say.

Setup (per band): D_m, eta_ap (aperture efficiency incl. surface), gain_dbi, edge_taper_db, hpbw_deg (optional,
measured), spill (fraction of the feed power on the dish), ground_frac (part of the spillover that sees the
ground), line_loss_db (feed → LNA), nf_db (LNA/transverter), tx_w (power at the feed), flux_sfu (15.4 GHz)."""
from __future__ import annotations

import math
from datetime import datetime

import numpy as np

from . import astro, atmos, link, sky

T0 = 290.0


def t_rx(nf_db: float) -> float:
    return T0 * (10 ** (nf_db / 10) - 1)


def hpbw_of(setup: dict) -> float:
    return float(setup.get("hpbw_deg") or sky.hpbw_deg(setup["band_ghz"], setup["D_m"], setup.get("edge_taper_db", 12)))


def tsys_cold(setup: dict, t_sky: float, t_ground: float = 290.0) -> dict:
    """Cold-sky system temperature at the antenna port of the LNA (K), with its parts."""
    spill = float(setup.get("spill", 0.9))
    gf = float(setup.get("ground_frac", 0.25))
    ta = spill * t_sky + (1 - spill) * (gf * t_ground + (1 - gf) * t_sky)
    line = 10 ** (-float(setup.get("line_loss_db", 0.0)) / 10)
    trx = t_rx(float(setup.get("nf_db", 1.5)))
    return {"t_ant": ta, "ant": ta * line, "line": (1 - line) * T0, "rx": trx, "sys": ta * line + (1 - line) * T0 + trx}


def snapshot(station: dict, setup: dict, dt: datetime, wx: dict | None = None, flux_sfu: float | None = None) -> dict:
    """Everything that can be computed for a measurement at time dt (UTC)."""
    f = float(setup["band_ghz"])
    s = astro.sky(dt, station["lat"], station["lon"], station.get("height_m") or 0.0)
    wx = wx or {}
    t_c = wx.get("t_c") if wx.get("t_c") is not None else 15.0
    rh = wx.get("rh") if wx.get("rh") is not None else 60.0
    p = wx.get("p_hpa") if wx.get("p_hpa") is not None else 1013.25
    z = atmos.zenith_attenuation(f, t_c, rh, p)
    out = {"f_ghz": f, "rho": z["rho"], "a_zen_db": z["total"], "a_zen_o2": z["oxygen"], "a_zen_h2o": z["vapour"]}
    hp = hpbw_of(setup)
    out["hpbw_deg"] = hp
    flux = flux_sfu or setup.get("flux_sfu") or 550.0
    gain = float(setup.get("gain_dbi", 0.0))
    eta = float(setup.get("eta_ap", 0.6))
    D = float(setup["D_m"])
    line = 10 ** (-float(setup.get("line_loss_db", 0.0)) / 10)
    # signed lunar phase: negative while waxing (Moon east of the Sun)
    waxing = ((s.moon.ra - s.sun.ra) % 360) < 180
    ph = -s.moon_phase_deg if waxing else s.moon_phase_deg
    for name, b in (("sun", s.sun), ("moon", s.moon)):
        a = atmos.slant_attenuation(z["total"], max(b.el_radio, 0.5)) if b.el > -1 else float("nan")
        tsk = atmos.sky_temperature(a, t_c) if b.el > -1 else float("nan")
        ts = tsys_cold(setup, tsk) if b.el > -1 else None
        tb = sky.sun_tb_from_flux(flux, f, b.diam_deg) if name == "sun" else sky.moon_tb(f, ph)
        ta_src = sky.antenna_temp_disk(tb, b.diam_deg * (sky.SUN_RADIO_DIAM_FACTOR if name == "sun" else 1), f, D, eta, hp)
        ta_src_rx = ta_src * 10 ** (-a / 10) * line if b.el > -1 else float("nan")
        out[name] = {"az": b.az, "el": b.el, "el_radio": b.el_radio, "dist_km": b.dist_km, "diam_deg": b.diam_deg,
                     "ra": b.ra, "dec": b.dec, "a_slant_db": a, "t_sky": tsk, "tb": tb, "t_src": ta_src_rx,
                     "tsys": ts["sys"] if ts else float("nan"),
                     "y_db": sky.y_db(ta_src_rx, ts["sys"]) if ts else float("nan")}
    out["sun_moon_deg"] = s.sun_moon_deg
    out["moon_phase_deg"] = ph
    out["moon_illum"] = s.moon_illum
    out["doppler_hz"] = s.doppler_hz_per_ghz * f
    out["spread_hz"] = s.spread_hz_per_ghz * f
    m = out["moon"]
    if m["el"] > -1 and setup.get("tx_w"):
        e = link.echo_snr(float(setup["tx_w"]), gain, f, m["dist_km"], m["diam_deg"], hp, m["a_slant_db"],
                          m["tsys"] + m["t_src"], out["spread_hz"])
        out["echo"] = e
    out["path_loss_db"] = link.path_loss_db(f, m["dist_km"])
    # G/T at the LNA input (the same reference point as the sun method): gain minus the feed → LNA loss
    out["gt_expected"] = (gain - float(setup.get("line_loss_db", 0.0)) - 10 * math.log10(out["sun"]["tsys"])
                          if out["sun"]["el"] > -1 else float("nan"))
    return out


def sun_gt_from_y(y_db: float, setup: dict, calc: dict, flux_sfu: float | None = None) -> float:
    """G/T (dB/K) from a measured sun Y-factor (standard sun-noise method, with atmosphere and beam-size
    correction): G/T = 8πk(Y−1) / (λ²·S·K·L)."""
    f = float(setup["band_ghz"])
    lam = sky.C / (f * 1e9)
    flux = flux_sfu or setup.get("flux_sfu") or 550.0
    tb = calc["sun"]["tb"]
    d = calc["sun"]["diam_deg"] * sky.SUN_RADIO_DIAM_FACTOR
    th = math.radians(d) / 2
    om_s = 2 * math.pi * (1 - math.cos(th))
    S = 2 * sky.K_B * tb * om_s / lam ** 2            # flux at f, W/m²/Hz
    hp = calc["hpbw_deg"]
    K = 1.133 * math.radians(hp) ** 2 * sky.disk_fill(d, hp) / om_s
    L = 10 ** (calc["sun"]["a_slant_db"] / 10)
    y = 10 ** (y_db / 10)
    return 10 * math.log10(8 * math.pi * sky.K_B * (y - 1) / (lam ** 2 * S * K) * L)


def evaluate_measurement(m: dict, setup: dict) -> dict:
    """Expected vs measured for one logged measurement (uses its stored snapshot)."""
    c = m.get("calc") or {}
    out = {}
    if not c:
        return out
    if m["kind"] in ("sun", "moon") and m.get("y_db") is not None:
        exp = c[m["kind"]]["y_db"]
        out["y_expected"] = exp
        out["y_delta"] = m["y_db"] - exp
        if m["kind"] == "sun":
            out["gt_measured"] = sun_gt_from_y(m["y_db"], setup, c)
            out["gt_expected"] = c.get("gt_expected")
            out["gt_delta"] = out["gt_measured"] - out["gt_expected"]
    if m["kind"] == "echo" and m.get("snr_db") is not None and c.get("echo"):
        out["snr_expected"] = c["echo"]["snr_1hz_db"]
        out["snr_delta"] = m["snr_db"] - out["snr_expected"]
    return out


def pointing_model(rows: list[dict]) -> dict | None:
    """Fit AZ/EL offsets measured at the Sun/Moon peak: constant + elevation terms. A constant AZ offset × cos(EL)
    is an encoder zero, an EL offset growing with cos(EL) is gravity sag, an AZ term with tan(EL) is a tilted
    axis (mount not level)."""
    pts = [(r["calc"][r["kind"]]["el"], r["az_off"], r["el_off"]) for r in rows
           if r.get("az_off") is not None and r.get("el_off") is not None and r.get("calc") and r["kind"] in ("sun", "moon")]
    if len(pts) < 3:
        return None
    el = np.radians([p[0] for p in pts])
    daz = np.array([p[1] for p in pts]) * np.cos(el)          # cross-elevation offset
    delv = np.array([p[2] for p in pts])
    A = np.vstack([np.ones_like(el), np.tan(el)]).T
    caz, *_ = np.linalg.lstsq(A, daz, rcond=None)
    B = np.vstack([np.ones_like(el), np.cos(el)]).T
    cel, *_ = np.linalg.lstsq(B, delv, rcond=None)
    return {"n": len(pts), "az_zero": float(caz[0]), "az_tilt": float(caz[1]), "el_zero": float(cel[0]),
            "el_sag": float(cel[1]), "rms_az": float(np.std(daz - A @ caz)), "rms_el": float(np.std(delv - B @ cel))}


def advice(rows: list[dict], setup: dict) -> list[str]:
    """Plain-language conclusions from the logged measurements of one setup."""
    tips = []
    ev = [(r, evaluate_measurement(r, setup)) for r in rows]
    sun = [(r, e) for r, e in ev if "gt_delta" in e]
    if sun:
        d = np.array([e["gt_delta"] for _, e in sun])
        el = np.array([r["calc"]["sun"]["el"] for r, _ in sun])
        tips.append(f"Sole: G/T misurato {np.mean([e['gt_measured'] for _, e in sun]):.2f} dB/K, atteso "
                    f"{np.mean([e['gt_expected'] for _, e in sun]):.2f} dB/K (differenza media {d.mean():+.2f} dB su {len(d)} misure).")
        if d.mean() < -1.0:
            tips.append("Ti mancano più di 1 dB rispetto al previsto: controlla nell'ordine fuoco del feed (spostamento "
                        "assiale), perdite tra feed e LNA, NF reale del preamplificatore, puntamento (correzione al picco) "
                        "e superficie della parabola.")
        if len(d) >= 4 and np.ptp(el) > 15:
            k = np.polyfit(el, d, 1)[0]
            if abs(k) * 30 > 0.5:
                tips.append(f"La differenza cambia con l'elevazione ({k * 10:+.2f} dB ogni 10°): " +
                            ("a bassa elevazione perdi più del previsto: rumore di terra (spillover) o ostacoli."
                             if k > 0 else "in alto perdi di più: deformazione della parabola o del supporto (gravità)."))
        rh = np.array([r.get("rh") or np.nan for r, _ in sun], float)
        ok = ~np.isnan(rh)
        if ok.sum() >= 4 and np.ptp(rh[ok]) > 20:
            k = np.polyfit(rh[ok], d[ok], 1)[0]
            tips.append(f"Con l'umidità la differenza varia di {k * 10:+.2f} dB ogni 10 %: " +
                        ("il modello atmosferico la descrive bene." if abs(k * 10) < 0.15 else
                         "più del modello: possibile condensa o acqua sul feed / sulla parabola, o radome bagnato."))
    pm = pointing_model(rows)
    if pm:
        tips.append(f"Puntamento ({pm['n']} misure): zero AZ {pm['az_zero']:+.3f}°, zero EL {pm['el_zero']:+.3f}°, "
                    f"inclinazione dell'asse {pm['az_tilt']:+.3f}°, cedimento {pm['el_sag']:+.3f}°·cos(EL); "
                    f"residui {pm['rms_az']:.3f}°/{pm['rms_el']:.3f}°. Correggi gli zeri nel programma di inseguimento.")
        hp = hpbw_of(setup)
        if max(abs(pm["az_zero"]), abs(pm["el_zero"])) > hp / 4:
            tips.append(f"Gli errori di zero superano 1/4 del fascio ({hp / 4:.3f}°): costano più di 0.7 dB in ricezione "
                        "e il doppio sulle eco.")
    echo = [(r, e) for r, e in ev if "snr_delta" in e]
    if echo:
        d = np.array([e["snr_delta"] for _, e in echo])
        tips.append(f"Eco: SNR misurato {d.mean():+.1f} dB rispetto al previsto (in 1 Hz, {len(d)} misure). "
                    "Se la differenza è stabile, è la riflettività efficace della Luna con il tuo fascio: EMELab la usa "
                    "per tarare le previsioni.")
    if not tips:
        tips.append("Registra almeno 4–5 misure di sole a elevazioni diverse (con il meteo) per avere le prime indicazioni.")
    return tips


def focus_fit(rows: list[dict]) -> dict | None:
    """Best feed position from a focusing scan (kind "focus": value = displacement in mm, y_db = sun/moon Y):
    parabola through the points, maximum and the Y lost at the starting position (0 mm)."""
    pts = [(r["value"], r["y_db"]) for r in rows if r["kind"] == "focus" and r.get("value") is not None
           and r.get("y_db") is not None]
    if len(pts) < 3:
        return None
    x = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    a, b, c = np.polyfit(x, y, 2)
    if a >= 0:
        return {"n": len(pts), "best_mm": None, "x": x.tolist(), "y": y.tolist(), "coef": [a, b, c]}
    xb = -b / (2 * a)
    return {"n": len(pts), "best_mm": float(xb), "y_best": float(c - b * b / (4 * a)), "gain_db": float(-b * b / (4 * a)),
            "x": x.tolist(), "y": y.tolist(), "coef": [float(a), float(b), float(c)]}


def improvements(setup: dict, el_deg: float = 30.0, t_c: float = 15.0, rh: float = 60.0) -> list[dict]:
    """Where the dB are: change of G/T (receive) and of the own-echo SNR for realistic improvements of the setup,
    from the same model used for the expected values."""
    from . import atmos
    f = float(setup["band_ghz"])
    lam = sky.C / (f * 1e9) * 1000                     # mm
    z = atmos.zenith_attenuation(f, t_c, rh)["total"]

    def figures(s, el=el_deg, rms=None, point_err=0.0):
        a = atmos.slant_attenuation(z, el)
        ts = tsys_cold(s, atmos.sky_temperature(a, t_c))["sys"]
        g = float(s.get("gain_dbi", 0)) - float(s.get("line_loss_db", 0))
        if rms is not None:                            # Ruze relative to the setup's own surface error
            r0 = float(s.get("rms_mm", 0.0))
            g += -10 * math.log10(math.e) * ((4 * math.pi * rms / lam) ** 2 - (4 * math.pi * r0 / lam) ** 2)
        hp = hpbw_of(s)
        pl = 12.04 * (point_err / hp) ** 2
        gt = g - pl - 10 * math.log10(ts)
        echo = 2 * (g - pl) - 2 * a - 10 * math.log10(ts)        # TX gain + RX gain, atmosphere twice, noise
        return gt, echo

    gt0, e0 = figures(setup)
    out = []

    def add(label, s=None, **kw):
        gt, e = figures(s or setup, **kw)
        out.append({"label": label, "d_gt": gt - gt0, "d_echo": e - e0})

    nf = float(setup.get("nf_db", 1.5))
    add(f"NF {nf:.1f} → {max(nf - 0.5, 0.3):.1f} dB", {**setup, "nf_db": max(nf - 0.5, 0.3)})
    ll = float(setup.get("line_loss_db", 0.0))
    if ll > 0:
        add(f"Perdite feed → LNA {ll:.2f} → {ll / 2:.2f} dB (LNA sul feed)", {**setup, "line_loss_db": ll / 2})
    r0 = float(setup.get("rms_mm", 0.3))
    add(f"Superficie della parabola {r0:.2f} → {r0 / 2:.2f} mm RMS", rms=r0 / 2)
    hp = hpbw_of(setup)
    add(f"Errore di puntamento di 1/4 del fascio ({hp / 4:.3f}°) corretto", point_err=0.0)
    out[-1]["d_gt"], out[-1]["d_echo"] = -(figures(setup, point_err=hp / 4)[0] - gt0), -(figures(setup, point_err=hp / 4)[1] - e0)
    add(f"Elevazione {el_deg:.0f}° → 60°", el=60.0)
    add(f"Elevazione {el_deg:.0f}° → 15°", el=15.0)
    dry = figures(setup)
    za = z
    z = atmos.zenith_attenuation(f, t_c, 30.0)["total"]
    gt_d, e_d = figures(setup)
    z = atmos.zenith_attenuation(f, t_c, 90.0)["total"]
    gt_w, e_w = figures(setup)
    z = za
    out.append({"label": f"Aria secca: umidità 30 % invece di {rh:.0f} %", "d_gt": gt_d - gt0, "d_echo": e_d - e0})
    out.append({"label": f"Aria umida: umidità 90 % invece di {rh:.0f} %", "d_gt": gt_w - gt0, "d_echo": e_w - e0})
    return out
