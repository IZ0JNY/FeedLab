"""Update check against the latest GitHub release: newer version detected, silent when offline."""
import io
import json

from feedlab import update_check


def test_version_compare():
    assert update_check.parse("v0.4.16") == (0, 4, 16) and update_check.parse("0.4.9 BETA") == (0, 4, 9)
    assert update_check.newer_than_running({"version": "0.4.16"}, "0.4.15")
    assert update_check.newer_than_running({"version": "0.5.0"}, "0.4.15")
    assert not update_check.newer_than_running({"version": "0.4.15"}, "0.4.15")
    assert not update_check.newer_than_running({"version": "0.4.9"}, "0.4.15")
    assert not update_check.newer_than_running(None, "0.4.15")


def test_latest_reads_github_and_is_silent_offline(monkeypatch):
    payload = {"tag_name": "v0.4.20", "html_url": "https://github.com/IZ0JNY/FeedLab/releases/tag/v0.4.20",
               "name": "FeedLab v0.4.20", "draft": False, "prerelease": False}

    class R(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(update_check.urllib.request, "urlopen", lambda req, timeout: R(json.dumps(payload).encode()))
    info = update_check.latest()
    assert info["version"] == "0.4.20" and info["url"].endswith("v0.4.20")

    def boom(*a, **k): raise OSError("offline")
    monkeypatch.setattr(update_check.urllib.request, "urlopen", boom)
    assert update_check.latest() is None
