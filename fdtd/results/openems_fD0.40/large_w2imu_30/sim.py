# -*- coding: utf-8 -*-
"""FeedLab - openEMS full-wave "deep analysis" of a dish feed. Auto-generated.

Run:      python -u sim.py            (openEMS >= 0.0.36 with its Python bindings)
Preview:  python sim.py --preview     (opens the model in AppCSXCAD, no simulation)
Post:     python sim.py --post        (only port + far field again from sim_data, after a full run)
Output:   results.json (load it in FeedLab, tab "Full-wave openEMS"), status.json, sim_data/
"""
import os, sys, json, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.loads(r"""{"format": "feedlab-openems-config", "version": 2, "geometry": {"kind": "large_w2imu", "f0_ghz": 10.368, "params": {"A_input": 20.496537807445993, "B_aperture": 26.1562373124315, "flare_half_deg": 29.997209534746748, "flare_length": 4.901994882109973, "C_phasing": 20.887159494464, "input_length": 51.42192250882888, "wall": 1.73, "flange_diam": 47.08867191238427, "flange_thickness": 3.4698201157407405}, "polys": [[[10.248268903722996, 10.248268903722996, 13.07811865621575, 13.07811865621575, 14.80811865621575, 14.80811865621575, 11.978268903722997, 11.978268903722997, 23.544335956192135, 23.544335956192135, 10.248268903722996], [0.0, 51.42192250882888, 56.32391739093885, 77.21107688540286, 77.21107688540286, 55.860410440314986, 50.958415558205004, 3.4698201157407405, 3.4698201157407405, 0.0, 0.0]]], "r_input": 10.248268903722996, "z_aperture": 77.21107688540286, "outer_radius": 23.544335956192135, "r_aperture": 13.07811865621575}, "config": {"f_lo": 9.3312, "f_hi": 11.404800000000002, "cells_per_lambda": 26, "nr_ts": 40000, "end_db": 30.0, "port_mode": "TE11", "n_freq": 201, "ff_freqs": [10.16064, 10.368, 10.57536], "theta_step": 1.0, "phi_cuts": [0.0, 45.0, 90.0], "sphere": false, "sphere_step": 3.0, "pad_lambda": 0.4, "dump_fields": false, "threads": 0, "min_cell_frac": 0.3, "openems_root": "", "label": "large_w2imu_30 best confirm"}, "notes": ["C interpolata dalla tabella pubblicata", "assottigliare il bordo (smusso a 45\u00b0)", "centro di fase \u2248 apertura"]}""")
G, C = CFG["geometry"], CFG["config"]
T_START = time.time()


def status(stage, **kw):
    d = dict(stage=stage, time=time.time(), elapsed=time.time() - T_START, pid=os.getpid())
    d.update(kw)
    tmp = os.path.join(HERE, "status.json.tmp")
    # Windows: the replace fails while FeedLab is reading status.json -> retry; a progress file must
    # never stop the simulation
    for i in range(40):
        try:
            with open(tmp, "w") as fh:
                json.dump(d, fh)
            os.replace(tmp, os.path.join(HERE, "status.json"))
            break
        except OSError:
            time.sleep(0.05)
    print("FEEDLAB:STAGE %s %s" % (stage, json.dumps(kw)), flush=True)


def setup_dlls():
    """Windows: the bindings need the openEMS folder (DLLs) on the DLL search path."""
    root = os.environ.get("OPENEMS_INSTALL_PATH") or C.get("openems_root") or ""
    if root and os.path.isdir(root):
        os.environ["OPENEMS_INSTALL_PATH"] = root
        os.environ["PATH"] = root + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(root)
            except OSError:
                pass
    return root


