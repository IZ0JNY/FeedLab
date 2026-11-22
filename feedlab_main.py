"""FeedLab entry point for the desktop program (feedlab.desktop) and for `streamlit run feedlab_main.py` on your PC.

FeedLab is distributed as a Windows program only: it is not meant to be hosted as a web app, and it refuses to
start on Streamlit Community Cloud.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT).startswith("/mount/src/"):            # Streamlit Community Cloud checkout
    import streamlit as st
    st.error("FeedLab non è disponibile come app web: scarica il programma per Windows da "
             "https://github.com/IZ0JNY/mwFeedDesign/releases")
    st.stop()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_path(str(ROOT / "feedlab" / "app.py"), run_name="__main__")
