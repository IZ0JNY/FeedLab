"""FeedLab as a desktop program (Windows): starts the app server locally and shows it in its own window.

The window is a native WebView2 window (pywebview). If that is not available, the default browser opens
the app instead and the server stays up until "Chiudi FeedLab" is pressed in the sidebar.

    python -m feedlab.desktop                 # normal start
    python -m feedlab.desktop --browser       # use the default browser
    python -m feedlab.desktop --server-only --port 8765    # just the server (tests, LAN use)
    python -m feedlab.desktop --selftest      # check that every component imports, then exit
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent           # folder with streamlit_app.py
IS_WIN = os.name == "nt"
NO_WINDOW = 0x08000000 if IS_WIN else 0


def config_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".config")
    p = Path(base) / "FeedLab"
    p.mkdir(parents=True, exist_ok=True)
    return p


def python_exe() -> str:
    """Console interpreter next to the running one (FeedLab.exe / pythonw.exe -> python.exe)."""
    exe = Path(sys.executable)
    alt = exe.with_name("python.exe")
    if exe.name.lower() != "python.exe" and alt.exists():
        return str(alt)
    return str(exe)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int, address: str = "127.0.0.1", mode: str = "window") -> subprocess.Popen:
    env = os.environ.copy()
    env["FEEDLAB_DESKTOP"] = mode
    env["MPLBACKEND"] = "Agg"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [python_exe(), "-m", "streamlit", "run", str(ROOT / "streamlit_app.py"),
           "--server.port", str(port), "--server.address", address, "--server.headless", "true",
           "--browser.gatherUsageStats", "false", "--server.fileWatcherType", "none",
           "--global.developmentMode", "false", "--server.maxUploadSize", "200", "--theme.base", "light"]
    log = open(config_dir() / "server.log", "w", encoding="utf-8")
    return subprocess.Popen(cmd, cwd=str(ROOT), env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)


def wait_ready(port: int, proc: subprocess.Popen | None = None, timeout: float = 120) -> bool:
    url = f"http://127.0.0.1:{port}/_stcore/health"
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc is not None and proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.read().decode().strip() == "ok":
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if IS_WIN:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
    else:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


LOADING = """<html><body style="font-family:Segoe UI,Arial;background:#0e1117;color:#ddd;display:flex;align-items:center;
justify-content:center;height:95vh;margin:0"><div style="text-align:center"><div style="font-size:42px">📡</div>
<div style="font-size:22px;margin-top:8px">FeedLab</div><div style="opacity:.7;margin-top:6px">avvio in corso…</div>
</div></body></html>"""


def selftest() -> int:
    import importlib
    mods = ["numpy", "scipy", "matplotlib", "plotly", "streamlit", "feedlab", "feedlab.app_openems",
            "feedlab.deep_analysis", "feedlab.openems_local", "feedlab.geometry", "feedlab.modematch"]
    opt = ["cadquery", "webview", "h5py"]
    bad = 0
    for m in mods + opt:
        try:
            importlib.import_module(m)
            print("ok  ", m)
        except Exception as e:
            print("FAIL", m, e)
            bad += m in mods or m == "cadquery"
    return 1 if bad else 0


def message_box(text: str) -> None:
    if IS_WIN:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, text, "FeedLab", 0x10)
            return
        except Exception:
            pass
    print(text, file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="feedlab.desktop")
    ap.add_argument("--browser", action="store_true", help="apri nel browser predefinito")
    ap.add_argument("--server-only", action="store_true")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--address", default="127.0.0.1")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    port = a.port or free_port()
    use_window = not (a.browser or a.server_only)
    if use_window:
        try:
            import webview  # noqa: F401
        except Exception:
            use_window = False
    proc = start_server(port, a.address, "window" if use_window else ("server" if a.server_only else "browser"))
    url = f"http://127.0.0.1:{port}"
    if a.server_only:
        ok = wait_ready(port, proc)
        print("FeedLab server", "pronto" if ok else "NON partito", url, flush=True)
        try:
            return proc.wait()
        except KeyboardInterrupt:
            stop(proc)
            return 0
    window = None
    if use_window:
        try:
            import webview
            try:
                webview.settings["ALLOW_DOWNLOADS"] = True
                webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
            except Exception:
                pass
            window = webview.create_window("FeedLab — Laboratorio di Progettazione di feed/illuminatori a microonde",
                                           html=LOADING, width=1440, height=920, min_size=(900, 600))

            def load():
                if wait_ready(port, proc):
                    window.load_url(url)
                else:
                    window.load_html(LOADING.replace("avvio in corso…", "il server non è partito: vedi "
                                                     + str(config_dir() / "server.log")))
            webview.start(load, private_mode=False, storage_path=str(config_dir() / "webview"))
            stop(proc)
            return 0
        except Exception as e:                       # no WebView2 / pywebview: fall back to the browser
            print("finestra nativa non disponibile:", e, file=sys.stderr)
    if not wait_ready(port, proc):
        message_box("FeedLab non è riuscito ad avviarsi. Dettagli in " + str(config_dir() / "server.log"))
        stop(proc)
        return 1
    webbrowser.open(url)
    try:
        return proc.wait()                           # ends with "Chiudi FeedLab" in the sidebar
    except KeyboardInterrupt:
        stop(proc)
        return 0


if __name__ == "__main__":
    sys.exit(main())
