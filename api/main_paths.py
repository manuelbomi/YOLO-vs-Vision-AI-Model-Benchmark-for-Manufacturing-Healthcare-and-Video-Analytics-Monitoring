"""Shared path constants. Split out from main.py so route modules can import
them without a circular import (main.py imports the routers, so the routers
can't import main.py back)."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = REPO_ROOT / "data" / "samples"
