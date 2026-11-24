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


def _start(at, band="24.048", feed="w2imu"):
    """The app starts blank: choose band, material, dish (catalogue) and feed type like a user."""
    b = next(s for s in at.selectbox if s.label == "Banda")
    b.select(next(o for o in b.options if o.startswith(band))).run()
    at.selectbox(key="material_sel").select("Ottone CuZn39Pb3").run()
    at.selectbox(key="dish_maker").select("Channel Master").run()
    m = at.selectbox(key="dish_model_Channel Master")
    m.select(next(o for o in m.options if "243" in o)).run()
    if feed:
        next(s for s in at.selectbox if s.label == "Tipo di feed").select(feed).run()
    return at


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("FEEDLAB_CONFIG", str(tmp_path / "cfg"))
    monkeypatch.setenv("FEEDLAB_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("OPENEMS_INSTALL_PATH", raising=False)
    monkeypatch.setenv("FEEDLAB_LANG", "it")          # CI runners have an English locale
    monkeypatch.setenv("FEEDLAB_NO_UPDATE_CHECK", "1")  # no network call / new-version popup in tests
    monkeypatch.chdir(ROOT)
    return tmp_path


def test_app_runs_without_openems(isolated):
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    assert not at.exception, _errors(at)
    text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "openEMS" in text
    assert any("Per iniziare seleziona" in i.value for i in at.info)       # blank start: nothing chosen yet
    _start(at)
    assert not at.exception, _errors(at)
    assert not any("Per iniziare seleziona" in i.value for i in at.info)


def test_app_with_openems_and_results(isolated, monkeypatch):
    from feedlab import geometry, openems_local, openems_sim
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(FAKE), str(ROOT)]))
    root = isolated / "oems" / "openEMS"
    root.mkdir(parents=True)
    (root / openems_local.EXE).write_text("")
    openems_local.save_settings(openems_root=str(root), python=sys.executable)
    # one completed job (the feed chosen in _start: W2IMU 24.048 GHz)
    geo = geometry.build("w2imu", 24.048, fD=0.6)
    jd = openems_local.create_job(geo, openems_sim.DeepConfig(cells_per_lambda=15, sphere_step=6), label="smoke")
    r = subprocess.run([sys.executable, "-u", str(jd / json.loads((jd / "job.json").read_text())["script"])], cwd=jd,
                       capture_output=True, text=True, env=os.environ.copy(), timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
    (jd / "runner.json").write_text(json.dumps({"state": "done"}))
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    _start(at)
    assert not at.exception, _errors(at)
    text = " ".join(m.value for m in at.markdown) + " ".join(str(s.value) for s in at.success)
    assert "Binding Python funzionanti" in text
    labels = [m.label for m in at.metric]
    assert "Centro di fase" in labels and "G/T" in labels


@pytest.mark.parametrize("lang", ["en"])
def test_app_runs_in_every_language(isolated, lang):
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.session_state["lang"] = lang
    at.run()
    assert not at.exception, _errors(at)
    tabs = [t.label for t in at.tabs]
    assert tabs and not any("Procedura guidata" in t or "Progetto feed" in t for t in tabs), tabs


def test_square_base_choice_in_sidebar(isolated):
    """At 24 GHz the sidebar offers the square base (WR-42 flange, 22.41 mm); the feed is rebuilt with it."""
    from feedlab import geometry
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    band = next(s for s in at.selectbox if s.label == "Banda")
    band.select(next(o for o in band.options if o.startswith("24.048"))).run()
    base = next(r for r in at.radio if r.label == "Base del feed")
    base.set_value("square").run()
    assert not at.exception, _errors(at)
    assert geometry.BASE == {"shape": "square", "wg": "WR-42", "thickness": None}
    assert any("22.41" in c.value for c in at.caption)
    geometry.BASE.update({"shape": "round", "wg": None})


@pytest.mark.parametrize("band,guides,square", [("10.368", ["WR-90", "WR-75"], True), ("24.048", ["WR-42"], True),
                                                ("47.088", ["WR-22", "WR-19"], False)])
def test_waveguide_choice_per_band(isolated, band, guides, square):
    """One waveguide choice in the sidebar, limited to the usual guides of the band: it sizes the matching plate
    (circular → WR) and, for square flanges, allows the square base."""
    from feedlab import geometry
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    _start(at, band)
    wr = next(s for s in at.selectbox if s.label == "Guida d'onda rettangolare")
    assert list(wr.options) == guides
    wr.select(guides[-1]).run()
    assert not at.exception, _errors(at)
    assert any(f"**Guida rettangolare:** {guides[-1]}" in m.value for m in at.markdown)
    assert any(r.label == "Base del feed" for r in at.radio) == square
    geometry.BASE.update({"shape": "round", "wg": None})


def test_dimension_edit_with_apply_button(isolated):
    """Editing a dimension and pressing "Applica modifiche" rebuilds the feed (e.g. the input guide length)."""
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    _start(at, feed="iz0jny")
    at.number_input(key="in_iz0jny_input_length").set_value(10.0).run()
    next(b for b in at.button if b.label == "Applica modifiche").click().run()
    assert not at.exception, _errors(at)
    assert at.session_state["overrides"]["iz0jny"]["input_length"] == 10.0
    assert at.number_input(key="in_iz0jny_input_length").value == 10.0


def test_square_flange_feed_counterbore_in_plate_tab(isolated):
    """24 GHz, WR-42, square base, holes + counterbores in the feed base: no error (0.4.17 'max() … empty')."""
    from feedlab import geometry
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    _start(at)
    next(r for r in at.radio if r.label == "Base del feed").set_value("square").run()
    next(c for c in at.checkbox if "Fori di fissaggio" in c.label).check().run()
    at.checkbox(key="mount_cbore").check().run()
    assert not at.exception, _errors(at)
    assert not [e.value for e in at.error]
    assert any("Feed con la base forata" in s.value for s in at.subheader)
    geometry.BASE.update({"shape": "round", "wg": None})
    geometry.MOUNT.clear()
    geometry.MOUNT.update({"wg": None})
