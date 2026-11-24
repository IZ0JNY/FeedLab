# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""How the feed and the λ/4 matching plate are fixed to the external waveguide section (WR-90, WR-75, WR-42,
round MIL flanges from WR-22): ready-made schemes that set every hole of the feed base and of the plate, and a
cross-section sketch of each one. The details (diameters, thread, counterbores, plate screws…) stay editable.
"""
from __future__ import annotations

from .flanges import FLANGES, base_thread_options, plate_screw_options

# key → (title, short explanation); the flange shape decides which schemes are offered
SCHEMES = {
    "feed_side": ("Viti dal lato del feed",
                  "Il feed + la piastrina si avvitano sul tronchetto di guida esterno (relè, LNA): le viti entrano dal "
                  "lato del feed, con la testa nella lamatura della base, attraversano base e piastrina e si avvitano "
                  "nella flangia della guida."),
    "guide_side": ("Viti dal lato della guida",
                   "Le viti della guida attraversano la flangia e la piastrina e si avvitano nei fori filettati della "
                   "base del feed."),
    "plate_screwed": ("Piastrina avvitata a guida e feed (IZ0JNY)",
                      "La guida si avvita alla piastrina (fori della flangia filettati nella piastrina); 4 viti a "
                      "brugola con la testa nella lamatura della piastrina (lato guida) la fissano alla base del feed."),
    "round_feed_side": ("Viti dal lato del feed + pin di allineamento",
                        "Flangia rotonda MIL: fori passanti in base e piastrina, viti dal lato del feed avvitate nella "
                        "flangia della guida; i pin della flangia allineano guida, piastrina e feed."),
    "round_guide_side": ("Viti della guida filettate nella base + pin",
                         "Flangia rotonda MIL: le viti 4-40 della guida attraversano la piastrina e si avvitano nella "
                         "base del feed (filettata passante); i pin della flangia allineano il tutto."),
    "none": ("Nessun foro", "Base del feed e piastrina senza fori (fissaggio a cura tua)."),
}


def schemes_for(wg: str | None) -> list[str]:
    """Schemes offered for this waveguide (square flanges 10/24 GHz, round MIL flanges from 47 GHz)."""
    fl = FLANGES.get(wg or "")
    if fl is None:
        return ["none"]
    if fl.shape == "round":
        return ["round_feed_side", "round_guide_side", "none"]
    return ["feed_side", "guide_side", "plate_screwed", "none"]


def defaults(scheme: str, wg: str, f_ghz: float | None, system: str = "metric") -> dict:
    """Mount settings (flanges.mount / plate.design_plate keywords) chosen by the scheme."""
    d = dict(holes=scheme != "none", base_holes="flange", hole_dia=None, plate_hole_dia=None, thread=None,
             cbore=False, cb_dia=None, cb_depth=None, pins=True, plate_screw=None, plate_head="allen", plate_tap=False)
    if scheme == "feed_side":
        d.update(cbore=True)
    elif scheme == "guide_side":
        d.update(base_holes="tap", thread=base_thread_options(wg, f_ghz, system)[0])
    elif scheme == "plate_screwed":
        d.update(plate_tap=True, plate_screw=plate_screw_options(f_ghz)[0])
    elif scheme == "round_guide_side":
        d.update(base_holes="tap", thread="4-40 UNC")
    return d


def section_fig(scheme: str, tr=lambda s: s, screw: str = "", plate_screw: str = ""):
    """Cross-section sketch (not to scale) of the stack external waveguide | λ/4 plate | feed base for a scheme."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle

    fig, ax = plt.subplots(figsize=(5.2, 4.0), dpi=110)
    ax.set_xlim(-12, 14); ax.set_ylim(-8.2, 13.2); ax.set_aspect("equal"); ax.axis("off")
    layers = [("guide", -3.0, 0.0, "#9fb7d6", tr("flangia della guida esterna")),
              ("plate", 0.0, 2.2, "#e0c46c", tr("piastrina λ/4")),
              ("base", 2.2, 5.0, "#c9a227", tr("base del feed"))]
    for _, y0, y1, col, lab in layers:
        for x0, x1 in ((-11, -2.2), (2.2, 11)):                    # the waveguide opening in the middle
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=col, ec="k", lw=0.8))
        ax.text(11.4, (y0 + y1) / 2, lab, va="center", fontsize=7)
    # feed horn above the base
    ax.add_patch(Polygon([(-2.2, 5), (-2.2, 9), (-5.5, 12.5), (-6.5, 12.5), (-3.2, 9), (-3.2, 5)], fc="#c9a227", ec="k", lw=0.8))
    ax.add_patch(Polygon([(2.2, 5), (2.2, 9), (5.5, 12.5), (6.5, 12.5), (3.2, 9), (3.2, 5)], fc="#c9a227", ec="k", lw=0.8))
    ax.text(0, 11.6, tr("feed"), ha="center", fontsize=7, bbox=dict(fc="white", ec="none", pad=0.5))
    ax.annotate("", (0, -4.2), (0, 12.8), arrowprops=dict(arrowstyle="-", ls="-.", lw=0.5, color="0.4"))

    def screw(x, y_head, y_tip, up=True, head_w=2.4, head_h=1.2, col="#555"):
        """head at y_head, shank to y_tip; up=True: head below, shank going up."""
        if up:
            ax.add_patch(Rectangle((x - head_w / 2, y_head - head_h), head_w, head_h, fc=col, ec="k", lw=0.6))
            ax.add_patch(Rectangle((x - 0.55, y_head), 1.1, y_tip - y_head, fc=col, ec="k", lw=0.6))
        else:
            ax.add_patch(Rectangle((x - head_w / 2, y_head), head_w, head_h, fc=col, ec="k", lw=0.6))
            ax.add_patch(Rectangle((x - 0.55, y_tip), 1.1, y_head - y_tip, fc=col, ec="k", lw=0.6))

    def thread(x, y0, y1):
        for y in [y0 + 0.35 * i for i in range(int((y1 - y0) / 0.35) + 1)]:
            ax.plot([x - 0.9, x + 0.9], [y, y + 0.2], lw=0.4, color="k")

    def cbore(x, y0, y1, w=2.8):
        ax.add_patch(Rectangle((x - w / 2, y0), w, y1 - y0, fc="white", ec="k", lw=0.6))

    notes = []
    if scheme in ("feed_side", "round_feed_side"):
        cbore(7.5, 3.4, 5.0)
        screw(7.5, 3.4, -2.6, up=False)
        thread(7.5, -2.6, -0.2)
        notes.append(tr("vite dal lato del feed, testa nella lamatura della base; filetto nella flangia della guida"))
    elif scheme in ("guide_side", "round_guide_side"):
        screw(7.5, -3.0, 4.8, up=True)
        thread(7.5, 2.4, 4.8)
        notes.append(tr("vite dal lato della guida; filetto nella base del feed"))
    elif scheme == "plate_screwed":
        screw(8.5, -3.0, 1.9, up=True)
        thread(8.5, 0.2, 2.0)
        cbore(-7.5, 0.0, 1.2)
        screw(-7.5, 1.2, 4.4, up=True, head_w=2.0, head_h=1.0, col="#a0429a")
        thread(-7.5, 2.4, 4.4)
        notes.append(tr("vite della guida filettata nella piastrina; vite piastrina→feed con la testa nella lamatura della piastrina"))
    else:
        notes.append(tr("nessun foro"))
    if scheme.startswith("round"):
        ax.add_patch(Rectangle((-8.4, -1.5), 0.8, 5.0, fc="#3a9a3a", ec="k", lw=0.5))
        notes.append(tr("pin di allineamento (verde)"))
    import textwrap
    # notes well below the stack (screw heads under the waveguide flange reach about −4.5)
    ax.text(-11.5, -5.8, "\n".join(textwrap.wrap(" · ".join(notes), 70)), fontsize=6.5, va="top")
    fig.tight_layout()
    return fig
