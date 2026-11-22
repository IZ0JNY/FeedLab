"""Credits tab: author, version and every source used by FeedLab.

Texts are Italian; the streamlit proxy (`i18n.wrap`) translates them through `i18n_catalog`.
"""
from __future__ import annotations

from . import __version__, dishes

AUTHOR = "Ivan De Cesaris, IZ0JNY"
EMAIL = "ivan@iz0jny.it"
REPO = "https://github.com/IZ0JNY/mwfeeddesign"

TECH_SOURCES = [
    ("Paul Wade, W1GHZ", "*The W1GHZ Online Microwave Antenna Book*, FEEDPATT/PHASEPAT, Microwave Update 2006–2024",
     "efficienza del riflettore, feed W2IMU, VE4MA, Chaparral, horn rettangolari, Cassegrain, misure di parabole offset",
     "https://www.w1ghz.org/antbook/contents.htm"),
    ("Gerald Ihninger, OE2IGL", "design guide (openEMS)",
     "W2IMU, Pickett-Potter, corrugato assiale, piastrina λ/4 guida circolare→rettangolare (ottimizzazione HB9PZK)",
     "https://wettersat.bplaced.net/index.html"),
    ("Per-Simon Kildal", "*Foundations of Antenna Engineering*",
     "fattorizzazione dell'efficienza, ottimo del subriflettore", "https://www.kildal.se"),
    ("Constantine A. Balanis", "*Antenna Theory: Analysis and Design*, Wiley (4ª ed. 2016)",
     "horn piramidali, settoriali e conici, efficienza dei riflettori, relazioni di base (VSWR, polarizzazione, Friis)", ""),
    ("P. D. Potter (1963), H. M. Pickett et al. (1984), Skobelev", "horn dual-mode", "", ""),
    ("Kumar / VE4MA, Wohlleben (Chaparral), G3RPE, Granet", "feed a choke, horn rettangolare per f/D, Cassegrain/Gregorian",
     "", ""),
    ("J. Ruze (1966), Hammerstad & Bekkadal", "perdita per errori di superficie, rugosità e perdite ohmiche", "", ""),
    ("Al Ward, W5LUA", "*The Excitement & Challenges of 24 GHz EME* (2012), con i calcolatori VK3UM",
     "feed W2IMU modificato a 24 GHz, perdita di percorso EME, rumore di Sole e Luna, assorbimento atmosferico", ""),
    ("J. D. Kraus", "*Radio Astronomy* (1966)", "temperatura della Luna in funzione della fase", ""),
    ("Jeffrey Pawlan, WA6KBL", "*Easy to Manufacture and Extremely High Performance Dual Mode Feedhorns with Direct "
     "Waveguide Input For the 10GHz and 24GHz Bands*, DUBUS", "feed dual-mode con ingresso diretto in guida rettangolare",
     "https://www.researchgate.net/publication/384900000"),
    ("Ivan De Cesaris, IZ0JNY", "iz0jny.it: feed W2IMU 24 GHz per EME (CST, disegni e STEP)",
     "accoppiamento piastra WR-42 / feed con viti in lamatura, misure di rumore solare", "https://www.iz0jny.it/"),
    ("Flann Microwave", "*Waveguide and Flange Data*; MIL-DTL-3922/67C", "foratura delle flange standard delle guide WR",
     "https://flann.com/wp-content/uploads/2025/02/Waveguide-and-Flange-Data.pdf"),
    ("Thorsten Liebig — openEMS", "FDTD, tutorial \"Conical Horn\"", "", "https://openems.de"),
]

GITHUB = ["rusk2ua/offset-microwave-dish-comparisons", "Abraxas3d/122GHz", "david-deboer/hera-cst",
          "diablowu/dish-fd-feed", "IRNAS/SatelliteDishHeadHolder", "vantalane/dual_band_LHCP_helical_feed"]

LIBRARIES = [("Python", "https://www.python.org"), ("NumPy", "https://numpy.org"), ("SciPy", "https://scipy.org"),
             ("Matplotlib", "https://matplotlib.org"), ("Plotly", "https://plotly.com/python/"),
             ("Streamlit", "https://streamlit.io"), ("CadQuery / Open CASCADE", "https://cadquery.readthedocs.io"),
             ("openEMS", "https://openems.de")]


def issue_url(feed_kind: str = "", f_ghz=None) -> str:
    """GitHub 'new issue' page with version, system and current design filled in."""
    import platform
    from urllib.parse import urlencode
    body = (f"**Versione FeedLab:** {__version__}\n**Sistema:** {platform.system()} {platform.release()}\n"
            f"**Feed / frequenza:** {feed_kind} {f_ghz if f_ghz is not None else ''} GHz\n\n"
            "**Cosa è successo:**\n\n**Cosa ti aspettavi:**\n\n**Passi per riprodurre:**\n1. \n")
    return f"{REPO}/issues/new?" + urlencode({"title": "", "body": body})


def dish_sources() -> list[str]:
    return sorted({d.source for d in dishes.CATALOG if d.source})


def render(st, header: bool = True) -> None:
    if header:
        st.header("ℹ️ Credits")
    st.markdown(f"**FeedLab — Laboratorio di Progettazione di feed/illuminatori a microonde**  \n"
                f"Versione **{__version__}**")
    st.markdown(f"Software sviluppato da **{AUTHOR}**  \n"
                f"✉️ [{EMAIL}](mailto:{EMAIL}) · GitHub: [{REPO.split('//')[1]}]({REPO})")
    st.subheader("Fonti tecniche")
    lines = []
    for who, what, topics, url in TECH_SOURCES:
        s = f"- **{who}** — {what}"
        if topics:
            s += f": {topics}"
        if url:
            s += f" — [{url.split('//')[1].rstrip('/')}]({url})"
        lines.append(s)
    st.markdown("\n".join(lines))
    st.subheader("Progetti GitHub di riferimento")
    st.markdown("\n".join(f"- [{g}](https://github.com/{g})" for g in GITHUB))
    st.subheader("Dati delle parabole commerciali")
    st.markdown("\n".join(f"- {x}" for x in dish_sources()))
    st.caption("I marchi citati appartengono ai rispettivi proprietari. I dati vengono dai datasheet pubblici e possono "
               "contenere stime, indicate nel catalogo.")
    st.subheader("Librerie software")
    st.markdown(" · ".join(f"[{n}]({u})" for n, u in LIBRARIES))
    st.caption("FeedLab è una reimplementazione indipendente: non contiene codice né file di dati originali delle fonti "
               "citate. I risultati sono stime di progetto: verificarli con simulazione full-wave e misure prima della "
               "produzione.")
