"""Linux package: built by linux/build.sh in the same workflow as Windows and published in the same release."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_build_script_and_package_files():
    build = (ROOT / "linux" / "build.sh").read_text(encoding="utf-8")
    assert "requirements-desktop.txt" in build and "appimagetool" in build and "SHA256SUMS-linux.txt" in build and "--selftest" in build
    control = (ROOT / "linux" / "control.in").read_text(encoding="utf-8")
    assert "Package: feedlab" in control and "@VERSION@" in control and "@SIZE@" in control
    assert "gir1.2-webkit2-4.1" in control                      # native window, else the browser
    desktop = (ROOT / "linux" / "feedlab.desktop").read_text(encoding="utf-8")
    assert "Exec=feedlab" in desktop and "Icon=feedlab" in desktop


def test_release_has_windows_and_linux():
    wf = (ROOT / ".github" / "workflows" / "windows.yml").read_text()
    assert "linux/build.sh" in wf and "needs: [build, linux]" in wf
    assert "feedlab_*_amd64.deb" in wf and "FeedLab-*-x86_64.AppImage" in wf and "FeedLab-Setup-*.exe" in wf
    assert "gh release upload" in wf                            # adds missing files, never overwrites
