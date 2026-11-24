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
    """One row per Moon pass (consecutive samples above the limits, also across midnight UTC): start, end,
    duration and the best moment (highest echo SNR with the Sun away from the Moon)."""
    passes, cur = [], []
    step = _step(samples)
    for s in samples:
        if cur and (s["utc"] - cur[-1]["utc"]).total_seconds() > 1.5 * step:
            passes.append(cur)
            cur = []
        cur.append(s)
    if cur:
        passes.append(cur)
    rows = []
    for ss in passes:
        good = [s for s in ss if s["sun_moon_deg"] >= sun_min_deg] or ss
        best = max(good, key=lambda s: (s["snr_1hz"] if s["snr_1hz"] is not None else -s["a_slant_db"]))
        rows.append({"day": ss[0]["utc"].date(), "start": ss[0]["utc"], "end": ss[-1]["utc"],
                     "hours": (ss[-1]["utc"] - ss[0]["utc"]).total_seconds() / 3600,
                     "best_utc": best["utc"], "best_el": max(s["el"] for s in ss), "dist_km": best["dist_km"],
                     "snr_1hz": best["snr_1hz"], "snr_spread": best["snr_spread"], "spread_hz": best["spread_hz"],
                     "sun_moon_deg": min(s["sun_moon_deg"] for s in ss), "a_slant_db": best["a_slant_db"]})
    return rows


def _step(samples):
    """Sampling step: the smallest gap between consecutive samples (the first two may straddle a gap)."""
    d = [(b["utc"] - a["utc"]).total_seconds() for a, b in zip(samples, samples[1:])]
    return min(d) if d else 600.0


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


MONTHS_IT = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]


def monthly_climate(lat: float, lon: float, setup: dict, el_deg: float = 30.0, year_end: datetime | None = None) -> list[dict]:
    """Monthly mean weather of the last 12 months (Open-Meteo archive) → zenith attenuation, sky temperature at
    el_deg and the change of G/T and of the echo SNR relative to the best month."""
    import json
    import math
    import urllib.parse
    from . import atmos, weather
    end = astro.utc(year_end or datetime.now(timezone.utc)) - timedelta(days=7)
    start = end - timedelta(days=365)
    q = {"latitude": f"{lat:.3f}", "longitude": f"{lon:.3f}", "start_date": str(start.date()), "end_date": str(end.date()),
         "daily": "temperature_2m_mean,relative_humidity_2m_mean", "timezone": "UTC"}
    js = json.loads(weather._get("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(q), 20))
    d = js["daily"]
    acc = {}
    for t, tc, rh in zip(d["time"], d["temperature_2m_mean"], d["relative_humidity_2m_mean"]):
        if tc is None or rh is None:
            continue
        acc.setdefault(int(t[5:7]), []).append((tc, rh))
    return monthly_from_means({m: (sum(a for a, _ in v) / len(v), sum(b for _, b in v) / len(v)) for m, v in acc.items()},
                              setup, el_deg)


def monthly_from_means(means: dict, setup: dict, el_deg: float = 30.0) -> list[dict]:
    import math
    from . import analysis, atmos
    f = float(setup["band_ghz"])
    rows = []
    for m in sorted(means):
        tc, rh = means[m]
        z = atmos.zenith_attenuation(f, tc, rh)["total"]
        a = atmos.slant_attenuation(z, el_deg)
        tsky = atmos.sky_temperature(a, tc)
        ts = analysis.tsys_cold(setup, tsky)["sys"]
        rows.append({"month": m, "t_c": tc, "rh": rh, "rho": atmos.vapour_density(tc, rh), "a_zen_db": z, "a_db": a,
                     "t_sky": tsky, "tsys": ts})
    if rows:
        best_ts = min(r["tsys"] for r in rows)
        best_a = min(r["a_db"] for r in rows)
        for r in rows:
            r["d_gt_db"] = -10 * math.log10(r["tsys"] / best_ts) - (r["a_db"] - best_a)
            r["d_echo_db"] = r["d_gt_db"] - (r["a_db"] - best_a)        # echo: atmosphere twice + noise
    return rows
