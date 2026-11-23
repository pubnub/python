"""Preflight: fails fast with the name of every missing keyset feature, before any test runs.

1. Admin API check (read only). With PUBNUB_ADMIN_API_KEY and a keyset id per role (DOCS_SNIPPETS_OPEN_KEYSET_ID,
   DOCS_SNIPPETS_PAM_KEYSET_ID) it reads GET /v2/keysets/{id} and /v2/keysets/{id}/config, confirms that the keyset of
   that id holds the role's subscribe key, and names every feature the role lacks. Without the key or the id the role
   is skipped here (a note says so) and only the probes below run.
2. Live probes on the open keyset: publish (keys and network), fetch_messages (Message Persistence), delete_messages
   on an empty range (Delete-From-History) and here_now (Presence).

Only feature names and flags are printed, never a key value. The PubNub-Version header follows the JavaScript tier
(2026-09-17). The old harness sent 2026-11-06 and listed every keyset (plan D15).
"""
import os
import time

import requests

from . import env, redact

BASE = 'https://admin-api.pubnub.com/v2/keysets'
VERSION = '2026-09-17'
SUBSCRIBE_ENV = {'open': 'SUBSCRIBE_KEY', 'pam': 'PAM_SUBSCRIBE_KEY'}


def _tracks_everything(rules):
    return any(r.get('pattern') == '*' and (r.get('tracking') or {}).get('enabled') for r in (rules or []))


# role -> [(feature name, path in the config, predicate)]
REQUIRED = {
    'open': [
        ('Message Persistence', ('messagePersistence', 'enabled'), lambda v: v is True),
        ('Message Persistence: Delete-From-History', ('messagePersistence', 'deleteFromHistory'), lambda v: v is True),
        ('Message Persistence: retention of at least 1 day', ('messagePersistence', 'retention'), lambda v: bool(v)),
        ('Presence', ('presence', 'enabled'), lambda v: v is True),
        ('Presence: tracking rule for *', ('presence', 'rules'), _tracks_everything),
        ('App Context', ('appContext', 'enabled'), lambda v: v is True),
        ('App Context: user metadata events', ('appContext', 'userMetadataEvents'), lambda v: v is True),
        ('App Context: channel metadata events', ('appContext', 'channelMetadataEvents'), lambda v: v is True),
        ('App Context: membership events', ('appContext', 'membershipEvents'), lambda v: v is True),
        ('App Context: referential integrity off', ('appContext', 'referentialIntegrity'), lambda v: not v),
        ('App Context: get all user metadata allowed', ('appContext', 'disallowGetAllUserMetadata'), lambda v: not v),
        ('App Context: get all channel metadata allowed', ('appContext', 'disallowGetAllChannelMetadata'),
         lambda v: not v),
        ('Files', ('files', 'enabled'), lambda v: v is True),
        ('Stream Controller', ('streamController', 'enabled'), lambda v: v is True),
        ('Stream Controller: wildcard subscribe', ('streamController', 'wildcardSubscribe'), lambda v: v is True),
        ('No Access Manager on the open keyset', ('accessManager', 'enabled'), lambda v: not v),
    ],
    'pam': [
        ('Access Manager', ('accessManager', 'enabled'), lambda v: v is True),
        ('Access Manager: token revocation', ('accessManager', 'tokenRevoke'), lambda v: v is True),
        ('Message Persistence', ('messagePersistence', 'enabled'), lambda v: v is True),
        # The janitor deletes the history of every resource name on this keyset too (HTTP 403 without it).
        ('Message Persistence: Delete-From-History', ('messagePersistence', 'deleteFromHistory'), lambda v: v is True),
        ('Presence', ('presence', 'enabled'), lambda v: v is True),
    ],
}


def _get(url):
    headers = {'Authorization': env.require('admin')['PUBNUB_ADMIN_API_KEY'], 'PubNub-Version': VERSION}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def missing_features(role, config):
    found = []
    for label, (group, key), ok in REQUIRED[role]:
        value = (config.get(group) or {}).get(key)
        if not ok(value):
            found.append(f'{role}: {label} ({group}.{key} = {value!r})')
    return found


def read_features(role):
    """('skipped' | 'read' | 'error', detail or config)."""
    if env.missing('admin'):
        return 'skipped', 'PUBNUB_ADMIN_API_KEY is not set'
    keyset_id = env.keyset_id(role)
    if not keyset_id:
        return 'skipped', f'{env.KEYSET_IDS[role]} is not set'
    if env.missing(role):
        return 'skipped', f'role {role} has no keys'
    try:
        keyset = _get(f'{BASE}/{keyset_id}')
        sub = (keyset.get('keyset') or keyset).get('subscribeKey')
        if sub != os.environ[SUBSCRIBE_ENV[role]]:
            return 'error', f'keyset {keyset_id} does not hold the subscribe key of role {role}'
        return 'read', _get(f'{BASE}/{keyset_id}/config')
    except Exception as error:
        return 'error', redact.scrub(f'{type(error).__name__}: {error}')


def probe_open_keyset(presence_vouched):
    from pubnub.pubnub import PubNub
    from .clients import config
    problems = []
    client = PubNub(config('open', 'preflight'))
    channel = f'preflight-{int(time.time())}'
    try:
        for label, call in (
            ('publish (keys and network)', lambda: client.publish().channel(channel).message('preflight').sync()),
            ('Message Persistence (fetch_messages)', lambda: client.fetch_messages().channels([channel]).sync()),
            ('Delete-From-History (empty range)',
             lambda: client.delete_messages().channel(channel).start(1).end(2).sync()),
        ):
            try:
                call()
            except Exception as error:
                problems.append(redact.scrub(f'open: probe {label} failed: {error}'))
        if not presence_vouched:
            try:
                client.here_now().channels([channel]).sync()
            except Exception as error:
                problems.append(redact.scrub(f'open: probe Presence (here_now) failed: {error}'))
    finally:
        client.stop()
    return problems


def run(roles=None):
    """Returns (notes, problems)."""
    notes, problems = [], []
    vouched = False
    for role in roles or env.KEYSET_ROLES:
        if env.missing(role):
            continue
        status, detail = read_features(role)
        if status == 'read':
            problems += missing_features(role, detail)
            vouched = vouched or (role == 'open' and (detail.get('presence') or {}).get('enabled') is True)
        elif status == 'skipped':
            notes.append(f'{role}: Admin API feature check skipped ({detail})')
        else:
            problems.append(f'{role}: Admin API feature check failed: {detail}')
    if not env.missing('open'):
        problems += probe_open_keyset(vouched)
    return notes, problems


def main(argv=()):
    env.load()
    notes, problems = run()
    for note in notes:
        print('preflight:', note)
    for problem in problems:
        print('preflight: missing:', problem)
    print('preflight:', 'keyset features ok' if not problems else f'{len(problems)} problems')
    return 1 if problems else 0