def build(sim_path):
    import numpy as np
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    from openEMS.physical_constants import C0

    unit = 1e-3                                         # mm
    f0, f_lo, f_hi = G["f0_ghz"] * 1e9, C["f_lo"] * 1e9, C["f_hi"] * 1e9
    POLYS, R_IN, Z_AP, R_MAX = G["polys"], G["r_input"], G["z_aperture"], G["outer_radius"]
    lam_min = C0 / f_hi / unit
    res = lam_min / C["cells_per_lambda"]
    lam0 = C0 / f0 / unit

    FDTD = openEMS(NrTS=int(C["nr_ts"]), EndCriteria=10 ** (-C["end_db"] / 10.0))
    FDTD.SetGaussExcite(0.5 * (f_lo + f_hi), 0.5 * (f_hi - f_lo))
    FDTD.SetBoundaryCond(["PML_8"] * 6)
    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(unit)

    pad = C["pad_lambda"] * lam0 + 10 * res
    z_back = -max(lam0, 3 * R_IN)                       # input guide runs into the back PML (matched)
    # wall of the input guide that runs into the back PML: at least two cells thick, with its own mesh lines
    # (a fixed 0.5 mm wall fell between the lines at 10 GHz, 1.3 mm cells, and the guide was open)
    w_in = max(1.0, 2.0 * res)
    xy = sorted(set([-R_MAX - pad, R_MAX + pad, 0.0, -R_IN, R_IN, -(R_IN + w_in), R_IN + w_in]
                    + [s * float(r) for p in POLYS for r in p[0] for s in (1, -1)]))
    dmin = float(C.get("min_cell_frac") or 0.0) * res

    def merge(lines, keep=()):
        """drop lines closer than dmin to the previous one (tiny cells shrink the time step)"""
        if dmin <= 0:
            return lines
        out = []
        for v in lines:
            if out and v - out[-1] < dmin:
                if v in keep:
                    out[-1] = v
                continue
            out.append(v)
        return out

    xy = merge(xy, keep=(0.0, -R_IN, R_IN))
    mesh.SetLines("x", xy)
    mesh.SmoothMeshLines("x", res, ratio=1.4)
    mesh.SetLines("y", mesh.GetLines("x"))
    zl = sorted(set([z_back, Z_AP + pad] + [float(z) for p in POLYS for z in p[1]]))
    zl = merge(zl, keep=(z_back,))
    mesh.SetLines("z", zl)
    mesh.SmoothMeshLines("z", res, ratio=1.4)
    x_lines, y_lines, z_lines = mesh.GetLines("x"), mesh.GetLines("y"), mesh.GetLines("z")

    metal = CSX.AddMetal("feed")
    metal.AddRotPoly(points=np.array([[R_IN + w_in, R_IN + w_in, R_IN, R_IN], [z_back, 0.0, 0.0, z_back]]),
                     norm_dir="x", elevation=0, rot_axis="z", angle=[0, 2 * np.pi], priority=10)
    for p in POLYS:
        metal.AddRotPoly(points=np.array(p), norm_dir="x", elevation=0, rot_axis="z",
                         angle=[0, 2 * np.pi], priority=10)

    start = [-R_IN, -R_IN, z_lines[10]]
    stop = [R_IN, R_IN, z_lines[10] + 0.25 * lam0]
    port = FDTD.AddCircWaveGuidePort(0, start, stop, "z", R_IN * unit, C["port_mode"], 0, 1)

    nf_start = [x_lines[10], y_lines[10], z_lines[10]]
    nf_stop = [x_lines[-11], y_lines[-11], z_lines[-11]]
    nf2ff = FDTD.CreateNF2FFBox("nf2ff", nf_start, nf_stop, directions=[1, 1, 1, 1, 0, 1])

    if C.get("dump_fields"):
        try:
            dump = CSX.AddDump("Ef_xz", dump_type=10, file_type=0, frequency=[f0])
            dump.AddBox([x_lines[0], 0, z_lines[0]], [x_lines[-1], 0, z_lines[-1]])
        except Exception as e:                           # optional
            print("field dump not available:", e, flush=True)

    info = dict(nx=len(x_lines), ny=len(y_lines), nz=len(z_lines),
                cells=len(x_lines) * len(y_lines) * len(z_lines), res_mm=res)
    return dict(FDTD=FDTD, CSX=CSX, port=port, nf2ff=nf2ff, unit=unit, info=info, Z_AP=Z_AP)


def preview():
    sim_path = os.path.join(HERE, "sim_data")
    m = build(sim_path)
    fn = os.path.join(HERE, "geometry.xml")
    m["CSX"].Write2XML(fn)
    exe = None
    try:
        from CSXCAD import AppCSXCAD_BIN
        exe = AppCSXCAD_BIN
    except Exception:
        root = os.environ.get("OPENEMS_INSTALL_PATH", "")
        for cand in ("AppCSXCAD.exe", "AppCSXCAD"):
            if root and os.path.exists(os.path.join(root, cand)):
                exe = os.path.join(root, cand)
        exe = exe or "AppCSXCAD"
    print("geometry written to", fn, "- opening", exe, flush=True)
    import subprocess
    subprocess.Popen([exe, fn])


def _l(a):
    """Array -> list with 9 significant digits relative to its largest value. openEMS fields are tiny
    (far field ~1e-11 V/m for its unit excitation): a fixed number of decimals would store zeros."""
    import numpy as np
    a = np.asarray(a, dtype=float)
    m = float(np.nanmax(np.abs(a))) if a.size else 0.0
    if not np.isfinite(m) or m == 0.0:
        return a.tolist()
    return a.round(int(8 - np.floor(np.log10(m)))).tolist()


