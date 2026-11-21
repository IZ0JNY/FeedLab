"""Mode-matching (generalized scattering matrix) simulation of circular-waveguide feeds.

Azimuthal order n = 1 modes (TE1m, TM1m) of a body of revolution excited by TE11. The interior
(steps and cones as fine staircases) is cascaded with Redheffer star products. The aperture is
modelled as a junction into a much larger guide whose modes are all matched ("flanged aperture /
large-waveguide approximation"), giving an estimate of the aperture reflection.

Outputs: S11 of the TE11 input versus frequency, and the modal content of the tangential aperture
field (used by `patterns.circular_aperture_pattern` for the far field).
Approximations: perfectly conducting walls, staircase cones, flanged aperture model, n=1 only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.special import jv, jvp, jn_zeros, jnp_zeros

C0 = 299_792_458.0


@lru_cache(maxsize=None)
def _roots(n_te: int = 40, n_tm: int = 40):
    te = jnp_zeros(1, n_te)
    tm = jn_zeros(1, n_tm)
    modes = [("TE", m + 1, float(x)) for m, x in enumerate(te)] + [("TM", m + 1, float(x)) for m, x in enumerate(tm)]
    return sorted(modes, key=lambda t: t[2])


def mode_list(radius: float, kc_max: float):
    return [(kind, m, chi) for kind, m, chi in _roots() if chi / radius <= kc_max]


def _radial(kind, chi, radius, rho):
    """Radial parts (e_rho, e_phi) of x-polarised n=1 mode (cos/sin factors removed)."""
    x = chi * rho / radius
    with np.errstate(divide="ignore", invalid="ignore"):
        j_over_x = np.where(x > 1e-12, jv(1, x) / np.where(x > 1e-12, x, 1), 0.5)
    if kind == "TE":
        return j_over_x, -jvp(1, x)
    return jvp(1, x), -j_over_x


@lru_cache(maxsize=4096)
def _norm(kind, chi, radius):
    xg, wg = np.polynomial.legendre.leggauss(200)
    rho = 0.5 * radius * (xg + 1); w = 0.5 * radius * wg
    er, ep = _radial(kind, chi, radius, rho)
    return math.sqrt(math.pi * np.sum((er * er + ep * ep) * rho * w))


def coupling(modes_a, ra, modes_b, rb):
    """M_ij = int_{S_a} e_a,i . e_b,j dS (ra <= rb), unit-normalised modes."""
    xg, wg = np.polynomial.legendre.leggauss(240)
    rho = 0.5 * ra * (xg + 1); w = 0.5 * ra * wg * rho
    A = []
    for kind, m, chi in modes_a:
        er, ep = _radial(kind, chi, ra, rho)
        A.append((er / _norm(kind, chi, ra), ep / _norm(kind, chi, ra)))
    B = []
    for kind, m, chi in modes_b:
        er, ep = _radial(kind, chi, rb, rho)
        B.append((er / _norm(kind, chi, rb), ep / _norm(kind, chi, rb)))
    Ar = np.array([a[0] for a in A]); Ap = np.array([a[1] for a in A])
    Br = np.array([b[0] for b in B]); Bp = np.array([b[1] for b in B])
    return math.pi * ((Ar * w) @ Br.T + (Ap * w) @ Bp.T)


def _beta_y(modes, radius, k):
    kc = np.array([chi / radius for _, _, chi in modes])
    b2 = k * k - kc * kc
    beta = np.where(b2 >= 0, np.sqrt(np.abs(b2)), -1j * np.sqrt(np.abs(b2)))
    te = np.array([kind == "TE" for kind, _, _ in modes])
    with np.errstate(divide="ignore", invalid="ignore"):
        Y = np.where(te, beta / k, k / beta)
    return beta, Y


def _step_gsm(M, Ya, Yb):
    """Step from small guide a (port 1) to large guide b (port 2), voltage-wave GSM."""
    Ya = np.diag(Ya); Yb = np.diag(Yb)
    MYbMt = M @ Yb @ M.T
    W = Ya + MYbMt
    Winv = np.linalg.inv(W)
    S11 = Winv @ (Ya - MYbMt)
    S12 = 2 * Winv @ M @ Yb
    S21 = M.T @ (np.eye(len(Ya)) + S11)
    S22 = M.T @ S12 - np.eye(Yb.shape[0])
    return [S11, S12, S21, S22]


def _star(A, B):
    A11, A12, A21, A22 = A
    B11, B12, B21, B22 = B
    I1 = np.eye(A22.shape[0])
    X = np.linalg.inv(I1 - B11 @ A22)
    Y = np.linalg.inv(I1 - A22 @ B11)
    return [A11 + A12 @ X @ B11 @ A21, A12 @ X @ B12, B21 @ Y @ A21, B22 + B21 @ Y @ A22 @ B12]


def _line(beta, L):
    d = np.diag(np.exp(-1j * beta * L))
    z = np.zeros_like(d)
    return [z, d, d, z]


@dataclass
class MMResult:
    f_ghz: np.ndarray
    s11: np.ndarray                 # complex TE11 reflection
    aperture_modes: list            # per frequency: dict name -> complex amplitude (tangential E)
    aperture_radius_mm: float
    power_balance: np.ndarray       # |S11|^2 + transmitted power (should be ~1)

    @property
    def s11_db(self):
        return 20 * np.log10(np.abs(self.s11) + 1e-15)

    @property
    def return_loss_db(self):
        return -self.s11_db


def simulate(sections: list[tuple[float, float]], f_ghz, n_modes: int = 16, aperture: str = "flange",
             flange_extra_lambda: float = 3.0) -> MMResult:
    """sections: [(radius_mm, length_mm)] from input to aperture. f_ghz: scalar or array."""
    f_arr = np.atleast_1d(np.asarray(f_ghz, float))
    rmax = max(r for r, _ in sections)
    s11s, apm, pb = [], [], []
    for f in f_arr:
        lam = C0 / (f * 1e9) * 1e3
        k = 2 * math.pi / lam
        kc_max = _roots()[n_modes - 1][2] / rmax
        R_big = sections[-1][0] + flange_extra_lambda * lam
        # mode sets
        guides = []
        for r, L in sections:
            ml = mode_list(r, max(kc_max, 1.0 / r * 2.0))
            if not ml:
                ml = _roots()[:1]
            beta, Y = _beta_y(ml, r, k)
            guides.append((r, L, ml, beta, Y))
        # input port: only TE11 incident; keep full set at input guide for reflection
        r0, L0, ml0, b0, Y0 = guides[0]
        G = _line(b0, L0)
        for (ra, La, mla, ba, Ya), (rb, Lb, mlb, bb, Yb) in zip(guides[:-1], guides[1:]):
            if rb >= ra:
                M = coupling(mla, ra, mlb, rb)
                J = _step_gsm(M, Ya, Yb)
            else:
                M = coupling(mlb, rb, mla, ra)
                S = _step_gsm(M, Yb, Ya)
                J = [S[3], S[2], S[1], S[0]]
            G = _star(G, J)
            G = _star(G, _line(bb, Lb))
        # aperture junction into large matched guide
        r_ap, L_ap, ml_ap, b_ap, Y_ap = guides[-1]
        if aperture == "flange":
            ml_big = mode_list(R_big, max(kc_max, k * 1.6))
            _, Y_big = _beta_y(ml_big, R_big, k)
            M = coupling(ml_ap, r_ap, ml_big, R_big)
            Jap = _step_gsm(M, Y_ap, Y_big)
            Rap = Jap[0]
        else:
            Rap = np.zeros((len(ml_ap), len(ml_ap)), complex)
        # input excitation TE11 (index 0 of input set is TE11 by sorting)
        a_in = np.zeros(len(ml0), complex); a_in[0] = 1.0
        A11, A12, A21, A22 = G
        cfw = np.linalg.solve(np.eye(len(ml_ap)) - Rap @ A22, Rap) if False else None
        # forward wave at aperture: c+ = (I - A22 Rap)^-1 A21 a_in ; reflected = Rap c+
        cplus = np.linalg.solve(np.eye(len(ml_ap)) - A22 @ Rap, A21 @ a_in)
        refl = A11 @ a_in + A12 @ (Rap @ cplus)
        s11 = refl[0]
        Etan = cplus + Rap @ cplus
        s11s.append(s11)
        names = {}
        prop = np.real(b_ap) > 0
        for (kind, m, chi), amp, p in zip(ml_ap, Etan, prop):
            if p:
                names[f"{kind}1{m}"] = complex(amp)
        apm.append(names)
        # power check (propagating modes, power ~ Re(Y)|V|^2)
        refl_p = np.sum(np.real(Y0) * np.abs(refl) ** 2 * (np.real(b0) > 0)) / np.real(Y0[0])
        trans_p = np.sum(np.real(Y_ap) * (np.abs(cplus) ** 2 - np.abs(Rap @ cplus) ** 2) * prop) / np.real(Y0[0])
        pb.append(refl_p + trans_p)
        _ = cfw
    return MMResult(f_arr, np.array(s11s), apm, sections[-1][0], np.array(pb))


def aperture_pattern(res: MMResult, idx: int, f_ghz: float, **kw):
    """Far field from the modal content at frequency index idx (aperture integration)."""
    from .patterns import circular_aperture_pattern
    lam = C0 / (f_ghz * 1e9) * 1e3
    return circular_aperture_pattern(2 * res.aperture_radius_mm / lam, res.aperture_modes[idx], **kw)
