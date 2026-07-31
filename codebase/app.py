# codebase/app.py
"""
Entry point for Hackathon Codebase submission.
Runs the NiceGUI Discord Student Assistant application from frontend/main.py
"""

import sys
import os

# Add frontend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'frontend'))

from main import main, ui

if __name__ in {"__main__", "__mp_main__"}:
    main()
    ui.run(title="Trợ lý Học viên Discord — Prototype NiceGUI", port=8080, reload=False, dark=True)
