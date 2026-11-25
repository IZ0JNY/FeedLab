"""File names for downloads: the user may type a name, otherwise the proposed default is used."""
from __future__ import annotations

import re

_BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_EXTS = (".feedlab.json", ".json", ".pdf", ".stp", ".step", ".stl", ".zip", ".html", ".csv", ".dat")
_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def clean(name: str | None, default: str) -> str:
    """Name without extension, safe on Windows and Linux; empty → default."""
    n = _BAD.sub("_", (name or "").strip())
    low = n.lower()
    for e in _EXTS:
        if low.endswith(e):
            n = n[: -len(e)]
            break
    n = n.strip(" .")
    if not n:
        return default
    if n.lower() in _RESERVED:
        n += "_"
    return n


def pick(st, default: str, key: str) -> str:
    """Text box prefilled with the default name; returns the name to use (without extension)."""
    v = st.text_input("Nome file", value=default, key=f"fname_{key}_{default}",
                      help="Lascia il nome proposto o scrivine uno tuo; l'estensione si aggiunge da sola.")
    return clean(v, default)