def main(post_only=False):
    """post_only (--post): skip the FDTD run and only redo port + far field from the data already in
    sim_data (same script, same mesh): seconds instead of the whole simulation."""
    import numpy as np
    status("setup")
    sim_path = os.path.join(HERE, "sim_data")
    m = build(sim_path)
    t0 = time.time()
    if post_only:
        if not os.path.isdir(sim_path):
            raise RuntimeError("--post: sim_data not found, run the full simulation first")
    else:
        status("fdtd", **m["info"])
        kw = {"numThreads": int(C["threads"])} if int(C.get("threads") or 0) > 0 else {}
        try:
            m["FDTD"].Run(sim_path, cleanup=True, **kw)
        except TypeError:
            m["FDTD"].Run(sim_path, cleanup=True)
    t_fdtd = time.time() - t0

    status("port")
    port, nf2ff, unit = m["port"], m["nf2ff"], m["unit"]
    f_lo, f_hi, f0 = C["f_lo"] * 1e9, C["f_hi"] * 1e9, G["f0_ghz"] * 1e9
    freq = np.linspace(f_lo, f_hi, int(C["n_freq"]))
    port.CalcPort(sim_path, freq)
    s11 = port.uf_ref / port.uf_inc
    try:
        zin = port.uf_tot / port.if_tot
    except Exception:
        zin = np.full_like(s11, np.nan)
    pacc = 0.5 * np.real(port.uf_tot * np.conj(port.if_tot))       # accepted power (incident - reflected)

    center = [0, 0, m["Z_AP"] * unit]
    theta = np.arange(0.0, 180.0 + C["theta_step"] / 2, C["theta_step"])
    phis = np.array(C["phi_cuts"], float)
    ffreqs = [f * 1e9 for f in C["ff_freqs"]]
    status("nf2ff", part="cuts", n=len(ffreqs))
    r = nf2ff.CalcNF2FF(sim_path, ffreqs, theta, phis, center=center, outfile="nf2ff_cuts.h5",
                         read_cached=False)
    ff = []
    for i, f in enumerate(ffreqs):
        Et, Ep = np.asarray(r.E_theta[i]), np.asarray(r.E_phi[i])
        ff.append(dict(f_ghz=f / 1e9, theta=_l(theta), phis=_l(phis),
                       Et_re=_l(Et.real), Et_im=_l(Et.imag), Ep_re=_l(Ep.real), Ep_im=_l(Ep.imag),
                       Prad=float(np.real(r.Prad[i])), Dmax_nf2ff_dbi=float(10 * np.log10(np.real(r.Dmax[i]))),
                       Pacc=float(np.interp(f, freq, pacc))))
    sphere = None
    if C.get("sphere"):
        status("nf2ff", part="sphere")
        st = float(C["sphere_step"])
        th_s = np.arange(0.0, 180.0 + st / 2, st)
        ph_s = np.arange(0.0, 360.0, st)
        rs = nf2ff.CalcNF2FF(sim_path, f0, th_s, ph_s, center=center, outfile="nf2ff_sphere.h5",
                                read_cached=False)
        Et, Ep = np.asarray(rs.E_theta[0]), np.asarray(rs.E_phi[0])
        sphere = dict(f_ghz=f0 / 1e9, theta=_l(th_s), phi=_l(ph_s), Et_re=_l(Et.real), Et_im=_l(Et.imag),
                      Ep_re=_l(Ep.real), Ep_im=_l(Ep.imag), Prad=float(np.real(rs.Prad[0])),
                      Dmax_dbi=float(10 * np.log10(np.real(rs.Dmax[0]))), Pacc=float(np.interp(f0, freq, pacc)))

    i0 = int(np.argmin([abs(x["f_ghz"] - G["f0_ghz"]) for x in ff]))
    out = dict(format="feedlab-openems-results", version=2,
               meta=dict(kind=G["kind"], f0_ghz=G["f0_ghz"], params=G["params"], label=C.get("label", "")),
               geometry=G, config=C, mesh=m["info"],
               timing=dict(fdtd_s=t_fdtd, total_s=time.time() - T_START, post_only=bool(post_only)),
               freq_ghz=_l(freq / 1e9), s11_re=_l(s11.real), s11_im=_l(s11.imag),
               zin_re=_l(np.real(zin)), zin_im=_l(np.imag(zin)), pacc=_l(pacc),
               ff=ff, sphere=sphere, phase_ref="aperture plane z = Z_AP",
               # v1-compatible keys (cuts at f0)
               theta=ff[i0]["theta"], phis=ff[i0]["phis"], Et_re=ff[i0]["Et_re"], Et_im=ff[i0]["Et_im"],
               Ep_re=ff[i0]["Ep_re"], Ep_im=ff[i0]["Ep_im"],
               Dmax_dbi=(sphere or ff[i0]).get("Dmax_dbi", ff[i0]["Dmax_nf2ff_dbi"]), Prad=ff[i0]["Prad"],
               cells_per_lambda=C["cells_per_lambda"])
    with open(os.path.join(HERE, "results.json"), "w") as fh:
        json.dump(out, fh)
    s11_f0 = 20 * np.log10(abs(np.interp(f0, freq, s11.real) + 1j * np.interp(f0, freq, s11.imag)) + 1e-15)
    status("done", s11_f0_db=float(s11_f0), Dmax_dbi=float(out["Dmax_dbi"]), total_s=time.time() - T_START)
    print("S11 @ f0 = %.1f dB, Dmax = %.2f dBi, %.0f s" % (s11_f0, out["Dmax_dbi"], time.time() - T_START), flush=True)


if __name__ == "__main__":
    setup_dlls()
    try:
        if "--preview" in sys.argv:
            preview()
        else:
            main(post_only="--post" in sys.argv)
    except BaseException as e:
        status("error", error="%s: %s" % (type(e).__name__, e), trace=traceback.format_exc()[-4000:])
        traceback.print_exc()
        sys.exit(1)
