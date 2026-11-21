"""Launcher: `feedlab-gui` starts the Streamlit interface in the default browser."""
import subprocess
import sys
from pathlib import Path


def main():
    app = Path(__file__).with_name("app.py")
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)] + sys.argv[1:]))


if __name__ == "__main__":
    main()
