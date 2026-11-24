# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""New-version notice: at start FeedLab asks GitHub for the latest release and, if it is newer, shows what's new.

Only the public GitHub API is contacted (no personal data is sent). Any network problem is silent.
Set FEEDLAB_NO_UPDATE_CHECK=1 to switch the check off.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

API_URL = "https://api.github.com/repos/IZ0JNY/FeedLab/releases/latest"
RELEASES_URL = "https://github.com/IZ0JNY/FeedLab/releases"

# headings of the release-notes sections (windows/RELEASE_NOTES.md)
_SECTION = {"it": "Novità", "en": "What's new"}


def version_tuple(v: str) -> tuple[int, ...]:
    """'v0.4.15' / '0.4.15' → (0, 4, 15); anything after the numbers (e.g. '-beta') is ignored."""
    m = re.match(r"\s*v?(\d+(?:\.\d+)*)", v or "")
    return tuple(int(x) for x in m.group(1).split(".")) if m else ()


def is_newer(latest: str, current: str) -> bool:
    a, b = version_tuple(latest), version_tuple(current)
    return bool(a) and bool(b) and a > b


def notes_for(body: str, lang: str = "it") -> str:
    """The 'what's new' section of the release notes in the given language (the whole text if not found)."""
    body = (body or "").replace("\r\n", "\n")
    title = _SECTION.get(lang, _SECTION["en"])
    lines = body.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("#") and title.lower() in line.lower():
            out = []
            for nxt in lines[i + 1:]:
                if re.match(r"#{1,3} ", nxt):
                    break
                out.append(nxt)
            return "\n".join(out).strip()
    return body.strip()


LAST_ERROR: str | None = None          # why the last check failed (shown by the manual check in the sidebar)


def _contexts():
    """TLS contexts to try: the system store first, then certifi's bundle. The embedded Python of the Windows
    build reads the Windows certificate store, which may not hold GitHub's root yet (Windows downloads roots on
    demand): that made the check fail silently on some PCs."""
    import ssl
    yield None
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return


def latest_release(timeout: float = 6.0) -> dict | None:
    """{'version', 'url', 'body'} of the latest GitHub release, or None (offline, disabled, any error)."""
    global LAST_ERROR
    LAST_ERROR = None
    if os.environ.get("FEEDLAB_NO_UPDATE_CHECK"):
        LAST_ERROR = "FEEDLAB_NO_UPDATE_CHECK"
        return None
    req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json",
                                                   "User-Agent": "FeedLab-update-check"})
    for ctx in _contexts():
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                data = json.loads(r.read().decode("utf-8"))
            return {"version": data.get("tag_name", ""), "url": data.get("html_url") or RELEASES_URL,
                    "body": data.get("body") or ""}
        except Exception as ex:
            LAST_ERROR = f"{type(ex).__name__}: {ex}"
    return None


def check(current: str, lang: str = "it") -> dict | None:
    """{'version', 'url', 'notes'} when a newer release exists, else None."""
    rel = latest_release()
    if not rel or not is_newer(rel["version"], current):
        return None
    return {"version": rel["version"].lstrip("v"), "url": rel["url"], "notes": notes_for(rel["body"], lang)}
