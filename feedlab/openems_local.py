"""openEMS on this PC: guided installation, detection, Python bindings and background simulations.

Everything here is optional: FeedLab works without openEMS. This module lets the user

  * install openEMS with a guided procedure (latest official Windows build from GitHub, unpacked in a
    user folder — no administrator rights — plus OPENEMS_INSTALL_PATH and the Python bindings);
  * find an existing installation and a Python interpreter whose openEMS bindings import;
  * run full-wave jobs in the background, one after the other, detached from the app: closing FeedLab
    does not stop a simulation; on reopening, the jobs and their progress are found again.

Command line (used by the Windows installer and handy for debugging):
    python -m feedlab.openems_local status
    python -m feedlab.openems_local install [--target DIR] [--zip FILE] [--status FILE] [--no-test]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

IS_WIN = os.name == "nt"
RELEASES_API = "https://api.github.com/repos/thliebig/openEMS-Project/releases"
RELEASES_PAGE = "https://github.com/thliebig/openEMS-Project/releases"
EXE = "openEMS.exe" if IS_WIN else "openEMS"
NO_WINDOW = 0x08000000 if IS_WIN else 0          # CREATE_NO_WINDOW
DETACHED = 0x00000008 | 0x00000200 if IS_WIN else 0   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP


# ------------------------------------------------------------------ settings & folders
def config_dir() -> Path:
    base = os.environ.get("APPDATA") if IS_WIN else os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    p = Path(os.environ.get("FEEDLAB_CONFIG", Path(base or Path.home()) / "FeedLab"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_settings() -> dict:
    try:
        return json.loads((config_dir() / "settings.json").read_text())
    except Exception:
        return {}


def save_settings(**kw) -> dict:
    s = load_settings()
    s.update({k: v for k, v in kw.items()})
    (config_dir() / "settings.json").write_text(json.dumps(s, indent=1))
    return s


def work_dir() -> Path:
    """Where simulations are stored: Documents/FeedLab/openEMS (or FEEDLAB_HOME/openEMS)."""
    s = load_settings()
    if s.get("work_dir"):
        p = Path(s["work_dir"])
    else:
        home = Path(os.environ.get("FEEDLAB_HOME", Path.home() / "Documents" / "FeedLab"))
        p = home / "openEMS"
    p.mkdir(parents=True, exist_ok=True)
    return p


def default_install_dir() -> Path:
    if IS_WIN:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / "openEMS"
    return Path.home() / "opt" / "openEMS"


# ------------------------------------------------------------------ detection
@dataclass
class OpenEMSInstall:
    root: str | None = None            # folder with openEMS(.exe) and the DLLs
    exe: str | None = None
    appcsxcad: str | None = None
    wheels: list = field(default_factory=list)
    version: str = ""
    source: str = ""                   # how it was found

    @property
    def found(self) -> bool:
        return bool(self.exe)

    def wheel_tags(self) -> list[str]:
        tags = set()
        for w in self.wheels:
            m = re.search(r"-(cp\d+)-", Path(w).name)
            if m:
                tags.add(m.group(1))
        return sorted(tags)


def _exe_in(d: Path) -> Path | None:
    for cand in (d / EXE, d / "bin" / EXE):
        if cand.is_file():
            return cand
    return None


def _scan_root(d: Path) -> Path | None:
    """Folder that contains openEMS(.exe) — d itself, d/bin or one level below (zip with a top folder)."""
    if not d or not d.is_dir():
        return None
    e = _exe_in(d)
    if e:
        return e.parent
    try:
        for sub in sorted(d.iterdir()):
            if sub.is_dir():
                e = _exe_in(sub)
                if e:
                    return e.parent
    except OSError:
        pass
    return None


def _version_of(root: Path) -> str:
    for f in ("README.txt", "readme.txt", "VERSION", "version.txt"):
        p = root / f
        if p.is_file():
            m = re.search(r"v?(\d+\.\d+\.\d+(?:[-.\w]*)?)", p.read_text(errors="ignore")[:4000])
            if m:
                return m.group(1)
    s = load_settings()
    return s.get("openems_version", "")


def find_install(root: str | Path | None = None) -> OpenEMSInstall:
    cands: list[tuple[Path, str]] = []
    if root:
        cands.append((Path(root), "scelta utente"))
    s = load_settings()
    if s.get("openems_root"):
        cands.append((Path(s["openems_root"]), "impostazioni FeedLab"))
    if os.environ.get("OPENEMS_INSTALL_PATH"):
        cands.append((Path(os.environ["OPENEMS_INSTALL_PATH"]), "OPENEMS_INSTALL_PATH"))
    cands.append((default_install_dir(), "cartella predefinita"))
    if IS_WIN:
        for d in (r"C:\openEMS", r"C:\opt\openEMS", r"C:\opt", r"C:\Program Files\openEMS", r"C:\tools\openEMS"):
            cands.append((Path(d), "percorso standard"))
    else:
        for d in ("/usr/local", "/usr", str(Path.home() / "opt" / "openEMS")):
            cands.append((Path(d), "percorso standard"))
    w = shutil.which("openEMS")
    if w:
        cands.append((Path(w).parent, "PATH"))
    for d, src in cands:
        r = _scan_root(d)
        if r:
            exe = r / EXE
            app = next((p for p in (r / "AppCSXCAD.exe", r / "AppCSXCAD") if p.is_file()), None)
            wheels = sorted(set(glob.glob(str(r / "python" / "*.whl")) + glob.glob(str(r / "*.whl"))
                                + glob.glob(str(r.parent / "python" / "*.whl"))))
            return OpenEMSInstall(str(r), str(exe), str(app) if app else None, wheels, _version_of(r), src)
    return OpenEMSInstall()


def sim_env(inst: OpenEMSInstall | None = None) -> dict:
    env = os.environ.copy()
    inst = inst or find_install()
    if inst.root:
        env["OPENEMS_INSTALL_PATH"] = inst.root
        env["PATH"] = inst.root + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("PYTHONHOME", None)
    return env


def prepare_dll_path(inst: OpenEMSInstall) -> None:
    """Make the openEMS DLLs importable in this process (Windows)."""
    if inst.root:
        os.environ["OPENEMS_INSTALL_PATH"] = inst.root
        if inst.root not in os.environ.get("PATH", ""):
            os.environ["PATH"] = inst.root + os.pathsep + os.environ.get("PATH", "")
        if IS_WIN and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(inst.root)
            except OSError:
                pass


# ------------------------------------------------------------------ Python interpreters
def own_python() -> str | None:
    """The interpreter running FeedLab (the bundled one in the Windows app), if it is a real python."""
    if getattr(sys, "frozen", False):
        return None
    exe = Path(sys.executable)
    alt = exe.with_name("python.exe")
    if IS_WIN and exe.name.lower() != "python.exe" and alt.exists():     # pythonw.exe / FeedLab.exe
        return str(alt)
    return str(exe)


def python_candidates() -> list[str]:
    out: list[str] = []

    def add(p):
        if p and Path(p).is_file() and str(Path(p)) not in out:
            out.append(str(Path(p)))

    add(load_settings().get("python"))
    add(own_python())
    if IS_WIN:
        try:
            r = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
            for line in r.stdout.splitlines():
                m = re.search(r"([A-Za-z]:\\.*python(?:w)?\.exe)", line, re.I)
                if m:
                    add(m.group(1))
        except Exception:
            pass
        la = os.environ.get("LOCALAPPDATA", "")
        for pat in (la + r"\Programs\Python\Python3*\python.exe", r"C:\Python3*\python.exe",
                    r"C:\Program Files\Python3*\python.exe", str(Path.home() / r"miniconda3\python.exe"),
                    str(Path.home() / r"anaconda3\python.exe"), r"C:\ProgramData\miniconda3\python.exe"):
            for p in sorted(glob.glob(pat), reverse=True):
                add(p)
    for n in ("python3", "python"):
        add(shutil.which(n))
    return out


def py_tag(python: str) -> str:
    try:
        r = subprocess.run([python, "-c", "import sys;print('cp%d%d' % sys.version_info[:2])"], capture_output=True,
                           text=True, timeout=30, creationflags=NO_WINDOW)
        return r.stdout.strip()
    except Exception:
        return ""


_CHECK = ("import sys, os\n"
          "r = os.environ.get('OPENEMS_INSTALL_PATH')\n"
          "if r and hasattr(os, 'add_dll_directory'):\n"
          "    try: os.add_dll_directory(r)\n"
          "    except OSError: pass\n"
          "import numpy, CSXCAD, openEMS\n"
          "import h5py\n"
          "print('OK', 'cp%d%d' % sys.version_info[:2], getattr(openEMS, '__version__', '?'), "
          "getattr(CSXCAD, '__version__', '?'))\n")


def check_bindings(python: str, inst: OpenEMSInstall | None = None, timeout: float = 60) -> dict:
    """Does `import CSXCAD, openEMS, h5py` work with this interpreter?"""
    inst = inst or find_install()
    try:
        r = subprocess.run([python, "-c", _CHECK], capture_output=True, text=True, timeout=timeout,
                           env=sim_env(inst), creationflags=NO_WINDOW)
    except Exception as e:
        return {"ok": False, "python": python, "error": str(e)}
    out = (r.stdout + r.stderr).strip()
    if r.returncode == 0 and out.startswith("OK"):
        parts = out.split()
        return {"ok": True, "python": python, "tag": parts[1], "openems": parts[2], "csxcad": parts[3]}
    last = out.splitlines()[-1] if out else f"exit {r.returncode}"
    return {"ok": False, "python": python, "error": last, "tag": py_tag(python)}


def find_working_python(inst: OpenEMSInstall | None = None) -> dict | None:
    inst = inst or find_install()
    for p in python_candidates():
        c = check_bindings(p, inst)
        if c["ok"]:
            return c
    return None


def matching_wheels(inst: OpenEMSInstall, tag: str) -> list[str]:
    return [w for w in inst.wheels if f"-{tag}-" in Path(w).name]


def install_bindings(python: str, inst: OpenEMSInstall, log=print) -> bool:
    """pip-install the openEMS/CSXCAD wheels shipped with openEMS (matching this Python) plus h5py."""
    tag = py_tag(python)
    wh = matching_wheels(inst, tag)
    if not wh:
        log(f"Nessuna wheel per {tag} in {inst.root}\\python (disponibili: {', '.join(inst.wheel_tags()) or 'nessuna'}).")
        return False
    cmd = [python, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", "--no-warn-script-location"]
    cmd += wh + ["h5py", "numpy"]
    log("pip install " + " ".join(Path(w).name for w in wh) + " h5py numpy")
    r = subprocess.run(cmd, capture_output=True, text=True, env=sim_env(inst), creationflags=NO_WINDOW)
    log((r.stdout + r.stderr)[-3000:])
    return r.returncode == 0


# ------------------------------------------------------------------ download & guided install
def _http_json(url: str, timeout: float = 30):
    import urllib.request
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "FeedLab"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def pick_windows_asset(release: dict) -> dict | None:
    assets = [a for a in release.get("assets", []) if a.get("name", "").lower().endswith(".zip")]

    def score(a):
        n = a["name"].lower()
        return (("win" in n) * 4 + ("64" in n) * 2 + ("msvc" in n) * 1 - ("src" in n or "source" in n) * 10)
    assets = [a for a in assets if score(a) > 0]
    return max(assets, key=score) if assets else None


def latest_release(include_prerelease: bool = False) -> dict:
    """Latest openEMS release with a Windows zip: {tag, name, url, size, published, page}."""
    rels = _http_json(RELEASES_API + "?per_page=15")
    for rel in rels:
        if rel.get("draft") or (rel.get("prerelease") and not include_prerelease):
            continue
        a = pick_windows_asset(rel)
        if a:
            return {"tag": rel["tag_name"], "name": a["name"], "url": a["browser_download_url"], "size": a.get("size", 0),
                    "published": rel.get("published_at", ""), "page": rel.get("html_url", RELEASES_PAGE)}
    raise RuntimeError("nessuna release openEMS con zip per Windows trovata")


def download(url: str, dest: Path, progress=None, chunk: int = 1 << 16) -> Path:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "FeedLab"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as fh:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            b = r.read(chunk)
            if not b:
                break
            fh.write(b)
            done += len(b)
            if progress:
                progress(done, total)
    return dest


def extract(zip_path: Path, target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for m in z.infolist():                      # refuse paths escaping the target folder
            p = (target / m.filename).resolve()
            if not str(p).startswith(str(target.resolve())):
                raise RuntimeError(f"percorso non valido nello zip: {m.filename}")
        z.extractall(target)
    root = _scan_root(target)
    if not root:
        raise RuntimeError(f"{EXE} non trovato nello zip estratto in {target}")
    return root


def set_user_env(name: str, value: str) -> bool:
    """Persistent user environment variable (HKCU\\Environment), like `setx`."""
    if not IS_WIN:
        return False
    try:
        import ctypes
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_EXPAND_SZ, value)
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None)
        return True
    except Exception:
        return False


class StatusFile:
    """Progress of the guided install, readable by the app while it runs in another process."""

    def __init__(self, path: Path | None):
        self.path = Path(path) if path else None
        self.d = {"step": "", "steps_done": [], "progress": 0.0, "log": [], "state": "running", "error": ""}

    def set(self, **kw):
        self.d.update(kw)
        self._write()

    def log(self, msg: str):
        print(msg, flush=True)
        self.d["log"] = (self.d["log"] + [str(msg)])[-200:]
        self._write()

    def _write(self):
        if self.path:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.d))
            os.replace(tmp, self.path)


INSTALL_STEPS = ["release", "download", "extract", "env", "bindings", "verify", "test"]
STEP_LABELS = {"release": "Cerco l'ultima versione", "download": "Scarico openEMS", "extract": "Estraggo i file",
               "env": "Imposto OPENEMS_INSTALL_PATH", "bindings": "Installo i binding Python",
               "verify": "Verifico l'importazione", "test": "Simulazione di prova"}


def guided_install(target: str | Path | None = None, zip_path: str | Path | None = None, python: str | None = None,
                   status_path: str | Path | None = None, run_test: bool = True, prerelease: bool = False) -> dict:
    """The whole guided procedure. Returns the final status dictionary."""
    st = StatusFile(status_path)
    target = Path(target) if target else default_install_dir()
    python = python or own_python() or (python_candidates() or [None])[0]
    try:
        rel = None
        if not zip_path:
            st.set(step="release", progress=0.02)
            rel = latest_release(prerelease)
            st.log(f"openEMS {rel['tag']} — {rel['name']} ({rel['size'] / 1e6:.0f} MB)")
            st.set(step="download", steps_done=["release"], release=rel)
            zip_path = Path(tempfile.gettempdir()) / rel["name"]

            def prog(done, total):
                if total:
                    st.d["progress"] = 0.05 + 0.55 * done / total
                    if done == total or done % (8 << 20) < (1 << 16):
                        st.set(downloaded_mb=done / 1e6, total_mb=total / 1e6)
            download(rel["url"], Path(zip_path), prog)
            st.log(f"Scaricato in {zip_path}")
        st.set(step="extract", steps_done=["release", "download"], progress=0.62)
        root = extract(Path(zip_path), target)
        st.log(f"openEMS estratto in {root}")
        save_settings(openems_root=str(root), openems_version=(rel or {}).get("tag", ""))
        st.set(step="env", steps_done=["release", "download", "extract"], progress=0.7, root=str(root))
        if set_user_env("OPENEMS_INSTALL_PATH", str(root)):
            st.log("Variabile OPENEMS_INSTALL_PATH impostata per l'utente")
        os.environ["OPENEMS_INSTALL_PATH"] = str(root)
        inst = find_install(root)
        st.set(step="bindings", steps_done=INSTALL_STEPS[:4], progress=0.75)
        st.log(f"Wheel Python incluse: {', '.join(inst.wheel_tags()) or 'nessuna'}")
        ok = False
        if python:
            chk = check_bindings(python, inst)
            if chk["ok"]:
                ok = True
                st.log("Binding già presenti in " + python)
            else:
                ok = install_bindings(python, inst, st.log)
        if not ok:
            for p in python_candidates():
                if p != python and matching_wheels(inst, py_tag(p)):
                    st.log(f"Provo con {p}")
                    if install_bindings(p, inst, st.log):
                        python, ok = p, True
                        break
        st.set(step="verify", steps_done=INSTALL_STEPS[:5], progress=0.85)
        chk = check_bindings(python, inst) if python else {"ok": False, "error": "nessun Python"}
        if not chk["ok"]:
            raise RuntimeError("i binding Python di openEMS non si importano: " + chk.get("error", "") +
                               f" — servono Python {', '.join(inst.wheel_tags())} (64 bit)")
        save_settings(python=python)
        st.log(f"openEMS {chk['openems']} / CSXCAD {chk['csxcad']} importati con {python}")
        if run_test:
            st.set(step="test", steps_done=INSTALL_STEPS[:6], progress=0.9)
            t = quick_test(python, inst, log=st.log)
            st.log(f"Simulazione di prova completata in {t['seconds']:.0f} s (S11 = {t['s11_db']:.1f} dB)")
        st.set(step="done", steps_done=INSTALL_STEPS, progress=1.0, state="done", python=python, root=str(root))
    except Exception as e:
        st.set(state="error", error=f"{type(e).__name__}: {e}")
        st.log("ERRORE: " + str(e))
    return st.d


def quick_test(python: str, inst: OpenEMSInstall, log=print, timeout: float = 900) -> dict:
    """Tiny real FDTD run (open circular guide, coarse mesh) to prove the chain works end to end."""
    from . import geometry
    from .openems_sim import DeepConfig, make_deep_script
    geo = geometry.build("open_circular", 10.368, fD=0.35)
    d = Path(tempfile.mkdtemp(prefix="feedlab_oems_test_"))
    cfg = DeepConfig(cells_per_lambda=10, nr_ts=20000, end_db=25, n_freq=21, ff_freqs=[10.368], sphere=False,
                     theta_step=5.0, pad_lambda=0.3, openems_root=inst.root or "", label="test")
    script = make_deep_script(geo, d, cfg)
    t0 = time.time()
    r = subprocess.run([python, "-u", str(script)], cwd=str(d), capture_output=True, text=True, timeout=timeout,
                       env=sim_env(inst), creationflags=NO_WINDOW)
    if r.returncode != 0 or not (d / "results.json").exists():
        log((r.stdout + r.stderr)[-2000:])
        raise RuntimeError("la simulazione di prova non è riuscita (vedi log)")
    st = json.loads((d / "status.json").read_text())
    return {"seconds": time.time() - t0, "s11_db": st.get("s11_f0_db", float("nan")), "dir": str(d)}


def start_guided_install(target: str | Path | None = None, zip_path: str | None = None, run_test: bool = True) -> Path:
    """Launch guided_install in a separate process; returns the status file the app polls."""
    status = config_dir() / "openems_install_status.json"
    if status.exists():
        status.unlink()
    py = own_python() or sys.executable
    cmd = [py, "-m", "feedlab.openems_local", "install", "--status", str(status)]
    if target:
        cmd += ["--target", str(target)]
    if zip_path:
        cmd += ["--zip", str(zip_path)]
    if not run_test:
        cmd += ["--no-test"]
    _spawn_detached(cmd, cwd=str(Path(__file__).resolve().parent.parent), log=config_dir() / "openems_install.log")
    return status


def read_status(path: str | Path) -> dict | None:
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


# ------------------------------------------------------------------ background jobs
_RUNNER = r'''# FeedLab queue runner (auto-generated, stdlib only): runs openEMS jobs one after the other.
import json, os, subprocess, sys, time
q = json.load(open(sys.argv[1]))
env = os.environ.copy(); env.update(q.get("env", {}))
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
def put(jd, **kw):
    p = os.path.join(jd, "runner.json")
    try:
        d = json.load(open(p))
    except Exception:
        d = {}
    d.update(kw)
    open(p + ".tmp", "w").write(json.dumps(d)); os.replace(p + ".tmp", p)
for jd in q["jobs"]:
    put(jd, state="queued", runner_pid=os.getpid())
for jd in q["jobs"]:
    if os.path.exists(os.path.join(os.path.dirname(sys.argv[1]), "STOP_" + q["id"])):
        put(jd, state="stopped"); continue
    script = os.path.join(jd, q["scripts"][jd])
    log = open(os.path.join(jd, "run.log"), "w")
    t0 = time.time()
    p = subprocess.Popen([q["python"], "-u", script], cwd=jd, stdout=log, stderr=subprocess.STDOUT, env=env,
                         creationflags=NO_WINDOW)
    put(jd, state="running", pid=p.pid, start=t0, runner_pid=os.getpid())
    rc = p.wait(); log.close()
    ok = rc == 0 and os.path.exists(os.path.join(jd, "results.json"))
    stopped = os.path.exists(os.path.join(jd, "STOP"))
    put(jd, state="done" if ok else ("stopped" if stopped else "error"), rc=rc, end=time.time())
'''


def _spawn_detached(cmd: list, cwd: str, log: Path | None = None) -> subprocess.Popen:
    out = open(log, "w") if log else subprocess.DEVNULL
    kw = dict(cwd=cwd, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, close_fds=True)
    if IS_WIN:
        kw["creationflags"] = DETACHED | NO_WINDOW
    else:
        kw["start_new_session"] = True
    return subprocess.Popen(cmd, **kw)


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s).strip("_")[:60] or "job"


def create_job(geo, cfg, label: str = "", study: str = "", project: dict | None = None) -> Path:
    from .openems_sim import make_deep_script
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = _slug(f"{stamp}_{geo.kind}_{geo.f_ghz:g}GHz_{label}")
    jd = work_dir() / name
    i = 1
    while jd.exists():
        jd = work_dir() / f"{name}_{i}"
        i += 1
    cfg.label = label
    inst = find_install()
    cfg.openems_root = inst.root or ""
    script = make_deep_script(geo, jd, cfg)
    meta = {"label": label or geo.kind, "study": study, "kind": geo.kind, "f_ghz": geo.f_ghz, "created": time.time(),
            "script": script.name, "params": {k: v for k, v in geo.params.items() if isinstance(v, (int, float))},
            "cells_per_lambda": cfg.cells_per_lambda, "project": project or {}}
    (jd / "job.json").write_text(json.dumps(meta, indent=1, default=str))
    return jd


def start_batch(job_dirs: list[Path], python: str, inst: OpenEMSInstall | None = None) -> str:
    """Run the jobs one after the other in a detached process (they survive closing FeedLab)."""
    inst = inst or find_install()
    wd = work_dir()
    runner = wd / "_queue_runner.py"
    runner.write_text(_RUNNER)
    qid = time.strftime("%Y%m%d%H%M%S")
    jobs = [str(Path(j).resolve()) for j in job_dirs]
    scripts = {j: json.loads((Path(j) / "job.json").read_text())["script"] for j in jobs}
    env = {"OPENEMS_INSTALL_PATH": inst.root or "", "PYTHONIOENCODING": "utf-8"}
    if inst.root:
        env["PATH"] = inst.root + os.pathsep + os.environ.get("PATH", "")
    q = {"id": qid, "python": python, "jobs": jobs, "scripts": scripts, "env": env}
    qf = wd / f"queue_{qid}.json"
    qf.write_text(json.dumps(q, indent=1))
    for j in jobs:
        (Path(j) / "runner.json").write_text(json.dumps({"state": "queued", "queue": qid}))
    _spawn_detached([python, str(runner), str(qf)], cwd=str(wd), log=wd / f"queue_{qid}.log")
    return qid


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if IS_WIN:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return code.value == 259                                           # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


_TS = re.compile(r"Timestep:\s*(\d+)")
_EN = re.compile(r"Energy:\s*~?\s*([0-9.eE+-]+)\s*\(\s*-?\s*([0-9.]+)\s*dB\)")
_SPEED = re.compile(r"Speed:\s*([0-9.]+)\s*MC/s")
_MAXTS = re.compile(r"[Mm]ax\.? (?:number of )?timesteps:?\s*(\d+)")


def _tail(p: Path, n: int = 40000) -> str:
    try:
        with open(p, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - n))
            return fh.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def job_state(jd: str | Path) -> dict:
    jd = Path(jd)
    meta = json.loads((jd / "job.json").read_text()) if (jd / "job.json").exists() else {}
    run = json.loads((jd / "runner.json").read_text()) if (jd / "runner.json").exists() else {}
    stt = json.loads((jd / "status.json").read_text()) if (jd / "status.json").exists() else {}
    cfg = {}
    try:
        cfg = json.loads((jd / "feed.json").read_text())["config"]
    except Exception:
        pass
    state = run.get("state", "nuovo")
    if (jd / "results.json").exists() and stt.get("stage") == "done":
        state = "done"
    elif stt.get("stage") == "error":
        state = "error"
    elif state in ("running", "queued"):
        alive = pid_alive(run.get("pid")) or pid_alive(run.get("runner_pid"))
        if not alive:
            state = "stopped" if (jd / "STOP").exists() else "interrotto"
    log = _tail(jd / "run.log")
    ts = [int(x) for x in _TS.findall(log)]
    en = _EN.findall(log)
    sp = _SPEED.findall(log)
    mx = _MAXTS.findall(log)
    end_db = float(cfg.get("end_db", 40))
    stage = stt.get("stage", "")
    e_db = float(en[-1][1]) if en else 0.0
    prog = {"": 0.0, "setup": 0.02, "fdtd": 0.05, "port": 0.9, "nf2ff": 0.93, "done": 1.0, "error": 0.0}.get(stage, 0.0)
    if stage == "fdtd":
        f_e = min(1.0, e_db / end_db) if e_db > 0 else 0.0
        f_t = ts[-1] / int(mx[-1]) if (ts and mx) else 0.0
        prog = 0.05 + 0.85 * max(f_e, f_t)
    start = run.get("start")
    elapsed = (run.get("end") or time.time()) - start if start else stt.get("elapsed", 0)
    eta = elapsed * (1 - prog) / prog if 0.06 < prog < 1 and state == "running" else None
    return {"dir": str(jd), "name": jd.name, "label": meta.get("label", jd.name), "study": meta.get("study", ""),
            "kind": meta.get("kind", ""), "f_ghz": meta.get("f_ghz"), "created": meta.get("created", 0),
            "cells_per_lambda": meta.get("cells_per_lambda"), "params": meta.get("params", {}),
            "state": state, "stage": stage, "progress": prog, "timestep": ts[-1] if ts else None,
            "energy_db": -e_db if en else None, "speed_mcs": float(sp[-1]) if sp else None,
            "elapsed_s": elapsed, "eta_s": eta, "error": stt.get("error", ""), "summary": stt,
            "has_results": (jd / "results.json").exists(), "log_tail": log[-4000:]}


def list_jobs() -> list[dict]:
    out = []
    for jd in sorted(work_dir().iterdir(), reverse=True):
        if jd.is_dir() and (jd / "job.json").exists():
            try:
                out.append(job_state(jd))
            except Exception:
                pass
    return out


def stop_job(jd: str | Path) -> None:
    jd = Path(jd)
    (jd / "STOP").write_text("stop")
    run = json.loads((jd / "runner.json").read_text()) if (jd / "runner.json").exists() else {}
    q = run.get("queue")
    if q:
        (work_dir() / f"STOP_{q}").write_text("stop")       # the rest of the queue is skipped
    pid = run.get("pid")
    if pid and pid_alive(pid):
        if IS_WIN:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)
        else:
            import signal
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass


def delete_job(jd: str | Path) -> None:
    jd = Path(jd).resolve()
    if work_dir().resolve() in jd.parents:
        shutil.rmtree(jd, ignore_errors=True)


def open_folder(path: str | Path) -> None:
    if IS_WIN:
        os.startfile(str(path))  # noqa: S606
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def preview_geometry(script: str | Path, python: str, inst: OpenEMSInstall | None = None) -> subprocess.Popen:
    """Open the model in AppCSXCAD (no simulation)."""
    script = Path(script)
    return subprocess.Popen([python, str(script), "--preview"], cwd=str(script.parent), env=sim_env(inst),
                            creationflags=NO_WINDOW)


# ------------------------------------------------------------------ status summary / CLI
def summary() -> dict:
    inst = find_install()
    py = find_working_python(inst) if inst.found else None
    return {"install": asdict(inst), "wheel_tags": inst.wheel_tags(), "python_ok": py,
            "own_python": own_python(), "own_tag": py_tag(own_python()) if own_python() else "",
            "work_dir": str(work_dir()), "default_dir": str(default_install_dir())}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="feedlab.openems_local")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    i = sub.add_parser("install")
    i.add_argument("--target")
    i.add_argument("--zip")
    i.add_argument("--python")
    i.add_argument("--status")
    i.add_argument("--no-test", action="store_true")
    i.add_argument("--prerelease", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        print(json.dumps(summary(), indent=1))
        return 0
    d = guided_install(a.target, a.zip, a.python, a.status, not a.no_test, a.prerelease)
    print("RISULTATO:", d["state"], d.get("error", ""))
    return 0 if d["state"] == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
