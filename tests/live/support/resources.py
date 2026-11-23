"""The literal resource names the live tier uses. DATA ONLY, plus the merge of the per-page lists.

The tests use the names the docs show, so the names are fixed, shared and persistent. The janitor (janitor.py) cleans
exactly what is listed, before and after every run, and nothing else. It never lists a keyset and deletes what it
finds.

Where the names live:
  GLOBAL_NAMES       names that many pages use (ported from the old harness names.REGISTERED)
  shared/<page>.py   NAMES, the names of one page (ported from the old REGISTERED_NAMES lists and the old
                     names.with_suffix calls outside the markers)
  PUSH_DEVICES       device tokens registered by the push samples: the FCM token and the APNs token (APNS2_DEVICE)

The old suite never classified the names by kind, so for now every listed name is cleaned as a channel (history and
files), a channel group, an App Context user and an App Context channel (with the memberships between listed names).
Classifying the names per kind, as the JavaScript resources.ts does, is part of plan Phase 4 step 2.
"""
import importlib
import pkgutil

GLOBAL_NAMES = [
    'my_channel',
    'my_channel_2',
    'my-channel',
    'ch1',
    'ch2',
    'ch3',
    'cg1',
    'my_group',
    'my_user',
    'my_user_id',
    'my_uuid',
    'my_custom_user',
    'my_authorized_uuid',
]

# The APNs device token the push samples show (64 hex characters, like a real token). It is fixed, so the janitor
# cleans it on every gateway.
APNS2_DEVICE = '5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a'
PUSH_DEVICES = ['deviceId', APNS2_DEVICE]
PUSH_TOPIC = 'myapptopic'


def page_names():
    """{page module name: NAMES} for every shared/<page>.py."""
    import shared
    out = {}
    for info in pkgutil.iter_modules(shared.__path__):
        module = importlib.import_module(f'shared.{info.name}')
        out[info.name] = list(getattr(module, 'NAMES', []))
    return out


def all_names():
    names = set(GLOBAL_NAMES)
    for listed in page_names().values():
        names.update(listed)
    return sorted(names)


def problems():
    """Shape check used by the lint: names are non-empty strings without the old run suffix marker."""
    found = []
    for page, listed in sorted(page_names().items()):
        for name in listed:
            if not isinstance(name, str) or not name:
                found.append(f'shared/{page}.py: NAMES holds a non-string or empty entry {name!r}')
            elif '-dsn-' in name:
                found.append(f'shared/{page}.py: {name!r} carries the old run suffix')
    return found
