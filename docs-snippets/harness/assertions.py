"""Assertion helpers. Every helper counts, so a step with zero assertions fails (honesty check)."""
import re

from . import recorder


def _count():
    rec = recorder.current()
    rec.assertions += 1
    if rec.started:
        rec.after_snippet_assertions += 1


def ok(condition, message='condition is false'):
    _count()
    if not condition:
        raise AssertionError(message)


def eq(actual, expected, message=''):
    _count()
    if actual != expected:
        raise AssertionError(f'{message} expected {expected!r}, got {actual!r}'.strip())


def contains(collection, item, message=''):
    _count()
    if item not in collection:
        raise AssertionError(f'{message} {item!r} not in {collection!r}'.strip())


def not_contains(collection, item, message=''):
    _count()
    if item in collection:
        raise AssertionError(f'{message} {item!r} unexpectedly in {collection!r}'.strip())


def timetoken(value, message='timetoken'):
    """A timetoken is a string of 17 digits (publish) or a digit string for older values."""
    _count()
    if not isinstance(value, (str, int)) or not re.fullmatch(r'\d{16,19}', str(value)):
        raise AssertionError(f'{message}: {value!r} is not a timetoken')


def raises(exc_type, fn, *args, match=None, **kwargs):
    _count()
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        if match and not re.search(match, str(e)):
            raise AssertionError(f'error {e!r} does not match {match!r}')
        return e
    raise AssertionError(f'{exc_type.__name__} was not raised')
