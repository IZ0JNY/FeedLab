"""Compare the synthesized feeds with the published ones on the Channel Master 243 at 10, 24 and 47 GHz,
with a Monte Carlo of machining errors (radius errors, Gaussian, σ = tol/2 on every wall point).
Usage: python tools/synth/compare.py <cg.json> [df.json] > report.json"""
import json, sys
sys.path.insert(0, ".")
import numpy as np
from feedlab import explore, geometry, modematch, synth
from feedlab.waveguide import wavelength_mm

SC = dict(dish_kind="offset", D_mm=2400, fD=0.6905, elev_deg=30, t_rx_K=90, surface_rms_mm=0.4)
TOL = {10.368: 0.05, 24.048: 0.03, 47.088: 0.02}           # ± mm, typical good CNC turning


def run(geo, f, sc, n_modes=14):
    lam = wavelength_mm(f)
    secs = geo.staircase(lam / 20)
    fl = [f * 0.99, f, f * 1.01]
    r = modematch.simulate(secs, fl, n_modes=n_modes)
    pat = modematch.aperture_pattern(r, 1, f, n_rho=28, n_phi=32, n_theta=181)
    res = explore.performance(geo.kind, f, sc, geo, pat, float(r.s11_db[1]), r.aperture_modes[1])
    return res, [float(v) for v in r.s11_db]


def perturbed(geo, sigma, rng):
    import copy
    g = copy.copy(geo)
    prof = []
    for z, r in geo.profile:
        prof.append((z, max(0.05, r + rng.normal(0, sigma))))
    g.profile = prof
    return g


def main():
    cg = json.load(open(sys.argv[1]))["best"]["x"]
    df = json.load(open(sys.argv[2]))["best"]["x"] if len(sys.argv) > 2 else None
    sc = explore.Scenario(**SC)
    out = {}
    rng = np.random.default_rng(7)
    for f in (10.368, 24.048, 47.088):
        geos = {"IZ0JNY Dual-Flare": geometry.build("iz0jny", f, fD=SC["fD"]),
                "W2IMU": geometry.build("w2imu", f, fD=SC["fD"]),
                "Large W2IMU": geometry.build("large_w2imu", f, fD=SC["fD"]),
                "Pickett-Potter": geometry.build("pickett_potter", f, fD=SC["fD"]),
                "Corrugato FeedLab": synth.cg_geometry(cg, f)}
        if df:
            geos["Dual-Flare ottimizzato"] = geometry.build("iz0jny", f, fD=SC["fD"], **synth.df_params(df, wavelength_mm(f)))
        out[f] = {}
        for name, g in geos.items():
            res, s11 = run(g, f, sc)
            mc = []
            for _ in range(12):
                r2, _ = run(perturbed(g, TOL[f] / 2, rng), f, sc)
                mc.append(r2.gain_dbi + r2.g_over_t)
            out[f][name] = {"G": res.gain_dbi, "GT": res.g_over_t, "EME": res.gain_dbi + res.g_over_t, "taper": res.edge_taper_db,
                            "eta": res.eta, "spill": res.spill, "illum": res.illum, "pol": res.pol, "phase": res.phase,
                            "s11": s11, "len_mm": g.length, "D_ap_mm": 2 * g.r_aperture, "pc_mm": res.pc_mm,
                            "mc_mean": float(np.mean(mc)), "mc_min": float(np.min(mc))}
            print(f, name, {k: round(v, 3) if isinstance(v, float) else v for k, v in out[f][name].items()}, file=sys.stderr, flush=True)
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
