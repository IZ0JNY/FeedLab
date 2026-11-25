"""Re-optimise the IZ0JNY Dual-Flare table (offset-equivalent f/D 0.6, 0.7, 0.8, 0.9) for EME (G + G/T),
S11 < −25 dB over ±1 %, input guide ≤ 0.76 λ (TE11 only), with a small preference for shorter feeds.
Usage: python tools/synth/run_table.py <out.json> [maxiter] [popsize]"""
import json, sys, time
sys.path.insert(0, ".")
from scipy.optimize import differential_evolution
from feedlab import geometry, synth
from feedlab.waveguide import wavelength_mm

F = 24.048
LEN_W = 0.003            # dB per λ of length: tie-breaker towards compact feeds


def cost(x, fD):
    sc = dict(dish_kind="offset", D_mm=2400, fD=fD, elev_deg=30, t_rx_K=90, surface_rms_mm=0.4)
    v = synth.df_cost(x, F, sc, fD)
    if v >= 1e3:
        return v
    lam = wavelength_mm(F)
    g = geometry.build("iz0jny", F, fD=fD, **synth.df_params(x, lam))
    return v + LEN_W * g.length / lam


def main():
    out = sys.argv[1]
    maxiter = int(sys.argv[2]) if len(sys.argv) > 2 else 35
    pop = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    res = json.load(open(out)) if len(sys.argv) > 4 else {}
    import numpy as np
    for fD, row in geometry.IZ0JNY_TABLE.items():
        if str(fD) in res:
            continue
        x0 = [0.76, *row[:1], row[1], row[2], row[3], row[4], row[5], row[6]]
        b = [(0.70, 0.76)] + [(max(0.0, v * 0.7), v * 1.3 + (0.05 if v < 0.1 else 0)) for v in x0[1:]]
        rng = np.random.default_rng(3)
        init = np.array([[np.clip(x * (1 + rng.normal(0, 0.08)), lo, hi) for x, (lo, hi) in zip(x0, b)]
                         for _ in range(pop * len(x0))])
        init[0] = x0
        t0 = time.time()
        r = differential_evolution(cost, b, args=(fD,), maxiter=maxiter, popsize=pop, tol=1e-5, mutation=(0.4, 0.9),
                                   recombination=0.7, seed=3, workers=4, updating="deferred", polish=False, init=init)
        base = cost(x0, fD)
        res[str(fD)] = {"x0": x0, "x": list(map(float, r.x)), "cost": float(r.fun), "base": float(base), "s": time.time() - t0}
        json.dump(res, open(out, "w"), indent=1)
        print(f"f/D {fD}: {-base:.3f} → {-r.fun:.3f}  ({time.time() - t0:.0f}s)  x={[round(v, 4) for v in r.x]}", flush=True)


if __name__ == "__main__":
    main()
