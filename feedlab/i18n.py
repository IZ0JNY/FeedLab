"""Interface languages of FeedLab: Italiano (source) and English.

The app is written in Italian; `tr()` translates any interface text into the current language:
first by exact match of the whole string, otherwise by replacing every known Italian phrase inside it
(longest first, on word boundaries), so that texts built with numbers (f-strings) are translated too.
The catalogue is `feedlab.i18n_catalog.ENTRIES` (it, en).

`wrap(streamlit)` returns a proxy of the streamlit module that translates labels, help texts, options
(only how they are displayed: the returned values stay the Italian ones the code compares with), table
headers and cells, metrics and plotly figure texts — so the app code stays plain Streamlit code.
"""
from __future__ import annotations

import functools
import locale
import os
import re

LANGS = {"it": "Italiano", "en": "English"}
INNO_LANG = {"italian": "it", "english": "en"}


def _dst(e, lang):
    return e[1]

_lang = "it"
_tables: dict = {}


def _build(lang: str):
    from .i18n_catalog import ENTRIES
    m = {}
    exact = {}
    for e in ENTRIES:
        src, dst = e[0], _dst(e, lang)
        if len(src) <= 3:                 # short words: whole-text match only, never inside sentences
            exact[src] = dst
            continue
        m[src] = dst
        if src[:1].isupper() and len(src) > 1 and not src[:2].isupper():      # lowercase variant
            low = src[0].lower() + src[1:]
            if low not in m:
                m[low] = dst if (len(dst) > 1 and dst[:2].isupper()) or not dst[:1].isalpha() \
                    else dst[0].lower() + dst[1:]
    keys = sorted(m, key=len, reverse=True)
    parts = []
    for k in keys:
        p = re.escape(k)
        if re.match(r"\w", k):
            p = r"(?<!\w)" + p
        if re.search(r"\w$", k):
            p = p + r"(?!\w)"
        parts.append(p)
    rx = re.compile("|".join(parts)) if parts else None
    return m, rx, exact


def set_lang(lang: str) -> str:
    global _lang
    _lang = lang if lang in LANGS else "it"
    if _lang != "it" and _lang not in _tables:
        _tables[_lang] = _build(_lang)
    return _lang


def get_lang() -> str:
    return _lang


def tr(s, lang: str | None = None):
    lang = lang or _lang
    if lang == "it" or not isinstance(s, str) or not s.strip():
        return s
    if lang not in _tables:
        _tables[lang] = _build(lang)
    m, rx, exact = _tables[lang]
    if s in m:
        return m[s]
    core = s.strip()
    if core in exact:
        return s.replace(core, exact[core])
    if core in m:
        return s.replace(core, m[core])
    if len(s) > 20000 or "base64," in s:          # embedded files: translate only the text around them
        parts = re.split(r"(data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+)", s)
        return "".join(x if i % 2 else (rx.sub(lambda mo: m[mo.group(0)], x) if rx and len(x) < 20000 else x)
                       for i, x in enumerate(parts))
    return rx.sub(lambda mo: m[mo.group(0)], s) if rx else s


def default_lang() -> str:
    """Saved choice → FEEDLAB_LANG → language chosen in the Windows installer → system language → Italian."""
    try:
        from .openems_local import load_settings
        s = load_settings().get("language")
        if s in LANGS:
            return s
    except Exception:
        pass
    env = os.environ.get("FEEDLAB_LANG", "")[:2].lower()
    if env in LANGS:
        return env
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\FeedLab") as k:
                v = winreg.QueryValueEx(k, "Language")[0]
                if INNO_LANG.get(v, v) in LANGS:
                    return INNO_LANG.get(v, v)
        except Exception:
            pass
    try:
        loc = (locale.getlocale()[0] or "")[:2].lower()
        if loc:
            return "it" if loc == "it" else "en"     # any other system language: English
    except Exception:
        pass
    return "it"


def translate_figure_mpl(fig) -> None:
    """Translate every text of a matplotlib figure (PDF drawings, report plots)."""
    if _lang == "it":
        return
    from matplotlib.text import Text
    for t in fig.findobj(Text):
        s = t.get_text()
        if s:
            t.set_text(tr(s))


