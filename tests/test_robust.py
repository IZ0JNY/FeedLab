"""Fabrication tolerances (Monte Carlo, critical dimensions) and openEMS-in-the-loop space mapping."""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from feedlab import drawing, explore, geometry, openems_sim, spacemap, tolerance

ROOT = Path(__file__).resolve().parent.parent
FAKE = Path(__file__).resolve().parent / "fake_openems"
SC = explore.Scenario(D_mm=630, fD=0.79)
F = 134.0


@pytest.fixture(scope="module")
def rep_loose():
    return tolerance.analyse("pickett_potter", F, SC, {}, "rx", tol_mm=0.05, n_verify=4)


def test_monte_carlo_surrogate_matches_solver(rep_loose):
    r = rep_loose
    assert r.n_runs == 1 + 2 * 4 + 6 + 4
    errs = dict(r.verify)
    assert errs["objective"] < 0.01 and errs["eta"] < 0.002
    assert r.stats["objective"]["mean"] <= r.nominal["objective"] + 1e-3        # tolerances cost, on average
    shares = [c["share"] for c in r.critical]
    assert shares == sorted(shares, reverse=True) and sum(shares) == pytest.approx(1.0, abs=1e-6)


def test_tighter_tolerance_better_yield(rep_loose):
    tight = tolerance.analyse("pickett_potter", F, SC, {}, "rx", tol_mm=0.01, n_verify=0)
    assert tight.yield_frac >= rep_loose.yield_frac
    assert tight.stats["objective"]["std"] < rep_loose.stats["objective"]["std"]


def test_recommended_tolerances_and_pdf(rep_loose, tmp_path):
    for c in rep_loose.critical:
        assert c["tol_ok"] > 0
    # the most critical dimension needs a tolerance no wider than the least critical one
    assert rep_loose.critical[0]["tol_ok"] <= rep_loose.critical[-1]["tol_ok"]
    geo = geometry.build("pickett_potter", F, fD=0.79)
    p = drawing.drawing_pdf(geo, tmp_path / "d.pdf", tolerances=rep_loose.critical)
    assert p.stat().st_size > 5000


def test_angle_tolerance_from_slant_length():
    dims = tolerance.dims_for("w2imu", 47.088, SC, {}, 0.05)
    a = [d for d in dims if d.key == "alpha"][0]
    assert a.unit == "°" and 0.05 < a.tol < 1.0


def test_space_mapping_finds_the_fullwave_optimum():
    """Synthetic 'full-wave': fast model with an efficiency bias peaked at a 6 % smaller aperture."""
    kind, f, keys = "pickett_potter", 47.088, ["Dap"]
    x0 = explore.base_values(kind, f, 0.79)

    def truth(over):
        r = explore.evaluate(kind, f, SC, over)
        m = spacemap.metrics_of(r, "rx")
        u = over.get("Dap", x0["Dap"]) / x0["Dap"] - 1
        eta = m["eta"] - 0.03 - 1.5 * (u + 0.06) ** 2
        dg = 10 * math.log10(eta / m["eta"])
        return {**m, "eta": eta, "objective": m["objective"] + dg, "g_over_t": m["g_over_t"] + dg,
                "gain_dbi": m["gain_dbi"] + dg, "s11_db": m["s11_db"] + 2.0}

    st = spacemap.new_study(kind, f, SC, "rx", keys, {}, max_iter=6, tol_mm=0.01)
    while spacemap.step(st, fullwave=lambda p: truth(p.over)) is not None:
        pass
    assert st.status in ("convergito", "massimo iterazioni")
    best = spacemap.best_point(st)
    grid = [truth({"Dap": x0["Dap"] * (1 + u)})["objective"] for u in np.linspace(-0.2, 0.2, 81)]
    assert best.fw["objective"] >= max(grid) - 0.01
    assert best.fw["objective"] > st.points[0].fw["objective"]
    # the bias of the first run is learnt
    a, _ = spacemap.correction(st)["s11_db"]
    assert a == pytest.approx(2.0, abs=0.05)


def test_space_mapping_reads_openems_results(tmp_path, monkeypatch):
    """Full chain with the fake openEMS: job script → results.json → full-wave metrics of a study point."""
    kind, f = "pickett_potter", 47.088
    st = spacemap.new_study(kind, f, SC, "rx", ["Dap"], {})
    geo = geometry.build(kind, f, fD=SC.fD)
    out = tmp_path / "job"
    p = openems_sim.make_deep_script(geo, out, openems_sim.DeepConfig(cells_per_lambda=12, ff_freqs=[f], sphere=False))
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(FAKE), str(ROOT)])
    r = subprocess.run([sys.executable, "-u", str(p)], cwd=out, capture_output=True, text=True, env=env, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    m = spacemap.fullwave_metrics(out / "results.json", st, {})
    assert 0.0 < m["eta"] < 1.0 and math.isfinite(m["objective"])
    st.points[0].job = str(out)
    saved = st.save(tmp_path)
    back = spacemap.SMStudy.load(saved)
    assert back.points[0].job == str(out) and back.keys == ["Dap"]
