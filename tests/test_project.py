"""Project file (.json) and project outputs (PDF, CSV, ZIP)."""
import io
import json
import zipfile

import pytest

from feedlab import dishes, geometry, project, report, wizard


@pytest.fixture
def proj_state(tmp_path, monkeypatch):
    monkeypatch.setenv("FEEDLAB_CONFIG", str(tmp_path / "cfg"))
    monkeypatch.setenv("FEEDLAB_HOME", str(tmp_path / "home"))
    dish = wizard.dish_from_catalog(next(d for d in dishes.CATALOG if "243" in d.model))
    S = {"f_ghz": 24.048, "dish": dish, "feed_kind": "iz0jny", "material": "Ottone CuZn39Pb3", "overrides": {},
         "wr_wg": "WR-42", "plate_rf": ("V", 9.48, 0.0, True), "fd_design": None}
    geo = geometry.build("iz0jny", 24.048, fD=dish.fD)
    return S, geo, project.build(S, geo, dish.fD)


def test_project_has_inputs_and_results(proj_state):
    S, geo, p = proj_state
    assert p["format"] == project.FORMAT and p["inputs"]["feed_kind"] == "iz0jny"
    r = p["results"]
    assert 50 < r["gain_dbi"] < 60 and 0.5 < r["eta"] < 0.9 and r["edge_taper_db"] > 8
    assert len(p["s11_sweep"]["f_ghz"]) == 21 and p["plate"]["wg"] == "WR-42"
    js = project.to_json(p)
    assert project.load(js)["results"]["gain_dbi"] == r["gain_dbi"]
    with pytest.raises(ValueError):
        project.load(json.dumps({"format": "altro"}))


def test_project_apply_restores_the_design(proj_state):
    S, geo, p = proj_state
    T = {}
    project.apply(T, project.load(project.to_json(p)))
    assert T["dish"].D_mm == S["dish"].D_mm and T["feed_kind"] == "iz0jny" and T["material"] == S["material"]
    assert T["overrides"] == {"iz0jny": {}}


def test_all_outputs_are_valid_pdfs(proj_state, tmp_path):
    from pypdf import PdfReader
    S, geo, p = proj_state
    docs = {"sims": report.sims_pdf(p), "dish": report.dish_pdf(p), "data": report.data_pdf(p),
            "openems": report.openems_pdf(p), "assembly": report.assembly_pdf(p, S),
            "feed": report.feed_pdf(p, geo, tmp_path), "plate": report.plate_pdf(S, p, tmp_path),
            "full": report.full_pdf(p, S, geo, tmp_path)}
    pages = {k: len(PdfReader(io.BytesIO(v)).pages) for k, v in docs.items()}
    assert all(n >= 1 for n in pages.values())
    assert pages["full"] >= pages["sims"] + pages["dish"] + pages["plate"] + pages["data"]
    csv = report.data_csv(p)
    assert "D_aperture" in csv and "gain_dbi" in csv
    z = zipfile.ZipFile(io.BytesIO(report.zip_all({"a.pdf": docs["sims"], "b.json": project.to_json(p)})))
    assert sorted(z.namelist()) == ["a.pdf", "b.json"]


def test_autosave_keeps_the_open_design(proj_state):
    S, geo, p = proj_state
    project.save_auto(p)
    assert project.load_auto()["inputs"]["feed_kind"] == "iz0jny"