def translate_plotly(fig):
    if _lang == "it" or fig is None:
        return fig
    try:
        lay = fig.layout
        if lay.title and lay.title.text:
            lay.title.text = tr(lay.title.text)
        for ax in ("xaxis", "yaxis", "yaxis2"):
            a = getattr(lay, ax, None)
            if a is not None and a.title and a.title.text:
                a.title.text = tr(a.title.text)
        if lay.scene:
            for ax in ("xaxis", "yaxis", "zaxis"):
                a = getattr(lay.scene, ax)
                if a.title and a.title.text:
                    a.title.text = tr(a.title.text)
        for an in lay.annotations or []:
            if an.text:
                an.text = tr(an.text)
        for d in fig.data:
            if getattr(d, "name", None):
                d.name = tr(d.name)
    except Exception:
        pass
    return fig


# ------------------------------------------------------------------ streamlit proxy
_ARG0 = {"title", "header", "subheader", "markdown", "caption", "text", "info", "warning", "success", "error",
         "button", "checkbox", "toggle", "number_input", "slider", "select_slider", "text_input", "text_area",
         "selectbox", "radio", "multiselect", "expander", "popover", "download_button", "file_uploader", "spinner",
         "toast", "color_picker", "date_input", "pills", "segmented_control", "link_button"}
_CHOICE = {"selectbox", "radio", "multiselect", "select_slider", "pills", "segmented_control"}
_CONTAINERS = {"columns", "tabs", "expander", "popover", "container", "empty", "form"}
_KW = ("help", "label", "text", "placeholder", "caption")
_HANDLED = _ARG0 | _CHOICE | _CONTAINERS | {"metric", "write", "tabs", "dataframe", "table", "plotly_chart", "progress",
                                            "set_page_config"}


def _tr_data(data):
    if _lang == "it":
        return data
    if isinstance(data, list) and data and all(isinstance(r, dict) for r in data):
        return [{tr(k): (tr(v) if isinstance(v, str) else v) for k, v in r.items()} for r in data]
    if isinstance(data, dict):
        return {tr(k): ([tr(x) if isinstance(x, str) else x for x in v] if isinstance(v, list) else
                        (tr(v) if isinstance(v, str) else v)) for k, v in data.items()}
    return data


def _call(fn, name, *args, **kw):
    if _lang != "it":
        args = list(args)
        if name in _ARG0 and args and isinstance(args[0], str):
            args[0] = tr(args[0])
        for k in _KW:
            if isinstance(kw.get(k), str):
                kw[k] = tr(kw[k])
        if name in _CHOICE:
            ff = kw.get("format_func", str)
            kw["format_func"] = lambda v, _f=ff: tr(str(_f(v)))
        elif name == "metric":
            for i in range(min(len(args), 3)):
                if isinstance(args[i], str):
                    args[i] = tr(args[i])
            if isinstance(kw.get("delta"), str):
                kw["delta"] = tr(kw["delta"])
        elif name == "write":
            args = [tr(a) if isinstance(a, str) else _tr_data(a) if isinstance(a, dict) else a for a in args]
        elif name == "tabs" and args:
            args[0] = [tr(x) for x in args[0]]
        elif name in ("dataframe", "table"):
            if args:
                args[0] = _tr_data(args[0])
            elif "data" in kw:
                kw["data"] = _tr_data(kw["data"])
        elif name == "plotly_chart" and args:
            translate_plotly(args[0])
        elif name == "progress" and len(args) > 1 and isinstance(args[1], str):
            args[1] = tr(args[1])
        elif name == "set_page_config" and isinstance(kw.get("page_title"), str):
            kw["page_title"] = tr(kw["page_title"])
        elif name in ("text_input", "text_area") and len(args) > 1 and isinstance(args[1], str):
            args[1] = tr(args[1])
    res = fn(*args, **kw)
    if name in _CONTAINERS:
        if isinstance(res, (list, tuple)):
            return [Proxy(r) for r in res]
        return Proxy(res)
    return res


class Proxy:
    """Translating stand-in for the streamlit module or a DeltaGenerator."""

    def __init__(self, obj):
        object.__setattr__(self, "_o", obj)

    def __getattr__(self, name):
        a = getattr(self._o, name)
        if name == "sidebar":
            return Proxy(a)
        if name in _HANDLED and callable(a):
            return functools.partial(_call, a, name)
        return a

    def __setattr__(self, name, value):
        setattr(self._o, name, value)

    def __enter__(self):
        self._o.__enter__()
        return self

    def __exit__(self, *exc):
        return self._o.__exit__(*exc)


def wrap(st_module):
    return Proxy(st_module)


# user manual PDF per language (docs/manual); a missing file falls back to English
MANUALS = {"it": "FeedLab_Manuale_IT.pdf", "en": "FeedLab_User_Manual_EN.pdf"}
