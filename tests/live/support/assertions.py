"""Assertion helpers. Plain functions that raise AssertionError, no recorder: the marker lint (rule H2) proves
statically that every test asserts after its snippet.

The asyncio rule: `await endpoint.future()` returns a PubNubAsyncioException instead of raising
(pubnub/pubnub_asyncio.py, request_future), so asyncio tests check the envelope with assert_ok().
"""
import re

from pubnub.exceptions import PubNubAsyncioException, PubNubException


def ok(condition, message='condition is false'):
    if not condition:
        raise AssertionError(message)


def eq(actual, expected, message=''):
    if actual != expected:
        raise AssertionError(f'{message} expected {expected!r}, got {actual!r}'.strip())


def contains(collection, item, message=''):
    if item not in collection:
        raise AssertionError(f'{message} {item!r} not in {collection!r}'.strip())


def not_contains(collection, item, message=''):
    if item in collection:
        raise AssertionError(f'{message} {item!r} unexpectedly in {collection!r}'.strip())


def timetoken(value, message='timetoken'):
    """A timetoken is a string of 17 digits (publish) or a digit string for older values."""
    if not isinstance(value, (str, int)) or not re.fullmatch(r'\d{16,19}', str(value)):
        raise AssertionError(f'{message}: {value!r} is not a timetoken')


assert_timetoken = timetoken


def raises(exc_type, fn, *args, match=None, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type as e:
        if match and not re.search(match, str(e)):
            raise AssertionError(f'error {e!r} does not match {match!r}')
        return e
    raise AssertionError(f'{exc_type.__name__} was not raised')


def assert_ok(envelope, message='call failed'):
    """An envelope of .sync(), .future() or a pn_async callback status is not an error. Returns the envelope."""
    if isinstance(envelope, PubNubAsyncioException):
        raise AssertionError(f'{message}: {envelope}')
    status = getattr(envelope, 'status', envelope)
    if status is not None and hasattr(status, 'is_error') and status.is_error():
        raise AssertionError(f'{message}: {getattr(status, "error_data", None)}')
    return envelope


def raises_pubnub(fn, *args, status_code=None, category=None, **kwargs):
    """fn raises PubNubException (sync) with the given status code or status category. Returns the exception."""
    try:
        fn(*args, **kwargs)
    except PubNubException as e:
        if status_code is not None and e.get_status_code() != status_code:
            raise AssertionError(f'expected status code {status_code}, got {e.get_status_code()}: {e}')
        if category is not None and getattr(getattr(e, 'status', None), 'category', None) != category:
            raise AssertionError(f'expected category {category}, got {getattr(e.status, "category", None)}')
        return e
    raise AssertionError('PubNubException was not raised')


def assert_server_time(value, slack_seconds=600):
    """A server time in 10 ns units close to this machine's clock."""
    import time
    timetoken(value, 'server time')
    if abs(int(value) / 1e7 - time.time()) > slack_seconds:
        raise AssertionError(f'server time {value} is more than {slack_seconds}s away from the local clock')
