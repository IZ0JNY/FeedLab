"""The f/D 0.4 feeds optimised with openEMS are project files (fdtd/results/feedlab/), not feed types: the list keeps
the historical feeds only, and a 0.4.28 project saved with «Feed 0.4 f/D» opens as an Axial Corrugated."""
import json
from pathlib import Path

import pytest

from feedlab import geometry, project

FILES = sorted((Path(__file__).resolve().parent.parent / "fdtd" / "results" / "feedlab").glob("*fD0.40*.feedlab.json"))


def test_no_feed_types_per_focal_length():
    assert not [k for k, v in geometry.FEED_TYPES.items() if "f/D" in v or k.startswith("fd04")]


@pytest.mark.parametrize("f", [10.368, 24.048])
def test_legacy_fd04_project_opens_as_axial_corrugated(f):
    S = {}
    p = {"inputs": {"f_ghz": f, "feed_kind": "fd04", "overrides": {"d1": 5.0},
                    "dish": {"kind": "prime", "D_mm": 3000.0, "fD": 0.4}}}
    project.apply(S, p)
    assert S["feed_kind"] == "axial_corrugated"
    over = S["overrides"]["axial_corrugated"]
    assert over["d1"] == 5.0                                           # the user's edits win
    assert over["pitch"] == pytest.approx(geometry.fd04_overrides(f)["pitch"])
    g = geometry.build("axial_corrugated", f, fD=0.4, **over)
    assert g.params["d1"] == pytest.approx(5.0)


def test_project_files_for_fd04():
    kinds = {json.loads(p.read_text(encoding="utf-8"))["inputs"]["feed_kind"] for p in FILES}
    assert {"axial_corrugated", "chaparral", "ve4ma", "large_w2imu"} <= kinds
    assert len(FILES) >= 16


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_project_files_open(path):
    p = project.load(path.read_text(encoding="utf-8"))
    S = {}
    project.apply(S, p)
    kind = S["feed_kind"]
    assert kind in geometry.FEED_TYPES
    g = geometry.build(kind, float(S["f_ghz"]), fD=0.4, **S["overrides"][kind])
    assert g.length > 0
