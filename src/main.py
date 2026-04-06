"""
PC Manager Lite - Main Entry Point
A lightweight PC management utility
"""

import sys
import os

# Add src directory to path
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from app import PCManagerApp

if __name__ == "__main__":
    app = PCManagerApp()
    app.run()
