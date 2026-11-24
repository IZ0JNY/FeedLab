"""Feed materials: conductivity, surface roughness and the resulting ohmic loss / noise of the feed.

Ohmic loss is estimated for the TE11 mode along the interior (staircase sections):
    alpha = Rs_eff / (a * eta0 * sqrt(1 - (fc/f)^2)) * ((fc/f)^2 + 1/(chi'^2 - 1)),  chi' = 1.8412
with Rs = sqrt(pi f mu0 / sigma) and the Hammerstad roughness factor
    K = 1 + (2/pi) atan(1.4 (Rq/delta)^2).
The noise added by a lossy feed at physical temperature T is (1 - eta_ohm) * T.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MU0 = 4e-7 * math.pi
ETA0 = 376.730313


@dataclass(frozen=True)
class Material:
    name: str
    sigma: float          # S/m
    rq_um: float          # typical RMS roughness of the finished inner surface (µm)
    density: float        # g/cm3 (for weight)
    notes: str = ""
    color: str = "#c9a227"   # display colour of the metal (section and 3D model)


MATERIALS = {m.name: m for m in [
    Material("Rame OFHC (Cu-ETP)", 5.80e7, 0.4, 8.94, "ottimo conduttore, si ossida: proteggere", "#b87333"),
    Material("Rame argentato (Ag ≥ 3 µm)", 6.10e7, 0.3, 8.94, "argentatura ≥ 3-5 δ; migliore per RX a mm-wave", "#c0c0c0"),
    Material("Rame dorato (Au flash su Ni)", 4.10e7, 0.3, 8.94, "evitare il nichel sotto: è magnetico e dissipa", "#d4af37"),
    Material("Ottone CuZn39Pb3", 1.50e7, 0.4, 8.47, "ottima lavorabilità al tornio; perdite ~2× rame", "#c9a227"),
    Material("Ottone argentato", 6.10e7, 0.3, 8.47, "lavorabilità dell'ottone + perdite dell'argento", "#c0c0c0"),
    Material("Alluminio 6082/6061 T6", 2.50e7, 0.6, 2.70, "leggero; anodizzazione solo esterna", "#a8a9ad"),
    Material("Alluminio 1050 puro", 3.50e7, 0.6, 2.71, "più conduttivo ma tenero", "#bfc1c2"),
    Material("Acciaio inox AISI 304", 1.40e6, 0.4, 8.0, "solo strutture: perdite elevate", "#8c9196"),
    Material("Stampa 3D + vernice al rame", 1.0e6, 5.0, 1.3, "perdite alte, solo prototipi/bande basse", "#9c5b34"),
    Material("Stampa 3D + elettrodeposizione rame", 5.0e7, 3.0, 2.0, "rugosità della stampa domina sopra 24 GHz", "#b87333"),
    # materials of the online CNC services JLCCNC, PCBWay and Weerg (typical conductivity of the alloy; roughness of
    # their standard "as machined" finish, Rq ≈ 2 µm: ask for a polished inside to get the lower losses above)
    Material('Alluminio 6061-T6 (JLCCNC, PCBWay)', 2.5e+07, 2.0, 2.7, "il più comune; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Alluminio 6082-T6 Anticorodal (Weerg)', 2.6e+07, 2.0, 2.7, "resistente alla corrosione; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Alluminio 7075-T6 Ergal (JLCCNC, PCBWay, Weerg)', 1.9e+07, 2.0, 2.81, "molto resistente, conduce meno del 6061; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Alluminio 5083 (Weerg)', 1.6e+07, 2.0, 2.66, "anticorrosione marina, conduce poco; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Alluminio 5052 (PCBWay)', 2e+07, 2.0, 2.68, "anticorrosione; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Alluminio 2011 (Weerg)', 2.3e+07, 2.0, 2.83, "da tornio, ottima lavorabilità; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Alluminio 2A12 / 2024 (PCBWay)', 1.74e+07, 2.0, 2.78, "aeronautico, conduce poco; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#a8a9ad'),
    Material('Ottone H59 (JLCCNC)', 1.6e+07, 2.0, 8.4, "ottone da lavorazione; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#c9a227'),
    Material('Ottone H62 (JLCCNC)', 1.57e+07, 2.0, 8.43, "ottone; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#c9a227'),
    Material('Ottone C360 (PCBWay)', 1.5e+07, 2.0, 8.5, "ottone da tornio (come CuZn39Pb3); finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#c9a227'),
    Material('Ottone OT58 CuZn40Pb2 (Weerg)', 1.5e+07, 2.0, 8.4, "ottone da tornio; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#c9a227'),
    Material('Rame T2 (JLCCNC)', 5.7e+07, 2.0, 8.9, "rame puro 99.9 %; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#b87333'),
    Material('Rame C101 OFE (Weerg)', 5.85e+07, 2.0, 8.94, "rame senza ossigeno; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#b87333'),
    Material('Rame C110 ETP (PCBWay)', 5.8e+07, 2.0, 8.94, "rame elettrolitico; finitura di serie Ra 1.6–3.2 µm: per l'interno chiedi Ra ≤ 0.8 (perdite più basse)", '#b87333'),
    Material('Bronzo CuSn12 (Weerg)', 5.5e+06, 2.0, 8.7, "perdite alte (circa 3× l'ottone): non consigliato per l'interno", '#a07a3c'),
    Material('Acciaio inox 316L (JLCCNC, PCBWay, Weerg)', 1.33e+06, 2.0, 8.0, 'solo strutture: perdite elevate', '#8c9196'),
    Material('Titanio Ti-6Al-4V (PCBWay)', 5.8e+05, 2.0, 4.43, 'solo strutture: perdite molto elevate', '#878681'),
]}


def skin_depth_um(sigma: float, f_ghz: float) -> float:
    return 1e6 / math.sqrt(math.pi * f_ghz * 1e9 * MU0 * sigma)


def surface_resistance(sigma: float, f_ghz: float, rq_um: float = 0.0) -> float:
    Rs = math.sqrt(math.pi * f_ghz * 1e9 * MU0 / sigma)
    d = skin_depth_um(sigma, f_ghz)
    K = 1 + 2 / math.pi * math.atan(1.4 * (rq_um / d) ** 2)
    return Rs * K


def te11_attenuation_db_per_m(radius_mm: float, f_ghz: float, sigma: float, rq_um: float = 0.0) -> float:
    a = radius_mm * 1e-3
    fc = 299_792_458.0 * 1.8412 / (2 * math.pi * a) / 1e9
    r = fc / f_ghz
    if r >= 1:
        return float("inf")
    Rs = surface_resistance(sigma, f_ghz, rq_um)
    alpha = Rs / (a * ETA0 * math.sqrt(1 - r * r)) * (r * r + 1 / (1.8412 ** 2 - 1))
    return 8.686 * alpha


def feed_ohmic_loss_db(sections, f_ghz: float, material: Material, rq_um: float | None = None,
                       skip_below_cutoff: bool = True) -> float:
    """Total TE11 conductor loss (dB) along staircase sections [(radius_mm, length_mm)]."""
    rq = material.rq_um if rq_um is None else rq_um
    tot = 0.0
    for r, L in sections:
        a = te11_attenuation_db_per_m(r, f_ghz, material.sigma, rq)
        if math.isinf(a):
            if skip_below_cutoff:
                continue
        tot += a * L * 1e-3
    return tot


def noise_from_loss(loss_db: float, t_phys: float = 290.0) -> float:
    return (1 - 10 ** (-loss_db / 10)) * t_phys


def color(name: str) -> str:
    """Display colour (hex) of a material, brass if unknown."""
    m = MATERIALS.get(name)
    return m.color if m else "#c9a227"


def rgba(name: str, alpha: float) -> str:
    h = color(name).lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# ---------------------------------------------------------------- guide for choosing the material
# ratings 1 (poor) … 5 (excellent): machinability, price (5 = cheapest), availability, outdoor resistance
# (weather, corrosion), surface treatments (how easily it is silver/gold plated, or protected), then pros and cons.
# Losses are not rated by hand: they come from the conductivity (see loss_vs_copper).
_CU = ("perdite minime; si argenta e si dora facilmente",
       "costa più di ottone e alluminio; tenero e «gommoso» da lavorare; si ossida (annerisce): proteggere")
_BRASS = ("facilissimo da tornire e fresare, economico; si argenta molto bene",
          "pesante; perdite circa 2× il rame; contiene piombo")
_AL_CNC = ("il più economico e veloce da ordinare; leggero",
           "finitura di serie ruvida: chiedi l'interno lucidato; argentatura difficile (serve zincatura)")
GUIDE = {
    "Rame argentato (Ag ≥ 3 µm)": (2, 1, 2, 2, 5, "le perdite più basse in assoluto: il migliore per ricezione a mm-wave",
                                   "costoso; l'argento annerisce all'aria (solfuri): tenere chiuso o proteggere"),
    "Ottone argentato": (5, 3, 3, 2, 5, "lavorabilità dell'ottone con le perdite dell'argento: ottimo compromesso",
                         "costo dell'argentatura; l'argento annerisce all'aria"),
    "Rame OFHC (Cu-ETP)": (2, 2, 3, 2, 5, *_CU),
    "Rame C101 OFE (Weerg)": (2, 2, 4, 2, 5, *_CU),
    "Rame C110 ETP (PCBWay)": (2, 2, 4, 2, 5, *_CU),
    "Rame T2 (JLCCNC)": (2, 2, 4, 2, 5, *_CU),
    "Stampa 3D + elettrodeposizione rame": (5, 3, 2, 3, 4, "leggero, forme complesse, con la conducibilità del rame",
                                            "rugosità della stampa; spessore del rame da verificare; servizio specializzato"),
    "Rame dorato (Au flash su Ni)": (2, 1, 2, 5, 5, "non si ossida mai: contatti e superfici stabili nel tempo",
                                     "costoso; il nichel sotto l'oro aumenta le perdite"),
    "Alluminio 1050 puro": (2, 4, 3, 4, 2, "conduce più delle leghe di alluminio; leggero",
                            "tenero: si impasta sull'utensile, bave, filetti deboli"),
    "Alluminio 6082-T6 Anticorodal (Weerg)": (4, 5, 5, 4, 2, "economico, leggero, buona resistenza alla corrosione",
                                              _AL_CNC[1]),
    "Alluminio 6082/6061 T6": (4, 5, 5, 4, 2, "leggero, economico, si trova ovunque",
                               "argentatura e doratura difficili (serve zincatura); l'anodizzazione all'interno aumenta le perdite"),
    "Alluminio 6061-T6 (JLCCNC, PCBWay)": (4, 5, 5, 4, 2, *_AL_CNC),
    "Alluminio 2011 (Weerg)": (5, 4, 3, 2, 2, "trucioli corti: ottimo al tornio", "si corrode facilmente all'aperto: proteggere"),
    "Alluminio 5052 (PCBWay)": (3, 4, 4, 5, 2, "buona resistenza alla corrosione", "più tenero del 6061 e con perdite maggiori"),
    "Alluminio 7075-T6 Ergal (JLCCNC, PCBWay, Weerg)": (4, 3, 4, 3, 2, "molto resistente meccanicamente",
                                                        "conduce meno del 6061 e costa di più: per un feed non serve"),
    "Alluminio 2A12 / 2024 (PCBWay)": (4, 3, 4, 2, 2, "resistente (aeronautico)", "conduce poco e si corrode: sconsigliato"),
    "Alluminio 5083 (Weerg)": (3, 4, 3, 5, 2, "ottimo all'esterno, anche in ambiente marino",
                               "conduce poco: perdite circa 1.25× il 6061"),
    "Ottone H59 (JLCCNC)": (5, 4, 5, 3, 5, *_BRASS),
    "Ottone H62 (JLCCNC)": (4, 4, 4, 3, 5, "ottone con poco piombo; si argenta molto bene",
                            "un po' meno lavorabile dell'H59; pesante"),
    "Ottone CuZn39Pb3": (5, 4, 5, 3, 5, *_BRASS),
    "Ottone C360 (PCBWay)": (5, 4, 5, 3, 5, *_BRASS),
    "Ottone OT58 CuZn40Pb2 (Weerg)": (5, 4, 5, 3, 5, *_BRASS),
    "Bronzo CuSn12 (Weerg)": (3, 2, 3, 5, 4, "durissimo e resistente alla corrosione", "perdite alte: non adatto all'interno del feed"),
    "Acciaio inox AISI 304": (2, 3, 5, 5, 2, "robusto e inossidabile", "perdite molto alte: solo staffe e strutture"),
    "Acciaio inox 316L (JLCCNC, PCBWay, Weerg)": (2, 2, 4, 5, 2, "il più resistente alla corrosione (anche marina)",
                                                  "perdite molto alte: solo staffe e strutture"),
    "Stampa 3D + vernice al rame": (5, 5, 5, 2, 1, "costo minimo, forme libere, pronto subito",
                                    "perdite alte; la plastica si deforma al sole e al caldo"),
    "Titanio Ti-6Al-4V (PCBWay)": (1, 1, 3, 5, 1, "leggero e indistruttibile", "perdite altissime e costo elevato: inutile per un feed"),
}


def loss_vs_copper(m: Material) -> float:
    """Ohmic loss of a smooth wall relative to copper (5.8·10⁷ S/m): R_s ∝ 1/√σ."""
    return (5.8e7 / m.sigma) ** 0.5
