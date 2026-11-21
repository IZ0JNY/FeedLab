"""Entry point for hosted deployments (Streamlit Community Cloud, Hugging Face Spaces, Docker).

Runs feedlab/app.py with the repository root on sys.path, so the package works without `pip install`.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "feedlab" / "app.py"), run_name="__main__")
