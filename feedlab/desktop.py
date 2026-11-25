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

ROOT = Path(__file__).resolve().parent.parent           # folder with feedlab_main.py
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


# the program: entry script, window title, AppUserModelID (same as the installer's shortcuts: the taskbar
# shows their icon), icon file and name used in messages
APPS = {
    "feedlab": dict(main="feedlab_main.py", title="FeedLab — Laboratorio di Progettazione di feed/illuminatori a microonde",
                    app_id="IZ0JNY.FeedLab", ico="feedlab.ico", name="FeedLab", emoji="📡"),
}
APP = APPS["feedlab"]
APP_ID = APP["app_id"]


def icon_path() -> Path | None:
    for p in (ROOT.parent / APP["ico"], ROOT / "windows" / APP["ico"]):
        if p.exists():
            return p
    return None


def win_identity() -> None:
    """Windows: group the window under FeedLab's shortcut (icon, pinning) rather than under Python."""
    if not IS_WIN:
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP["app_id"])
    except Exception:
        pass


def win_set_icon(title: str) -> None:
    """Windows: FeedLab's icon on the window (title bar, Alt+Tab); the interpreter is python.org's own."""
    ico = icon_path()
    if not IS_WIN or ico is None:
        return
    try:
        import ctypes
        u = ctypes.windll.user32
        u.FindWindowW.restype = ctypes.c_void_p
        u.LoadImageW.restype = ctypes.c_void_p
        u.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
        hwnd = u.FindWindowW(None, title)
        if not hwnd:
            return
        for which, size in ((1, 32), (0, 16)):          # ICON_BIG, ICON_SMALL
            h = u.LoadImageW(None, str(ico), 1, size, size, 0x10)   # IMAGE_ICON, LR_LOADFROMFILE
            if h:
                u.SendMessageW(hwnd, 0x0080, which, h)               # WM_SETICON
    except Exception:
        pass


def patch_downloads() -> None:
    """Windows/WebView2: pywebview's "Save as" dialog has only an "All files (*.*)" filter and no default
    extension, so with hidden extensions a .stp/.stl/.pdf could be saved without it. Same dialog, with a
    filter for the file's own type and that extension as default (added when the user leaves it out)."""
    if not IS_WIN:
        return
    try:
        import os as _os
        from webview.platforms import edgechromium as ec
    except Exception:
        return

    def on_download_starting(self, sender, args):
        if not ec.webview_settings["ALLOW_DOWNLOADS"]:
            args.Cancel = True
            return
        name = _os.path.basename(args.ResultFilePath)
        ext = _os.path.splitext(name)[1].lstrip(".")
        dialog = ec.WinForms.SaveFileDialog()
        try:
            with ec.winreg.OpenKey(ec.winreg.HKEY_CURRENT_USER,
                                   r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as k:
                dialog.InitialDirectory = ec.winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
        except Exception:
            pass
        every = "*.*"
        dialog.Filter = (f"{ext.upper()} (*.{ext})|*.{ext}|" if ext else "") + f"All files ({every})|{every}"
        if ext:
            dialog.DefaultExt = ext
            dialog.AddExtension = True
        dialog.RestoreDirectory = True
        dialog.FileName = name
        if dialog.ShowDialog(self.form) == ec.WinForms.DialogResult.OK:
            fn = dialog.FileName
            if ext and not fn.lower().endswith("." + ext.lower()):
                fn += "." + ext
            args.ResultFilePath = fn
        else:
            args.Cancel = True

    try:
        ec.EdgeChrome.on_download_starting = on_download_starting
    except Exception:
        pass


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int, address: str = "127.0.0.1", mode: str = "window") -> subprocess.Popen:
    env = os.environ.copy()
    env["FEEDLAB_DESKTOP"] = mode
    env["MPLBACKEND"] = "Agg"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [python_exe(), "-m", "streamlit", "run", str(ROOT / APP["main"]),
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
justify-content:center;height:95vh;margin:0"><div style="text-align:center"><div style="font-size:42px">@EMOJI@</div>
<div style="font-size:22px;margin-top:8px">@NAME@</div><div style="opacity:.7;margin-top:6px">avvio in corso…</div>
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
            ctypes.windll.user32.MessageBoxW(0, text, APP["name"], 0x10)
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
    ap.add_argument("--app", choices=list(APPS), default="feedlab", help="feedlab (default)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    global APP
    APP = APPS[a.app]
    win_identity()
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
        print(APP["name"], "server", "pronto" if ok else "NON partito", url, flush=True)
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
            from . import i18n
            i18n.set_lang(i18n.default_lang())
            patch_downloads()
            title = i18n.tr(APP["title"])
            loading = i18n.tr(LOADING).replace("@NAME@", APP["name"]).replace("@EMOJI@", APP["emoji"])
            window = webview.create_window(title, html=loading, width=1440, height=920, min_size=(900, 600))

            def load():
                win_set_icon(title)
                if wait_ready(port, proc):
                    window.load_url(url)
                else:
                    window.load_html(loading.replace(i18n.tr("avvio in corso…"), i18n.tr("il server non è partito: vedi ")
                                                     + str(config_dir())))
            webview.start(load, private_mode=False, storage_path=str(config_dir() / "webview"))
            stop(proc)
            return 0
        except Exception as e:                       # no WebView2 / pywebview: fall back to the browser
            print("finestra nativa non disponibile:", e, file=sys.stderr)
    if not wait_ready(port, proc):
        message_box(APP["name"] + " non è riuscito ad avviarsi. Dettagli in " + str(config_dir()))
        stop(proc)
        return 1
    webbrowser.open(url)
    try:
        return proc.wait()                           # ends with "Chiudi FeedLab" in the sidebar
    except KeyboardInterrupt:
        stop(proc)
        return 0


def launch_other(app: str) -> None:
    """Start the other program (FeedLab ↔ EMELab) as its own process and window."""
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    cmd = [str(pyw if IS_WIN and pyw.exists() else exe), "-m", "feedlab.desktop", "--app", app]
    if not IS_WIN:
        cmd.append("--browser")
    subprocess.Popen(cmd, cwd=str(ROOT), creationflags=NO_WINDOW if IS_WIN else 0,
                     start_new_session=not IS_WIN)


if __name__ == "__main__":
    sys.exit(main())
