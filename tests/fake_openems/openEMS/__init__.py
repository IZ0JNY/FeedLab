"""Minimal stand-in for the openEMS Python bindings, used only by FeedLab's tests.

It produces analytic but physically consistent data: a BOR1 feed with cos^q patterns (different in E and
H), its phase centre FAKE_PC_MM millimetres in front of the NF2FF reference, and a small S11.
"""
import math
import os
import time

import numpy as np

__version__ = "fake-0.0"
C0 = 299792458.0


class _Port:
    def __init__(self, f_center):
        self.f_center = f_center

    def CalcPort(self, sim_path, freq):
        f = np.asarray(freq, float)
        g = 0.03 + 0.2 * ((f - self.f_center) / self.f_center) ** 2
        self.uf_inc = np.ones_like(f, complex)
        self.uf_ref = g * np.exp(-1j * 2 * np.pi * f / self.f_center * 3)
        self.uf_tot = self.uf_inc + self.uf_ref
        self.if_inc = self.uf_inc / 500.0
        self.if_ref = -self.uf_ref / 500.0
        self.if_tot = self.if_inc + self.if_ref
        self.P_inc = 0.5 * np.real(self.uf_inc * np.conj(self.if_inc))
        self.P_ref = 0.5 * np.real(self.uf_ref * np.conj(-self.if_ref))
        self.P_acc = self.P_inc - self.P_ref


class _NFRes:
    pass


def fake_fields(f, theta_deg, phi_deg, qE=6.0, qH=8.0, pc_mm=None):
    pc_mm = float(os.environ.get("FAKE_PC_MM", "2.0")) if pc_mm is None else pc_mm
    t = np.radians(np.asarray(theta_deg, float))[:, None]
    p = np.radians(np.asarray(phi_deg, float))[None, :]
    c = np.clip(np.cos(t), 0, None)
    A = c ** qE + 1e-3
    B = c ** qH + 1e-3
    k = 2 * math.pi * f / C0 * 1e-3
    ph = np.exp(1j * k * pc_mm * np.cos(t))
    Et = A * np.cos(p) * ph
    Ep = -B * np.sin(p) * ph
    return Et, Ep


class _NF2FF:
    def CalcNF2FF(self, sim_path, freq, theta, phi, center=None, outfile=None, **kw):
        fs = np.atleast_1d(freq).astype(float)
        r = _NFRes()
        r.E_theta, r.E_phi, r.Prad, r.Dmax = [], [], [], []
        for f in fs:
            Et, Ep = fake_fields(f, theta, phi)
            # radiated power of the analytic BOR1 pattern (|A|^2 cos^2 + |B|^2 sin^2)
            tt = np.radians(np.arange(0, 180.01, 0.25))
            Ef, Hf = fake_fields(f, np.degrees(tt), [0.0, 90.0])
            P = math.pi * np.trapezoid((np.abs(Ef[:, 0]) ** 2 + np.abs(Hf[:, 1]) ** 2) * np.sin(tt), tt) \
                if hasattr(np, "trapezoid") else math.pi * np.trapz((np.abs(Ef[:, 0]) ** 2 + np.abs(Hf[:, 1]) ** 2) * np.sin(tt), tt)
            U0 = abs(Ef[0, 0]) ** 2
            r.E_theta.append(Et)
            r.E_phi.append(Ep)
            r.Prad.append(0.98 * 0.5 / 500.0)   # same units as the fake port power
            r.Dmax.append(4 * math.pi * U0 / P)
        return r


class openEMS:
    def __init__(self, NrTS=1000, EndCriteria=1e-4, **kw):
        self.NrTS, self.EndCriteria = NrTS, EndCriteria

    def SetGaussExcite(self, f0, fc):
        self.f0 = f0

    def SetBoundaryCond(self, bc):
        assert len(bc) == 6

    def SetCSX(self, csx):
        self.csx = csx

    def AddCircWaveGuidePort(self, nr, start, stop, d, radius, mode, pol_ang=0, excite=0, **kw):
        assert mode.startswith("TE") or mode.startswith("TM")
        return _Port(self.f0)

    def CreateNF2FFBox(self, name, start, stop, directions=None, **kw):
        return _NF2FF()

    def Run(self, sim_path, cleanup=False, numThreads=None, **kw):
        os.makedirs(sim_path, exist_ok=True)
        print("Max. number of timesteps: %d ( --> 3.2 * Excitation signal length)" % self.NrTS, flush=True)
        delay = float(os.environ.get("FAKE_RUN_SECONDS", "0"))
        n = 6
        for i in range(1, n + 1):
            db = 40.0 * i / n
            print("[@%10ds] Timestep: %12d || Speed:  123.4 MC/s (1.0e-03 s/TS) || Energy: ~1.00e-%02d (- %.2fdB)"
                  % (i, 1000 * i, int(db / 10) + 1, db), flush=True)
            time.sleep(delay / n)
