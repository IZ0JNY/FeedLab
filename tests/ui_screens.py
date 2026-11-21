"""Screenshots of the app (CI review): main page and every part of the openEMS tab, with a fake openEMS
installed and one completed simulation. Needs: streamlit, playwright, Microsoft Edge.

    python tests/ui_screens.py OUTPUT_DIR
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAKE = Path(__file__).resolve().parent / "fake_openems"


def prepare(tmp: Path) -> dict:
    env = os.environ.copy()
    env.update({"FEEDLAB_CONFIG": str(tmp / "cfg"), "FEEDLAB_HOME": str(tmp / "home"),
                "PYTHONPATH": os.pathsep.join([str(FAKE), str(ROOT)])})
    os.environ.update(env)
    sys.path[:0] = [str(ROOT)]
    from feedlab import geometry, openems_local, openems_sim
    root = tmp / "oems" / "openEMS"
    root.mkdir(parents=True)
    (root / openems_local.EXE).write_text("")
    openems_local.save_settings(openems_root=str(root), python=sys.executable)
    geo = geometry.build("pickett_potter", 47.088, fD=0.6)
    for cells, done in ((20, True), (30, False)):
        jd = openems_local.create_job(geo, openems_sim.DeepConfig(cells_per_lambda=cells, sphere_step=4),
                                      label=f"{cells} celle/λ", study="convergenza")
        if done:
            script = jd / json.loads((jd / "job.json").read_text())["script"]
            subprocess.run([sys.executable, "-u", str(script)], cwd=jd, env=env, check=True, capture_output=True)
            (jd / "runner.json").write_text(json.dumps({"state": "done"}))
    return env


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    env = prepare(tmp)
    port = 8799
    srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "streamlit_app.py"), "--server.port",
                            str(port), "--server.headless", "true", "--browser.gatherUsageStats", "false"],
                           cwd=ROOT, env=env)
    try:
        for _ in range(120):
            try:
                if urllib.request.urlopen(f"http://127.0.0.1:{port}/_stcore/health", timeout=2).read() == b"ok":
                    break
            except Exception:
                time.sleep(1)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(channel="msedge")
            pg = b.new_page(viewport={"width": 1440, "height": 1000})
            pg.goto(f"http://127.0.0.1:{port}")
            pg.wait_for_selector("text=FeedLab", timeout=120000)
            pg.wait_for_timeout(8000)
            pg.screenshot(path=str(out / "01_home.png"), full_page=False)
            pg.get_by_role("tab", name="🖥️ Full-wave openEMS").click()
            pg.wait_for_timeout(4000)
            try:
                pg.get_by_text("Reinstalla o aggiorna openEMS").click()
                pg.wait_for_timeout(1500)
            except Exception:
                pass
            pg.screenshot(path=str(out / "02_openems_install.png"), full_page=True)
            for i, name in enumerate(["② Nuova analisi", "③ Simulazioni", "④ Risultati"], start=3):
                pg.get_by_role("tab", name=name).click()
                pg.wait_for_timeout(9000 if "Risultati" in name else 4000)
                pg.screenshot(path=str(out / f"0{i}_{name[2:].replace(' ', '_')}.png"), full_page=True)
            b.close()
    finally:
        srv.terminate()
    print("screenshots in", out)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "screens"))
