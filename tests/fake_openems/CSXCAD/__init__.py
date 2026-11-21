"""Minimal stand-in for the CSXCAD Python bindings, used only by FeedLab's tests (no real FDTD)."""
import numpy as np

__version__ = "fake-0.0"
AppCSXCAD_BIN = "AppCSXCAD"


class _Grid:
    def __init__(self):
        self.lines = {"x": [], "y": [], "z": []}
        self.unit = 1.0

    def SetDeltaUnit(self, u):
        self.unit = u

    def SetLines(self, d, lines):
        self.lines[d] = sorted(float(x) for x in lines)

    def SmoothMeshLines(self, d, res, ratio=1.4):
        a, b = min(self.lines[d]), max(self.lines[d])
        n = max(20, int(np.ceil((b - a) / res)) + 1)
        self.lines[d] = list(np.linspace(a, b, n))

    def GetLines(self, d):
        return np.array(self.lines[d])


class _Prop:
    def __init__(self, name):
        self.name = name
        self.prims = []

    def AddRotPoly(self, **kw):
        pts = np.asarray(kw["points"])
        assert pts.shape[0] == 2 and pts.shape[1] >= 3, "AddRotPoly needs 2 x N points"
        self.prims.append(("rotpoly", kw))

    def AddBox(self, start, stop, **kw):
        self.prims.append(("box", start, stop))


class ContinuousStructure:
    def __init__(self):
        self.grid = _Grid()
        self.props = []

    def GetGrid(self):
        return self.grid

    def AddMetal(self, name):
        p = _Prop(name)
        self.props.append(p)
        return p

    def AddDump(self, name, **kw):
        p = _Prop(name)
        self.props.append(p)
        return p

    def Write2XML(self, fn):
        with open(fn, "w") as fh:
            fh.write("<ContinuousStructure/>")
