"""Refine the compact Dual-Flare (new f/D 0.7 row) directly at 10.368 and 47.088 GHz on the Channel Master 243
(Nelder-Mead from the 24 GHz optimum): shows whether material losses move the optimum in λ.
Usage: python tools/synth/refine_bands.py tools/synth/table.json out.json"""
import json, sys
sys.path.insert(0, ".")
import numpy as np
from scipy.optimize import minimize
from tools.synth.run_table import cost

tab = json.load(open(sys.argv[1]))
x0 = np.array(tab["0.7"]["x"])
out = {}
import tools.synth.run_table as rt
for f in (10.3682, 24.0482, 47.0882):
    rt.F = f
    c0 = cost(list(x0), 0.6905)
    r = minimize(lambda x: cost(list(x), 0.6905), x0, method="Nelder-Mead",
                 options={"maxfev": 160, "initial_simplex": np.vstack([x0] + [x0 * (1 + 0.03 * np.eye(len(x0))[i]) for i in range(len(x0))])})
    out[str(f)] = {"x_start": list(x0), "cost_start": c0, "x": list(map(float, r.x)), "cost": float(r.fun),
                   "rel_change": list(map(float, r.x / x0 - 1))}
    print(f, round(-c0, 3), "→", round(-r.fun, 3), "max change", round(float(np.max(np.abs(r.x / x0 - 1))) * 100, 2), "%", flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
