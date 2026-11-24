"""Global optimisation of a conical corrugated EME horn for one dish (differential evolution, fast solver).
Usage: python tools/synth/run_cg.py <f_ghz> <out.json> [maxiter] [popsize]"""
import json, sys, time
sys.path.insert(0, ".")
from scipy.optimize import differential_evolution
from feedlab import synth

SC = dict(dish_kind="offset", D_mm=2400, fD=0.6905, elev_deg=30, t_rx_K=90, surface_rms_mm=0.4)   # Channel Master 243


def main():
    f = float(sys.argv[1]); out = sys.argv[2]
    maxiter = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    pop = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    hist, t0 = [], time.time()

    def cb(xk, convergence=None):
        v = synth.cg_cost(xk, f, SC)
        hist.append({"t": time.time() - t0, "cost": v, "x": list(map(float, xk))})
        json.dump({"f": f, "scenario": SC, "best": hist[-1], "history": hist}, open(out, "w"), indent=1)
        print(f"{len(hist):4d} {time.time() - t0:7.0f}s  EME={-v:.3f}  conv={convergence:.3f}", flush=True)

    r = differential_evolution(synth.cg_cost, synth.CG_BOUNDS, args=(f, SC), maxiter=maxiter, popsize=pop, tol=1e-5,
                               mutation=(0.5, 1.0), recombination=0.7, seed=4, workers=4, updating="deferred",
                               polish=False, callback=cb, integrality=[False] * 5 + [True, False])
    cb(r.x, 0.0)
    print("done", r.fun, list(r.x))


if __name__ == "__main__":
    main()
