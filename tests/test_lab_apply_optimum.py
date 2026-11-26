"""«Applica l'ottimo al progetto» (Laboratorio) must carry the optimised dimensions to the lab sliders and to the
design used by Progetto feed, drawing, STEP and openEMS (bug in 0.4.27: the sliders went back to +0%)."""
import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest
from test_app_smoke import ROOT, _errors, _start, isolated  # noqa: F401


def test_apply_optimum_carries_dimensions(isolated):  # noqa: F811
    from feedlab import explore
    at = AppTest.from_file(str(ROOT / "feedlab_main.py"), default_timeout=600)
    at.run()
    _start(at)
    assert not at.exception, _errors(at)
    keys = [k for k, _, _ in explore.TUNABLE["w2imu"]]
    base = {k: at.slider(key=f"lab_w2imu_{k}").value for k in keys}
    next(m for m in at.multiselect if m.label == "Quote da ottimizzare").set_value(keys).run()
    next(s for s in at.slider if s.label == "Valutazioni massime").set_value(12).run()
    next(b for b in at.button if b.label.startswith("Ottimizza per")).click().run()
    assert not at.exception, _errors(at)
    over = at.session_state["opt"][0]
    assert any(abs(over[k] / base[k] - 1) > 1e-3 for k in over), over      # the optimiser moved something
    btn = next(b for b in at.button if b.label == "Applica l'ottimo al progetto")
    btn.click().run()
    assert not at.exception, _errors(at)
    for k, v in over.items():
        assert at.slider(key=f"lab_w2imu_{k}").value == pytest.approx(v, rel=1e-6), k
    assert at.session_state["overrides"]["w2imu"] == pytest.approx(over)
    # Progetto feed shows the optimised dimensions (fields are rebuilt from the new geometry)
    names = {"A": "A_input", "B": "B_aperture", "C": "C_phasing", "alpha": "flare_half_deg"}
    for k, v in over.items():
        f = next(n for n in at.number_input if n.key == f"in_w2imu_{names[k]}")
        assert f.value == pytest.approx(v, abs=1e-3), k
    # one more interaction elsewhere: the optimum must stay applied
    at.run()
    assert not at.exception, _errors(at)
    assert at.session_state["overrides"]["w2imu"] == pytest.approx(over)
    for k, v in over.items():
        assert at.slider(key=f"lab_w2imu_{k}").value == pytest.approx(v, rel=1e-6), k
