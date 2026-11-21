"""Example: feed designs for an offset dish (f/D eq. 0.7) on 10-134 GHz and efficiency curves."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from feedlab import horns, patterns, efficiency, reflector, waveguide

OPENING = 2 * reflector.half_angle_from_fD(0.70)      # full opening angle for f/D 0.7
for band in ("3cm", "1.2cm", "6mm", "4mm", "2.5mm", "2mm"):
    f = waveguide.HAM_BANDS_GHZ[band]
    print("=" * 70)
    print(horns.w2imu(f, fD=0.70))
    print(horns.skobelev(f, fD=0.70))
    print(horns.pickett_potter_oe2igl(f, OPENING))
    print("rect WG:", waveguide.suggest_rect_wg(f), " circular input (mm):",
          [round(x, 3) for x in waveguide.suggest_circular_diameter(f)])

# efficiency curves from the aperture model
fig, ax = plt.subplots(figsize=(8, 5))
fds = np.arange(0.3, 1.2, 0.01)
cases = {
    "open circular 0.76λ (coffee can)": patterns.circular_aperture_pattern(0.76, {"TE11": 1}),
    "W2IMU 1.31λ (TE11+0.15 TM11)": patterns.circular_aperture_pattern(1.31, {"TE11": 1, "TM11": 0.15}),
    "W2IMU 1.78λ (TE11+0.20 TM11)": patterns.circular_aperture_pattern(1.78, {"TE11": 1, "TM11": 0.20}),
}
for name, p in cases.items():
    ax.plot(fds, [100 * e.total for e in efficiency.efficiency_vs_fD(p, fds)], label=name)
ax.set_xlabel("f/D (prime focus or offset equivalent)"); ax.set_ylabel("efficiency %  (no blockage)")
ax.set_title("FeedLab aperture-model efficiency (illum·spill·phase·xpol)")
ax.grid(True, alpha=.3); ax.legend(); ax.set_ylim(30, 90)
fig.savefig("efficiency_curves.png", dpi=120, bbox_inches="tight")
print("saved efficiency_curves.png")
