# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""openEMS 3D run of a pyramidal / square horn fed by a rectangular guide (WR), TE10.

    /opt/openEMS/venv/bin/python -u fdtd/rect_horn_sim.py <run folder>     (reads <run folder>/feed.json)

Same results.json as feedlab.openems_sim (format "feedlab-openems-results" v2), so fdtd_eval, deep_analysis and the
charts read it unchanged. Geometry: guide a along x, b along y (TE10, E along y), input guide into the back PML,
horn = outer frustum of metal (inner + wall) with the inner frustum of air, aperture at z = Z_AP.
The far field is computed on the cuts phi = 90/135/180° and stored as 0/45/90° (frame turned by -90° about z):
the BOR convention of FeedLab (x polarisation, E plane = phi 0, H plane = phi 90) then holds unchanged.
"""
import json
import os
import sys
import time

HERE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
CFG = json.load(open(os.path.join(HERE, "feed.json")))
G, C = CFG["geometry"], CFG["config"]
T_START = time.time()


def _l(a):
    import numpy as np
    a = np.asarray(a, dtype=float)
    m = float(np.nanmax(np.abs(a))) if a.size else 0.0
    if not np.isfinite(m) or m == 0.0:
        return a.tolist()
    return a.round(int(8 - np.floor(np.log10(m)))).tolist()


def frustum(z0, w0, h0, z1, w1, h1):
    """8 vertices + 6 quads of a rectangular frustum (outward faces)"""
    v = [[-w0 / 2, -h0 / 2, z0], [w0 / 2, -h0 / 2, z0], [w0 / 2, h0 / 2, z0], [-w0 / 2, h0 / 2, z0],
         [-w1 / 2, -h1 / 2, z1], [w1 / 2, -h1 / 2, z1], [w1 / 2, h1 / 2, z1], [-w1 / 2, h1 / 2, z1]]
    f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return v, f


def add_frustum(prop, z0, w0, h0, z1, w1, h1, priority):
    v, f = frustum(z0, w0, h0, z1, w1, h1)
    p = prop.AddPolyhedron(priority=priority)
    for x in v:
        p.AddVertex(*x)
    for q in f:                                           # two triangles per quad
        p.AddFace([q[0], q[1], q[2]])
        p.AddFace([q[0], q[2], q[3]])
    return p


def build(sim_path):
    import numpy as np
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    from openEMS.physical_constants import C0

    unit = 1e-3
    P = G["params"]
    a, b, AH, AE, L, t = P["a"], P["b"], P["aperture_H"], P["aperture_E"], P["axial_length"], P["wall"]
    f0, f_lo, f_hi = G["f0_ghz"] * 1e9, C["f_lo"] * 1e9, C["f_hi"] * 1e9
    lam0 = C0 / f0 / unit
    res = C0 / f_hi / unit / C["cells_per_lambda"]
    Z_AP = L

    FDTD = openEMS(NrTS=int(C["nr_ts"]), EndCriteria=10 ** (-C["end_db"] / 10.0))
    FDTD.SetGaussExcite(0.5 * (f_lo + f_hi), 0.5 * (f_hi - f_lo))
    FDTD.SetBoundaryCond(["PML_8"] * 6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(unit)

    pad = C["pad_lambda"] * lam0 + 10 * res
    z_back = -max(lam0, 2 * a)
    tw = max(t, 2.0 * res)                                 # input guide wall: >= 2 cells (see openems_sim)
    xh = max(AH / 2 + t, a / 2 + tw)
    yh = max(AE / 2 + t, b / 2 + tw)
    dmin = float(C.get("min_cell_frac") or 0.0) * res

    def merge(lines, keep=()):
        out = []
        for v in sorted(set(lines)):
            if out and v - out[-1] < dmin:
                if v in keep:
                    out[-1] = v
                continue
            out.append(v)
        return out

    for ax, inner, ap, half in (("x", a, AH, xh), ("y", b, AE, yh)):
        ls = [-half - pad, half + pad, 0.0]
        for s in (1, -1):
            ls += [s * inner / 2, s * (inner / 2 + tw), s * ap / 2, s * (ap / 2 + t)]
        mesh.SetLines(ax, merge(ls, keep=(0.0, a / 2, -a / 2, b / 2, -b / 2)))
        mesh.SmoothMeshLines(ax, res, ratio=1.4)
    mesh.SetLines("z", merge([z_back, 0.0, Z_AP, Z_AP + pad], keep=(z_back, 0.0, Z_AP)))
    mesh.SmoothMeshLines("z", res, ratio=1.4)
    x_lines, y_lines, z_lines = mesh.GetLines("x"), mesh.GetLines("y"), mesh.GetLines("z")

    metal = CSX.AddMetal("feed")
    air = CSX.AddMaterial("air", epsilon=1.0)
    # input guide (into the back PML)
    metal.AddBox([-a / 2 - tw, -b / 2 - tw, z_back], [a / 2 + tw, b / 2 + tw, 0.0], priority=10)
    air.AddBox([-a / 2, -b / 2, z_back], [a / 2, b / 2, 0.0], priority=20)
    # horn: walls of thickness t normal to the axis (machined block or sheet: same inner shape)
    if L > 1e-6:
        add_frustum(metal, 0.0, a + 2 * tw, b + 2 * tw, Z_AP, AH + 2 * t, AE + 2 * t, 10)
        k = 0.5 * res                                      # inner air a bit past the mouth: clean aperture
        add_frustum(air, -k, a - (AH - a) * k / L, b - (AE - b) * k / L,
                    Z_AP + k, AH + (AH - a) * k / L, AE + (AE - b) * k / L, 20)

    start = [-a / 2, -b / 2, z_lines[10]]
    stop = [a / 2, b / 2, z_lines[10] + 0.25 * lam0]
    port = FDTD.AddRectWaveGuidePort(0, start, stop, "z", a * unit, b * unit, "TE10", 1)

    nf2ff = FDTD.CreateNF2FFBox("nf2ff", [x_lines[10], y_lines[10], z_lines[10]],
                                [x_lines[-11], y_lines[-11], z_lines[-11]], directions=[1, 1, 1, 1, 0, 1])
    info = dict(nx=len(x_lines), ny=len(y_lines), nz=len(z_lines),
                cells=len(x_lines) * len(y_lines) * len(z_lines), res_mm=res)
    return dict(FDTD=FDTD, CSX=CSX, port=port, nf2ff=nf2ff, unit=unit, info=info, Z_AP=Z_AP)


def main():
    import numpy as np
    sim_path = os.path.join(HERE, "sim_data")
    m = build(sim_path)
    if "--xml" in sys.argv:
        m["CSX"].Write2XML(os.path.join(HERE, "geometry.xml"))
        print(m["info"])
        return
    print("mesh", m["info"], flush=True)
    t0 = time.time()
    kw = {"numThreads": int(C["threads"])} if int(C.get("threads") or 0) > 0 else {}
    m["FDTD"].Run(sim_path, cleanup=True, **kw)
    t_fdtd = time.time() - t0

    port, nf2ff, unit = m["port"], m["nf2ff"], m["unit"]
    f_lo, f_hi, f0 = C["f_lo"] * 1e9, C["f_hi"] * 1e9, G["f0_ghz"] * 1e9
    freq = np.linspace(f_lo, f_hi, int(C["n_freq"]))
    port.CalcPort(sim_path, freq)
    s11 = port.uf_ref / port.uf_inc
    zin = port.uf_tot / port.if_tot
    pacc = 0.5 * np.real(port.uf_tot * np.conj(port.if_tot))

    center = [0, 0, m["Z_AP"] * unit]
    theta = np.arange(0.0, 180.0 + C["theta_step"] / 2, C["theta_step"])
    phis_sim = np.array([90.0, 135.0, 180.0])
    phis = phis_sim - 90.0                                 # frame turned: x' = y (E-field), see the docstring
    ffreqs = [f * 1e9 for f in C["ff_freqs"]]
    r = nf2ff.CalcNF2FF(sim_path, ffreqs, theta, phis_sim, center=center, outfile="nf2ff_cuts.h5", read_cached=False)
    ff = []
    for i, f in enumerate(ffreqs):
        Et, Ep = np.asarray(r.E_theta[i]), np.asarray(r.E_phi[i])
        ff.append(dict(f_ghz=f / 1e9, theta=_l(theta), phis=_l(phis),
                       Et_re=_l(Et.real), Et_im=_l(Et.imag), Ep_re=_l(Ep.real), Ep_im=_l(Ep.imag),
                       Prad=float(np.real(r.Prad[i])), Dmax_nf2ff_dbi=float(10 * np.log10(np.real(r.Dmax[i]))),
                       Pacc=float(np.interp(f, freq, pacc))))
    i0 = int(np.argmin([abs(x["f_ghz"] - G["f0_ghz"]) for x in ff]))
    out = dict(format="feedlab-openems-results", version=2,
               meta=dict(kind=G["kind"], f0_ghz=G["f0_ghz"], params=G["params"], label=C.get("label", "")),
               geometry=G, config=C, mesh=m["info"],
               timing=dict(fdtd_s=t_fdtd, total_s=time.time() - T_START, post_only=False),
               freq_ghz=_l(freq / 1e9), s11_re=_l(s11.real), s11_im=_l(s11.imag),
               zin_re=_l(np.real(zin)), zin_im=_l(np.imag(zin)), pacc=_l(pacc), ff=ff, sphere=None,
               phase_ref="aperture plane z = Z_AP; cuts phi' = phi - 90 (x' along the TE10 E-field)",
               theta=ff[i0]["theta"], phis=ff[i0]["phis"], Et_re=ff[i0]["Et_re"], Et_im=ff[i0]["Et_im"],
               Ep_re=ff[i0]["Ep_re"], Ep_im=ff[i0]["Ep_im"], Dmax_dbi=ff[i0]["Dmax_nf2ff_dbi"], Prad=ff[i0]["Prad"],
               cells_per_lambda=C["cells_per_lambda"])
    with open(os.path.join(HERE, "results.json"), "w") as fh:
        json.dump(out, fh)
    s11_f0 = 20 * np.log10(abs(np.interp(f0, freq, s11.real) + 1j * np.interp(f0, freq, s11.imag)) + 1e-15)
    print("S11 @ f0 = %.1f dB, Dmax = %.2f dBi, %.0f s" % (s11_f0, out["Dmax_dbi"], time.time() - T_START), flush=True)


if __name__ == "__main__":
    main()
