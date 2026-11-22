"""The whole Streamlit app runs without exceptions — without openEMS, and with an (fake) openEMS installed and a
completed simulation, so that the deep-analysis views are rendered too. Skipped where streamlit is missing."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FAKE = Path(__file__).resolve().parent / "fake_openems"


def _errors(at):
    return [e.value for e in at.exception]


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("FEEDLAB_CONFIG", str(tmp_path / "cfg"))
    monkeypatch.setenv("FEEDLAB_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OPENEMS_INSTALL_PATH", raising=False)
    monkeypatch.setenv("FEEDLAB_LANG", "it")          # CI runners have an English locale
    monkeypatch.chdir(ROOT)
    return tmp_path


def test_app_runs_without_openems(isolated):
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    assert not at.exception, _errors(at)
    text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "openEMS" in text


def test_app_with_openems_and_results(isolated, monkeypatch):
    from feedlab import geometry, openems_local, openems_sim
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(FAKE), str(ROOT)]))
    root = isolated / "oems" / "openEMS"
    root.mkdir(parents=True)
    (root / openems_local.EXE).write_text("")
    openems_local.save_settings(openems_root=str(root), python=sys.executable)
    # one completed job (default app feed: Pickett-Potter 47.088 GHz)
    geo = geometry.build("pickett_potter", 47.088, fD=0.6)
    jd = openems_local.create_job(geo, openems_sim.DeepConfig(cells_per_lambda=15, sphere_step=6), label="smoke")
    r = subprocess.run([sys.executable, "-u", str(jd / json.loads((jd / "job.json").read_text())["script"])], cwd=jd,
                       capture_output=True, text=True, env=os.environ.copy(), timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    (jd / "runner.json").write_text(json.dumps({"state": "done"}))
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    assert not at.exception, _errors(at)
    text = " ".join(m.value for m in at.markdown) + " ".join(str(s.value) for s in at.success)
    assert "Binding Python funzionanti" in text
    labels = [m.label for m in at.metric]
    assert "Centro di fase" in labels and "G/T" in labels


@pytest.mark.parametrize("lang", ["en", "de", "fr", "es"])
def test_app_runs_in_every_language(isolated, lang):
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.session_state["lang"] = lang
    at.run()
    assert not at.exception, _errors(at)
    tabs = [t.label for t in at.tabs]
    assert tabs and not any("Procedura guidata" in t or "Progetto feed" in t for t in tabs), tabs
