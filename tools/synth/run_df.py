"""Global search in the IZ0JNY Dual-Flare family for one dish (differential evolution, fast solver).
Usage: python tools/synth/run_df.py <f_ghz> <out.json> [maxiter] [popsize]"""
import json, sys, time
sys.path.insert(0, ".")
from scipy.optimize import differential_evolution
from feedlab import synth

SC = dict(dish_kind="offset", D_mm=2400, fD=0.6905, elev_deg=30, t_rx_K=90, surface_rms_mm=0.4)   # Channel Master 243
FD = 0.6905
X0 = [0.76, 0.9543, 0.0777, 1.6342, 0.5776, 1.763, 1.8316, 1.3452]   # current IZ0JNY at this f/D (λ)
BOUNDS = [(0.72, 0.80)] + [(max(0.0, v * 0.7), v * 1.3 + (0.05 if v < 0.1 else 0)) for v in X0[1:]]


def main():
    f = float(sys.argv[1]); out = sys.argv[2]
    maxiter = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    pop = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    hist, t0 = [], time.time()
    base = synth.df_cost(X0, f, SC, FD)

    def cb(xk, convergence=None):
        v = synth.df_cost(xk, f, SC, FD)
        hist.append({"t": time.time() - t0, "cost": v, "x": list(map(float, xk))})
        json.dump({"f": f, "scenario": SC, "x0": X0, "base_cost": base, "best": hist[-1], "history": hist}, open(out, "w"), indent=1)
        print(f"{len(hist):4d} {time.time() - t0:7.0f}s  EME={-v:.3f}  (IZ0JNY {-base:.3f})  conv={convergence:.3f}", flush=True)

    import numpy as np
    rng = np.random.default_rng(2)
    n = pop * len(X0)
    init = np.array([[np.clip(x * (1 + rng.normal(0, 0.08)), lo, hi) for x, (lo, hi) in zip(X0, BOUNDS)] for _ in range(n)])
    init[0] = X0
    r = differential_evolution(synth.df_cost, BOUNDS, args=(f, SC, FD), maxiter=maxiter, popsize=pop, tol=1e-5,
                               mutation=(0.4, 0.9), recombination=0.7, seed=2, workers=4, updating="deferred",
                               polish=False, callback=cb, init=init)
    cb(r.x, 0.0)
    print("done", r.fun, list(r.x))


if __name__ == "__main__":
    main()
