# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""FeedLab — design and analysis of microwave dish feeds, 10-134 GHz.

Knowledge base: W1GHZ Online Microwave Antenna Book (Paul W1GHZ), OE2IGL design guides (Gerald OE2IGL),
Kildal, Milligan, Baars. See docs/KNOWLEDGE_BASE.md.
"""
from . import waveguide, reflector, patterns, efficiency, horns, cassegrain, noise  # noqa: F401

__version__ = "0.4.26"
