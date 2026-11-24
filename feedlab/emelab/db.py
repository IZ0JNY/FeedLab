# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Local EMELab database (SQLite) in the user settings folder: station, setups per band and measurements.

Nothing here is ever uploaded: the file stays on this computer (export/import as CSV). Every time is stored
as ISO 8601 UTC ("2026-11-24T22:15:00Z")."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

KINDS = {
    "sun": "Rumore solare (Y sole / cielo freddo)",
    "moon": "Rumore lunare (Y luna / cielo freddo)",
    "cold_sky": "Cielo freddo (riferimento)",
    "ground": "Terra / orizzonte (Y terra / cielo freddo)",
    "echo": "Eco proprie (SNR)",
    "beacon": "Beacon / segnale di un'altra stazione",
    "qso": "QSO / tentativo",
    "focus": "Messa a fuoco (spostamento del feed)",
    "other": "Altro",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS station (id INTEGER PRIMARY KEY CHECK (id = 1), callsign TEXT, locator TEXT,
    lat REAL, lon REAL, height_m REAL, notes TEXT);
CREATE TABLE IF NOT EXISTS setups (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, band_ghz REAL, created_utc TEXT,
    data TEXT);
CREATE TABLE IF NOT EXISTS measurements (id INTEGER PRIMARY KEY AUTOINCREMENT, utc TEXT NOT NULL, setup_id INTEGER,
    band_ghz REAL, kind TEXT, y_db REAL, snr_db REAL, value REAL, unit TEXT, az_read REAL, el_read REAL,
    az_off REAL, el_off REAL, partner TEXT, notes TEXT,
    t_c REAL, rh REAL, p_hpa REAL, wind_ms REAL, rain_mmh REAL, cloud_pct REAL, wx_utc TEXT, wx_source TEXT,
    calc TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS m_utc ON measurements(utc);
"""

COLS = ["id", "utc", "setup_id", "band_ghz", "kind", "y_db", "snr_db", "value", "unit", "az_read", "el_read", "az_off",
        "el_off", "partner", "notes", "t_c", "rh", "p_hpa", "wind_ms", "rain_mmh", "cloud_pct", "wx_utc", "wx_source",
        "calc", "extra"]


def iso_utc(dt: datetime) -> str:
    d = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(s: str) -> datetime:
    return datetime.strptime(s.replace("Z", ""), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def default_path() -> Path:
    from .. import openems_local
    return openems_local.config_dir() / "emelab.sqlite"


class DB:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(self.path))
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)

    # station ---------------------------------------------------------------
    def station(self) -> dict:
        r = self.con.execute("SELECT * FROM station WHERE id = 1").fetchone()
        return dict(r) if r else {}

    def save_station(self, **kw):
        cur = {**self.station(), **kw, "id": 1}
        keys = ["id", "callsign", "locator", "lat", "lon", "height_m", "notes"]
        self.con.execute(f"INSERT OR REPLACE INTO station ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
                         [cur.get(k) for k in keys])
        self.con.commit()

    # setups ----------------------------------------------------------------
    def setups(self, band: float | None = None) -> list[dict]:
        q = "SELECT * FROM setups" + (" WHERE abs(band_ghz - ?) < 1" if band else "") + " ORDER BY band_ghz, id"
        rows = self.con.execute(q, (band,) if band else ()).fetchall()
        return [{**dict(r), **json.loads(r["data"] or "{}")} for r in rows]

    def save_setup(self, name: str, band_ghz: float, data: dict, setup_id: int | None = None) -> int:
        js = json.dumps(data)
        if setup_id:
            self.con.execute("UPDATE setups SET name=?, band_ghz=?, data=? WHERE id=?", (name, band_ghz, js, setup_id))
        else:
            cur = self.con.execute("INSERT INTO setups (name, band_ghz, created_utc, data) VALUES (?,?,?,?)",
                                   (name, band_ghz, iso_utc(datetime.now(timezone.utc)), js))
            setup_id = cur.lastrowid
        self.con.commit()
        return int(setup_id)

    def delete_setup(self, setup_id: int):
        self.con.execute("DELETE FROM setups WHERE id=?", (setup_id,))
        self.con.commit()

    # measurements ------------------------------------------------------------
    def add(self, **m) -> int:
        m = dict(m)
        if isinstance(m.get("utc"), datetime):
            m["utc"] = iso_utc(m["utc"])
        for k in ("calc", "extra"):
            if isinstance(m.get(k), dict):
                m[k] = json.dumps(m[k])
        keys = [k for k in COLS if k != "id" and k in m]
        cur = self.con.execute(f"INSERT INTO measurements ({','.join(keys)}) VALUES ({','.join('?' * len(keys))})",
                               [m[k] for k in keys])
        self.con.commit()
        return int(cur.lastrowid)

    def update(self, mid: int, **m):
        for k in ("calc", "extra"):
            if isinstance(m.get(k), dict):
                m[k] = json.dumps(m[k])
        keys = [k for k in m if k in COLS and k != "id"]
        self.con.execute(f"UPDATE measurements SET {','.join(k + '=?' for k in keys)} WHERE id=?",
                         [m[k] for k in keys] + [mid])
        self.con.commit()

    def delete(self, mid: int):
        self.con.execute("DELETE FROM measurements WHERE id=?", (mid,))
        self.con.commit()

    def measurements(self, band: float | None = None, kind: str | None = None) -> list[dict]:
        q, a = "SELECT * FROM measurements WHERE 1=1", []
        if band:
            q += " AND abs(band_ghz - ?) < 1"
            a.append(band)
        if kind:
            q += " AND kind = ?"
            a.append(kind)
        rows = self.con.execute(q + " ORDER BY utc", a).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            for k in ("calc", "extra"):
                d[k] = json.loads(d[k]) if d.get(k) else {}
            out.append(d)
        return out

    # CSV ----------------------------------------------------------------------
    def export_csv(self) -> str:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(COLS)
        for r in self.con.execute("SELECT * FROM measurements ORDER BY utc"):
            w.writerow([r[k] for k in COLS])
        return buf.getvalue()

    def import_csv(self, text: str) -> int:
        n = 0
        for row in csv.DictReader(io.StringIO(text)):
            m = {k: (row.get(k) if row.get(k) not in ("", None) else None) for k in COLS if k != "id"}
            if not m.get("utc"):
                continue
            for k in ("band_ghz", "y_db", "snr_db", "value", "az_read", "el_read", "az_off", "el_off", "t_c", "rh",
                      "p_hpa", "wind_ms", "rain_mmh", "cloud_pct"):
                if m.get(k) is not None:
                    m[k] = float(m[k])
            self.add(**m)
            n += 1
        return n
