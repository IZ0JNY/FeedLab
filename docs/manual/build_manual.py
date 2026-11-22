"""Build the user manuals (PDF, Italian and English) from the Markdown sources in this folder.

    python docs/manual/build_manual.py

Markdown → HTML (python-markdown) → PDF with headless Chromium (Playwright for Node, or any
Chromium/Chrome/Edge executable given in CHROME=...). The version is read from feedlab.__version__.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
from feedlab import __version__  # noqa: E402

from feedlab.i18n import MANUALS  # noqa: E402

# source Markdown per language; screenshots in img/<lang>/ (docs/manual/tools/make_screens.py)
SOURCES = {"it": "manuale_it.md", "en": "user_manual_en.md"}
DOCS = {SOURCES[l]: (MANUALS[l], l) for l in SOURCES}
TITLES = {"it": "Manuale d’uso", "en": "User Manual"}

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: "Segoe UI", "DejaVu Sans", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1d1d1f; }
h1 { font-size: 24pt; color: #8b1a1a; margin: 0 0 4pt 0; }
h2 { font-size: 15pt; color: #8b1a1a; border-bottom: 1.5px solid #e2c2c2; padding-bottom: 3pt; margin-top: 18pt;
     page-break-after: avoid; }
h3 { font-size: 12pt; color: #333; margin-top: 12pt; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
img { display: block; max-width: 100%; max-height: 105mm; margin: 6pt auto 10pt auto; border: 1px solid #ccc;
      page-break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt 0; font-size: 9.5pt; page-break-inside: avoid; }
th, td { border: 1px solid #d0d0d0; padding: 4pt 6pt; vertical-align: top; text-align: left; }
th { background: #f4eeee; }
code, pre { font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 9.5pt; background: #f5f5f5; }
pre { padding: 6pt 8pt; border-radius: 3pt; }
hr { border: 0; border-top: 1px solid #ddd; margin: 10pt 0; }
"""

PRINT_JS = r"""
const { chromium } = require('playwright');
(async () => {
  const [html, pdf, title] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + html, { waitUntil: 'load' });
  await p.pdf({ path: pdf, format: 'A4', printBackground: true, displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: `<div style="font-size:7pt;width:100%;text-align:center;color:#888">${title} — <span class="pageNumber"></span>/<span class="totalPages"></span></div>`,
    margin: { top: '16mm', bottom: '18mm', left: '14mm', right: '14mm' } });
  await b.close();
})();
"""


def _normalise(md: str) -> str:
    """python-markdown needs a blank line before a list and 4-space indentation for nested lists."""
    import re
    out, prev = [], ""
    for line in md.split("\n"):
        m = re.match(r"^( {2,3})([-*]|\d+\.) ", line)
        if m:
            line = "    " + line.lstrip(" ")
        is_item = bool(re.match(r"^\s*([-*]|\d+\.) ", line))
        prev_item = bool(re.match(r"^\s*([-*]|\d+\.) ", prev))
        if is_item and prev.strip() and not prev_item and not prev.startswith("    "):
            out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def build(src: str, out_name: str, lang: str) -> Path:
    md = _normalise((HERE / src).read_text(encoding="utf-8").replace("{VERSION}", __version__)
                    .replace("{IMG}", f"img/{lang}"))
    body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    html = HERE / f"_{Path(src).stem}.html"
    html.write_text(f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>{CSS}</style></head>'
                    f"<body>{body}</body></html>", encoding="utf-8")
    out = HERE / out_name
    title = f"FeedLab {__version__} — {TITLES[lang]}"
    chrome = os.environ.get("CHROME")
    if chrome:
        subprocess.run([chrome, "--headless", "--no-sandbox", f"--print-to-pdf={out}", "--no-pdf-header-footer",
                        html.as_uri()], check=True)
    else:
        js = HERE / "_print.js"
        js.write_text(PRINT_JS)
        subprocess.run(["node", str(js), str(html), str(out), title], check=True, cwd=str(HERE))
        js.unlink()
    html.unlink()
    return out


if __name__ == "__main__":
    want = sys.argv[1:] or list(SOURCES)
    for src, (out, lang) in DOCS.items():
        if lang in want and (HERE / src).exists():
            print(build(src, out, lang))
