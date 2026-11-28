# -*- coding: utf-8 -*-
"""FeedLab - openEMS full-wave "deep analysis" of a dish feed. Auto-generated.

Run:      python -u sim.py            (openEMS >= 0.0.36 with its Python bindings)
Preview:  python sim.py --preview     (opens the model in AppCSXCAD, no simulation)
Post:     python sim.py --post        (only port + far field again from sim_data, after a full run)
Output:   results.json (load it in FeedLab, tab "Full-wave openEMS"), status.json, sim_data/
"""
import os, sys, json, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.loads(r"""{"format": "feedlab-openems-config", "version": 2, "geometry": {"kind": "axial_corrugated", "f0_ghz": 10.368, "params": {"pitch": 12.87281895881635, "w": 10.819613662109271, "axi": 2.7329196362807746, "delta": 4.333837659331518, "Di": 22.078420342234505, "Ds": 23.124934685346368, "las": 16.083952914819548, "d1": 14.353952914819548, "d2": 8.824183424707465, "d3": 8.824183424707465, "d4": 8.824183424707465, "d5": 8.824183424707465, "d6": 8.824183424707465, "d7": 8.824183424707465, "d8": 8.824183424707465, "outer_diam": 246.52412171047317, "length": 66.86247763623858, "opening_deg": 128.02153283233397, "eta_guide_pct": 85.237359530582, "wall": 1.73, "L_guide": 28.91516763117284, "z_head": 28.91516763117284, "flange_diam": 48.670554447172776, "flange_thickness": 3.4698201157407405}, "polys": [[[11.039210171117253, 11.039210171117253, 12.769210171117253, 12.769210171117253, 24.335277223586388, 24.335277223586388, 11.039210171117253], [0.0, 28.91516763117284, 28.91516763117284, 3.4698201157407405, 3.4698201157407405, 0.0, 0.0]], [[11.039210171117253, 11.039210171117253, 11.562467342673184, 15.896305002004702, 15.896305002004702, 26.71591866411397, 26.71591866411397, 28.76912396082105, 28.76912396082105, 39.588737622930324, 39.588737622930324, 41.6419429196374, 41.6419429196374, 52.46155658174667, 52.46155658174667, 54.51476187845375, 54.51476187845375, 65.33437554056302, 65.33437554056302, 67.3875808372701, 67.3875808372701, 78.20719449937937, 78.20719449937937, 80.26039979608646, 80.26039979608646, 91.08001345819574, 91.08001345819574, 93.1332187549028, 93.1332187549028, 103.95283241701208, 103.95283241701208, 106.00603771371914, 106.00603771371914, 116.82565137582841, 116.82565137582841, 123.26206085523658, 123.26206085523658], [28.91516763117284, 44.99912054599238, 44.99912054599238, 44.99912054599238, 30.64516763117284, 30.64516763117284, 47.73204018227317, 47.73204018227317, 38.907856757565696, 38.907856757565696, 50.464959818553936, 50.464959818553936, 41.64077639384647, 41.64077639384647, 53.197879454834705, 53.197879454834705, 44.37369603012724, 44.37369603012724, 55.93079909111549, 55.93079909111549, 47.10661566640802, 47.10661566640802, 58.66371872739626, 58.66371872739626, 49.8395353026888, 49.8395353026888, 61.39663836367703, 61.39663836367703, 52.57245493896957, 52.57245493896957, 64.12955799995781, 64.12955799995781, 55.30537457525034, 55.30537457525034, 66.86247763623858, 66.86247763623858, 28.91516763117284]]], "r_input": 11.039210171117253, "z_aperture": 66.86247763623858, "outer_radius": 123.26206085523658, "r_aperture": 116.82565137582841}, "config": {"f_lo": 9.3312, "f_hi": 11.404800000000002, "cells_per_lambda": 26, "nr_ts": 40000, "end_db": 30.0, "port_mode": "TE11", "n_freq": 201, "ff_freqs": [10.16064, 10.368, 10.57536], "theta_step": 1.0, "phi_cuts": [0.0, 45.0, 90.0], "sphere": false, "sphere_step": 3.0, "pad_lambda": 0.4, "dump_fields": false, "threads": 0, "min_cell_frac": 0.3, "openems_root": "", "label": "axial_corrugated best confirm"}, "notes": ["efficienza secondo la design guide OE2IGL: 85.2% (spillover 93.2%, illuminazione 93.5%)", "tolleranza di lavorazione \u00b10.1 mm (OE2IGL)", "valido 10\u201376 GHz, prime focus f/D 0.33\u20130.90, offset 0.33\u20130.80", "usa l\u0027angolo di apertura della parabola, non l\u0027f/D (OE2IGL)", "simulazione rapida non disponibile (scalini assiali): verifica con openEMS", "guida d\u0027ingresso portata a 16.08 mm per contenere lo scalino pi\u00f9 profondo"]}""")
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
