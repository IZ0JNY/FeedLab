# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Ivan De Cesaris, IZ0JNY
"""EMELab entry point for the desktop program (python -m feedlab.desktop --app emelab) and for
`streamlit run emelab_main.py` on your PC."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT).startswith("/mount/src/"):            # Streamlit Community Cloud checkout
    import streamlit as st
    st.error("EMELab non è disponibile come app web: scarica il programma per Windows da "
             "https://github.com/IZ0JNY/FeedLab/releases")
    st.stop()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "feedlab" / "emelab" / "app.py"), run_name="__main__")
