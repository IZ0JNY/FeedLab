"""Fabrication tolerances: Monte Carlo yield, critical dimensions and robust optimisation.

A design that is optimal only at its exact nominal dimensions is worthless if the workshop cannot hold
them. This module answers three questions with FeedLab's fast solver (mode matching, ~0.5 s per variant):

  1. How much do efficiency, gain, G/T and S11 spread when every machined dimension varies within its
     tolerance? (Monte Carlo on a quadratic surrogate fitted to 1 + 2N + N(N-1)/2 solver runs, checked
     against a few direct solver runs.)
  2. Which dimensions are critical, and which tolerance does each one really need? (Variance shares and
     the largest tolerance that keeps the loss of that dimension within its share of a loss budget.)
  3. Which design keeps its performance best within the tolerances? (Nelder-Mead on mean - k·sigma of the
     objective instead of the nominal peak.)

Tolerance model: each dimension is either uniform within ±t (default: any value in the band is equally
likely, pessimistic) or normal with ±t = 3σ (a capable CNC process).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import explore, geometry
from .drawing import tolerance_mm

# machined dimensions per feed type: (override key, geometry param key, label, "len" | "ang")
TOL_KEYS = {
    "open_circular": [("diam", "diam", "Ø guida", "len"), ("length", "length", "Lunghezza", "len")],
    "w2imu": [("A", "A_input", "Ø ingresso A", "len"), ("B", "B_aperture", "Ø apertura B", "len"),
              ("C", "C_phasing", "Lunghezza di fase C", "len"), ("alpha", "flare_half_deg", "Semiangolo flare", "ang")],
    "pickett_potter": [("Di", "Di_input", "Ø ingresso", "len"), ("Ds", "Ds_step", "Ø dopo il gradino", "len"),
                       ("Dap", "D_aperture", "Ø apertura", "len"), ("flare_length", "flare_length", "Lunghezza flare", "len")],
    "conical": [("d_in", "d_input", "Ø ingresso", "len"), ("D", "D_aperture", "Ø apertura", "len"),
                ("alpha", "flare_half_deg", "Semiangolo flare", "ang")],
}
TOL_KEYS["w2imu_oe2igl"] = TOL_KEYS["w2imu"]
TOL_KEYS["large_w2imu"] = TOL_KEYS["w2imu"]
TOL_KEYS["skobelev"] = TOL_KEYS["pickett_potter"]

TOL_CLASSES_MM = [0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.5]
METRICS = ("objective", "eta", "gain_dbi", "g_over_t", "s11_db", "edge_taper_db")


@dataclass
class Dim:
    key: str
    label: str
    unit: str          # "mm" | "°"
    nominal: float
    tol: float         # half-width of the tolerance band in the dimension's unit


@dataclass
class Surrogate:
    """Quadratic model y = y0 + g·u + ½ uᵀHu per metric, u = (x - x0)/t (dimension change in tolerances)."""
    dims: list
    y0: dict
    g: dict
    H: dict
    n_runs: int

    def predict(self, U: np.ndarray, metric: str) -> np.ndarray:
        g, H = self.g[metric], self.H[metric]
        return self.y0[metric] + U @ g + 0.5 * np.einsum("ni,ij,nj->n", U, H, U)


@dataclass
class ToleranceReport:
    dims: list
    dist: str
    samples: dict                   # metric -> array of Monte Carlo values
    nominal: dict
    stats: dict                     # metric -> {mean, std, p05, p95}
    yield_frac: float
    spec: dict
    critical: list                  # per dimension: dict(label, share, d_obj, d_s11, tol_now, tol_ok)
    verify: list = field(default_factory=list)   # (metric, max |surrogate - solver|)
    n_runs: int = 0


def dims_for(kind: str, f_ghz: float, sc: explore.Scenario, over: dict, tol_mm: float | None = None,
             wall=None, fD_design=None, tol_by_key: dict | None = None) -> list[Dim]:
    if kind not in TOL_KEYS:
        raise ValueError("analisi di tolleranza disponibile per i feed a guida circolare (non VE4MA/Chaparral/rettangolare)")
    t = tol_mm if tol_mm is not None else tolerance_mm(f_ghz)
    geo = explore._geo(kind, f_ghz, fD_design or sc.fD, over, wall)
    out = []
    for key, pk, label, typ in TOL_KEYS[kind]:
        x0 = float(geo.params[pk])
        tk = (tol_by_key or {}).get(key, t)
        if typ == "ang":
            slant = float(geo.params.get("flare_length", 5 * geo.lam)) / max(math.cos(math.radians(x0)), 0.2)
            out.append(Dim(key, label, "°", x0, math.degrees(tk / slant)))
        else:
            out.append(Dim(key, label, "mm", x0, tk))
    return out


def _metrics(r: explore.Result, objective: str) -> dict:
    return {"objective": explore.metric(r, objective), "eta": r.eta, "gain_dbi": r.gain_dbi, "g_over_t": r.g_over_t,
            "s11_db": r.s11_db if r.s11_db is not None else np.nan, "edge_taper_db": r.edge_taper_db}


def _run(kind, f, sc, over, dims, u, wall, fD_design, objective):
    o = dict(over)
    for d, ui in zip(dims, u):
        o[d.key] = d.nominal + ui * d.tol
    return _metrics(explore.evaluate(kind, f, sc, o, wall, fD_design), objective)


def fit_surrogate(kind, f_ghz, sc, over, dims, objective="rx", wall=None, fD_design=None, step: float = 1.0,
                  progress=None) -> Surrogate:
    """Centre, ±step on each axis (gradient + curvature) and (+,+) on each pair (cross terms)."""
    n = len(dims)
    plan = [np.zeros(n)]
    for i in range(n):
        for s in (1, -1):
            u = np.zeros(n); u[i] = s * step; plan.append(u)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    for i, j in pairs:
        u = np.zeros(n); u[i] = step; u[j] = step; plan.append(u)
    res = []
    for k, u in enumerate(plan):
        res.append(_run(kind, f_ghz, sc, over, dims, u, wall, fD_design, objective))
        if progress:
            progress(k + 1, len(plan))
    y0, g, H = {}, {}, {}
    for m in METRICS:
        c = res[0][m]
        gm, Hm = np.zeros(n), np.zeros((n, n))
        for i in range(n):
            yp, ym = res[1 + 2 * i][m], res[2 + 2 * i][m]
            gm[i] = (yp - ym) / (2 * step)
            Hm[i, i] = (yp - 2 * c + ym) / step ** 2
        for p, (i, j) in enumerate(pairs):
            ypp = res[1 + 2 * n + p][m]
            yi, yj = res[1 + 2 * i][m], res[1 + 2 * j][m]
            Hm[i, j] = Hm[j, i] = (ypp - yi - yj + c) / step ** 2
        y0[m], g[m], H[m] = c, gm, Hm
    return Surrogate(dims, y0, g, H, len(plan))


def _draw(n_dims, n, dist, rng):
    if dist == "normal":
        return rng.normal(0.0, 1.0 / 3.0, (n, n_dims))
    return rng.uniform(-1.0, 1.0, (n, n_dims))


def analyse(kind, f_ghz, sc, over, objective="rx", tol_mm=None, dist="uniform", n_samples=5000, n_verify=6,
            loss_budget_db=0.1, s11_limit_db=-18.0, wall=None, fD_design=None, seed=1, tol_by_key=None,
            progress=None) -> ToleranceReport:
    """Monte Carlo of the manufactured feed. Yield: objective within loss_budget_db of nominal and S11 below the limit."""
    dims = dims_for(kind, f_ghz, sc, over, tol_mm, wall, fD_design, tol_by_key)
    sur = fit_surrogate(kind, f_ghz, sc, over, dims, objective, wall, fD_design, progress=progress)
    rng = np.random.default_rng(seed)
    U = _draw(len(dims), n_samples, dist, rng)
    samples = {m: sur.predict(U, m) for m in METRICS}
    stats = {m: {"mean": float(np.nanmean(v)), "std": float(np.nanstd(v)), "p05": float(np.nanpercentile(v, 5)),
                 "p95": float(np.nanpercentile(v, 95))} for m, v in samples.items()}
    ok = samples["objective"] >= sur.y0["objective"] - loss_budget_db
    if not np.all(np.isnan(samples["s11_db"])):
        ok &= samples["s11_db"] <= s11_limit_db
    # critical dimensions: variance share (first order + curvature) and the tolerance each one needs
    var_u = 1.0 / 3.0 if dist == "uniform" else 1.0 / 9.0
    gO, HO = sur.g["objective"], sur.H["objective"]
    contrib = np.array([gO[i] ** 2 * var_u + 0.5 * HO[i, i] ** 2 * var_u ** 2 for i in range(len(dims))])
    share = contrib / contrib.sum() if contrib.sum() > 0 else np.zeros(len(dims))
    budget_each = loss_budget_db / math.sqrt(len(dims))
    critical = []
    for i, d in enumerate(dims):
        worst = max(-(gO[i] * s + 0.5 * HO[i, i]) for s in (1, -1))      # objective loss at ±t (in dB-like units)
        gs, hs = sur.g["s11_db"][i], sur.H["s11_db"][i, i]
        d_s11 = max(gs * s + 0.5 * hs for s in (1, -1)) if not np.isnan(gs) else float("nan")
        # largest scale a (tolerance = a·t) with loss(a) = |g| a + ½|h| a² <= budget_each
        a_g, a_h = abs(gO[i]), abs(HO[i, i])
        if a_g < 1e-12 and a_h < 1e-12:
            a = 50.0
        elif a_h < 1e-12:
            a = budget_each / a_g
        else:
            a = (-a_g + math.sqrt(a_g ** 2 + 2 * a_h * budget_each)) / a_h
        need = d.tol * a
        if d.unit == "mm":
            cls = [c for c in TOL_CLASSES_MM if c <= need]
            tol_ok = cls[-1] if cls else TOL_CLASSES_MM[0]
        else:
            tol_ok = round(need, 3)
        critical.append({"key": d.key, "label": d.label, "unit": d.unit, "nominal": d.nominal, "tol_now": d.tol,
                         "share": float(share[i]), "d_obj": float(max(worst, 0.0)), "d_s11": float(d_s11),
                         "tol_ok": float(tol_ok)})
    critical.sort(key=lambda c: -c["share"])
    verify = []
    if n_verify:
        Uv = _draw(len(dims), n_verify, dist, np.random.default_rng(seed + 1))
        direct = [_run(kind, f_ghz, sc, over, dims, u, wall, fD_design, objective) for u in Uv]
        for m in ("objective", "eta", "s11_db"):
            pred = sur.predict(Uv, m)
            true = np.array([r[m] for r in direct])
            if not np.all(np.isnan(true)):
                verify.append((m, float(np.nanmax(np.abs(pred - true)))))
    return ToleranceReport(dims, dist, samples, dict(sur.y0), stats, float(np.mean(ok)),
                           {"loss_budget_db": loss_budget_db, "s11_limit_db": s11_limit_db,
                            "tol_mm": tol_mm if tol_mm is not None else tolerance_mm(f_ghz), "objective": objective},
                           critical, verify, sur.n_runs + n_verify)


def robust_score(kind, f_ghz, sc, over, objective="rx", tol_mm=None, k_sigma=2.0, dist="uniform", wall=None,
                 fD_design=None) -> tuple[float, float, float, dict]:
    """Mean - k·σ of the objective within the tolerances (diagonal quadratic model, 2N+1 runs)."""
    dims = dims_for(kind, f_ghz, sc, over, tol_mm, wall, fD_design)
    n = len(dims)
    c = _run(kind, f_ghz, sc, over, dims, np.zeros(n), wall, fD_design, objective)
    var_u = 1.0 / 3.0 if dist == "uniform" else 1.0 / 9.0
    mean, var = c["objective"], 0.0
    for i in range(n):
        u = np.zeros(n); u[i] = 1.0
        yp = _run(kind, f_ghz, sc, over, dims, u, wall, fD_design, objective)["objective"]
        ym = _run(kind, f_ghz, sc, over, dims, -u, wall, fD_design, objective)["objective"]
        gi, hi = (yp - ym) / 2, yp - 2 * c["objective"] + ym
        mean += 0.5 * hi * var_u
        var += gi ** 2 * var_u + 0.5 * hi ** 2 * var_u ** 2
    sd = math.sqrt(max(var, 0.0))
    return mean - k_sigma * sd, mean, sd, c


def robust_optimize(kind, f_ghz, sc, start_over, objective="rx", keys=None, tol_mm=None, k_sigma=2.0,
                    max_eval=25, s11_limit_db=-18.0, wall=None, fD_design=None, progress=None):
    """Nelder-Mead on mean - k·σ (tolerance-aware) instead of the nominal peak. Each step costs 2N+1 runs."""
    from scipy.optimize import minimize
    cur = {**explore.base_values(kind, f_ghz, fD_design or sc.fD, wall), **start_over}
    tun = {k: sp for k, _, sp in explore.TUNABLE[kind]}
    keys = keys or list(tun)[:2]
    calls = {"n": 0, "best": None}

    def f_obj(x):
        calls["n"] += 1
        over = dict(start_over)
        for k, v in zip(keys, x):
            over[k] = cur[k] * (1 + float(np.clip(v, -tun[k], tun[k])))
        try:
            score, mean, sd, c = robust_score(kind, f_ghz, sc, over, objective, tol_mm, k_sigma, "uniform", wall, fD_design)
        except Exception:
            return 1e3
        val = -score
        if not np.isnan(c["s11_db"]) and c["s11_db"] > s11_limit_db:
            val += (c["s11_db"] - s11_limit_db) * 0.5
        if calls["best"] is None or val < calls["best"][0]:
            calls["best"] = (val, over, {"score": score, "mean": mean, "sd": sd, **c})
        if progress:
            progress(calls["n"], max_eval, score)
        return val

    x0 = np.zeros(len(keys))
    minimize(f_obj, x0, method="Nelder-Mead", options={"maxfev": max_eval, "initial_simplex":
             np.vstack([x0] + [np.eye(len(keys))[i] * 0.05 for i in range(len(keys))]), "xatol": 0.003, "fatol": 0.003})
    return calls["best"][1], calls["best"][2]
