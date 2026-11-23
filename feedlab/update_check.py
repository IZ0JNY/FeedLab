"""Check on GitHub whether a newer FeedLab release is out (latest published release of IZ0JNY/FeedLab).

Silent on any problem (no internet, GitHub unreachable, rate limit): the program never waits more than a few
seconds and never fails because of this check."""
from __future__ import annotations

import json
import re
import urllib.request

from . import __version__

API = "https://api.github.com/repos/IZ0JNY/FeedLab/releases/latest"
RELEASES = "https://github.com/IZ0JNY/FeedLab/releases/latest"


def parse(v: str) -> tuple[int, ...]:
    """'v0.4.15' / '0.4.15 BETA' -> (0, 4, 15); () if there is no version number."""
    m = re.search(r"(\d+(?:\.\d+)*)", v or "")
    return tuple(int(x) for x in m.group(1).split(".")) if m else ()


def latest(timeout: float = 3.0) -> dict | None:
    """{'version': '0.4.16', 'url': '…/releases/tag/v0.4.16', 'name': …} or None."""
    try:
        req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "FeedLab"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        tag = d.get("tag_name") or ""
        if not parse(tag) or d.get("draft") or d.get("prerelease"):
            return None
        return {"version": tag.lstrip("vV"), "url": d.get("html_url") or RELEASES, "name": d.get("name") or tag}
    except Exception:
        return None


def newer_than_running(info: dict | None, current: str = __version__) -> bool:
    return bool(info) and parse(info["version"]) > parse(current)
