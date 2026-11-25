"""Feed-horn design calculators (dimensions in mm unless suffix _lambda).

Each function returns a `Design` with dimensions, the source of the rule and validity notes.
Sources: W1GHZ (HDL_ANT, Antenna Book ch.6, MUD 2006/2023/2024 papers), OE2IGL design guides (2024-2026),
Skobelev et al. 2001, Turrin 1967, G3RPE, Kraus, Balanis/Reilly (pyramidal phase centre).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.special import fresnel

from .waveguide import wavelength_mm, guide_wavelength

DEG = math.pi / 180.0


def _is_length(key: str) -> bool:
    return not (key.endswith(("_deg", "_pct", "_dbi", "_ghz", "fD")) or key in ("rings",))


@dataclass
class Design:
    kind: str
    f_ghz: float
    dims_mm: dict
    source: str
    notes: list = field(default_factory=list)

    @property
    def lam(self) -> float:
        return wavelength_mm(self.f_ghz)

    def in_lambda(self) -> dict:
        return {k: (v / self.lam if isinstance(v, (int, float)) and _is_length(k) else v)
                for k, v in self.dims_mm.items()}

    def __str__(self):
        lines = [f"{self.kind} @ {self.f_ghz} GHz (λ = {self.lam:.3f} mm) — {self.source}"]
        for k, v in self.dims_mm.items():
            if isinstance(v, (int, float)):
                extra = f"  ({v / self.lam:.3f} λ)" if _is_length(k) else ""
                lines.append(f"  {k:22s} {v:10.3f}{extra}")
            else:
                lines.append(f"  {k:22s} {v}")
        lines += [f"  note: {n}" for n in self.notes]
        return "\n".join(lines)


# ---------------- W2IMU dual-mode ----------------
def w2imu_phasing_length_lambda(B_lambda: float) -> float:
    """C = 0.75 / (1/lg_TE11 - 1/lg_TM11) in the output section of diameter B (Turrin/W1GHZ)."""
    lg1 = guide_wavelength(1.0, 1.706 * B_lambda)
    lg2 = guide_wavelength(1.0, 0.82 * B_lambda)
    return 0.75 / (1 / lg1 - 1 / lg2)


def w2imu(f_ghz: float, B_lambda: float | None = None, fD: float | None = None,
          input_lambda: float = 0.76, flare_half_deg: float | None = None) -> Design:
    """Classic W2IMU (W1GHZ book 6.5): flare = 44.6 deg * lambda/B, C from mode phasing; B ~ 2.35 f/D."""
    lam = wavelength_mm(f_ghz)
    if B_lambda is None:
        if fD is None:
            raise ValueError("give B_lambda or fD")
        B_lambda = 2.35 * fD
    notes = []
    if not 1.22 <= B_lambda <= 1.9:
        notes.append("B fuori da 1.22-1.9 λ: TM11 sotto il taglio o propagano modi superiori (TE12)")
    flare = flare_half_deg or 44.6 / B_lambda
    C = w2imu_phasing_length_lambda(B_lambda)
    A = input_lambda
    flare_len = (B_lambda - A) / 2 / math.tan(flare * DEG)
    return Design("W2IMU dual-mode", f_ghz,
                  {"input_diam": A * lam, "aperture_diam_B": B_lambda * lam, "flare_half_deg": flare,
                   "flare_length": flare_len * lam, "phasing_length_C": C * lam},
                  "Turrin 1967 / W1GHZ ch.6.5", notes + ["centro di fase ≈ apertura", "banda stretta (fasatura dei modi)"])


def w2imu_oe2igl(f_ghz: float, opening_angle_deg: float) -> Design:
    """OE2IGL W2IMU dual-mode design guide (parametric calculation) (openEMS-verified); input = full dish opening angle."""
    lam = wavelength_mm(f_ghz)
    th = opening_angle_deg
    fc = 0.77 * f_ghz
    A = 299.792458 / 1.706 / fc
    B = (-1.77531e-8 * th ** 4 + 5.66609e-6 * th ** 3 - 6.67931e-4 * th ** 2 + 0.0340124 * th - 0.60017) * th * lam
    lg1 = lam / math.sqrt(1 - (lam / 1.706 / B) ** 2)
    lg2 = lam / math.sqrt(1 - (lam / 0.82 / B) ** 2)
    C = (-7.41104e-10 * th ** 5 + 3.00061e-7 * th ** 4 - 4.83865e-5 * th ** 3 + 3.88389e-3 * th ** 2
         - 0.155265 * th + 2.4863) * th / (1 / lg1 - 1 / lg2)
    alpha = 44.6 * lam / B
    return Design("W2IMU Dual-Mode Feedhorn (parametric calculation OE2IGL)", f_ghz,
                  {"input_diam_A": A, "aperture_diam_B": B, "length_C": C, "flare_half_deg": alpha,
                   "f_min_ghz": 1.15 * fc, "f_max_ghz": 1.57 * fc},
                  "OE2IGL DualModeHorn-design-guide 2024",
                  ["η 77% (f/D 0.5) … 80% (f/D 0.8)", "usa l'angolo di apertura completo della parabola, non l'f/D"])


def large_w2imu_30deg(f_ghz: float, B_lambda: float = 1.78) -> Design:
    """W1GHZ/W1FKF 2023: large W2IMU with 30 deg flare (60 deg centre drill); C re-adjusted.
    Published: 1.78λ → C 3.7λ, 13.9 dBi, BW-10 ±35°; 1.65λ → 2.9λ; 1.94λ → 4.3λ."""
    table = np.array([[1.63, 2.9], [1.65, 2.9], [1.74, 3.7], [1.78, 3.7], [1.79, 3.7], [1.94, 4.3]])
    C = float(np.interp(B_lambda, table[:, 0], table[:, 1]))
    lam = wavelength_mm(f_ghz)
    return Design("Large W2IMU, 30° flare", f_ghz,
                  {"aperture_diam_B": B_lambda * lam, "length_C": C * lam, "flare_half_deg": 30.0,
                   "input_diam": 0.76 * lam},
                  "W1GHZ & W1FKF, MUD 2023 (Table 1)",
                  ["C interpolata dalla tabella pubblicata", "assottigliare il bordo (smusso a 45°)", "centro di fase ≈ apertura"])


# ---------------- Skobelev / Pickett-Potter ----------------
SKOBELEV_BEST = np.array([
    # D_ap λ, L_flare λ, f/D, eta, PC λ, F/B dB, SLL dB, gain dBi, BW10 deg
    [1.5, 2.01, 0.59, .779, .03, 31.5, -27, 11.5, 94],
    [1.6, 2.17, 0.65, .771, .13, 35.8, -20, 12.1, 87],
    [1.7, 2.34, 0.73, .796, .07, 28.6, -30, 13.0, 77],
    [1.75, 2.46, 0.72, .800, .08, 30, -31, 13.1, 77],
    [1.8, 2.48, 0.73, .795, .03, 45, -38, 13.5, 74],
    [2.0, 2.79, 0.86, .800, 0, 39.5, -32, 14.7, 65],
    [2.3, 3.26, 0.98, .805, 0, 30, -28, 15.9, 56],
    [2.75, 3.96, 1.15, .805, -.15, 28, -25, 17.4, 47],
    [3.0, 4.36, 1.3, .807, -.25, 35, -25, 18.2, 42],
    [4.0, 6.55, 1.7, .785, -1.2, 32, -32, 20.2, 33],
    [5.0, 8.25, 1.9, .752, -3.4, 31, -29, 21.7, 28],
    [6.0, 10.5, 1.9, .749, -6.5, 31, -24, 22.5, 26],
])


def skobelev(f_ghz: float, fD: float | None = None, D_lambda: float | None = None) -> Design:
    """'Optimum' dual-mode horn (Skobelev 2001, W1GHZ 2006 HFSS table): step 1.016λ→1.3λ then flare."""
    t = SKOBELEV_BEST
    if D_lambda is None:
        if fD is None:
            raise ValueError("give fD or D_lambda")
        D_lambda = float(np.interp(fD, t[:, 2], t[:, 0]))
    row = [float(np.interp(D_lambda, t[:, 0], t[:, i])) for i in range(t.shape[1])]
    lam = wavelength_mm(f_ghz)
    return Design("Skobelev optimum dual-mode", f_ghz,
                  {"input_diam": 1.016 * lam, "step_diam": 1.3 * lam, "aperture_diam": D_lambda * lam,
                   "flare_length": row[1] * lam, "best_fD": row[2], "eta_calc_pct": 100 * row[3],
                   "phase_center": row[4] * lam, "gain_dbi": row[7], "bw10_deg": row[8]},
                  "Skobelev et al. 2001; W1GHZ 'Optimized dual-mode feedhorns' 2006 (BEST table)",
                  ["phase_center > 0 = davanti all'apertura", "serve una transizione adattata all'ingresso da 1.016λ",
                   "flare nominale L ≈ 3.45 r - 0.35 (λ); spesso meglio il 10% più corto"])


def pickett_potter_oe2igl(f_ghz: float, opening_angle_deg: float, length_corr: float = 0.0) -> Design:
    lam = wavelength_mm(f_ghz)
    R = 60.907 * opening_angle_deg ** -0.98422
    L = (-0.53504 * R ** 4 + 4.1757 * R ** 3 - 11.589 * R ** 2 + 16.963 * R - 5.8895) * (1 + length_corr)
    return Design("Pickett-Potter", f_ghz,
                  {"input_diam_Di": 1.02 * lam, "step_diam_Ds": 1.30 * lam, "aperture_diam": 2 * R * lam,
                   "flare_length": L * lam},
                  "OE2IGL DualModeHorn-design-guide 2025 (Milligan + openEMS)",
                  ["η 78% (f/D 0.6) … 81% (f/D > 1)", "adatto a offset f/D 0.58-0.8 e oltre 76 GHz"])


# ---------------- corrugated (OE2IGL axial) ----------------
def _poly(c, x):
    return sum(ci * x ** (len(c) - 1 - i) for i, ci in enumerate(c))


def axial_corrugated_oe2igl(f_ghz: float, opening_angle_deg: float) -> Design:
    """OE2IGL v1.4 axial-corrugated feed with 8 steps (base CT1DMK), 10-76 GHz; psi = half opening angle."""
    lam = wavelength_mm(f_ghz)
    psi = opening_angle_deg / 2
    step = 0.05 if f_ghz < 30 else 0.025 if f_ghz < 55 else 0.02 if f_ghz < 80 else 0.025
    rnd = lambda v: round(v / step) * step
    P = {
        "pitch": [-6.72759e-9, 2.13419809e-6, -2.7793768348e-4, 0.01900638584665, -0.71948851201245, 14.2975507272445, -116.265581374344],
        "w": [-5.00164e-9, 1.57372735e-6, -2.0304694239e-4, 0.0137396440128, -0.51402558573511, 10.0836505431737, -80.8959001275667],
        "axi": [-7.14481e-9, 2.25111842e-6, -2.9166230154e-4, 0.01987517595131, -0.7508309146383, 14.8952165691508, -120.835516302193],
        "delta": [-3.5684e-9, 1.15051226e-6, -1.5125028602e-4, 0.01035505492211, -0.38867044924585, 7.58012720956018, -60.0565016846105],
        "Di_half": [-9.4718e-10, 2.8274745e-7, -3.469444174e-5, 0.00224733479491, -0.0814076296413, 1.56778931797874, -12.1322259993015],
        "Ds_half": [-1.38043e-9, 4.5403189e-7, -6.178883658e-5, 0.00444598271875, -0.17774710208844, 3.71538298037237, -30.9065313607455],
        "d1": [2.37e-10, -2.133e-8, -4.303976e-6, 7.77088212e-4, -0.047141193767, 1.270049062497, -12.635629680167],
    }
    d = {
        "pitch": rnd(_poly(P["pitch"], psi) * lam),
        "w": rnd(_poly(P["w"], psi) * lam),
        "axi": _poly(P["axi"], psi) * lam,
        "delta": max(0.0, rnd(_poly(P["delta"], psi) * lam)),
        "Di": rnd(2 * _poly(P["Di_half"], psi) * lam),
        "Ds": rnd(2 * _poly(P["Ds_half"], psi) * lam),
        "las": 3.0,
        "d1": rnd(_poly(P["d1"], psi) * lam),
        "d2_to_d8": rnd(0.25 * lam),
    }
    eff = {
        "eta_pct": 100 * _poly([7.03e-10, -1.04718e-7, 4.80878e-7, 5.19517223e-4, -0.023415967549, 1.099049534637], psi),
        "spill_pct": 100 * _poly([-1.1072e-8, 2.812104e-6, -2.78323455e-4, 0.013360124165, -0.30880181878, 3.64266475677], psi),
        "illum_pct": 100 * _poly([5.333e-9, -1.262187e-6, 1.12395799e-4, -4.636545892e-3, 0.087318389246, 0.323315663532], psi),
    }
    tol = 0.1 if f_ghz < 30 else 0.05 if f_ghz < 55 else 0.02
    notes = [f"tolleranza di lavorazione ±{tol} mm (OE2IGL)",
             "valido 10–76 GHz, prime focus f/D 0.33–0.90, offset 0.33–0.80"]
    if not 10 <= f_ghz <= 76:
        notes.append("ATTENZIONE: fuori dall'intervallo di frequenza validato (10–76 GHz)")
    return Design("Axial Corrugated Feedhorn CT1DMK (parametric calculation OE2IGL)", f_ghz, {**d, **eff}, "OE2IGL high-performance-axial-corrugated-feed v1.4", notes)


# ---------------- choke-ring feeds ----------------
def ve4ma(f_ghz: float, variant: str = "super") -> Design:
    """VE4MA/Kumar family (W1GHZ & WD5AGO 2006). Ring setback = behind horn rim."""
    lam = wavelength_mm(f_ghz)
    v = {
        "original": (0.77, 0.50, 0.50, 0.15, "f/D 0.3-0.45 (spostando l'anello), ~69-71% calcolato"),
        "super": (0.71, 0.60, 0.45, 0.15, "f/D 0.35-0.45, ~79% calcolato, 65% misurato"),
        "small": (0.71, 0.35, 0.35, 0.15, "meno blocking, ≈ originale"),
        "tiny_ct1dmk": (0.71, 0.12, 0.26, 0.15, "ingombro < 1λ, η leggermente minore"),
    }[variant]
    horn, w, dpt, back, note = v
    return Design(f"VE4MA ({variant})", f_ghz,
                  {"horn_diam": horn * lam, "ring_width": w * lam, "ring_depth": dpt * lam,
                   "ring_setback": back * lam, "outer_diam": (horn + 2 * w) * lam},
                  "W1GHZ & WD5AGO, 'High-efficiency feedhorns for prime-focus dishes', MUD 2006",
                  [note, "posizione dell'anello: avanti → f/D maggiore, indietro → f/D minore", "≥6 punti di contatto o fondo del choke spesso λ/4"])


def chaparral(f_ghz: float, variant: str = "best") -> Design:
    lam = wavelength_mm(f_ghz)
    v = {"best": (0.71, 3, 0.20, 0.20, 0.40, "78% calcolato @ f/D 0.35 (63-64% misurato)"),
         "deep_dish": (0.71, 3, 0.17, 0.26, 0.40, "71% calcolato @ f/D 0.25"),
         "septum_cp": (0.71, 3, 0.17, 0.30, 0.35, "con septum: 75% @ f/D 0.32")}[variant]
    horn, n, w, dpt, back, note = v
    return Design(f"Chaparral 3-ring ({variant})", f_ghz,
                  {"horn_diam": horn * lam, "rings": n, "ring_width": w * lam, "ring_depth": dpt * lam,
                   "ring_setback": back * lam, "outer_diam": (horn + 2 * n * w) * lam},
                  "W1GHZ & WD5AGO MUD 2006", [note, "anelli uguali; pareti tra gli anelli trascurate"])


# ---------------- rectangular / pyramidal ----------------
def rect_feedhorn_g3rpe(f_ghz: float, fD: float, wg_a_mm: float, wg_b_mm: float) -> Design:
    """G3RPE straight-line approximation (HDL_ANT), ±2% for f/D < 0.8."""
    lam = wavelength_mm(f_ghz)
    AH = lam * (2.864 * fD - 0.575)
    AE = lam * (1.727 * fD - 0.129)
    notes = []
    if AH < wg_a_mm:
        notes.append(f"apertura H più piccola della guida: f/D minimo con questa guida ≈ {(wg_a_mm / lam + 0.575) / 2.864:.2f}")
    L_apex = AH * AH / lam
    L = L_apex * (AH - wg_a_mm) / AH
    return Design("Rectangular feedhorn (G3RPE)", f_ghz,
                  {"aperture_H": AH, "aperture_E": AE, "axial_length": L, "wg_a": wg_a_mm, "wg_b": wg_b_mm},
                  "G3RPE curves / W1GHZ HDL_ANT", notes + ["centro di fase ≈ 0.1-0.2λ dentro l'apertura"])


def pyramidal_phase_center(aperture_mm: float, guide_mm: float, axial_len_mm: float, f_ghz: float, plane: str) -> float:
    """Phase centre distance inside the mouth (λ), M. Reilly formulas used in HDL_ANT."""
    lam = wavelength_mm(f_ghz)
    a = aperture_mm / lam
    l = math.hypot(axial_len_mm, (aperture_mm - guide_mm) / 2) / lam
    v = math.sqrt(l / 2)
    if plane.upper() == "E":
        q = a / (2 * v)
        S, C = fresnel(q)
        c2, s2 = math.cos(math.pi / 2 * q * q), math.sin(math.pi / 2 * q * q)
        return l * (1 - q * (c2 * C + s2 * S) / (C * C + S * S))
    U = v / a + a / (2 * v)
    W = v / a - a / (2 * v)
    R = W * math.cos(math.pi / 2 * U * U) - U * math.cos(math.pi / 2 * W * W)
    T = U * math.sin(math.pi / 2 * W * W) - W * math.sin(math.pi / 2 * U * U)
    SU, CU = fresnel(U); SW, CW = fresnel(W)
    CD = CU - CW; SD = -SU + SW
    return l * (1 + (R * CD + T * SD) / (CD * CD + SD * SD))


def pyramidal_gain_dbi(AE_mm: float, AH_mm: float, axial_len_mm: float, wg_a: float, wg_b: float, f_ghz: float) -> float:
    """Directivity of a pyramidal horn (TE10 aperture with quadratic phase), closed form of Balanis ch. 13
    (sectoral directivities with Fresnel integrals). Agrees with a full 2-D aperture integral within 0.01 dB.
    (Until 0.4.2 this was integrated from the E/H cuts only, a body-of-revolution approximation that
    under-estimated a rectangular aperture by 0.15-0.5 dB.)"""
    from .balanis import pyramidal_directivity
    lam = wavelength_mm(f_ghz)
    rho1 = axial_len_mm * AE_mm / max(AE_mm - wg_b, 1e-9)       # E-plane apex to aperture, along the axis
    rho2 = axial_len_mm * AH_mm / max(AH_mm - wg_a, 1e-9)       # H-plane
    return 10 * math.log10(pyramidal_directivity(wg_a, wg_b, AH_mm, AE_mm, rho1, rho2, lam))


def conical_optimum(f_ghz: float, gain_dbi: float, guide_diam_mm: float) -> Design:
    """Optimum-gain smooth conical horn (HDL_ANT / Jasik)."""
    lam = wavelength_mm(f_ghz)
    D = lam * 10 ** ((gain_dbi + 2.82) / 20) / math.pi
    l = D * D / (3 * lam)
    flare = math.asin(0.5 * D / l)
    L = 0.5 * (D - guide_diam_mm) / math.tan(flare)
    return Design("Optimum conical horn", f_ghz, {"aperture_diam": D, "slant_length": l, "flare_half_deg": flare / DEG,
                  "axial_length": L}, "HDL_ANT (Jasik, η≈52%)", ["non è un buon illuminatore (E/H diversi, correnti sul bordo)"])


def diagonal_horn_side(f_ghz: float, bw10_full_deg: float) -> Design:
    lam = wavelength_mm(f_ghz)
    d = 101.0 * lam / bw10_full_deg
    return Design("Diagonal horn (Love)", f_ghz, {"side": d, "bw3_full_deg": 58.5 * lam / d},
                  "A.W. Love / W1GHZ 6.5.3", ["flare < 30° full", "45° plane sidelobes (cross-pol)"])
