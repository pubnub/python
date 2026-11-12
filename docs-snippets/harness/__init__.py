"""Harness for the live docs snippet tests. See ../README.md."""
import sys
from pathlib import Path

# Test the checkout, never an installed build: put the repository root first on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
