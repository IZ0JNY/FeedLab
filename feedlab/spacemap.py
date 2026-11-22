"""openEMS in the loop: space mapping (output/response correction) of the fast model.

The fast solver (mode matching + aperture integration) explores; a few full-wave openEMS runs check the
candidates; the measured differences correct the fast model, which is optimised again:

    corrected(x) = fast(x) + Δ(x),   Δ(x) = a + b·u,   u = relative change of the tuned dimensions

With one full-wave run Δ is a constant (bias); with two or more it also gets a linear part (least squares
with a small ridge, so that two close runs cannot produce wild slopes). Corrected quantities: dish efficiency
η (gain and G/T follow from it) and S11 in dB. The loop stops when the full-wave objective improves by less
than `tol_db` between two iterations and the dimensions change by less than the fabrication tolerance, or
after `max_iter` full-wave runs.

A study is a JSON file in FeedLab's openEMS work folder: it survives closing FeedLab (the openEMS jobs run
detached) and is advanced when the app sees that the last job has finished.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from . import explore, geometry


@dataclass
class SMPoint:
    over: dict                       # tuned dimensions (override keys)
    fast: dict                       # fast-model metrics
    fw: dict | None = None           # full-wave metrics (when the openEMS job has finished)
    job: str = ""                    # openEMS job folder


@dataclass
class SMStudy:
    id: str
    kind: str
    f_ghz: float
    scenario: dict
    objective: str
    keys: list
    base_over: dict
    wall: float | None = None
    fD_design: float | None = None
    s11_limit_db: float = -18.0
    tol_mm: float = 0.02
    tol_db: float = 0.03
    max_iter: int = 5
    points: list = field(default_factory=list)
    status: str = "in corso"         # in corso | convergito | massimo iterazioni | errore
    created: float = field(default_factory=time.time)
    note: str = ""

    # -------------------------------------------------- persistence
    def save(self, folder: str | Path) -> Path:
        p = Path(folder) / f"spacemap_{self.id}.json"
        d = asdict(self)
        p.write_text(json.dumps(d, indent=1, default=float))
        return p

    @staticmethod
    def load(path: str | Path) -> "SMStudy":
        d = json.loads(Path(path).read_text())
        pts = [SMPoint(**p) for p in d.pop("points", [])]
        s = SMStudy(**d)
        s.points = pts
        return s

    @property
    def sc(self) -> explore.Scenario:
        return explore.Scenario(**self.scenario)

    def x0(self) -> dict:
        return {**explore.base_values(self.kind, self.f_ghz, self.fD_design or self.sc.fD, self.wall), **self.base_over}


def metrics_of(r: explore.Result, objective: str) -> dict:
    return {"objective": explore.metric(r, objective), "eta": r.eta, "gain_dbi": r.gain_dbi, "g_over_t": r.g_over_t,
            "s11_db": r.s11_db if r.s11_db is not None else float("nan"), "edge_taper_db": r.edge_taper_db,
            "pc_mm": r.pc_mm}


def fullwave_metrics(results_path: str | Path, study: SMStudy, over: dict) -> dict:
    """Same dish formulas as the fast model, applied to the openEMS pattern and S11 at f0."""
    from . import deep_analysis
    r = deep_analysis.load(results_path)
    ff = r.ff_at(study.f_ghz)
    geo = explore._geo(study.kind, study.f_ghz, study.fD_design or study.sc.fD, over, study.wall)
    i0 = int(np.argmin(np.abs(r.freq_ghz - study.f_ghz)))
    s11 = float(r.s11_db[i0])
    res = explore.performance(study.kind, study.f_ghz, study.sc, geo, ff.pattern(), s11)
    return metrics_of(res, study.objective)


# -------------------------------------------------- correction model
def _u(study: SMStudy, over: dict) -> np.ndarray:
    x0 = study.x0()
    return np.array([over.get(k, x0[k]) / x0[k] - 1.0 for k in study.keys])


def correction(study: SMStudy, ridge: float = 1e-3) -> dict:
    """Δ = a + b·u for η and S11 from the points that have full-wave results."""
    pts = [p for p in study.points if p.fw]
    out = {}
    for m in ("eta", "s11_db"):
        rows = [(p, p.fw[m] - p.fast[m]) for p in pts if not (math.isnan(p.fw[m]) or math.isnan(p.fast[m]))]
        if not rows:
            out[m] = (0.0, np.zeros(len(study.keys)))
            continue
        d = np.array([r[1] for r in rows])
        if len(rows) == 1:
            out[m] = (float(d[0]), np.zeros(len(study.keys)))
            continue
        U = np.array([_u(study, r[0].over) for r in rows])
        A = np.hstack([np.ones((len(rows), 1)), U])
        reg = np.diag([0.0] + [ridge] * len(study.keys))
        coef = np.linalg.solve(A.T @ A + reg, A.T @ d)
        out[m] = (float(coef[0]), coef[1:])
    return out


def corrected(study: SMStudy, r: explore.Result, over: dict, corr: dict) -> dict:
    u = _u(study, over)
    a, b = corr["eta"]
    eta_c = max(r.eta + a + float(b @ u), 1e-4)
    dg = 10 * math.log10(eta_c / max(r.eta, 1e-9))
    a2, b2 = corr["s11_db"]
    s11 = (r.s11_db + a2 + float(b2 @ u)) if r.s11_db is not None else float("nan")
    g, gt = r.gain_dbi + dg, r.g_over_t + dg
    obj = {"tx": g, "rx": gt, "eme": g + gt}[study.objective]
    return {"objective": obj, "eta": eta_c, "gain_dbi": g, "g_over_t": gt, "s11_db": s11,
            "edge_taper_db": r.edge_taper_db, "pc_mm": r.pc_mm}


def next_candidate(study: SMStudy, max_eval: int = 30, evaluate=None) -> tuple[dict, dict]:
    """Optimise fast + correction from the best full-wave point; returns (over, fast metrics)."""
    from scipy.optimize import minimize
    evaluate = evaluate or explore.evaluate
    corr = correction(study)
    done = [p for p in study.points if p.fw]
    start = max(done, key=lambda p: p.fw["objective"]).over if done else dict(study.base_over)
    x0 = study.x0()
    tun = {k: sp for k, _, sp in explore.TUNABLE[study.kind]}
    best = {"v": None}

    def over_of(x):
        o = dict(start)
        for k, v in zip(study.keys, x):
            o[k] = x0[k] * (1 + float(np.clip(v, -tun[k], tun[k])))
        return o

    def f_obj(x):
        o = over_of(x)
        try:
            r = evaluate(study.kind, study.f_ghz, study.sc, o, study.wall, study.fD_design)
        except Exception:
            return 1e3
        c = corrected(study, r, o, corr)
        val = -c["objective"]
        if not math.isnan(c["s11_db"]) and c["s11_db"] > study.s11_limit_db:
            val += (c["s11_db"] - study.s11_limit_db) * 0.5
        if best["v"] is None or val < best["v"][0]:
            best["v"] = (val, o, metrics_of(r, study.objective), c)
        return val

    xs = np.array([start.get(k, x0[k]) / x0[k] - 1.0 for k in study.keys])
    minimize(f_obj, xs, method="Nelder-Mead", options={"maxfev": max_eval, "initial_simplex":
             np.vstack([xs] + [xs + np.eye(len(study.keys))[i] * 0.04 for i in range(len(study.keys))]),
             "xatol": 0.002, "fatol": 0.003})
    return best["v"][1], best["v"][2]


def _dist(study: SMStudy, a: dict, b: dict) -> float:
    x0 = study.x0()
    return max(abs(a.get(k, x0[k]) - b.get(k, x0[k])) for k in study.keys)


def check_converged(study: SMStudy) -> str:
    done = [p for p in study.points if p.fw]
    if len(done) >= 2:
        a, b = done[-2], done[-1]
        if abs(b.fw["objective"] - a.fw["objective"]) < study.tol_db and _dist(study, a.over, b.over) < study.tol_mm:
            return "convergito"
    if len(done) >= study.max_iter:
        return "massimo iterazioni"
    return "in corso"


def new_study(kind, f_ghz, sc: explore.Scenario, objective, keys, base_over, wall=None, fD_design=None,
              s11_limit_db=-18.0, tol_mm=0.02, max_iter=5) -> SMStudy:
    if kind not in geometry.MODEMATCH_OK or kind not in explore.TUNABLE:
        raise ValueError("space mapping disponibile per i feed a guida circolare simulati dal modello rapido")
    sid = time.strftime("%Y%m%d-%H%M%S")
    s = SMStudy(sid, kind, float(f_ghz), dict(sc.__dict__), objective, list(keys), dict(base_over), wall, fD_design,
                s11_limit_db, tol_mm, max_iter=max_iter)
    r = explore.evaluate(kind, f_ghz, sc, base_over, wall, fD_design)
    s.points.append(SMPoint(dict(base_over), metrics_of(r, objective)))
    return s


def step(study: SMStudy, fullwave=None, evaluate=None) -> SMPoint | None:
    """Advance the study: read finished full-wave results, update the status, propose the next point.
    `fullwave(point) -> metrics | None` returns the openEMS metrics of a point when its run is finished
    (default: the job folder's results.json). Returns the new point to simulate, or None."""
    fullwave = fullwave or (lambda p: fullwave_metrics(Path(p.job) / "results.json", study, p.over)
                            if p.job and (Path(p.job) / "results.json").exists() else None)
    for p in study.points:
        if p.fw is None:
            m = fullwave(p)
            if m is None:
                return None              # still running
            p.fw = m
    study.status = check_converged(study)
    if study.status != "in corso":
        return None
    over, fast = next_candidate(study, evaluate=evaluate)
    if any(p.fw and _dist(study, p.over, over) < study.tol_mm for p in study.points):
        study.status = "convergito"          # the corrected optimum is a point already checked full-wave
        return None
    pt = SMPoint(over, fast)
    study.points.append(pt)
    return pt


def best_point(study: SMStudy) -> SMPoint | None:
    done = [p for p in study.points if p.fw]
    return max(done, key=lambda p: p.fw["objective"]) if done else None


def list_studies(folder: str | Path) -> list[SMStudy]:
    out = []
    for p in sorted(Path(folder).glob("spacemap_*.json"), reverse=True):
        try:
            out.append(SMStudy.load(p))
        except Exception:
            pass
    return out
