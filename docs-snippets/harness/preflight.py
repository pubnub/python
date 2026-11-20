"""Preflight: reads the keyset configuration through the Admin API (read only) and names every missing feature.

Only the feature names and flags are printed, never a key value. The Admin API key is used here and nowhere else.
"""
import os
import sys

import requests

from . import env

BASE = 'https://admin-api.pubnub.com'
VERSION = '2026-11-06'

# role -> (label, [(feature name, path in the config, predicate)])
REQUIRED = {
    'open': [
        ('Message Persistence', ('messagePersistence', 'enabled'), lambda v: v is True),
        ('Message Persistence: Delete-From-History', ('messagePersistence', 'deleteFromHistory'), lambda v: v is True),
        ('Message Persistence: retention of at least 1 day', ('messagePersistence', 'retention'), lambda v: bool(v)),
        ('Presence', ('presence', 'enabled'), lambda v: v is True),
        ('Presence: tracking rule for *', ('presence', 'rules'), lambda v: _tracks_everything(v)),
        ('App Context', ('appContext', 'enabled'), lambda v: v is True),
        ('App Context: user metadata events', ('appContext', 'userMetadataEvents'), lambda v: v is True),
        ('App Context: channel metadata events', ('appContext', 'channelMetadataEvents'), lambda v: v is True),
        ('App Context: membership events', ('appContext', 'membershipEvents'), lambda v: v is True),
        ('App Context: referential integrity off', ('appContext', 'referentialIntegrity'), lambda v: not v),
        ('Files', ('files', 'enabled'), lambda v: v is True),
        ('Stream Controller', ('streamController', 'enabled'), lambda v: v is True),
        ('Stream Controller: wildcard subscribe', ('streamController', 'wildcardSubscribe'), lambda v: v is True),
        ('No Access Manager on the open keyset', ('accessManager', 'enabled'), lambda v: not v),
    ],
    'pam': [
        ('Access Manager', ('accessManager', 'enabled'), lambda v: v is True),
        ('Access Manager: token revocation', ('accessManager', 'tokenRevoke'), lambda v: v is True),
        ('Message Persistence', ('messagePersistence', 'enabled'), lambda v: v is True),
        ('Presence', ('presence', 'enabled'), lambda v: v is True),
    ],
}


def _tracks_everything(rules):
    return any(r.get('pattern') == '*' and (r.get('tracking') or {}).get('enabled') for r in (rules or []))


SUBSCRIBE_ENV = {'open': 'SUBSCRIBE_KEY', 'pam': 'PAM_SUBSCRIBE_KEY'}


def _get(path, **params):
    headers = {'Authorization': os.environ['PUBNUB_ADMIN_API_KEY'], 'PubNub-Version': VERSION}
    response = requests.get(BASE + path, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def keyset_for(role):
    sub = os.environ[SUBSCRIBE_ENV[role]]
    page = 1
    while True:
        data = _get('/v2/keysets', limit=100, page=page)
        for item in data['keysets']:
            if item.get('subscribeKey') == sub:
                return item['id'], item.get('name', '')
        if page * data['limit'] >= data['total']:
            return None, ''
        page += 1


def check(role):
    """Return (keyset name, [missing feature names])."""
    if env.missing('admin'):
        raise RuntimeError('preflight needs PUBNUB_ADMIN_API_KEY')
    keyset_id, name = keyset_for(role)
    if keyset_id is None:
        return '', ['keyset not found for the loaded subscribe key']
    config = _get(f'/v2/keysets/{keyset_id}/config')
    missing = []
    for label, (group, key), ok in REQUIRED[role]:
        value = (config.get(group) or {}).get(key)
        if not ok(value):
            missing.append(f'{label} ({group}.{key} = {value!r})')
    return name, missing


def main(argv=None):
    env.load()
    roles = [r for r in ('open', 'pam') if not env.missing(r)]
    bad = 0
    for role in roles:
        name, missing = check(role)
        print(f'preflight {role} ({name}): ' + ('ok' if not missing else f'{len(missing)} missing'))
        for m in missing:
            print('  missing:', m)
        bad += len(missing)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
