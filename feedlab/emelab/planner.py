# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Moon windows for one station, mutual windows with another station, and a ranking of the next days."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import analysis, astro


def windows(station: dict, setup: dict, start: datetime, days: int = 14, step_min: int = 10, min_el: float = 10.0,
            partner: tuple[float, float] | None = None, wx_series: list[dict] | None = None,
            partner_min_el: float = 10.0) -> list[dict]:
    """Samples every step_min minutes while the Moon is above min_el (and above the partner's horizon)."""
    start = astro.utc(start)
    wx_by_hour = {w["utc"].replace(minute=0, second=0, microsecond=0): w for w in (wx_series or [])}
    out = []
    n = int(days * 24 * 60 / step_min)
    for i in range(n):
        t = start + timedelta(minutes=i * step_min)
        s = astro.sky(t, station["lat"], station["lon"], station.get("height_m") or 0.0)
        if s.moon.el < min_el:
            continue
        pel = None
        if partner:
            ps = astro.sky(t, partner[0], partner[1], 0.0)
            pel = ps.moon.el
            if pel < partner_min_el:
                continue
        wx = wx_by_hour.get(t.replace(minute=0, second=0, microsecond=0))
        c = analysis.snapshot(station, setup, t, wx)
        out.append({"utc": t, "el": s.moon.el, "az": s.moon.az, "dist_km": s.moon.dist_km, "partner_el": pel,
                    "sun_moon_deg": s.sun_moon_deg, "spread_hz": c["spread_hz"], "doppler_hz": c["doppler_hz"],
                    "a_slant_db": c["moon"]["a_slant_db"], "tsys_moon": c["moon"]["tsys"] + c["moon"]["t_src"],
                    "snr_1hz": c.get("echo", {}).get("snr_1hz_db"), "snr_spread": c.get("echo", {}).get("snr_spread_db"),
                    "rh": (wx or {}).get("rh")})
    return out


def daily(samples: list[dict], sun_min_deg: float = 10.0) -> list[dict]:
    """One row per UTC day: window, best moment (highest echo SNR with the Sun away from the Moon)."""
    days = {}
    for s in samples:
        days.setdefault(s["utc"].date(), []).append(s)
    rows = []
    for d, ss in sorted(days.items()):
        good = [s for s in ss if s["sun_moon_deg"] >= sun_min_deg] or ss
        best = max(good, key=lambda s: (s["snr_1hz"] if s["snr_1hz"] is not None else -s["a_slant_db"]))
        rows.append({"day": d, "start": ss[0]["utc"], "end": ss[-1]["utc"], "hours": len(ss) * (
            (ss[1]["utc"] - ss[0]["utc"]).total_seconds() / 3600 if len(ss) > 1 else 0),
            "best_utc": best["utc"], "best_el": best["el"], "dist_km": best["dist_km"],
            "snr_1hz": best["snr_1hz"], "snr_spread": best["snr_spread"], "spread_hz": best["spread_hz"],
            "sun_moon_deg": min(s["sun_moon_deg"] for s in ss), "a_slant_db": best["a_slant_db"]})
    return rows


def perigees(start: datetime, days: int = 400) -> list[tuple[datetime, float, str]]:
    """Moon perigees and apogees (geocentric distance minima/maxima) in the period: the echo is up to 2.2 dB
    stronger at perigee."""
    import numpy as np
    start = astro.utc(start)
    ts = [start + timedelta(hours=3 * i) for i in range(int(days * 8))]
    d = np.array([astro.moon_geocentric_km(t) for t in ts])
    out = []
    for i in range(1, len(d) - 1):
        kind = "perigeo" if d[i] < d[i - 1] and d[i] <= d[i + 1] else "apogeo" if d[i] > d[i - 1] and d[i] >= d[i + 1] else None
        if kind:                                   # refine to the hour with a parabola through the 3 samples
            a, b, c = d[i - 1], d[i], d[i + 1]
            den = a - 2 * b + c
            x = 0.5 * (a - c) / den if den else 0.0
            out.append((ts[i] + timedelta(hours=3 * x), float(b - 0.25 * (a - c) * x), kind))
    return out
