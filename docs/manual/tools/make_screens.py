"""Screenshots of the app in every language for the user manuals: docs/manual/img/<lang>/NN_*.png

    python docs/manual/tools/make_screens.py [it en de …]

Starts FeedLab (Streamlit) with FEEDLAB_LANG=<lang> and a fresh settings folder, then drives it with
Playwright (screens.js): guided procedure → Pickett-Potter on the Gibertini OP 65 at 47 GHz → every tab.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from feedlab import i18n  # noqa: E402

HERE = Path(__file__).resolve().parent


def labels(lang):
    i18n.set_lang(lang)
    t = lambda s: i18n.tr(s, lang)
    return {"find": t("Trova il feed migliore"), "use": t("Usa questo feed"),
            "tol": t("🎲 Analizza tolleranze (≈ 20 simulazioni rapide)"),
            "tolhead": t("🎯 Tolleranze di lavorazione e resa"),
            "holes": t("Fori di fissaggio guida → piastrina → feed"), "ftype": t("Tipo di feed"), "crit": t("Quote critiche")}


def run(lang, port=8700):
    out = ROOT / "docs" / "manual" / "img" / lang
    cfg = tempfile.mkdtemp(prefix="feedlab_cfg_")
    env = {**os.environ, "FEEDLAB_LANG": lang, "FEEDLAB_CONFIG": cfg}
    srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "feedlab" / "app.py"),
                            "--server.port", str(port), "--server.headless", "true"], env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=2)
                break
            except Exception:
                time.sleep(1)
        lf = Path(cfg) / "labels.json"
        lf.write_text(json.dumps(labels(lang), ensure_ascii=False), encoding="utf-8")
        subprocess.run(["node", str(HERE / "screens.js"), f"http://localhost:{port}", str(out), str(lf)], check=True,
                       env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True,
                                                                        text=True).stdout.strip()})
    finally:
        srv.terminate()
    return out


if __name__ == "__main__":
    for i, lang in enumerate(sys.argv[1:] or list(i18n.LANGS)):
        print(lang, run(lang, 8700 + i))
