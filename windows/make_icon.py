"""Draw FeedLab's icon (a dish with its feed) and EMELab's (the same dish looking at the Moon) and write
windows/feedlab.ico and windows/emelab.ico (PNG-compressed ICO).  python windows/make_icon.py [feedlab|emelab]"""
import io
import struct
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon  # noqa: E402


def draw(size: int, moon: bool = False) -> bytes:
    fig = plt.figure(figsize=(1, 1), dpi=size)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.patch.set_alpha(0)
    ax.add_patch(FancyBboxPatch((0.04, 0.04), 0.92, 0.92, boxstyle="round,pad=0,rounding_size=0.2",
                                fc="#1d1b3a" if moon else "#12324f", ec="none"))
    if moon:                                    # full Moon with two maria, up-right
        from matplotlib.patches import Circle
        ax.add_patch(Circle((0.80, 0.80), 0.12, fc="#f4efd8", ec="none"))
        ax.add_patch(Circle((0.77, 0.83), 0.035, fc="#d8d0b0", ec="none"))
        ax.add_patch(Circle((0.84, 0.76), 0.025, fc="#d8d0b0", ec="none"))
    y = np.linspace(-0.38, 0.38, 80)
    x = 0.16 + 1.25 * y ** 2                    # reflector, concave to the right
    outer = np.c_[x, 0.5 + y]
    inner = np.c_[x + 0.05 + 0.08 * (1 - (y / 0.38) ** 2), 0.5 + y][::-1]
    ax.add_patch(Polygon(np.vstack([outer, inner]), closed=True, fc="#e8eef4", ec="none"))
    lw = max(0.8, size / 90)
    xf = 0.70                                   # focus
    for yy in (0.38, -0.38):
        ax.plot([0.16 + 1.25 * yy ** 2 + 0.03, xf + 0.08], [0.5 + yy * 0.97, 0.5], color="#7f95ab", lw=lw)
    # feed horn: wide aperture toward the dish
    ax.add_patch(Polygon([[xf - 0.04, 0.39], [xf - 0.04, 0.61], [xf + 0.10, 0.545], [xf + 0.10, 0.455]], closed=True,
                         fc="#f2a900", ec="none"))
    ax.add_patch(Polygon([[xf + 0.10, 0.47], [xf + 0.10, 0.53], [xf + 0.17, 0.53], [xf + 0.17, 0.47]], closed=True,
                         fc="#f2a900", ec="none"))
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=size, transparent=True)
    plt.close(fig)
    return buf.getvalue()


def main(which: str = "feedlab"):
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pngs = [draw(s, moon=which == "emelab") for s in sizes]
    head = struct.pack("<HHH", 0, 1, len(sizes))
    off = 6 + 16 * len(sizes)
    entries, data = b"", b""
    for s, p in zip(sizes, pngs):
        entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(p), off + len(data))
        data += p
    out = Path(__file__).with_name(f"{which}.ico")
    out.write_bytes(head + entries + data)
    Path(__file__).with_name(f"{which}_256.png").write_bytes(pngs[-1])
    print(out, out.stat().st_size)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "feedlab")
