"""Key loader. Fixed env names, grouped in roles. Real env vars win over the optional env file.

The loader never falls back to demo keys and prints only "set" or "missing" per role.
"""
import os
from pathlib import Path

from . import redact

ROLES = {
    'open': ['PUBLISH_KEY', 'SUBSCRIBE_KEY'],
    'pam': ['PAM_PUBLISH_KEY', 'PAM_SUBSCRIBE_KEY', 'PAM_SECRET_KEY'],
    # Read only Admin API access for the preflight. No test step uses it.
    'admin': ['PUBNUB_ADMIN_API_KEY'],
}

_loaded = False


def _read_env_file(path):
    values = {}
    p = Path(path)
    if not p.is_file():
        return values
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, _, value = line.partition('=')
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def load():
    """Fill os.environ from DOCS_SNIPPETS_ENV_FILE (or docs-snippets/.env.local) without overriding real env vars."""
    global _loaded
    if _loaded:
        return
    path = os.environ.get('DOCS_SNIPPETS_ENV_FILE') or str(Path(__file__).resolve().parent.parent / '.env.local')
    for name, value in _read_env_file(path).items():
        if name in {n for names in ROLES.values() for n in names} and not os.environ.get(name):
            os.environ[name] = value
    for names in ROLES.values():
        for name in names:
            redact.register(os.environ.get(name, ''))
    _loaded = True


def missing(role):
    load()
    return [name for name in ROLES[role] if not os.environ.get(name)]


def status():
    """One line per role: 'set' or 'missing: NAME, NAME'. Never prints a value."""
    load()
    lines = []
    for role in ROLES:
        gone = missing(role)
        lines.append(f'{role}: ' + ('set' if not gone else 'missing: ' + ', '.join(gone)))
    return lines


def require(role):
    """Return the env values of a role. A missing key fails the run with the exact names, there is no fallback."""
    gone = missing(role)
    if gone:
        raise RuntimeError(f'role {role!r} is missing env: ' + ', '.join(gone))
    return {name: os.environ[name] for name in ROLES[role]}
