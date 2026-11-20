"""Run suffix and the registered names that staging rewrites.

Every channel, group, user and file name carries a base36 run suffix and the fixed marker "dsn", so the janitor can
recognise leftovers and never touches a name another run could use.
"""
import os
import random
import zlib
import string
import time

MARKER = 'dsn'
_BASE36 = string.digits + string.ascii_lowercase


def _b36(n):
    out = ''
    while n:
        n, r = divmod(n, 36)
        out = _BASE36[r] + out
    return out or '0'


def run_suffix():
    """Same value for the whole process. CI sets DOCS_SNIPPETS_RUN_ID to include run id, attempt and shard."""
    existing = os.environ.get('DOCS_SNIPPETS_SUFFIX')
    if existing:
        return existing
    base = os.environ.get('DOCS_SNIPPETS_RUN_ID') or f'{_b36(int(time.time()))}{"".join(random.choices(_BASE36, k=3))}'
    value = f'{MARKER}-{base}'.lower()
    os.environ['DOCS_SNIPPETS_SUFFIX'] = value
    return value


_tag = ''


def test_tag(relpath, func):
    """Short tag of one step. Staging and the runtime derive it the same way, so every step gets its own names and a
    client that lingers in presence after a step can never show up in the next one."""
    return format(zlib.crc32(f'{relpath}:{func}'.encode()), '08x')[:6]


def set_tag(tag):
    global _tag
    _tag = tag


def with_suffix(name):
    return f'{name}-{run_suffix()}' + (f'-{_tag}' if _tag else '')


# Literal names the docs code uses. Staging appends the run suffix to these string literals in the staged copy only.
REGISTERED = [
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
