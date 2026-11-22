"""Interface languages: catalogue integrity, translation of composed texts, streamlit proxy."""
import re

import pytest

from feedlab import i18n
from feedlab.i18n_catalog import ENTRIES


def test_catalogue_complete():
    assert all(len(e) == 2 and all(isinstance(x, str) and x for x in e) for e in ENTRIES)
    srcs = [e[0] for e in ENTRIES]
    assert len(srcs) == len(set(srcs))


@pytest.mark.parametrize("lang", ["en"])
def test_tabs_and_composed_texts(lang):
    tabs = ["🧭 Procedura guidata", "📐 Progetto feed", "🎛️ Laboratorio", "📈 Simulazione & S11", "🖥️ Full-wave openEMS"]
    out = [i18n.tr(t, lang) for t in tabs]
    assert out[0] != tabs[0] and out[0].startswith("🧭 ")
    s = i18n.tr("Spillover 81.2% · illuminazione 90.1% · centro di fase +1.20 mm (davanti all'apertura).", lang)
    assert "81.2%" in s and "+1.20 mm" in s and "illuminazione" not in s and "centro di fase" not in s


def test_italian_is_identity_and_short_words_exact_only():
    assert i18n.tr("Celle per λ", "it") == "Celle per λ"
    assert i18n.tr("A", "en") == "To"
    assert i18n.tr("S11 a 47 GHz", "en") == "S11 a 47 GHz" or "To" not in i18n.tr("S11 a 47 GHz", "en")


def test_base64_untouched():
    b = "data:image/png;base64," + "Tm9uIGRpIHF1ZWxsbw==" * 50
    html = f"<h2>Avvisi</h2><img src=\"{b}\">"
    out = i18n.tr(html, "en")
    assert b in out and "Warnings" in out


class _FakeSt:
    def __init__(self):
        self.calls = []

    def button(self, label, **kw):
        self.calls.append(("button", label, kw))
        return False

    def radio(self, label, options, **kw):
        self.calls.append(("radio", label, [kw["format_func"](o) for o in options]))
        return options[0]

    def columns(self, n):
        return [_FakeSt() for _ in range(n)]

    def metric(self, label, value, delta=None, **kw):
        self.calls.append(("metric", label, value))

    def dataframe(self, data, **kw):
        self.calls.append(("dataframe", data))


def test_proxy_translates_display_but_not_values():
    i18n.set_lang("en")
    try:
        fake = _FakeSt()
        st = i18n.wrap(fake)
        assert st.radio("Polarizzazione", ["Lineare", "Circolare"]) == "Lineare"     # value stays Italian
        st.button("Applica modifiche", help="Ripristina progetto")
        st.dataframe([{"Valore": "Lineare"}])
        c = st.columns(2)
        c[0].metric("Centro di fase", "1 mm")
        assert fake.calls[0] == ("radio", "Polarisation", ["Linear", "Circular"])
        assert fake.calls[1][1] == "Apply changes" and fake.calls[1][2]["help"] == "Reset design"
        assert fake.calls[2][1] == [{"Value": "Linear"}]
        assert c[0]._o.calls[0][1] == "Phase centre"
    finally:
        i18n.set_lang("it")


def test_default_lang_from_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("FEEDLAB_CONFIG", str(tmp_path))
    from feedlab import openems_local
    openems_local.save_settings(language="en")
    assert i18n.default_lang() == "en"


def test_only_italian_and_english_with_manuals():
    from pathlib import Path
    assert set(i18n.LANGS) == {"it", "en"} == set(i18n.MANUALS)
    man = Path(__file__).resolve().parent.parent / "docs" / "manual"
    for lang, src in (("it", "manuale_it.md"), ("en", "user_manual_en.md")):
        imgs = re.findall(r"\{IMG\}/([\w.]+)", (man / src).read_text(encoding="utf-8"))
        assert len(imgs) >= 13 and all((man / "img" / lang / f).exists() for f in imgs), lang
