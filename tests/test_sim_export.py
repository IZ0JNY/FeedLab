"""Scripts for other simulators: stand-alone openEMS script and CST Studio Suite VBA macro."""
import io
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from feedlab import geometry, sim_export

FAKE = Path(__file__).resolve().parent / "fake_openems"
KINDS = ["w2imu", "pickett_potter", "ve4ma", "chaparral", "conical", "axial_corrugated", "fd04", "iz0jny"]


def _geo(kind, f=10.368):
    return geometry.build(kind, f, fD=0.4 if kind == "fd04" else 0.6)


def test_openems_zip_runs_without_feedlab(tmp_path):
    """the exported script needs only openEMS (here the fake bindings), not FeedLab"""
    z = zipfile.ZipFile(io.BytesIO(sim_export.openems_zip(_geo("w2imu"), band_pct=5, cells_per_lambda=12, n_ff=3)))
    names = z.namelist()
    script = [n for n in names if n.startswith("sim_") and n.endswith(".py")]
    assert script and "feed.json" in names and "LEGGIMI_README.txt" in names
    z.extractall(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(PYTHONPATH=str(FAKE), FEEDLAB_HOME=str(tmp_path / "h"), FAKE_PC_MM="2.5")
    r = subprocess.run([sys.executable, "-u", script[0]], cwd=tmp_path, env=env,
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "results.json").exists()


def _blocks(macro):
    """the command blocks the macro adds to the History List: (caption, VBA lines)"""
    out, cur = [], []
    for ln in macro.splitlines():
        ln = ln.strip()
        m = re.fullmatch(r'sCmd = sCmd & "(.*)" & vbLf', ln)
        if m:
            body = m.group(1)
            assert '"' not in body.replace('""', ""), ln          # every quote doubled inside the VBA string
            cur.append(body.replace('""', '"'))
        elif ln.startswith("AddToHistory"):
            out.append((re.match(r'AddToHistory "([^"]*)", sCmd', ln).group(1), cur))
            cur = []
    return out


@pytest.mark.parametrize("kind", KINDS)
def test_cst_macro_structure(kind):
    geo = _geo(kind)
    m = sim_export.cst_macro(geo, band_pct=10, cells_per_lambda=20, n_ff=3)
    m.encode("ascii")
    assert "Sub Main ()" in m and m.rstrip().endswith("End Sub")
    blocks = _blocks(m)
    caps = [c for c, _ in blocks]
    assert len(caps) == len(set(caps))                             # History List captions are unique
    for _, lines in blocks:
        assert sum(x.startswith("With ") for x in lines) == sum(x == "End With" for x in lines)
        for x in lines:
            assert not re.search(r'"\d+,\d+"', x)                  # decimal point, never comma
    rot = [ls for c, ls in blocks if c.startswith("define rotate")]
    assert len(rot) == 1 + len(geo.polygons)
    for ls in rot:
        pts = [tuple(map(float, re.findall(r'"([-\d.]+)"', x))) for x in ls if x.strip().startswith((".Point", ".LineTo"))]
        assert len(pts) >= 4 and pts[0] == pts[-1]                 # closed profile
        assert all(a != b for a, b in zip(pts, pts[1:]))           # no zero-length edge
        assert min(p[0] for p in pts) >= 0                         # r >= 0: right of the axis
    assert sum(c.startswith("boolean add") for c in caps) == len(geo.polygons)
    port = dict(blocks)["define port: 1"]
    assert any("zmin" in x for x in port)
    ff = [c for c in caps if c.startswith("define farfield monitor")]
    assert len(ff) == 3 and any("f=10.368" in c for c in ff)
    fr = dict(blocks)["define frequency range"][0]
    lo, hi = map(float, re.findall(r'"([\d.]+)"', fr))
    assert lo == pytest.approx(10.368 * 0.9, rel=1e-5) and hi == pytest.approx(10.368 * 1.1, rel=1e-5)


def test_cst_zip_contents():
    z = zipfile.ZipFile(io.BytesIO(sim_export.cst_zip(_geo("fd04"), name="mio_feed")))
    assert set(z.namelist()) == {"mio_feed.bas", "LEGGIMI_README.txt", "feed.json"}


def test_rect_horn_refused():
    g = geometry.build_rect(10.368, 0.6, "WR-90")
    assert not sim_export.supported(g)
    with pytest.raises(ValueError):
        sim_export.cst_macro(g)
    with pytest.raises(ValueError):
        sim_export.openems_zip(g)
