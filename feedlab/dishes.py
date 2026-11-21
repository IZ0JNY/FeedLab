"""Catalogue of commercial / well-documented dishes.

Every entry states where each number comes from. Manufacturer datasheets of TV offset dishes usually
give size, offset angle and an "F/D" in the *offset* convention (f / reflector width) plus, sometimes,
the required feed illumination angle — that angle is what the feed must be designed for (OE2IGL:
"use the opening angle, not f/D"). Focal lengths are rarely published: where absent they are estimated
as f ≈ F/D × outer width (checked against OE2IGL's measurement of the OP65: 0.66 × 670 ≈ 445 mm
measured) and flagged as estimates — measure your own dish (depth + string method) before final setup.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import reflector


@dataclass
class DishModel:
    maker: str
    model: str
    kind: str                       # offset | prime
    width_mm: float                 # outer width (offset: horizontal / short axis)
    height_mm: float                # outer height (offset: long axis)
    active_w_mm: float | None = None
    active_h_mm: float | None = None
    fD_maker: float | None = None   # as printed by the maker (offset convention for offset dishes)
    focal_mm: float | None = None   # published or measured focal length
    focal_source: str = ""          # "datasheet" | "measured (…)" | "estimated"
    offset_deg: float | None = None
    illum_deg: float | None = None  # required feed illumination (full angle)
    efficiency_pct: float | None = None
    gain: dict = field(default_factory=dict)   # GHz -> dBi
    collar_mm: str = ""
    material: str = ""
    source: str = ""
    notes: str = ""

    @property
    def label(self) -> str:
        return f"{self.maker} {self.model} ({self.kind}, {self.width_mm / 10:.0f}×{self.height_mm / 10:.0f} cm)"

    @property
    def D_mm(self) -> float:
        """Aperture diameter used for gain: projected (≈ active width) for offset, diameter for prime."""
        return self.active_w_mm or self.width_mm

    def focal(self) -> tuple[float | None, str]:
        if self.focal_mm:
            return self.focal_mm, self.focal_source
        if self.fD_maker and self.kind == "offset":
            return self.fD_maker * self.width_mm, "stimata (F/D × larghezza)"
        if self.fD_maker and self.kind == "prime":
            return self.fD_maker * self.width_mm, "datasheet (f/D)"
        return None, "non pubblicata: misura profondità e stringhe"

    def opening_deg(self) -> float | None:
        """Full illumination angle the feed must cover."""
        if self.illum_deg:
            return self.illum_deg
        f, _ = self.focal()
        if f is None:
            return None
        if self.kind == "prime":
            return 2 * reflector.half_angle_from_fD(f / self.width_mm)
        g = reflector.offset_geometry(f, self.D_mm, 0.0)
        return 2 * g.psi_S

    def fD_equiv(self) -> float | None:
        o = self.opening_deg()
        return None if o is None else reflector.fD_from_half_angle(o / 2)


GIB_SRC = "Gibertini datasheet serie XP (GB-TS-GR-001, 2010) — via conrad.com"
GIB_LN = "Gibertini OP LN datasheet — via telmor.pl"

CATALOG: list[DishModel] = [
    # --- Gibertini (datasheet: active area, F/D, offset, required feed illumination) ---
    DishModel("Gibertini", "OP 65 XP", "offset", 670, 715, 630, 675, 0.66, None, "", 21.3, 70, 69,
              {10.7: 35.38, 11.7: 36.20, 12.75: 36.90}, "40/23", "Alu 1.0 mm", GIB_SRC,
              "OE2IGL ha misurato 676×630, profondità 52 mm → f ≈ 445 mm"),
    DishModel("Gibertini", "OP 75 XP", "offset", 750, 800, 720, 770, 0.66, None, "", 21.0, 70, 69,
              {10.7: 36.54, 11.7: 37.32, 12.75: 38.10}, "40/23", "Alu", GIB_SRC),
    DishModel("Gibertini", "OP 85 XP", "offset", 850, 905, 815, 870, 0.67, None, "", 21.1, 69, 69,
              {10.7: 37.62, 11.7: 38.40, 12.75: 39.15}, "40/23", "Alu 1.2 mm", GIB_SRC),
    DishModel("Gibertini", "OP 100 XP", "offset", 970, 1040, 940, 1010, 0.66, None, "", 21.0, 70, 70,
              {10.7: 38.90, 11.7: 39.70, 12.75: 40.44}, "40/23", "Alu 1.3 mm", GIB_SRC),
    DishModel("Gibertini", "OP 75 LN", "offset", 750, 800, 720, 770, 0.67, None, "", 21.0, 70, 69,
              {10.7: 36.6, 11.7: 37.4, 12.75: 38.2}, "40/23", "acciaio zincato", GIB_LN),
    DishModel("Gibertini", "OP 85 LN", "offset", 850, 905, 815, 870, 0.67, None, "", 21.1, 69, 70,
              {10.7: 37.8, 11.7: 38.5, 12.75: 39.2}, "40/23", "acciaio zincato", GIB_LN),
    DishModel("Gibertini", "OP 125 L", "offset", 1245, 1335, 1210, 1300, 0.66, None, "", 21.3, None, None,
              {}, "", "Alu", "Gibertini OP125L installation guide (kosmosat.gr) + listini",
              "datasheet: F/D 0.66, beam 1.32° @11.7 GHz"),
    # --- Fracarro ---
    DishModel("Fracarro", "RO125AP", "offset", 1240, 1345, None, None, None, None, "", 23.0, None, 74,
              {10.7: 41.0, 11.7: 41.6, 12.7: 42.4}, "", "Alu", "Fracarro RO125AP datasheet",
              "il datasheet riporta '0.66' nella riga 'front back ratio': probabile F/D — non usato"),
    # --- Triax ---
    DishModel("Triax", "TDS 80LG (120509)", "offset", 710, 790, None, None, 0.62, None, "", 25.6, None, None,
              {11.7: 37.5}, "40", "acciaio", "Triax datasheet art. 120509 (av-connection)"),
    DishModel("Triax", "TDS 80A (126508)", "offset", 745, 845, None, None, 0.60, None, "", 25.0, None, None,
              {10.75: 37.0, 11.75: 38.1, 12.75: 39.1}, "40", "acciaio", "Triax datasheet art. 126508 (alltrade)"),
    DishModel("Triax", "TDS PRO 65", "offset", 620, 680, 600, 660, 0.60, None, "", None, None, None,
              {}, "40", "acciaio 0.6 mm", "Triax TDS PRO leaflet (alltrade)"),
    DishModel("Triax", "TDS PRO 80", "offset", 790, 850, 750, 830, 0.60, None, "", None, None, None,
              {}, "40", "acciaio 0.7 mm", "Triax TDS PRO leaflet (alltrade)"),
    DishModel("Triax", "TDA 64", "offset", 600, 650, None, None, None, None, "", 26.0, None, None,
              {11.7: 35.8}, "40", "Alu", "Triax TDA 64 datasheet (zajadacz.de)", "F/D non pubblicato"),
    # --- Kathrein (no f/D published in the datasheets found) ---
    DishModel("Kathrein", "CAS 90", "offset", 900, 900, None, None, None, None, "", None, None, None,
              {}, "", "Alu", "Kathrein CAS 90 datasheet (diametro e banda)", "F/D/focale non pubblicati: misurare"),
    DishModel("Kathrein", "CAS 120", "offset", 1200, 1200, None, None, None, None, "", None, None, None,
              {11.2: 41.5, 12.1: 42.15, 12.6: 42.5}, "", "Alu", "Kathrein CAS 120/G datasheet (radiomuseum/zajadacz)",
              "HPBW < 1.43°; F/D/focale non pubblicati: misurare"),
    # --- Channel Master / Andrew / Skyware ---
    DishModel("Channel Master / Skyware", "Type 123 1.2 m", "offset", 1200, 1300, 1200, None, None, None, "",
              16.97, None, None, {12.0: 41.8, 14.3: 43.3}, "", "SMC/acciaio",
              "Skyware Global Type 123 Class II datasheet; offset 16.97° da manuale Andrew (citato su satsig)",
              "'long focal length optics'; focale non pubblicata"),
    DishModel("Andrew / Channel Master / Skyware", "Type 243 2.4 m", "offset", 2460, 2664, 2400, None, None, None, "",
              22.62, None, 60, {3.9: 38.0, 6.1: 42.0, 12.0: 47.4, 14.3: 48.9}, "", "SMC / vetroresina, 2 pezzi",
              "Channel Master 2.4 m Offset Tx/Rx manual (outline drawing App. A, purplesat.com) + Skyware Global "
              "Type 243 datasheet Ku Class III (REV 11/14) e C-band Linear (REV 03/15)",
              "riflettore 96.87\" × 104.87\" (2460 × 2664 mm), apertura efficace 2.4 m, offset 22.62° tra asse "
              "meccanico e asse del fascio (manuale); HPBW 0.71° @12 GHz, 0.59° @14.3 GHz; η ≈ 60% calcolata dal "
              "guadagno; feed originale WR75 (Ku) / CPR-229 (C). Focale non pubblicata: misura la profondità al "
              "centro e usa 'Misure sul campo' (asse lungo 2664, corto 2460)"),
    DishModel("Channel Master", "1 m (W1GHZ)", "offset", 997, 1083, None, None, None, 604, "misurata W1GHZ (App.5A)", None,
              None, None, {}, "", "", "W1GHZ Antenna Book App. 5A", "tilt 67.5° dall'orizzontale, stringa sup. 1018 mm, f/D eq. 0.68"),
    # --- dishes measured by W1GHZ (App. 5A) ---
    DishModel("Sony", "DSS 18\"", "offset", 451, 521, None, None, None, 266, "misurata W1GHZ", None, None, None, {}, "", "",
              "W1GHZ App. 5A", "tilt 65.9°, f/D eq. 0.68"),
    DishModel("RCA", "DSS 18\" (SMC)", "offset", 457, 495, None, None, None, 278, "misurata W1GHZ", None, None, 63, {}, "", "SMC",
              "W1GHZ App. 5A / cap. 5", "63% misurato a 10 GHz con horn rettangolare"),
    DishModel("Dish Network", "18\"", "offset", 460, 504, None, None, None, 287, "misurata W1GHZ", None, None, None, {}, "", "",
              "W1GHZ App. 5A"),
    DishModel("generico", "offset 60 cm acciaio (W1GHZ)", "offset", 600, 640, None, None, None, 403, "misurata W1GHZ", None,
              None, None, {}, "", "acciaio", "W1GHZ App. 5A"),
    DishModel("generico", "offset 80 cm metallo (W1GHZ)", "offset", 797, 848, None, None, None, 593, "misurata W1GHZ", None,
              None, None, {}, "", "", "W1GHZ App. 5A", "f/D eq. 0.81"),
    # --- prime focus ---
    DishModel("Edmund Optics", "parabolic 12\" (305 mm)", "prime", 305, 305, None, None, 0.25, None, "", None, None, None,
              {}, "", "Alu quasi ottico", "Edmund Optics / W1GHZ MUD 2023", "ideale per Cassegrain 47-122 GHz"),
    DishModel("Edmund Optics", "parabolic 18\" (457 mm)", "prime", 457, 457, None, None, 0.25, None, "", None, None, None,
              {}, "", "Alu", "Edmund Optics / W1GHZ"),
    DishModel("Edmund Optics", "parabolic 24\" (609 mm)", "prime", 609, 609, None, None, 0.25, None, "", None, None, None,
              {}, "", "Alu", "Edmund Optics / W1GHZ / VE2UG 47 GHz Cassegrain"),
    DishModel("SHF Microwave", "300 mm f/D 0.6", "prime", 300, 300, None, None, 0.6, None, "", None, None, None,
              {}, "", "Alu", "W1GHZ 'Optimized Cassegrain' 2023 (47 GHz)"),
    DishModel("link 38 GHz", "30 cm f/D 0.3 (OE2IGL)", "prime", 300, 300, None, None, 0.3, 90, "OE2IGL", None, None, None,
              {}, "", "Alu tornito", "OE2IGL pagina 241/134/122 GHz", "superficie adatta a 122-241 GHz"),
]


def by_label() -> dict[str, DishModel]:
    return {d.label: d for d in CATALOG}
