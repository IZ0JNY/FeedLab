"""Waveguide helpers: cutoff, guide wavelength, standard sizes for 10-134 GHz."""
from __future__ import annotations

import math
from dataclasses import dataclass

C0 = 299_792_458.0  # m/s

# Bessel roots for circular waveguide modes (TE: zeros of J'_n, TM: zeros of J_n)
CHI_TE = {"TE11": 1.84118, "TE21": 3.05424, "TE01": 3.83171, "TE31": 4.20119, "TE12": 5.33144}
CHI_TM = {"TM01": 2.40483, "TM11": 3.83171, "TM21": 5.13562, "TM02": 5.52008, "TM12": 7.01559}


def wavelength_mm(f_ghz: float) -> float:
    return C0 / (f_ghz * 1e9) * 1e3


def circular_cutoff_wavelength(diameter: float, mode: str = "TE11") -> float:
    """Cutoff wavelength (same units as diameter). TE11: 1.706 D, TM11: 0.82 D."""
    chi = CHI_TE.get(mode) or CHI_TM.get(mode)
    if chi is None:
        raise ValueError(f"unknown mode {mode}")
    return math.pi * diameter / chi


def guide_wavelength(lam: float, lam_c: float) -> float:
    """Guide wavelength; raises if below cutoff."""
    r = lam / lam_c
    if r >= 1.0:
        raise ValueError("mode is below cutoff")
    return lam / math.sqrt(1.0 - r * r)


def propagating_circular_modes(diameter: float, lam: float) -> list[str]:
    modes = {**CHI_TE, **CHI_TM}
    return sorted([m for m in modes if circular_cutoff_wavelength(diameter, m) > lam],
                  key=lambda m: -circular_cutoff_wavelength(diameter, m))


@dataclass(frozen=True)
class RectWG:
    name: str
    a_mm: float
    b_mm: float
    f_lo_ghz: float
    f_hi_ghz: float

    @property
    def fc_te10_ghz(self) -> float:
        return C0 / (2 * self.a_mm * 1e-3) / 1e9


RECT_WG = {w.name: w for w in [
    RectWG("WR-90", 22.86, 10.16, 8.2, 12.4),
    RectWG("WR-75", 19.05, 9.525, 10.0, 15.0),
    RectWG("WR-42", 10.668, 4.318, 18.0, 26.5),
    RectWG("WR-28", 7.112, 3.556, 26.5, 40.0),
    RectWG("WR-22", 5.690, 2.845, 33.0, 50.0),
    RectWG("WR-19", 4.775, 2.388, 40.0, 60.0),
    RectWG("WR-15", 3.759, 1.880, 50.0, 75.0),
    RectWG("WR-12", 3.099, 1.549, 60.0, 90.0),
    RectWG("WR-10", 2.540, 1.270, 75.0, 110.0),
    RectWG("WR-8", 2.032, 1.016, 90.0, 140.0),
    RectWG("WR-6", 1.651, 0.826, 110.0, 170.0),
    RectWG("WR-5", 1.295, 0.648, 140.0, 220.0),
]}

# Amateur microwave bands commonly used (narrowband segments), GHz
HAM_BANDS_GHZ = {
    "3cm": 10.368, "1.2cm": 24.048, "6mm": 47.088, "4mm": 76.032,
    "2.5mm": 122.25, "2mm": 134.928, "1.2mm": 241.92,
}


def suggest_rect_wg(f_ghz: float) -> list[str]:
    return [w.name for w in RECT_WG.values() if w.f_lo_ghz <= f_ghz <= w.f_hi_ghz]


def suggest_circular_diameter(f_ghz: float, lo: float = 0.70, hi: float = 0.81) -> tuple[float, float]:
    """Single-mode circular guide diameter range in mm (W1GHZ: 0.7-0.81 lambda for dual-mode input)."""
    lam = wavelength_mm(f_ghz)
    return lo * lam, hi * lam
