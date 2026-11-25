"""Shared support package of the live tier (tests/live/README.md). Serves the sync and the asyncio docset.

Importing it puts the repository root first on the import path, so the tier always tests the checkout and never an
installed build of the SDK.
"""
import sys
from pathlib import Path

LIVE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = LIVE_DIR.parent.parent
LIVE_REL = 'tests/live'
DOCSETS = ('sync', 'asyncio')

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
