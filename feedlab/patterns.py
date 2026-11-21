"""Feed radiation patterns.

A `Pattern` stores complex co-polar far fields in the E-plane (phi=0) and H-plane (phi=90) on a common
theta grid 0..180 deg, under the BOR1 assumption (body of revolution, single-mode excitation):
    E_theta = A(theta) cos(phi),  E_phi = -B(theta) sin(phi)
which covers horns, dual-mode, choke and corrugated feeds. Cross-polar (Ludwig-3) is then implied:
    X = (A - B) sin(phi) cos(phi)   -> max at 45 deg.

Sources of patterns:
  * analytic models (gaussian, cos^q)
  * aperture-integration models of circular/rectangular apertures with arbitrary waveguide mode mixes
    and quadratic phase (horn flare) -> W2IMU, Potter, Skobelev, conical, pyramidal, corrugated (HE11)
  * files: W1GHZ FEEDPATT/PHASEPAT .dat (angle, dB [, phase]), generic CSV from openEMS/CST/HFSS.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.special import j0, j1, jvp

from .waveguide import CHI_TE, CHI_TM

DEG = math.pi / 180.0


@dataclass
class Pattern:
    theta_deg: np.ndarray          # 0..180
    E: np.ndarray                  # complex co-pol field, E-plane (A)
    H: np.ndarray                  # complex co-pol field, H-plane (B)
    name: str = ""
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        self.theta_deg = np.asarray(self.theta_deg, float)
        self.E = np.asarray(self.E, complex)
        self.H = np.asarray(self.H, complex)

    # --- helpers ---
    def resample(self, step_deg: float = 0.25) -> "Pattern":
        t = np.arange(0.0, 180.0 + 1e-9, step_deg)
        def interp(v):
            mag = np.interp(t, self.theta_deg, np.abs(v))
            ph = np.interp(t, self.theta_deg, np.unwrap(np.angle(v)))
            return mag * np.exp(1j * ph)
        return Pattern(t, interp(self.E), interp(self.H), self.name, dict(self.meta))

    def normalized(self) -> "Pattern":
        m = max(np.abs(self.E).max(), np.abs(self.H).max())
        return Pattern(self.theta_deg, self.E / m, self.H / m, self.name, dict(self.meta))

    def db(self) -> tuple[np.ndarray, np.ndarray]:
        n = self.normalized()
        return 20 * np.log10(np.abs(n.E) + 1e-12), 20 * np.log10(np.abs(n.H) + 1e-12)

    def shifted(self, d_lambda: float) -> "Pattern":
        """Move the phase reference d (wavelengths) along +z (toward the dish)."""
        k = 2 * math.pi
        f = np.exp(-1j * k * d_lambda * np.cos(self.theta_deg * DEG))
        return Pattern(self.theta_deg, self.E * f, self.H * f, self.name, dict(self.meta))

    def angle_at_level(self, level_db: float = -10.0, plane: str = "avg") -> float:
        e, h = self.db()
        y = {"E": e, "H": h, "avg": 10 * np.log10(0.5 * (10 ** (e / 10) + 10 ** (h / 10)))}[plane]
        idx = np.argmax(y <= level_db)
        if idx == 0:
            return float("nan")
        t0, t1, y0, y1 = self.theta_deg[idx - 1], self.theta_deg[idx], y[idx - 1], y[idx]
        return float(t0 + (level_db - y0) * (t1 - t0) / (y1 - y0))


# ---------------- analytic models ----------------
def gaussian_pattern(taper_db: float, at_deg: float, n: int = 721) -> Pattern:
    """Gaussian beam: power falls by taper_db at +-at_deg (no phase error, no back lobe)."""
    t = np.linspace(0, 180, n)
    p_db = -taper_db * (t / at_deg) ** 2
    v = 10 ** (p_db / 20)
    return Pattern(t, v, v, f"gauss {taper_db}dB@{at_deg}deg")


def cosq_pattern(q: float, n: int = 721) -> Pattern:
    """Field ~ cos^q(theta) in the forward hemisphere, zero behind."""
    t = np.linspace(0, 180, n)
    c = np.cos(t * DEG)
    v = np.where(c > 0, np.abs(c) ** q, 0.0)
    return Pattern(t, v, v, f"cos^{q}")


# ---------------- file I/O ----------------
def load_w1ghz_dat(path_e: str | Path, path_h: str | Path | None = None) -> Pattern:
    """Read W1GHZ FEEDPATT/PHASEPAT files: 'angle dB [phase_deg]', comments '//'.
    dB are levels below max (positive numbers in W1GHZ files)."""
    def read(p):
        a, m, ph = [], [], []
        for line in Path(p).read_text(errors="replace").splitlines():
            s = line.split("//")[0].strip()
            if not s or not (s[0].isdigit() or s[0] in "-."):
                continue
            parts = s.replace(",", " ").split()
            try:
                vals = [float(x) for x in parts[:3]]
            except ValueError:
                continue
            a.append(vals[0]); m.append(vals[1]); ph.append(vals[2] if len(vals) > 2 else 0.0)
        a, m, ph = map(np.asarray, (a, m, ph))
        lvl = -np.abs(m)  # W1GHZ stores dB below max as positive numbers
        return a, 10 ** (lvl / 20) * np.exp(1j * np.unwrap(ph * DEG))
    ae, ve = read(path_e)
    ah, vh = read(path_h) if path_h else (ae, ve)
    t = np.arange(0, 180.0001, 0.5)
    def interp(a, v):
        mag = np.interp(t, a, np.abs(v))
        ph = np.interp(t, a, np.angle(v))
        return mag * np.exp(1j * ph)
    return Pattern(t, interp(ae, ve), interp(ah, vh), Path(path_e).stem)


def save_w1ghz_dat(p: Pattern, path_prefix: str | Path) -> None:
    e, h = p.db()
    for tag, d, v in (("e", e, p.E), ("h", h, p.H)):
        lines = [f"{t:.2f}\t{-x:.3f}\t{np.degrees(np.angle(c)):.2f}" for t, x, c in zip(p.theta_deg, d, v)]
        Path(f"{path_prefix}_{tag}.dat").write_text("\n".join(lines) + f"\n// {p.name} {tag.upper()}-plane, FeedLab\n")


# ---------------- aperture-integration models ----------------
def _circ_mode_field(mode: str, rho, phi, a):
    """Transverse E field (x-polarised orientation) of circular-guide mode, returns (Ex, Ey)."""
    if mode.startswith("TE"):
        chi = CHI_TE[mode]; n = int(mode[2])
        kc = chi / a
        x = kc * rho
        with np.errstate(invalid="ignore", divide="ignore"):
            jn_over_x = np.where(x > 1e-9, _jn(n, x) / x, 0.5 if n == 1 else 0.0)
        er = n * jn_over_x * np.cos(n * phi)       # E_rho ~ (n/kc rho) J_n cos(n phi)
        ep = -jvp(n, x) * np.sin(n * phi)          # E_phi ~ -J_n' sin(n phi)
    elif mode.startswith("TM"):
        chi = CHI_TM[mode]; n = int(mode[2])
        kc = chi / a
        x = kc * rho
        with np.errstate(invalid="ignore", divide="ignore"):
            jn_over_x = np.where(x > 1e-9, _jn(n, x) / x, 0.5 if n == 1 else 0.0)
        er = jvp(n, x) * np.cos(n * phi)
        ep = -n * jn_over_x * np.sin(n * phi)
    elif mode == "HE11":  # balanced hybrid mode in corrugated guide: linearly polarised J0 profile
        x = 2.405 * rho / a
        return j0(x), np.zeros_like(rho)
    else:
        raise ValueError(mode)
    ex = er * np.cos(phi) - ep * np.sin(phi)
    ey = er * np.sin(phi) + ep * np.cos(phi)
    return ex, ey


def _jn(n, x):
    from scipy.special import jv
    return jv(n, x)


def _mode_beta_over_k(mode: str, a_lambda: float) -> float:
    if mode == "HE11":
        return 1.0
    chi = CHI_TE.get(mode) or CHI_TM.get(mode)
    kc_over_k = chi / (2 * math.pi * a_lambda)
    return math.sqrt(max(1 - kc_over_k ** 2, 0.0))


def circular_aperture_pattern(diameter_lambda: float,
                              modes: dict[str, complex] | None = None,
                              slant_radius_lambda: float | None = None,
                              n_rho: int = 60, n_phi: int = 72, n_theta: int = 361,
                              name: str = "") -> Pattern:
    """Far field of a circular aperture excited by a mix of waveguide modes.

    modes: {"TE11": 1.0, "TM11": 0.35*exp(1j*pi), ...}; amplitudes refer to unit-power-normalised modes.
    slant_radius_lambda: apex-to-aperture slant length of a conical flare -> spherical (quadratic) phase
        error exp(-j k rho^2 / (2 R)). None for a cylindrical (in-phase) aperture.
    Equivalence: Huygens source with per-mode wave impedance (TE: beta/k, TM: k/beta).
    Valid for the forward hemisphere; the rear field is a rough estimate (no rim diffraction).
    """
    modes = modes or {"TE11": 1.0}
    a = diameter_lambda / 2.0
    k = 2 * math.pi
    # Gauss-Legendre in rho, uniform in phi
    xg, wg = np.polynomial.legendre.leggauss(n_rho)
    rho = 0.5 * a * (xg + 1); wr = 0.5 * a * wg
    phi = np.linspace(0, 2 * math.pi, n_phi, endpoint=False)
    R, P = np.meshgrid(rho, phi, indexing="ij")
    dA = (wr * rho)[:, None] * (2 * math.pi / n_phi)
    quad = np.exp(-1j * k * R ** 2 / (2 * slant_radius_lambda)) if slant_radius_lambda else 1.0
    theta = np.linspace(0, 180, n_theta) * DEG
    st, ct = np.sin(theta), np.cos(theta)
    EE = np.zeros(n_theta, complex)
    HH = np.zeros(n_theta, complex)
    for mode, amp in modes.items():
        ex, ey = _circ_mode_field(mode, R, P, a)
        pw = np.sum((np.abs(ex) ** 2 + np.abs(ey) ** 2) * dA)
        ex = ex / math.sqrt(pw) * amp * quad
        ey = ey / math.sqrt(pw) * amp * quad
        g = _mode_beta_over_k(mode, a)
        gh = g if (mode.startswith("TE") or mode == "HE11") else (1.0 / g if g > 0 else 0.0)
        for cut_phi, store in ((0.0, EE), (math.pi / 2, HH)):
            # phase kernel exp(j k rho sin(theta) cos(phi' - cut_phi))
            ker = np.exp(1j * k * np.einsum("t,ij->tij", st, R * np.cos(P - cut_phi)))
            Fx = np.einsum("tij,ij->t", ker, ex * dA)
            Fy = np.einsum("tij,ij->t", ker, ey * dA)
            cp, sp = math.cos(cut_phi), math.sin(cut_phi)
            Eth = (Fx * cp + Fy * sp) * (1 + gh * ct)
            Eph = (-Fx * sp + Fy * cp) * (ct + gh)
            # co-pol amplitude along the BOR1 convention
            store += Eth if cut_phi == 0.0 else -Eph
    p = Pattern(np.linspace(0, 180, n_theta), EE, HH, name or f"circ {diameter_lambda:.2f}λ {list(modes)}")
    return p


def rectangular_aperture_pattern(a_lambda: float, b_lambda: float,
                                 RH_lambda: float | None = None, RE_lambda: float | None = None,
                                 n: int = 64, n_theta: int = 361, name: str = "") -> Pattern:
    """Pyramidal horn / open waveguide (TE10): cos in H (width a), uniform in E (height b),
    quadratic phase from flare slant lengths RH, RE (None = no flare). E-plane = phi 0 = along b."""
    k = 2 * math.pi
    xg, wg = np.polynomial.legendre.leggauss(n)
    x = 0.5 * a_lambda * xg; wx = 0.5 * a_lambda * wg
    y = 0.5 * b_lambda * xg; wy = 0.5 * b_lambda * wg
    fx = np.cos(math.pi * x / a_lambda) * (np.exp(-1j * k * x ** 2 / (2 * RH_lambda)) if RH_lambda else 1)
    fy = np.ones_like(y) * (np.exp(-1j * k * y ** 2 / (2 * RE_lambda)) if RE_lambda else 1)
    theta = np.linspace(0, 180, n_theta) * DEG
    st, ct = np.sin(theta), np.cos(theta)
    g = math.sqrt(max(1 - (1 / (2 * a_lambda)) ** 2, 0.0))
    Ix0 = np.sum(fx * wx)
    Iy0 = np.sum(fy * wy)
    # E-plane: scan along y (field polarised along y)
    Iy = np.exp(1j * k * np.outer(st, y)) @ (fy * wy)
    Ix = np.exp(1j * k * np.outer(st, x)) @ (fx * wx)
    E = Ix0 * Iy * (1 + g * ct)
    H = Iy0 * Ix * (ct + g)
    return Pattern(np.linspace(0, 180, n_theta), E, H, name or f"rect {a_lambda:.2f}x{b_lambda:.2f}λ")
