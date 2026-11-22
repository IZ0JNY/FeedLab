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
