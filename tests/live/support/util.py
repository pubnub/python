"""Unique names for things a test asserts on but does not own (the docs names stay literal)."""
import secrets
import string
import time

_BASE36 = string.digits + string.ascii_lowercase


def _b36(n):
    out = ''
    while n:
        n, r = divmod(n, 36)
        out = _BASE36[r] + out
    return out or '0'


def unique_suffix():
    """Base36 time plus 6 random characters."""
    return _b36(int(time.time() * 1000)) + ''.join(secrets.choice(_BASE36) for _ in range(6))


def unique(base):
    return f'{base}-{unique_suffix()}'
