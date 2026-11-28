"""fdtd/ (openEMS iterative optimisation): families build valid geometries, the figure of merit on a real
openEMS result (W2IMU, f/D 0.6, 10.368 GHz, 14 cells/λ) and the cache key. No FDTD run here."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "fdtd"))
import fdtd_eval as fe  # noqa: E402
import optimize  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "openems_w2imu_fD060_14cpl.json"


@pytest.mark.parametrize("name", sorted(optimize.FAMILIES))
def test_families_build(name):
    fam = optimize.FAMILIES[name]
    assert len(fam.keys) == len(fam.bounds)
    for fD in (0.55, 0.7, 0.8):  # W2IMU range (B 1.22-1.9 λ)
        x0 = fam.seed(fD)
        assert len(x0) == len(fam.keys)
        for x in (x0, [b[0] for b in fam.bounds], [b[1] for b in fam.bounds]):
            geo = fam.build(x, 10.368, fD)
            assert geo.length > 0 and geo.r_aperture > geo.r_input * 0.99
            assert hasattr(geo, "polygons") and len(geo.polygons) >= 1


def test_w2imu_seed_is_literature():
    x = optimize.FAMILIES["w2imu"].seed(0.6)
    assert x[1] == pytest.approx(2.35 * 0.6)                 # B = 2.35 f/D (W1GHZ)
    assert x[2] == pytest.approx(44.6 / x[1])                # flare 44.6°·λ/B


def test_figure_of_merit_on_openems_result(tmp_path):
    shutil.copy(DATA, tmp_path / "results.json")
    r = fe.figure_of_merit(tmp_path, fe.EvalConfig(fD=0.6), length_mm=113.9)
    assert r["eta_f0"] == pytest.approx(0.759, abs=0.005)
    assert 0.70 < r["eta_mean"] < 0.78 and r["penalty"] == 0.0
    assert r["s11_max_db"] < -20
    for x in r["per_freq"]:
        assert x["eta"] <= x["eta_ill"] <= x["spill"] + 1e-9
    # a stricter match requirement is penalised
    r2 = fe.figure_of_merit(tmp_path, fe.EvalConfig(fD=0.6, s11_max_db=-30), length_mm=113.9)
    assert r2["fom"] < r["fom"]


def test_cache_key_depends_on_geometry_and_mesh():
    fam = optimize.FAMILIES["w2imu"]
    g1, g2 = fam.build(fam.seed(0.6), 10.368, 0.6), fam.build(fam.seed(0.7), 10.368, 0.7)
    c = fe.EvalConfig()
    assert fe._key(g1, c) == fe._key(fam.build(fam.seed(0.6), 10.368, 0.6), c)
    assert fe._key(g1, c) != fe._key(g2, c)
    assert fe._key(g1, c) != fe._key(g1, fe.EvalConfig(cells_per_lambda=24))


def test_prime_focus_blocking_lowers_fom(tmp_path):
    shutil.copy(DATA, tmp_path / "results.json")
    free = fe.figure_of_merit(tmp_path, fe.EvalConfig(fD=0.6), length_mm=113.9)
    blk = fe.figure_of_merit(tmp_path, fe.EvalConfig(fD=0.6, dish_diam_lambda=10.0), length_mm=113.9, block_mm=30.0)
    assert blk["eta_mean"] < free["eta_mean"]
    assert 0.9 < blk["per_freq"][1]["block"] < 1.0


@pytest.mark.parametrize("name", ["ve4ma", "chaparral", "axial_corrugated", "large_w2imu", "dualflare_wide"])
def test_export_overrides_rebuild_same_feed(name):
    """The FeedLab project overrides rebuild exactly the geometry simulated by the optimiser."""
    import export_feedlab
    from feedlab import geometry
    fam = optimize.FAMILIES[name]
    x = fam.seeds(0.4)[0]
    for f in (10.368, 24.048):
        kind, kw = export_feedlab.overrides(fam, x, f)
        a, b = fam.build(x, f, 0.4), geometry.build(kind, f, fD=0.4, **kw)
        assert a.profile == b.profile and a.blockage_diameter() == pytest.approx(b.blockage_diameter())
