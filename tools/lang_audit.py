# Usage: python3 tools/lang_audit.py <repo> <it|en> <out.json>  then  python3 tools/lang_check.py <out.json> <it|en>
"""Render the whole FeedLab app in one language (AppTest) for several feeds/bands, collect every visible text
(widgets, markdown, tables, plotly figures, matplotlib texts) and report the ones with words of the other language."""
import json, os, re, sys, subprocess, tempfile
from pathlib import Path
ROOT = Path(sys.argv[1]); LANG = sys.argv[2]; OUT = sys.argv[3]
tmp = Path(tempfile.mkdtemp())
os.environ.update(FEEDLAB_CONFIG=str(tmp/"cfg"), FEEDLAB_HOME=str(tmp/"home"), FEEDLAB_LANG=LANG,
                  FEEDLAB_NO_UPDATE_CHECK="1")
os.environ.pop("OPENEMS_INSTALL_PATH", None)
os.chdir(ROOT); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"tests"/"fake_openems"))
# fake openEMS + one completed job so that the full-wave views are rendered too
from feedlab import geometry, openems_local, openems_sim
os.environ["PYTHONPATH"] = os.pathsep.join([str(ROOT/"tests"/"fake_openems"), str(ROOT)])
root = tmp/"oems"/"openEMS"; root.mkdir(parents=True); (root/openems_local.EXE).write_text("")
openems_local.save_settings(openems_root=str(root), python=sys.executable, language=LANG)
geo = geometry.build("w2imu", 24.048, fD=0.6)
jd = openems_local.create_job(geo, openems_sim.DeepConfig(cells_per_lambda=15, sphere_step=6), label="audit")
subprocess.run([sys.executable, "-u", str(jd/json.loads((jd/"job.json").read_text())["script"])], cwd=jd,
               capture_output=True, env=os.environ.copy(), timeout=600)
(jd/"runner.json").write_text(json.dumps({"state": "done"}))

import matplotlib; matplotlib.use("Agg")
import matplotlib.text as mtext
MPL = set()
_orig = mtext.Text.draw
def _draw(self, r, *a, **k):
    t = self.get_text()
    if t: MPL.add(t)
    return _orig(self, r, *a, **k)
mtext.Text.draw = _draw
from streamlit.testing.v1 import AppTest
from google.protobuf.json_format import MessageToDict

TEXTS = {}
SKIP = {"id", "key", "formId", "deltaPath", "elementHash", "src", "url", "type", "format", "cssClass", "fragmentId",
        "activeScriptHash", "scriptRunId", "icon", "color", "fontsrc"}
def walk(obj, where):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP: continue
            if isinstance(v, str) and v.startswith("{"):
                try: walk(json.loads(v), where + ":json"); continue
                except Exception: pass
            walk(v, where)
    elif isinstance(obj, list):
        for v in obj: walk(v, where)
    elif isinstance(obj, str) and len(obj) < 5000 and not obj.startswith(("data:", "http")) \
            and re.search(r"[A-Za-zÀ-ú]{3}", obj):
        TEXTS.setdefault(obj, where)

def collect(at, where):
    for node in at._tree.root_block if False else []: pass
    def rec(n):
        p = getattr(n, "proto", None)
        if p is not None:
            try: walk(MessageToDict(p), where)
            except Exception: pass
        v = getattr(n, "value", None)
        try:
            import pandas as pd
            if isinstance(v, pd.DataFrame):
                for c in v.columns: TEXTS.setdefault(str(c), where + ":df")
                for x in v.astype(str).values.ravel(): TEXTS.setdefault(x, where + ":df")
        except Exception: pass
        for c in (getattr(n, "children", {}) or {}).values(): rec(c)
    rec(at._tree)

def start(at, band, feed, maker="Channel Master", model="243"):
    b = at.selectbox(key="band_sel"); b.select(next(o for o in b.options if o.startswith(band))).run()
    at.selectbox(key="material_sel").select("Ottone CuZn39Pb3").run()
    at.selectbox(key="dish_maker").select(maker).run()
    m = at.selectbox(key=f"dish_model_{maker}"); m.select(next(o for o in m.options if model in o)).run()
    k = next(s for s in at.selectbox if s.key and "feed_kind" in str(s.key) or s.label in ("Tipo di feed", "Feed type"))
    if feed: k.select(feed).run()
    return at

kinds = list(geometry.FEED_TYPES)
runs = [("24.048", k) for k in kinds] + [("10.368", "w2imu"), ("10.368", "rect_horn"), ("47.088", "w2imu"), ("47.088", "iz0jny")]
for band, fk in runs:
    if True:
        at = AppTest.from_file(str(ROOT/"feedlab_main.py"), default_timeout=900); at.run()
        try:
            start(at, band, fk)
            for btn in at.button:
                if "🔎" in str(btn.label):
                    btn.click().run(); break
        except Exception as e:
            print("start failed", band, fk, e)
        collect(at, f"{band}/{fk}")
        for e in at.exception: print("EXC", band, fk, e.value[:300])
json.dump({"texts": TEXTS, "mpl": sorted(MPL)}, open(OUT, "w"), ensure_ascii=False, indent=0)
print(len(TEXTS), len(MPL))
