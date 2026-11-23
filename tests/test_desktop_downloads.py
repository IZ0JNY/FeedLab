"""Desktop app (Windows/WebView2): the save dialog proposes the file's own extension and never drops it."""
import sys
import types

from feedlab import desktop


def _fake_edgechromium(chosen):
    ec = types.ModuleType("webview.platforms.edgechromium")
    ec.webview_settings = {"ALLOW_DOWNLOADS": True}

    class Dialog:
        def __init__(self):
            self.Filter = self.DefaultExt = self.FileName = ""
            self.AddExtension = False

        def ShowDialog(self, form):
            ec.last = self
            self.FileName = chosen
            return "OK"
    ec.WinForms = types.SimpleNamespace(SaveFileDialog=Dialog, DialogResult=types.SimpleNamespace(OK="OK"))
    ec.winreg = types.SimpleNamespace(OpenKey=lambda *a: (_ for _ in ()).throw(OSError()), HKEY_CURRENT_USER=0)

    class EdgeChrome:
        form = None
    ec.EdgeChrome = EdgeChrome
    return ec


def test_save_dialog_keeps_extension(monkeypatch):
    ec = _fake_edgechromium(r"C:\Users\x\Downloads\feed_24GHz")            # user typed the name without .stp
    plat = types.ModuleType("webview.platforms"); plat.edgechromium = ec
    wv = types.ModuleType("webview"); wv.platforms = plat
    monkeypatch.setitem(sys.modules, "webview", wv)
    monkeypatch.setitem(sys.modules, "webview.platforms", plat)
    monkeypatch.setitem(sys.modules, "webview.platforms.edgechromium", ec)
    monkeypatch.setattr(desktop, "IS_WIN", True)
    desktop.patch_downloads()
    args = types.SimpleNamespace(ResultFilePath=r"C:\tmp\iz0jny_24p048GHz.stp", Cancel=False)
    ec.EdgeChrome().on_download_starting(None, args)
    assert args.ResultFilePath.endswith("feed_24GHz.stp") and not args.Cancel
    assert ec.last.DefaultExt == "stp" and ec.last.Filter.startswith("STP (*.stp)|*.stp")
