"""BETA TEST builds. From 0.4.15 FeedLab no longer expires (EXPIRY = False): it is free software under the
GPLv3, so the version is only labelled BETA. The 30-day mechanism below stays available but is switched off.

With EXPIRY = True, every version is valid for 30 days from its installation, then FeedLab stops.

The first start of a version records the date (FeedLab's settings folder, beta.json, one entry per version):
a new release therefore gets its own 30 days. A clock moved back by more than a day counts as expired.

This is a soft limit for test builds: FeedLab is open source, so it is a notice to testers, not a protection.
Set BETA = False to build a normal release.
"""
from __future__ import annotations

import datetime as _dt
import json
import os

from . import __version__

BETA = True
EXPIRY = False                                              # no 30-day limit (since 0.4.15)
VALID_DAYS = 30
RELEASES_URL = "https://github.com/IZ0JNY/FeedLab/releases"


def _file():
    from .openems_local import config_dir
    return config_dir() / "beta.json"


def _now() -> _dt.datetime:
    fake = os.environ.get("FEEDLAB_BETA_NOW")              # tests: ISO date-time
    return _dt.datetime.fromisoformat(fake) if fake else _dt.datetime.now()


def status(version: str = __version__) -> dict:
    """{'beta', 'expiry', 'installed', 'expires', 'days_left', 'expired', 'reason'} for this version."""
    if not BETA or not EXPIRY:
        return {"beta": BETA, "expiry": False, "expired": False, "days_left": None}
    now = _now()
    try:
        data = json.loads(_file().read_text())
    except Exception:
        data = {}
    rec = data.get(version)
    if rec is None:
        rec = {"installed": now.isoformat(timespec="seconds"), "last_seen": now.isoformat(timespec="seconds")}
    installed = _dt.datetime.fromisoformat(rec["installed"])
    last_seen = _dt.datetime.fromisoformat(rec.get("last_seen", rec["installed"]))
    expires = installed + _dt.timedelta(days=VALID_DAYS)
    reason = ""
    if now < last_seen - _dt.timedelta(days=1):
        reason = "orologio"                                 # clock moved back
    elif now >= expires:
        reason = "scaduta"
    if not reason and now > last_seen:
        rec["last_seen"] = now.isoformat(timespec="seconds")
    data[version] = rec
    try:
        _file().write_text(json.dumps(data, indent=1))
    except Exception:
        pass
    left = (expires - now).total_seconds() / 86400
    return {"beta": True, "expiry": True, "installed": installed, "expires": expires, "days_left": max(0, int(left + 0.999)),
            "expired": bool(reason), "reason": reason}
