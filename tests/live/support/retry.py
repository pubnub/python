"""retry_transient(fn): retries a call outside the snippet markers when the failure is transient (5xx, 429, timeout,
network). Never retries 4xx and never an AssertionError. A retried write can be stored twice, so tests that count
stored messages use seed_publish plus settle_seeded (history.py).

PubNubException carries status (PNStatus with category) and get_status_code() (pubnub/exceptions.py). asyncio calls
return a PubNubAsyncioException instead of raising, so a returned one counts as a failure here.
"""
import asyncio
import time

from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubAsyncioException, PubNubException

TRANSIENT_CATEGORIES = {PNStatusCategory.PNTimeoutCategory, PNStatusCategory.PNNetworkIssuesCategory}


def _transport_errors():
    errors = []
    try:
        import httpx
        errors.append(httpx.TransportError)
    except ImportError:
        pass
    try:
        import requests
        errors.append(requests.ConnectionError)
    except ImportError:
        pass
    try:
        import aiohttp
        errors.append(aiohttp.ClientConnectionError)
    except ImportError:
        pass
    return tuple(errors)


TRANSPORT_ERRORS = _transport_errors()


def status_code(error):
    if isinstance(error, PubNubException):
        return error.get_status_code() or getattr(getattr(error, 'status', None), 'status_code', None)
    if isinstance(error, PubNubAsyncioException):
        return getattr(error.status, 'status_code', None)
    return None


def category(error):
    return getattr(getattr(error, 'status', None), 'category', None)


def is_transient(error):
    if isinstance(error, AssertionError):
        return False
    if isinstance(error, TRANSPORT_ERRORS):
        return True
    code = status_code(error)
    if code:
        return code >= 500 or code == 429
    cat = category(error)
    if cat in TRANSIENT_CATEGORIES:
        return True
    return cat == PNStatusCategory.PNUnknownCategory and isinstance(error, (PubNubException, PubNubAsyncioException))


def retry_transient(fn, attempts=3, pause=1.0, label='call'):
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as error:
            if attempt == attempts or not is_transient(error):
                raise
            print(f'retry_transient: {label} attempt {attempt} failed ({type(error).__name__} {status_code(error)})')
            time.sleep(pause * attempt)


async def aretry_transient(fn, attempts=3, pause=1.0, label='call'):
    """fn is a coroutine function. A returned PubNubAsyncioException is raised, so it is retried or reported."""
    for attempt in range(1, attempts + 1):
        try:
            result = await fn()
            if isinstance(result, PubNubAsyncioException):
                raise result
            return result
        except Exception as error:
            if attempt == attempts or not is_transient(error):
                raise
            print(f'retry_transient: {label} attempt {attempt} failed ({type(error).__name__} {status_code(error)})')
            await asyncio.sleep(pause * attempt)
