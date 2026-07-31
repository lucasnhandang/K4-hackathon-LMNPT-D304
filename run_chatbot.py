"""Shortcut để chạy chatbot từ root directory."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "codebase", "backend"))

from cli import main

if __name__ == "__main__":
    main()
