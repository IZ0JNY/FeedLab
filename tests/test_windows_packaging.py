"""Windows package: python.org's interpreters stay untouched (signed), so antivirus heuristics have nothing to
flag; the FeedLab icon comes from the shortcuts (same AppUserModelID as the process) and the window."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_no_modified_interpreter():
    build = (ROOT / "windows" / "build.ps1").read_text(encoding="utf-8")
    iss = (ROOT / "windows" / "feedlab.iss").read_text(encoding="utf-8-sig")
    assert "rcedit-x64.exe" not in build and "& $rcedit" not in build and 'Copy-Item "$build\\python\\pythonw.exe"' not in build
    for line in iss.splitlines():
        if line.startswith(("Name:", "Filename:")) and "Filename:" in line:
            assert "FeedLab.exe" not in line
    assert 'Type: files; Name: "{app}\\python\\FeedLab.exe"' in iss       # removed on upgrade from 0.4.10


def test_shortcuts_share_the_app_id():
    """Each shortcut carries the AppUserModelID of the program it starts (FeedLab or EMELab)."""
    from feedlab import desktop
    iss = (ROOT / "windows" / "feedlab.iss").read_text(encoding="utf-8-sig")
    shortcuts = [l for l in iss.splitlines() if l.startswith('Name: "{auto')]
    assert shortcuts
    for l in shortcuts:
        app = desktop.APPS["emelab" if "--app emelab" in l else "feedlab"]
        assert f'AppUserModelID: "{app["app_id"]}"' in l and app["ico"] in l



def test_checksums_published():
    wf = (ROOT / ".github" / "workflows" / "windows.yml").read_text()
    assert "SHA256SUMS.txt" in (ROOT / "windows" / "build.ps1").read_text(encoding="utf-8")
    assert "SHA256SUMS.txt" in wf and "Get-AuthenticodeSignature" in wf


def test_installer_does_not_download_openems():
    """openEMS is installed from inside the app (tab Full-wave openEMS), never by the setup."""
    iss = (ROOT / "windows" / "feedlab.iss").read_text(encoding="utf-8-sig")
    assert "openems" not in iss.lower()
