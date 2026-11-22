"""FeedLab — design and analysis of microwave dish feeds, 10-134 GHz.

Knowledge base: W1GHZ Online Microwave Antenna Book (P. Wade), OE2IGL design guides (G. Ihninger),
Kildal, Milligan, Baars. See docs/KNOWLEDGE_BASE.md.
"""
from . import waveguide, reflector, patterns, efficiency, horns, cassegrain, noise  # noqa: F401

__version__ = "0.4.4"
