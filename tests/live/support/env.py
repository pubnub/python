"""Key loader. Fixed env names, grouped in roles. Real env vars win over the optional env file.

The file is LIVE_ENV_FILE, or tests/live/.env.local when that is not set. The loader never falls back to demo keys and
prints only "set" or "missing" per role. Role variable names match the JavaScript live tier.
"""
import os
from pathlib import Path

from . import LIVE_DIR, redact

ROLES = {
    'open': ['PUBLISH_KEY', 'SUBSCRIBE_KEY'],
    'pam': ['PAM_PUBLISH_KEY', 'PAM_SUBSCRIBE_KEY', 'PAM_SECRET_KEY'],
    # Read only Admin API access for the preflight. No test uses it.
    'admin': ['PUBNUB_ADMIN_API_KEY'],
}
KEYSET_ROLES = ('open', 'pam')

# Not secret: keyset ids for the Admin API feature read of the preflight (repository variables in CI).
KEYSET_IDS = {'open': 'DOCS_SNIPPETS_OPEN_KEYSET_ID', 'pam': 'DOCS_SNIPPETS_PAM_KEYSET_ID'}

# Switches, read from the real environment or the env file.
SWITCHES = ('LIVE_JANITOR', 'LIVE_PREFLIGHT', 'LIVE_GROUP')

DEFAULT_ENV_FILE = LIVE_DIR / '.env.local'

_loaded = False


def _read_env_file(path):
    values = {}
    p = Path(path)
    if not p.is_file():
        return values
    for raw in p.read_text().splitlines():
        line = raw.strip()
        if line.startswith('export '):
            line = line[len('export '):].strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, _, value = line.partition('=')
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def known_names():
    return {n for names in ROLES.values() for n in names} | set(KEYSET_IDS.values()) | set(SWITCHES)


def env_file():
    return Path(os.environ.get('LIVE_ENV_FILE') or DEFAULT_ENV_FILE)


def load():
    """Fill os.environ from the env file without overriding real env vars. Registers every key with redact."""
    global _loaded
    if _loaded:
        return
    for name, value in _read_env_file(env_file()).items():
        if name in known_names() and not os.environ.get(name):
            os.environ[name] = value
    for names in ROLES.values():
        for name in names:
            redact.register(os.environ.get(name, ''))
    _loaded = True


def missing(role):
    load()
    return [name for name in ROLES[role] if not os.environ.get(name)]


def has(role):
    return not missing(role)


def status():
    """One line per role: 'set' or 'missing: NAME, NAME'. Never prints a value."""
    load()
    lines = []
    for role in ROLES:
        gone = missing(role)
        lines.append(f'{role}: ' + ('set' if not gone else 'missing: ' + ', '.join(gone)))
    return lines


def require(role):
    """Return the env values of a role. A missing key fails with the exact names, there is no fallback."""
    gone = missing(role)
    if gone:
        names = ', '.join(gone)
        raise RuntimeError(f'role {role!r} is missing env: {names}. Set them in the environment or in '
                           'tests/live/.env.local (see .env.example).')
    return {name: os.environ[name] for name in ROLES[role]}


def keyset_id(role):
    load()
    return os.environ.get(KEYSET_IDS[role], '').strip()


def switch_on(name):
    """LIVE_JANITOR and LIVE_PREFLIGHT are on unless set to off."""
    load()
    return os.environ.get(name, '').strip().lower() != 'off'


def use_open_keys(pnconfig):
    """Hidden line helper: put the open keyset keys on a sample's own PNConfiguration."""
    keys = require('open')
    pnconfig.publish_key = keys['PUBLISH_KEY']
    pnconfig.subscribe_key = keys['SUBSCRIBE_KEY']
    return pnconfig


def use_pam_keys(pnconfig, secret=True):
    """Hidden line helper: put the Access Manager keyset keys on a sample's own PNConfiguration."""
    keys = require('pam')
    pnconfig.publish_key = keys['PAM_PUBLISH_KEY']
    pnconfig.subscribe_key = keys['PAM_SUBSCRIBE_KEY']
    if secret:
        pnconfig.secret_key = keys['PAM_SECRET_KEY']
    return pnconfig
