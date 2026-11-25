"""Every interface text must be all Italian in Italian and all English in English.

Checks each catalogue entry (Italian source → English): the Italian text must not contain English words and the
English one must not contain Italian words. Proper names, quoted titles, links, code and {fields} are ignored.
The whole interface can also be rendered and checked with tools/lang_audit.py (slower, run it before a release).
"""
import re

from feedlab.i18n_catalog import ENTRIES

IT_WORDS = ("il gli della dello dei delle degli alla nella nelle sono una dalla sulla più anche oppure ogni questo "
            "questa senza sotto sopra guida piastrina foro fori viti parabola perdite lunghezza diametro spessore "
            "nessun nessuna scegli seleziona clicca vedi valore valori qui ancora tutti tutte perché quindi poi già")
EN_WORDS = ("the and with from this that which your you click select choose plate hole holes screw screws dish dishes "
            "waveguide thickness length width value values copper brass will should between than when")   # "horn" stays in feed names


def _rx(words):
    return re.compile(r"(?<![\w'’])(" + "|".join(words.split()) + r")(?![\w'’])", re.I)


def _strip(s):
    """drop what is not interface language: links, URLs, *titles*, 'quotes', `code`, {fields}"""
    return re.sub(r"\[[^\]]*\]\([^)]*\)|https?://\S+|\*[^*]+\*|'[^']{3,}'|`[^`]*`|\{[^}]*\}", " ", s)


def test_italian_texts_have_no_english_words():
    rx = _rx(EN_WORDS)
    bad = [(sorted({m.group(1).lower() for m in rx.finditer(_strip(it))}), it) for it, _ in ENTRIES]
    bad = [b for b in bad if b[0]]
    assert not bad, "\n".join(f"{w} | {t[:120]}" for w, t in bad)


def test_english_texts_have_no_italian_words():
    rx = _rx(IT_WORDS)
    bad = [(sorted({m.group(1).lower() for m in rx.finditer(_strip(en))}), en) for _, en in ENTRIES]
    bad = [b for b in bad if b[0]]
    assert not bad, "\n".join(f"{w} | {t[:120]}" for w, t in bad)


def test_dish_catalogue_texts():
    """Materials and notes of the dish catalogue: Italian in Italian, translated in English (no German either)."""
    from feedlab import dishes, i18n
    it_rx, de_rx = _rx(IT_WORDS + " vetroresina riscaldabile pressofusione"), _rx("pulverbeschichtet brennpunkt und mit")
    bad = []
    for d in dishes.CATALOG:
        for v in (d.material, d.notes):
            if not v:
                continue
            en = i18n.tr(v, "en")
            if de_rx.search(v) or it_rx.search(_strip(en)):
                bad.append((v, en))
    assert not bad, bad
