# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""Dish illumination chosen by the user (edge taper in dB) and what it means on the reflector.

Model: feed pattern cos^q(θ) (the usual one for horn feeds, Balanis / Kildal), plus the space attenuation
from the focus to the rim, 20·log10((1 + cos ψ)/2). A feed designed for a dish of f/D_d gives -10 dB at the
rim of that dish (the design rule of W1GHZ/OE2IGL feeds); on the user's dish (half-angle ψ) the edge taper is
then the feed pattern at ψ plus the space attenuation. The user's taper → the f/D the feed is designed for.
"""
from __future__ import annotations

import math

import numpy as np

from .reflector import fD_from_half_angle, half_angle_from_fD

FEED_EDGE_DB = 10.0              # feed pattern at the rim of its design dish (W1GHZ / OE2IGL rule)
AUTO_FACTOR = {"gain": 1.0, "gt": 1.08, "rx": 1.12}   # wizard default: design f/D = factor × dish f/D


def space_loss_db(psi_deg: float) -> float:
    """Free-space attenuation at the rim relative to the vertex (positive dB)."""
    return -20 * math.log10((1 + math.cos(math.radians(psi_deg))) / 2)


def q_for_design(fD_design: float, feed_edge_db: float = FEED_EDGE_DB) -> float:
    """Exponent q of the cos^q feed pattern that is -feed_edge_db at the rim of a dish of f/D = fD_design."""
    c = math.cos(math.radians(half_angle_from_fD(fD_design)))
    return feed_edge_db / (-20 * math.log10(c))


def edge_taper_db(fD: float, q: float) -> float:
    """Total edge taper (feed pattern + space attenuation, positive dB) on a dish of f/D = fD."""
    psi = half_angle_from_fD(fD)
    return -20 * q * math.log10(math.cos(math.radians(psi))) + space_loss_db(psi)


def design_fD_for_taper(fD: float, taper_db: float) -> float:
    """f/D the feed must be designed for to give `taper_db` of edge taper on the user's dish (bisection)."""
    lo, hi = 0.26, 5.0                      # f/D 0.26: half-angle ≈ 88°
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if edge_taper_db(fD, q_for_design(mid)) < taper_db:
            lo = mid              # wider beam than wanted → design for a larger f/D (narrower beam)
        else:
            hi = mid
    return 0.5 * (lo + hi)


def profile_db(fD: float, q: float, n: int = 121):
    """Illumination over the aperture: (ρ/R array 0…1, relative level in dB, 0 at the centre)."""
    psi = math.radians(half_angle_from_fD(fD))
    rho = np.linspace(0.0, 1.0, n)
    # aperture radius of the ray at angle θ: ρ = 2f·tan(θ/2); at the rim ρ = R
    th = 2 * np.arctan(rho * math.tan(psi / 2))
    lev = 20 * q * np.log10(np.cos(th)) + 20 * np.log10((1 + np.cos(th)) / 2)
    return rho, lev


def efficiencies(fD: float, q: float) -> dict:
    """Spillover, illumination (taper) and their product for a cos^q feed on a prime-focus dish of f/D = fD."""
    psi = math.radians(half_angle_from_fD(fD))
    spill = 1 - math.cos(psi) ** (2 * q + 1)                     # power intercepted by the dish
    th = np.linspace(0, psi, 2001)
    integ = np.trapezoid(np.cos(th) ** q * np.tan(th / 2), th)
    total = 2 * (2 * q + 1) / math.tan(psi / 2) ** 2 * integ ** 2   # Balanis (15-41), spill × taper
    return {"spillover": spill, "taper": total / spill if spill > 0 else 0.0, "total": total}


def area_fraction(fD: float, q: float, level_db: float) -> float:
    """Fraction of the aperture area illuminated within `level_db` (positive) of the centre."""
    rho, lev = profile_db(fD, q, 2001)
    inside = rho[lev >= -abs(level_db)]
    return float(inside.max() ** 2) if inside.size else 0.0


def setting(fD: float, priority: str = "gain", taper_db: float | None = None) -> dict:
    """Everything the wizard shows: design f/D, q, edge taper, efficiencies and illuminated areas."""
    fD_d = design_fD_for_taper(fD, taper_db) if taper_db else fD * AUTO_FACTOR.get(priority, 1.0)
    q = q_for_design(fD_d)
    return {"fD_design": fD_d, "factor": fD_d / fD, "q": q, "edge_db": edge_taper_db(fD, q),
            "half_angle": half_angle_from_fD(fD), **efficiencies(fD, q),
            "area3": area_fraction(fD, q, 3.0), "area10": area_fraction(fD, q, 10.0)}


__all__ = ["setting", "profile_db", "design_fD_for_taper", "edge_taper_db", "q_for_design", "fD_from_half_angle"]
