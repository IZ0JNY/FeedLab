# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Weather at the time of a measurement, always with its UTC timestamp and its source.

Sources: Open-Meteo (free, no account: forecast API for the last days and the next 16, archive API for older
dates) and an optional personal station. The station address is typed by the user in EMELab and saved only in
the local settings of this computer: it is never written in the program or sent anywhere else.
Supported station formats: Meteotemplate (live JSON), Cumulus realtime.txt, Weather Display clientraw.txt and
a plain JSON with the usual names."""
from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

HOURLY = ["temperature_2m", "relative_humidity_2m", "surface_pressure", "dew_point_2m", "cloud_cover",
          "precipitation", "wind_speed_10m", "wind_gusts_10m", "total_column_integrated_water_vapour"]


def _get(url: str, timeout: float = 10.0) -> bytes:
    from ..updates import _contexts
    err = None
    for _, ctx in _contexts():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FeedLab-EMELab"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read()
        except Exception as e:                    # try the next TLS context
            err = e
            if url.startswith("http://"):
                break
    raise err


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def open_meteo(lat: float, lon: float, dt: datetime, timeout: float = 10.0) -> dict:
    """Hourly model values interpolated to dt (UTC)."""
    dt = _utc(dt)
    old = dt < datetime.now(timezone.utc) - timedelta(days=60)
    base = "https://archive-api.open-meteo.com/v1/archive" if old else "https://api.open-meteo.com/v1/forecast"
    day = dt.date()
    q = {"latitude": f"{lat:.3f}", "longitude": f"{lon:.3f}", "hourly": ",".join(HOURLY), "timezone": "UTC",
         "wind_speed_unit": "ms", "start_date": str(day - timedelta(days=0)), "end_date": str(day + timedelta(days=1))}
    js = json.loads(_get(base + "?" + urllib.parse.urlencode(q), timeout))
    if js.get("error"):
        raise RuntimeError(js.get("reason", "Open-Meteo"))
    h = js["hourly"]
    times = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in h["time"]]
    i = max(0, min(len(times) - 2, int((dt - times[0]).total_seconds() // 3600)))
    w = (dt - times[i]).total_seconds() / 3600.0

    def val(k):
        a, b = (h.get(k) or [None] * len(times))[i], (h.get(k) or [None] * len(times))[i + 1]
        if a is None or b is None:
            return a if b is None else b
        return a + (b - a) * w
    return {"t_c": val("temperature_2m"), "rh": val("relative_humidity_2m"), "p_hpa": val("surface_pressure"),
            "dew_c": val("dew_point_2m"), "cloud_pct": val("cloud_cover"), "rain_mmh": val("precipitation"),
            "wind_ms": val("wind_speed_10m"), "gust_ms": val("wind_gusts_10m"),
            "iwv_kg_m2": val("total_column_integrated_water_vapour"),
            "wx_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "wx_source": "Open-Meteo"}


def open_meteo_series(lat: float, lon: float, start: datetime, days: int, timeout: float = 10.0) -> list[dict]:
    """Hourly forecast (or recent past) for the planner: humidity at 24 GHz matters a lot."""
    start = _utc(start)
    q = {"latitude": f"{lat:.3f}", "longitude": f"{lon:.3f}", "hourly": ",".join(HOURLY[:4] + ["cloud_cover",
         "precipitation"]), "timezone": "UTC", "start_date": str(start.date()),
         "end_date": str((start + timedelta(days=days)).date())}
    js = json.loads(_get("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q), timeout))
    h = js["hourly"]
    return [{"utc": datetime.fromisoformat(t).replace(tzinfo=timezone.utc), "t_c": h["temperature_2m"][i],
             "rh": h["relative_humidity_2m"][i], "p_hpa": h["surface_pressure"][i],
             "cloud_pct": h["cloud_cover"][i], "rain_mmh": h["precipitation"][i]} for i, t in enumerate(h["time"])]


# ------------------------------------------------------------------ personal station
def _num(x):
    try:
        v = float(str(x).replace(",", "."))
        return None if math.isnan(v) else v
    except Exception:
        return None


def parse_station(text: str) -> dict:
    """Current values from a station file. Returns °C, %, hPa, m/s, mm/h and the station time (UTC) if present."""
    s = text.strip()
    out = {}
    if s.startswith("{"):
        js = json.loads(s)
        js = {str(k).lower(): v for k, v in js.items()}
        pick = lambda *ks: next((_num(js[k]) for k in ks if k in js and _num(js[k]) is not None), None)
        out = {"t_c": pick("t", "temp", "temperature", "outtemp"), "rh": pick("h", "hum", "humidity", "outhumidity"),
               "p_hpa": pick("p", "press", "pressure", "barometer"), "dew_c": pick("d", "dew", "dewpoint"),
               "rain_mmh": pick("rr", "rainrate", "rain_rate")}
        w = pick("w", "wind", "windspeed", "wind_speed")       # Meteotemplate: km/h
        if w is not None:
            out["wind_ms"] = w / 3.6 if "w" in js or "wind" in js else w
        ts = pick("u", "time", "timestamp", "unix", "datetime")
        if ts and ts > 1e9:
            out["station_utc"] = datetime.fromtimestamp(ts, timezone.utc)
        out["format"] = "json"
    elif s.startswith("12345"):                               # Weather Display clientraw.txt
        f = s.split()
        out = {"wind_ms": _num(f[1]) * 0.514444 if _num(f[1]) is not None else None, "t_c": _num(f[4]),
               "rh": _num(f[5]), "p_hpa": _num(f[6]), "rain_mmh": _num(f[10]), "dew_c": _num(f[72]) if len(f) > 72 else None,
               "format": "clientraw"}
    else:                                                     # Cumulus realtime.txt: date time temp hum dew wspeed …
        f = s.split()
        if len(f) > 10:
            out = {"t_c": _num(f[2]), "rh": _num(f[3]), "dew_c": _num(f[4]), "p_hpa": _num(f[10]),
                   "rain_mmh": _num(f[8]), "format": "cumulus"}
    return {k: v for k, v in out.items() if v is not None}


def station_now(url: str, timeout: float = 8.0) -> dict:
    """Read the personal station. For a Meteotemplate site the live file next to the home page is tried too."""
    tried = []
    urls = [url]
    if not url.rstrip("/").endswith((".txt", ".json", ".php")):
        root = url.rstrip("/") + "/"
        urls = [root + "meteotemplateLive.txt", root + "realtime.txt", root + "clientraw.txt"]
    for u in urls:
        try:
            d = parse_station(_get(u, timeout).decode("utf-8", "replace"))
            if d.get("t_c") is not None or d.get("rh") is not None:
                now = datetime.now(timezone.utc)
                t = d.pop("station_utc", now)
                d.update(wx_utc=t.strftime("%Y-%m-%dT%H:%M:%SZ"), wx_source="stazione personale")
                return d
        except Exception as e:
            tried.append(f"{u}: {e}")
    raise RuntimeError("; ".join(tried) or "nessun dato")
