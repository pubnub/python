"""Root conftest of the live tier. Thin: the hooks and fixtures live in support/hooks.py."""
import sys
from pathlib import Path

# "import support" and "import shared" work without pythonpath too (for example under -p no:python_path).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import support  # noqa: E402,F401  (puts the repository root first on the import path)

pytest_plugins = ['support.hooks', 'support.explain']
