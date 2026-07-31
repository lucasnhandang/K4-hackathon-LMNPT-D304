"""Chạy cả Backend (FastAPI) và Frontend (NiceGUI) cùng lúc."""

import subprocess
import sys
import time
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

def run_backend():
    return subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=os.path.join(ROOT, "codebase", "backend"),
    )

def run_frontend():
    return subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=os.path.join(ROOT, "frontend"),
    )

if __name__ == "__main__":
    print("🚀 Starting Backend (port 8000)...")
    be = run_backend()

    print("🎨 Starting Frontend (port 8080)...")
    fe = run_frontend()

    print("\n✅ Both services running!")
    print("   Backend  → http://localhost:8000")
    print("   Frontend → http://localhost:8080")
    print("   Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹  Stopping...")
        be.terminate()
        fe.terminate()
        be.wait()
        fe.wait()
        print("Done.")
